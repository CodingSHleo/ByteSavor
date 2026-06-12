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
    if user:
        profile = await user_svc.get_profile(db, user["sub"])
        if profile:
            preferences = profile.get("preferences", [])
            goal = profile.get("goal", "")

    tools = ToolRegistry()

    async def sense_tool(state):
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

    if settings.vlm_api_url:
        tools.register("sense", sense_tool)
    tools.register("decision", decision_tool)
    tools.register("task", task_tool)
    tools.register("nutrition", nutrition_tool)
    tools.register("quality", quality_tool)
    tools.register("guide", guide_tool)

    tool_key = tuple(tools.names())
    runtime = _agent_instances.get(tool_key)
    if runtime is None:
        runtime = LangGraphAgent(tools=tools)
        _agent_instances[tool_key] = runtime
    else:
        runtime.tools = tools
    result = await runtime.run(
        user_input=req.input,
        conversation_id=req.conversation_id,
        image_url=req.image_url,
        preferences=preferences,
    )
    result["parsed_intent"] = result["intent"]
    result["stages"] = _events_to_stages(result["events"])
    return SuccessResponse(data=result)


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
            "retry_count": 0,
        })
    return stages
