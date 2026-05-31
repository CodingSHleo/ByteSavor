from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import AgentRequest, SuccessResponse
from app.services.agent import execute as run_pipeline
from app.services.vlm import analyze_food
from app.services.decision import recommend
from app.services.shopping import merge_shopping_list
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.post("/v1/agent/execute", tags=["Agent"])
async def agent_entry(req: AgentRequest, db: AsyncSession = Depends(get_db)):
    async def decide_fn(ingredients, constraints, prefs):
        return await recommend(db, ingredients, constraints, prefs)
    async def task_fn(ids):
        return await merge_shopping_list(db, ids)

    sense_fn = None
    if settings.vlm_api_url:
        async def _sense(img): return await analyze_food(img)
        sense_fn = _sense

    result = await run_pipeline(
        req.input,
        sense_fn=sense_fn,
        decide_fn=decide_fn,
        task_fn=task_fn,
    )
    return SuccessResponse(data=result)
