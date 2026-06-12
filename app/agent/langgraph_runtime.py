from __future__ import annotations

import time
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.planner import plan_next_action
from app.agent.runtime import AgentRuntime
from app.agent.state import AgentState, new_agent_state
from app.agent.tools import ToolRegistry


class GraphState(TypedDict, total=False):
    agent: AgentState
    action: dict[str, Any]
    outcome: str


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
        builder.add_node("final", self._final_node)
        builder.add_edge(START, "planner")
        builder.add_conditional_edges(
            "planner",
            self._route_action,
            {
                "tool": "tool",
                "ask_user": "ask_user",
                "finish": "final",
                "max_steps": "final",
            },
        )
        builder.add_edge("tool", "planner")
        builder.add_edge("ask_user", END)
        builder.add_edge("final", END)
        return builder.compile(checkpointer=InMemorySaver())

    async def run(
        self,
        user_input: str,
        conversation_id: str,
        image_url: str | None = None,
        preferences: list[str] | None = None,
    ) -> dict:
        state = new_agent_state(user_input, conversation_id, image_url, preferences)
        previous = self._conversation_states.get(conversation_id)
        if previous:
            if not state["ingredients"]:
                state["ingredients"] = list(previous["ingredients"])
            state["recipes"] = list(previous["recipes"])
            if preferences is None:
                state["preferences"] = list(previous["preferences"])
        result = await self.graph.ainvoke(
            {"agent": state, "action": {}, "outcome": ""},
            config={"configurable": {"thread_id": conversation_id}},
        )
        agent_state = result["agent"]
        self._conversation_states[conversation_id] = agent_state
        outcome = result.get("outcome") or "complete"
        status = "needs_input" if outcome == "ask_user" else "degraded" if agent_state["errors"] else "success"
        return AgentRuntime._result(agent_state, status, outcome)

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
            }

        action = plan_next_action(state)
        return {
            "agent": state,
            "action": {
                "kind": action.kind,
                "tool": action.tool,
                "reason": action.reason,
                "message": action.message,
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
            "tool": tool_name,
            "reason": action.get("reason", ""),
            "step": state["step_count"],
        })
        state["events"].append({
            "type": "tool_start",
            "tool": tool_name,
            "step": state["step_count"],
        })
        started = time.perf_counter()
        try:
            output = await self.tools.get(tool_name)(state)
            AgentRuntime._merge_tool_output(state, tool_name, output)
            state["events"].append({
                "type": "tool_result",
                "tool": tool_name,
                "status": "success",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "summary": AgentRuntime._summarize_output(tool_name, output),
                "step": state["step_count"],
            })
            state["completed_tools"].append(tool_name)
            state["step_count"] += 1
        except Exception as exc:
            error = {
                "tool": tool_name,
                "error_code": type(exc).__name__,
                "message": str(exc)[:200],
            }
            state["errors"].append(error)
            state["events"].append({
                "type": "tool_result",
                "tool": tool_name,
                "status": "error",
                **error,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "step": state["step_count"],
            })
            state["completed_tools"].append(tool_name)
            state["step_count"] += 1
        return {"agent": state, "action": {}}

    async def _ask_user_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        state["events"].append({
            "type": "ask_user",
            "message": graph_state["action"].get("message", "请补充信息。"),
            "step": state["step_count"],
        })
        return {"agent": state, "outcome": "ask_user"}

    async def _final_node(self, graph_state: GraphState) -> GraphState:
        state = graph_state["agent"]
        message = (
            graph_state["action"].get("message")
            or AgentRuntime._build_reply(state)
        )
        state["events"].append({
            "type": "final",
            "message": message,
            "step": state["step_count"],
        })
        outcome = "max_steps" if state["errors"] and state["errors"][-1]["error_code"] == "MAX_STEPS" else "complete"
        return {"agent": state, "outcome": outcome}
