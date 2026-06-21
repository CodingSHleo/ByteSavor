from __future__ import annotations

from copy import deepcopy

from app.agent.evaluator import evaluate_hard
from app.agent.llm_judge import judge_agent_result
from app.agent.llm_planner import select_next_action
from app.agent.state import AgentState, new_agent_state
from app.agent.tools import SkillExecutionResult, ToolRegistry, execute_tool


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
        memory_context: dict | None = None,
    ) -> dict:
        previous = self.store.get(conversation_id)
        state = new_agent_state(user_input, conversation_id, image_url, preferences, memory_context)
        if previous:
            if not state["ingredients"]:
                state["ingredients"] = list(previous["ingredients"])
            if preferences is None:
                state["preferences"] = list(previous["preferences"])
            state["inventory"] = list(previous.get("inventory", []))
            state["favorites"] = list(previous.get("favorites", []))

        while state["step_count"] < self.max_steps:
            action = await select_next_action(state, self.tools.describe())
            if action.kind == "ask_user":
                state["events"].append({
                    "type": "ask_user",
                    "phase": "CLARIFYING",
                    "message": action.message,
                    "step": state["step_count"],
                })
                self.store.set(state)
                return self._result(state, "needs_input", "ask_user", "NEEDS_INPUT")

            if action.kind == "finish":
                return await self._finish_run(state, "complete", "GOAL_ACHIEVED")

            state["events"].append({
                "type": "plan",
                "phase": "ROUTING",
                "tool": action.tool,
                "reason": action.reason,
                "available_skills": self.tools.names(),
                "planner_source": action.planner_source,
                "candidate_tools": action.candidate_tools or [],
                "llm_reason": action.llm_reason,
                "step": state["step_count"],
            })
            state["events"].append({
                "type": "tool_start",
                "phase": "EXECUTING",
                "tool": action.tool,
                "skill": self._skill_event_summary(self.tools.descriptor(action.tool or "")),
                "step": state["step_count"],
            })
            tool_result = await execute_tool(self.tools, action.tool or "", state)
            if tool_result.status == "success":
                self._merge_tool_output(state, action.tool or "", tool_result.output)
                state["events"].append(self._tool_result_event(action.tool or "", tool_result, state["step_count"]))
            else:
                error = {
                    "tool": action.tool,
                    "error_code": tool_result.error_code,
                    "message": tool_result.message,
                }
                state["errors"].append(error)
                state["events"].append(self._tool_result_event(action.tool or "", tool_result, state["step_count"]))
                state["completed_tools"].append(action.tool or "")
                state["step_count"] += 1
                self.store.set(state)
                return await self._finish_run(state, "tool_error", "TOOL_ERROR")

            state["completed_tools"].append(action.tool or "")
            state["step_count"] += 1

        # max_steps exceeded
        state["errors"].append({
            "tool": "runtime",
            "error_code": "MAX_STEPS",
            "message": f"Agent exceeded {self.max_steps} steps",
        })
        return await self._finish_run(state, "max_steps", "MAX_STEPS")

    async def _finish_run(self, state: AgentState, outcome: str, default_reason: str) -> dict:
        """完成运行：先硬规则评估 → 再生成 final 事件 → 返回结果。
        P1-3: 统一事件顺序为 ROUTING → EXECUTING → EVALUATING → FINISHED
        """
        # 硬规则评估（在 final 之前）
        eval_result = evaluate_hard(state)
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

        reason = default_reason
        if eval_result.verdict == "FAIL":
            for issue in eval_result.issues:
                state["errors"].append({
                    "tool": "evaluator",
                    "error_code": issue.get("code", "EVAL_FAIL"),
                    "message": issue.get("message", ""),
                })
            reason = "TOOL_ERROR"
        elif outcome == "max_steps":
            pass  # reason already MAX_STEPS

        await self._append_soft_judge_event(state)

        # 生成 final 事件
        message = self._build_reply(state)
        state["events"].append({
            "type": "final",
            "phase": "FINISHED",
            "message": message,
            "step": state["step_count"],
        })

        status = "success"
        if eval_result.verdict == "FAIL":
            status = "degraded"
        elif outcome == "max_steps":
            status = "degraded"
        elif state["errors"]:
            status = "degraded"

        self.store.set(state)
        result = self._result(state, status, outcome, reason)
        return result

    @staticmethod
    async def _append_soft_judge_event(state: AgentState) -> None:
        try:
            judge = await judge_agent_result(state)
        except Exception as exc:
            state["events"].append({
                "type": "soft_judge",
                "phase": "EVALUATING",
                "verdict": "SKIPPED",
                "issues": [{"code": "JUDGE_ERROR", "message": str(exc)[:200]}],
                "suggestions": [],
                "step": state["step_count"],
            })
            return
        if judge is None:
            return
        state["events"].append({
            "type": "soft_judge",
            "phase": "EVALUATING",
            "verdict": judge.get("verdict", "WARN"),
            "scores": judge.get("scores", {}),
            "issues": judge.get("issues", []),
            "suggestions": judge.get("suggestions", []),
            "step": state["step_count"],
        })

    @staticmethod
    def _merge_tool_output(state: AgentState, tool: str, output: dict) -> None:
        if tool == "sense":
            names = [
                item["name"]
                for item in output.get("ingredients", [])
                if isinstance(item, dict) and item.get("name")
            ]
            state["ingredients"] = list(dict.fromkeys(state["ingredients"] + names))
            state["sense_result"] = output
        elif tool == "decision":
            state["recipes"] = output.get("recipes", [])
        elif tool == "task":
            state["shopping_list"] = output.get("shopping_list", [])
        elif tool == "inventory":
            state["inventory"] = output.get("items", [])
        elif tool == "favorites":
            state["favorites"] = output.get("favorites", [])
        elif tool == "recipe_check":
            state["recipe_check"] = output
            if output.get("shopping_list"):
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
        if tool == "inventory":
            return {"inventory_count": len(output.get("items", []))}
        if tool == "favorites":
            return {"favorite_count": len(output.get("favorites", []))}
        if tool == "recipe_check":
            return {"fit_ratio": output.get("fit_ratio", 0), "missing_count": len(output.get("missing", []))}
        return {"has_result": bool(output)}

    @staticmethod
    def _skill_event_summary(descriptor) -> dict:
        return {
            "name": descriptor.name,
            "category": descriptor.category,
            "timeout_ms": descriptor.timeout_ms,
        }

    @staticmethod
    def _tool_result_event(tool: str, result: SkillExecutionResult, step: int) -> dict:
        descriptor = result.descriptor or {}
        event = {
            "type": "tool_result",
            "phase": "EXECUTING",
            "tool": tool,
            "skill": {
                "name": descriptor.get("name", tool),
                "category": descriptor.get("category", "domain"),
                "timeout_ms": descriptor.get("timeout_ms", 8000),
            },
            "status": result.status,
            "latency_ms": result.latency_ms,
            "retry_count": result.retry_count,
            "error_code": result.error_code,
            "summary": AgentRuntime._summarize_output(tool, result.output),
            "step": step,
        }
        if result.status == "error":
            event["message"] = result.message
        return event

    @staticmethod
    def _build_reply(state: AgentState) -> str:
        if state["shopping_list"]:
            return f"已完成推荐并生成 {len(state['shopping_list'])} 项购物清单。"
        if state.get("recipe_check"):
            check = state["recipe_check"]
            missing = check.get("missing", [])
            if missing:
                names = "、".join(item.get("name", "") for item in missing[:4])
                return f"我已按当前库存清点「{check.get('target', {}).get('title', '这道菜')}」，还缺 {len(missing)} 项：{names}。"
            return f"我已清点「{check.get('target', {}).get('title', '这道菜')}」，当前库存基本可以做。"
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
    def _result(state: AgentState, status: str, outcome: str, termination_reason: str) -> dict:
        # P1-4: 只从 final event 取 reply
        final_message = next(
            (event.get("message", "") for event in reversed(state["events"]) if event.get("type") == "final"),
            "",
        )
        if not final_message:
            final_message = AgentRuntime._build_reply(state)
        return {
            "status": status,
            "conversation_id": state["conversation_id"],
            "trace_id": state["trace_id"],
            "outcome": outcome,
            "next_action": outcome,  # 兼容旧字段名
            "termination_reason": termination_reason,
            "reply": final_message,
            "intent": state["intent"],
            "ingredients": state["ingredients"],
            "recipes": state["recipes"],
            "shopping_list": state["shopping_list"],
            "inventory": state.get("inventory", []),
            "favorites": state.get("favorites", []),
            "recipe_check": state.get("recipe_check"),
            "nutrition": state["nutrition"],
            "quality": state["quality"],
            "guide": state["guide"],
            "events": state["events"],
            "errors": state["errors"],
            "degraded": bool(state["errors"]),
            "memory_context": state.get("memory_context", {}),
            "memory_used": state.get("memory_used", []),
        }
