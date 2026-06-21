from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.evaluator import evaluate_hard
from app.agent.llm_planner import select_next_action
from app.agent.runtime import AgentRuntime
from app.agent.state import AgentState, new_agent_state
from app.agent.tools import ToolRegistry, execute_tool
from app.core.cache import get as cache_get, set as cache_set, make_key

logger = logging.getLogger("langgraph_agent")

CONVERSATION_TTL = 900  # 15 分钟


class GraphState(TypedDict, total=False):
    agent: AgentState
    action: dict[str, Any]
    outcome: str
    termination_reason: str


class LangGraphAgent:
    def __init__(self, tools: ToolRegistry, max_steps: int = 8):
        self.tools = tools
        self.max_steps = max_steps
        self._conversation_states: dict[str, AgentState] = {}
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(GraphState)
        builder.add_node("planner", self._planner_node)
        builder.add_node("tool", self._tool_node)
        builder.add_node("ask_user", self._ask_user_node)
        builder.add_node("evaluator", self._evaluator_node)
        builder.add_node("final", self._final_node)
        builder.add_edge(START, "planner")
        builder.add_conditional_edges(
            "planner",
            self._route_action,
            {
                "tool": "tool",
                "ask_user": "ask_user",
                "finish": "evaluator",
                "max_steps": "evaluator",
            },
        )
        builder.add_edge("tool", "planner")
        builder.add_edge("ask_user", END)
        builder.add_edge("evaluator", "final")
        builder.add_edge("final", END)
        return builder.compile(checkpointer=InMemorySaver())

    def _conv_cache_key(self, conversation_id: str) -> str:
        return make_key("agent", "conv", conversation_id)

    async def get_previous_state(self, conversation_id: str) -> dict | None:
        """公开方法，供路由层读取上一轮会话状态用于 MemoryContext。"""
        return await self._load_previous_state(conversation_id)

    async def _load_previous_state(self, conversation_id: str) -> dict | None:
        """从 Redis 加载上一轮会话状态，失败则回退到内存。"""
        # 先查内存
        mem = self._conversation_states.get(conversation_id)
        if mem:
            return mem
        # 再查 Redis
        cached = await cache_get(self._conv_cache_key(conversation_id))
        if cached:
            logger.info("agent_conv_redis_hit conv_id=%s", conversation_id)
            return cached
        return None

    async def _save_state(self, conversation_id: str, state: AgentState) -> None:
        """保存会话状态到内存 + Redis。"""
        # 挑选可序列化的字段
        serializable = {
            "ingredients": state.get("ingredients", []),
            "recipes": state.get("recipes", []),
            "inventory": state.get("inventory", []),
            "favorites": state.get("favorites", []),
            "recipe_check": state.get("recipe_check"),
            "preferences": state.get("preferences", []),
            "intent": state.get("intent", {}),
        }
        self._conversation_states[conversation_id] = serializable
        await cache_set(self._conv_cache_key(conversation_id), serializable, ttl=CONVERSATION_TTL)

    async def run(
        self,
        user_input: str,
        conversation_id: str,
        image_url: str | None = None,
        preferences: list[str] | None = None,
        memory_context: dict | None = None,
    ) -> dict:
        state = new_agent_state(user_input, conversation_id, image_url, preferences, memory_context)
        previous = await self._load_previous_state(conversation_id)
        if previous:
            if not state["ingredients"]:
                state["ingredients"] = list(previous.get("ingredients", []))
            state["recipes"] = list(previous.get("recipes", []))
            state["inventory"] = list(previous.get("inventory", []))
            state["favorites"] = list(previous.get("favorites", []))
            state["recipe_check"] = previous.get("recipe_check")
            if preferences is None:
                state["preferences"] = list(previous.get("preferences", []))
        result = await self.graph.ainvoke(
            {"agent": state, "action": {}, "outcome": "", "termination_reason": ""},
            config={"configurable": {"thread_id": conversation_id}},
        )
        agent_state = result["agent"]
        await self._save_state(conversation_id, agent_state)
        outcome = result.get("outcome") or "complete"
        termination_reason = result.get("termination_reason") or "GOAL_ACHIEVED"
        if outcome == "ask_user":
            status = "needs_input"
            termination_reason = "NEEDS_INPUT"
        elif agent_state["errors"]:
            status = "degraded"
            if termination_reason == "GOAL_ACHIEVED":
                termination_reason = "TOOL_ERROR"
        else:
            status = "success"
        final = AgentRuntime._result(agent_state, status, outcome, termination_reason)
        return final

    async def _planner_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        if state["step_count"] >= self.max_steps:
            state["errors"].append({
                "tool": "runtime",
                "error_code": "MAX_STEPS",
                "message": f"Agent exceeded {self.max_steps} steps",
            })
            return {
                "agent": state,
                "action": {"kind": "max_steps", "message": "已达到最大步骤数。"},
                "termination_reason": "MAX_STEPS",
            }

        action = await select_next_action(state, self.tools.describe())
        return {
            "agent": state,
            "action": {
                "kind": action.kind,
                "tool": action.tool,
                "reason": action.reason,
                "message": action.message,
                "planner_source": action.planner_source,
                "candidate_tools": action.candidate_tools or [],
                "llm_reason": action.llm_reason,
            },
        }

    @staticmethod
    def _route_action(graph_state: GraphState) -> str:
        return graph_state["action"]["kind"]

    async def _tool_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        action = graph_state["action"]
        tool_name = action["tool"]
        state["events"].append({
            "type": "plan",
            "phase": "ROUTING",
            "tool": tool_name,
            "reason": action.get("reason", ""),
            "available_skills": self.tools.names(),
            "planner_source": action.get("planner_source", "rule"),
            "candidate_tools": action.get("candidate_tools", []),
            "llm_reason": action.get("llm_reason", ""),
            "step": state["step_count"],
        })
        state["events"].append({
            "type": "tool_start",
            "phase": "EXECUTING",
            "tool": tool_name,
            "skill": AgentRuntime._skill_event_summary(self.tools.descriptor(tool_name)),
            "step": state["step_count"],
        })
        tool_result = await execute_tool(self.tools, tool_name, state)
        if tool_result.status == "success":
            AgentRuntime._merge_tool_output(state, tool_name, tool_result.output)
            state["events"].append(AgentRuntime._tool_result_event(tool_name, tool_result, state["step_count"]))
            state["completed_tools"].append(tool_name)
            state["step_count"] += 1
        else:
            error = {
                "tool": tool_name,
                "error_code": tool_result.error_code,
                "message": tool_result.message,
            }
            state["errors"].append(error)
            state["events"].append(AgentRuntime._tool_result_event(tool_name, tool_result, state["step_count"]))
            state["completed_tools"].append(tool_name)
            state["step_count"] += 1
        return {"agent": state, "action": {}}

    async def _evaluator_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        eval_result = evaluate_hard(state)
        # 取第一个 issue 的 tool 作为 evaluation event 的主 tool
        eval_tool = eval_result.issues[0].get("tool", "") if eval_result.issues else ""
        state["events"].append({
            "type": "evaluation",
            "phase": "EVALUATING",
            "tool": eval_tool,
            "verdict": eval_result.verdict,
            "issues": eval_result.issues,
            "suggestions": eval_result.suggestions,
            "step": state["step_count"],
        })
        reason = graph_state.get("termination_reason") or "GOAL_ACHIEVED"
        if eval_result.verdict == "FAIL":
            for issue in eval_result.issues:
                state["errors"].append({
                    "tool": "evaluator",
                    "error_code": issue.get("code", "EVAL_FAIL"),
                    "message": issue.get("message", ""),
                })
            reason = "TOOL_ERROR"
        await AgentRuntime._append_soft_judge_event(state)
        return {"agent": state, "termination_reason": reason}

    async def _ask_user_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        state["events"].append({
            "type": "ask_user",
            "phase": "CLARIFYING",
            "message": graph_state["action"].get("message", "请补充信息。"),
            "step": state["step_count"],
        })
        return {"agent": state, "outcome": "ask_user", "termination_reason": "NEEDS_INPUT"}

    async def _final_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        message = (
            graph_state["action"].get("message")
            or AgentRuntime._build_reply(state)
        )
        state["events"].append({
            "type": "final",
            "phase": "FINISHED",
            "message": message,
            "step": state["step_count"],
        })
        if state["errors"]:
            max_steps_err = any(e.get("error_code") == "MAX_STEPS" for e in state["errors"])
            outcome = "max_steps" if max_steps_err else "degraded"
        else:
            outcome = "complete"
        reason = graph_state.get("termination_reason")
        if not reason:
            reason = "MAX_STEPS" if outcome == "max_steps" else "GOAL_ACHIEVED"
        return {"agent": state, "outcome": outcome, "termination_reason": reason}
