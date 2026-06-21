from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.schemas import SuccessResponse
from app.services.assistant import chat
from app.core.config import settings
from app.core.database import get_db
from app.middleware.auth import get_optional_user
from app.services import user as user_svc
from app.services.agent import _parse_intent_regex

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list = []


@router.post("/v1/assistant/chat", tags=["Assistant"])
async def assistant_chat(
    req: ChatRequest,
    user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    goal = ""
    preferences = []
    if user:
        profile = await user_svc.get_profile(db, user["sub"])
        if profile:
            goal = profile.get("goal") or ""
            preferences = profile.get("preferences") or []
    result = await chat(
        req.message,
        api_key=settings.llm_api_key,
        history=req.history,
        ingredients=_parse_intent_regex(req.message).get("ingredients", []),
        goal=goal,
        preferences=preferences,
    )
    return SuccessResponse(data=result)
