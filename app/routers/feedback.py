from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import FeedbackRequest, SuccessResponse
from app.services.feedback import submit_feedback as do_feedback
from app.core.database import get_db
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/v1/feedback/meal", tags=["Feedback"])
async def meal_feedback(
    req: FeedbackRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await do_feedback(db, user["sub"], req.recipe_id, req.rating, req.comment)
    return SuccessResponse(data=result)
