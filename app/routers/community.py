from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.schemas import ErrorResponse, SuccessResponse
from app.services import community

router = APIRouter()

VALID_CATEGORIES = {"recipe", "health", "checkin", "all"}


class CommunityPostRequest(BaseModel):
    title: str = Field(default="", min_length=1)
    content: str = ""
    category: str = Field(default="recipe", pattern="^(recipe|health|checkin)$")
    images: list = Field(default_factory=list, max_length=9)
    recipe_payload: dict = Field(default_factory=dict)


class CommentRequest(BaseModel):
    content: str = ""


@router.get("/v1/community/posts", tags=["Community"])
async def list_posts(
    category: str = Query("all"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    if category not in VALID_CATEGORIES:
        return ErrorResponse(error={"code": "INVALID_CATEGORY", "message": f"分类不支持: {category}"})
    user_id = user["sub"] if user else ""
    return SuccessResponse(data=await community.list_posts(db, category, limit=limit, offset=offset, user_id=user_id))


@router.post("/v1/community/posts", tags=["Community"])
async def create_post(
    req: CommunityPostRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await community.create_post(db, user["sub"], req.model_dump())
    except ValueError as e:
        return ErrorResponse(error={"code": "INVALID_COMMUNITY_POST", "message": str(e)})
    return SuccessResponse(data={"post": community.post_dict(row)})


@router.get("/v1/community/posts/{post_id}", tags=["Community"])
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    user_id = user["sub"] if user else ""
    data = await community.get_post(db, post_id, user_id=user_id)
    if data is None:
        return ErrorResponse(error={"code": "POST_NOT_FOUND", "message": "帖子不存在"})
    return SuccessResponse(data={"post": data, "comments": await community.list_comments(db, post_id)})


@router.delete("/v1/community/posts/{post_id}", tags=["Community"])
async def delete_post(post_id: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    deleted, code = await community.delete_post(db, user["sub"], post_id)
    if code == "NOT_FOUND":
        return ErrorResponse(error={"code": "POST_NOT_FOUND", "message": "帖子不存在"})
    if code == "FORBIDDEN":
        return ErrorResponse(error={"code": "FORBIDDEN", "message": "只能删除自己的帖子"})
    return SuccessResponse(data={"deleted": True})


@router.post("/v1/community/posts/{post_id}/like", tags=["Community"])
async def like_post(post_id: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await community.like_post(db, user["sub"], post_id)
    if data.get("code") == "POST_NOT_FOUND":
        return ErrorResponse(error={"code": "POST_NOT_FOUND", "message": "帖子不存在"})
    return SuccessResponse(data=data)


@router.delete("/v1/community/posts/{post_id}/like", tags=["Community"])
async def unlike_post(post_id: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await community.unlike_post(db, user["sub"], post_id)
    if data.get("code") == "POST_NOT_FOUND":
        return ErrorResponse(error={"code": "POST_NOT_FOUND", "message": "帖子不存在"})
    return SuccessResponse(data=data)


@router.get("/v1/community/posts/{post_id}/comments", tags=["Community"])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data={"comments": await community.list_comments(db, post_id)})


@router.post("/v1/community/posts/{post_id}/comments", tags=["Community"])
async def add_comment(
    post_id: int,
    req: CommentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await community.add_comment(db, user["sub"], post_id, req.content)
    except ValueError as e:
        return ErrorResponse(error={"code": "INVALID_COMMENT", "message": str(e)})
    return SuccessResponse(data={"comment": community.comment_dict(row)})
