from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas import SuccessResponse
from app.services.assistant import chat
from app.core.config import settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list = []


@router.post("/v1/assistant/chat", tags=["Assistant"])
async def assistant_chat(req: ChatRequest):
    result = await chat(req.message, api_key=settings.llm_api_key, history=req.history)
    return SuccessResponse(data=result)
