from __future__ import annotations

import time
from copy import deepcopy

from app.agent.planner import plan_next_action
from app.agent.state import AgentState, new_agent_state
from app.agent.tools import ToolRegistry


class ConversationStore:
    def __init__(self):
        self._states: dict[str, AgentState] = {}

    def get(self, conversation_id: str) -> AgentState | None:
        state = self._states.get(conversation_id)
        return deepcopy(state) if state else None

    def set(self, state: AgentState) -> None:
        self._states[state["conversation_id"]] = deepcopy(state)


class AgentRuntime:
    def __init__(
        self,
        tools: ToolRegistry,
        store: ConversationStore | None = None,
        max_steps: int = 8,
    ):
        self.tools = tools
        self.store = store or ConversationStore()
        self.max_steps = max_steps

    async def run(
        self,
        user_input: str,
        conversation_id: str,
        image_url: str | None = None,
        preferences: list[str] | None = None,
    ) -> dict:
        previous = self.store.get(conversation_id)
        state = new_agent_state(user_input, conversation_id, image_url, preferences)
        if previous:
            if not state["ingredients"]:
                state["ingredients"] = list(previous["ingredients"])
            if preferences is None:
                state["preferences"] = list(previous["preferences"])

        while state["step_count"] < self.max_steps:
            action = plan_next_action(state)
            if action.kind == "ask_user":
                state["events"].append({
                    "type": "ask_user",
                    "message": action.message,
                    "step": state["step_count"],
                })
                self.store.set(state)
                return self._result(state, "needs_input", "ask_user")

            if action.kind == "finish":
                state["events"].append({
                    "type": "final",
                    "message": self._build_reply(state),
                    "step": state["step_count"],
                })
                self.store.set(state)
                return self._result(state, "success", "complete")

            state["events"].append({
                "type": "plan",
                "tool": action.tool,
                "reason": action.reason,
                "step": state["step_count"],
            })
            state["events"].append({
                "type": "tool_start",
                "tool": action.tool,
                "step": state["step_count"],
            })
            started = time.perf_counter()
            try:
                tool = self.tools.get(action.tool or "")
                output = await tool(state)
                self._merge_tool_output(state, action.tool or "", output)
                state["events"].append({
                    "type": "tool_result",
                    "tool": action.tool,
                    "status": "success",
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "summary": self._summarize_output(action.tool or "", output),
                    "step": state["step_count"],
                })
            except Exception as exc:
                error = {
                    "tool": action.tool,
                    "error_code": type(exc).__name__,
                    "message": str(exc)[:200],
                }
                state["errors"].append(error)
                state["events"].append({
                    "type": "tool_result",
                    "tool": action.tool,
                    "status": "error",
                    **error,
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "step": state["step_count"],
                })
                self.store.set(state)
                return self._result(state, "degraded", "tool_error")

            state["completed_tools"].append(action.tool or "")
            state["step_count"] += 1

        state["errors"].append({
            "tool": "runtime",
            "error_code": "MAX_STEPS",
            "message": f"Agent exceeded {self.max_steps} steps",
        })
        self.store.set(state)
        return self._result(state, "degraded", "max_steps")

    @staticmethod
    def _merge_tool_output(state: AgentState, tool: str, output: dict) -> None:
        if tool == "sense":
            names = [
                item["name"]
                for item in output.get("ingredients", [])
                if isinstance(item, dict) and item.get("name")
            ]
            state["ingredients"] = list(dict.fromkeys(state["ingredients"] + names))
        elif tool == "decision":
            state["recipes"] = output.get("recipes", [])
        elif tool == "task":
            state["shopping_list"] = output.get("shopping_list", [])
        elif tool == "nutrition":
            state["nutrition"] = output
        elif tool == "quality":
            state["quality"] = output
        elif tool == "guide":
            state["guide"] = output

    @staticmethod
    def _summarize_output(tool: str, output: dict) -> dict:
        if tool == "sense":
            return {"ingredient_count": len(output.get("ingredients", []))}
        if tool == "decision":
            return {"recipe_count": len(output.get("recipes", []))}
        if tool == "task":
            return {"shopping_item_count": len(output.get("shopping_list", []))}
        return {"has_result": bool(output)}

    @staticmethod
    def _build_reply(state: AgentState) -> str:
        if state["shopping_list"]:
            return f"已完成推荐并生成 {len(state['shopping_list'])} 项购物清单。"
        if state["recipes"]:
            return f"已找到 {len(state['recipes'])} 个菜谱，优先推荐「{state['recipes'][0].get('title', '推荐菜谱')}」。"
        if state["nutrition"]:
            return "餐食营养分析已完成。"
        if state["quality"]:
            return "食材品质鉴定已完成。"
        if state["guide"]:
            return "菜品识别与文化讲解已完成。"
        return "本轮处理已完成。"

    @staticmethod
    def _result(state: AgentState, status: str, next_action: str) -> dict:
        final_message = next(
            (event["message"] for event in reversed(state["events"]) if "message" in event),
            "",
        )
        return {
            "status": status,
            "conversation_id": state["conversation_id"],
            "trace_id": state["trace_id"],
            "next_action": next_action,
            "reply": final_message,
            "intent": state["intent"],
            "ingredients": state["ingredients"],
            "recipes": state["recipes"],
            "shopping_list": state["shopping_list"],
            "nutrition": state["nutrition"],
            "quality": state["quality"],
            "guide": state["guide"],
            "events": state["events"],
            "errors": state["errors"],
            "degraded": bool(state["errors"]),
        }
