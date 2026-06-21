from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import AgentRequest, SuccessResponse
from app.services.vlm import analyze_food
from app.services.decision import recommend
from app.services.shopping import merge_shopping_list
from app.services.nutrition_analyzer import analyze_meal
from app.services.quality import assess
from app.services.food_guide import guide
from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_optional_user
from app.services import user as user_svc
from app.services import favorites as favorites_svc
from app.services import inventory as inventory_svc
from app.services import recipe_checker
from app.services.agent_memory import build_memory_context, build_memory_used
from app.agent.langgraph_runtime import LangGraphAgent
from app.agent.tools import ToolRegistry

router = APIRouter()
_agent_instances: dict[tuple[str, ...], LangGraphAgent] = {}


@router.post("/v1/agent/execute", tags=["Agent"])
async def agent_entry(
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    preferences = []
    goal = ""
    user_id = ""
    if user:
        user_id = user["sub"]
        profile = await user_svc.get_profile(db, user_id)
        if profile:
            preferences = profile.get("preferences", [])
            goal = profile.get("goal", "")

    tools = ToolRegistry()

    async def sense_tool(state):
        if not state.get("image_url"):
            raise ValueError("NO_IMAGE")
        if not settings.vlm_api_url:
            raise RuntimeError("VLM_NOT_CONFIGURED")
        result = await analyze_food(state["image_url"])
        if result is None:
            raise RuntimeError("VLM_UNAVAILABLE")
        return result

    async def decision_tool(state):
        constraints = {
            "time_limit": state["intent"].get("time_limit", 30),
            "taste": state["intent"].get("taste", ""),
            "goal": state["intent"].get("goal") or goal or "balanced",
        }
        pref_mem = state.get("memory_context", {}).get("preference_memory", {})
        constraints["avoid_tags"] = pref_mem.get("avoid_tags", [])
        constraints["avoid_ingredients"] = pref_mem.get("avoid_ingredients", [])
        recipes = await recommend(
            db,
            state["ingredients"],
            constraints,
            state["preferences"],
        )
        return {"recipes": recipes}

    async def task_tool(state):
        recipe_ids = [r["recipe_id"] for r in state["recipes"][:3]]
        items = await merge_shopping_list(db, recipe_ids)
        return {"shopping_list": items}

    async def nutrition_tool(state):
        return await analyze_meal(state["image_url"], goal or state["intent"].get("goal", "balanced"))

    async def quality_tool(state):
        return await assess(state["image_url"])

    async def guide_tool(state):
        return await guide(state["image_url"])

    async def inventory_tool(state):
        if not user:
            return {"items": []}
        return {"items": await inventory_svc.current_inventory(db, user["sub"])}

    async def favorites_tool(state):
        if not user:
            return {"favorites": []}
        return {"favorites": await favorites_svc.list_favorites(db, user["sub"])}

    async def recipe_check_tool(state):
        if not user:
            return {"owned": [], "missing": [], "shopping_list": [], "fit_ratio": 0, "can_cook": False}
        target_type = "system_recipe"
        target_id = ""
        if state.get("favorites"):
            fav = state["favorites"][0]
            target_type = fav.get("target_type", target_type)
            target_id = fav.get("target_id", "")
        elif state.get("recipes"):
            first = state["recipes"][0]
            target_id = first.get("recipe_id") or first.get("recipeId") or ""
        if not target_id:
            return {"owned": [], "missing": [], "shopping_list": [], "fit_ratio": 0, "can_cook": False}
        return await recipe_checker.check_recipe(db, user["sub"], target_type, str(target_id))

    tools.register("sense", sense_tool)
    tools.register("decision", decision_tool)
    tools.register("task", task_tool)
    tools.register("nutrition", nutrition_tool)
    tools.register("quality", quality_tool)
    tools.register("guide", guide_tool)
    tools.register("inventory", inventory_tool)
    tools.register("favorites", favorites_tool)
    tools.register("recipe_check", recipe_check_tool)

    tool_key = tuple(tools.names())
    runtime = _agent_instances.get(tool_key)
    if runtime is None:
        runtime = LangGraphAgent(tools=tools)
        _agent_instances[tool_key] = runtime
    else:
        runtime.tools = tools
    # P1-1: 前置读取上一轮会话状态，让 MemoryContext 真正体现 conversation memory
    previous_state = await runtime.get_previous_state(req.conversation_id)
    memory_context = await build_memory_context(
        db, user_id or None,
        previous_state=previous_state,
        goal=goal,
    )
    result = await runtime.run(
        user_input=req.input,
        conversation_id=req.conversation_id,
        image_url=req.image_url,
        preferences=preferences,
        memory_context=memory_context,
    )
    result["parsed_intent"] = result["intent"]
    result["stages"] = _events_to_stages(result["events"])
    # P1-2: 优先用 runtime state 中的 memory，静态构建的作 fallback
    result["memory_context"] = result.get("memory_context") or memory_context
    result["memory_used"] = result.get("memory_used") or build_memory_used(result["memory_context"])
    result["confirmation_prompts"] = _build_confirmation_prompts(result)
    return SuccessResponse(data=result)


def _build_confirmation_prompts(result: dict) -> list[dict]:
    """P1-5: 按 evaluation issue code 独立生成确认提示，不嵌套。"""
    prompts: list[dict] = []
    seen_codes: set[str] = set()

    # 收集所有 evaluation issue codes
    codes: set[str] = set()
    for event in result.get("events", []):
        if event.get("type") == "evaluation":
            for issue in event.get("issues", []):
                codes.add(issue.get("code", ""))

    # 低置信食材 → INGREDIENT_CONFIRM
    if "LOW_CONFIDENCE_INGREDIENT" in codes and "LOW_CONFIDENCE_INGREDIENT" not in seen_codes:
        seen_codes.add("LOW_CONFIDENCE_INGREDIENT")
        prompts.append({
            "code": "INGREDIENT_CONFIRM",
            "question": "部分食材识别置信度较低，是否需要核实后再推荐？",
            "options": [
                {"key": "confirm", "label": "先确认食材", "action": "confirm"},
                {"key": "skip", "label": "暂不处理", "action": "skip"},
            ],
        })

    # 核心食材冲突 → SUBSTITUTE_CONFIRM
    if "CORE_INGREDIENT_MISSED" in codes and "CORE_INGREDIENT_MISSED" not in seen_codes:
        seen_codes.add("CORE_INGREDIENT_MISSED")
        prompts.append({
            "code": "SUBSTITUTE_CONFIRM",
            "question": "部分食材没有完全匹配的菜谱，是否接受替代食材的推荐？",
            "options": [
                {"key": "accept", "label": "接受替代", "action": "accept"},
                {"key": "retry", "label": "重新搜索", "action": "retry"},
            ],
        })

    # 需用户确认 → TASTE_CONFIRM
    if ("NEEDS_USER_CONFIRMATION" in codes or result.get("recipes")) and "TASTE_CONFIRM" not in seen_codes:
        seen_codes.add("TASTE_CONFIRM")
        prompts.append({
            "code": "TASTE_CONFIRM",
            "question": "这些推荐是否符合您的口味偏好？",
            "options": [
                {"key": "like", "label": "看起来不错", "action": "confirm"},
                {"key": "retry", "label": "换一批推荐", "action": "retry"},
                {"key": "skip", "label": "先这样", "action": "skip"},
            ],
        })

    return prompts


def _events_to_stages(events: list[dict]) -> list[dict]:
    stages = []
    for event in events:
        if event.get("type") != "tool_result":
            continue
        stages.append({
            "stage": event.get("tool"),
            "status": event.get("status"),
            "latency_ms": event.get("latency_ms", 0),
            "error_code": event.get("error_code"),
            "retry_count": event.get("retry_count", 0),
        })
    return stages
