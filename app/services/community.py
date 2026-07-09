from __future__ import annotations

from sqlalchemy import delete, select, func
from sqlalchemy.orm import defer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CommunityComment, CommunityLike, CommunityPost, User
from app.services import favorites as favorites_svc

VALID_CATEGORIES = {"recipe", "health", "checkin"}


async def create_post(db: AsyncSession, user_id: str, payload: dict) -> CommunityPost:
    title = str(payload.get("title") or "").strip()
    content = str(payload.get("content") or "").strip()
    category = payload.get("category") or "recipe"
    recipe_payload = payload.get("recipe_payload") or {}
    if not title:
        raise ValueError("标题不能为空")
    if category not in VALID_CATEGORIES:
        raise ValueError("不支持的社区分类")
    if category == "recipe":
        ingredients = recipe_payload.get("ingredients") or []
        if not recipe_payload.get("title"):
            recipe_payload["title"] = title
        if not ingredients:
            raise ValueError("菜谱帖必须包含结构化食材")
    post = CommunityPost(
        user_id=user_id,
        title=title,
        content=content,
        category=category,
        images=payload.get("images") or [],
        recipe_payload=recipe_payload,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def list_posts(
    db: AsyncSession,
    category: str = "all",
    limit: int = 20,
    offset: int = 0,
    user_id: str = "",
) -> dict:
    # 列表不加载 images 字段（base64 过大导致 MySQL sort buffer 溢出）
    q = select(CommunityPost).options(defer(CommunityPost.images)).order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())
    if category and category != "all":
        q = q.where(CommunityPost.category == category)

    # total count
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # pagination
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    posts = result.scalars().all()

    # liked_by_me
    liked_ids: set[int] = set()
    favorited_map: dict[str, bool] = {}
    if user_id and posts:
        post_ids = [p.id for p in posts]
        like_result = await db.execute(
            select(CommunityLike.post_id).where(
                CommunityLike.post_id.in_(post_ids),
                CommunityLike.user_id == user_id,
            )
        )
        liked_ids = {row[0] for row in like_result.all()}
        favorited_map = await favorites_svc.favorite_status_map(
            db,
            user_id,
            "community_post",
            [str(post_id) for post_id in post_ids],
        )

    author_map = await _author_map(db, [p.user_id for p in posts])
    return {
        "posts": [
            post_dict(
                p,
                liked_by_me=(p.id in liked_ids),
                favorited_by_me=favorited_map.get(str(p.id), False),
                author=author_map.get(p.user_id, {}),
                include_images=False,  # 列表不传 base64 图片，防止 MySQL sort buffer 溢出
            )
            for p in posts
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


async def get_post(db: AsyncSession, post_id: int, user_id: str = "") -> dict | None:
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    liked = False
    favorited = False
    if user_id:
        like_row = await db.execute(
            select(CommunityLike).where(CommunityLike.post_id == post_id, CommunityLike.user_id == user_id)
        )
        liked = like_row.scalar_one_or_none() is not None
        favorited = await favorites_svc.favorite_status(db, user_id, "community_post", str(post_id))
    author = (await _author_map(db, [row.user_id])).get(row.user_id, {})
    return post_dict(row, liked_by_me=liked, favorited_by_me=favorited, author=author)


async def delete_post(db: AsyncSession, user_id: str, post_id: int, is_admin: bool = False) -> tuple[bool, str]:
    post_result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = post_result.scalar_one_or_none()
    if post is None:
        return False, "NOT_FOUND"
    if post.user_id != user_id and not is_admin:
        return False, "FORBIDDEN"
    await db.execute(delete(CommunityComment).where(CommunityComment.post_id == post_id))
    await db.execute(delete(CommunityLike).where(CommunityLike.post_id == post_id))
    await db.delete(post)
    await db.commit()
    return True, ""


async def like_post(db: AsyncSession, user_id: str, post_id: int) -> dict:
    post = await _get_post_orm(db, post_id)
    if post is None:
        return {"liked": False, "like_count": 0, "error": "NOT_FOUND", "code": "POST_NOT_FOUND"}
    result = await db.execute(
        select(CommunityLike).where(CommunityLike.post_id == post_id, CommunityLike.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        db.add(CommunityLike(post_id=post_id, user_id=user_id))
        post.like_count = int(post.like_count or 0) + 1
        await db.commit()
        await db.refresh(post)
    return {"liked": True, "like_count": post.like_count or 0}


async def unlike_post(db: AsyncSession, user_id: str, post_id: int) -> dict:
    post = await _get_post_orm(db, post_id)
    if post is None:
        return {"liked": False, "like_count": 0, "error": "NOT_FOUND", "code": "POST_NOT_FOUND"}
    result = await db.execute(
        select(CommunityLike).where(CommunityLike.post_id == post_id, CommunityLike.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        await db.delete(row)
        post.like_count = max(0, int(post.like_count or 0) - 1)
        await db.commit()
        await db.refresh(post)
    return {"liked": False, "like_count": post.like_count or 0}


async def add_comment(db: AsyncSession, user_id: str, post_id: int, content: str) -> CommunityComment:
    post = await _get_post_orm(db, post_id)
    if post is None:
        raise ValueError("帖子不存在")
    text = str(content or "").strip()
    if not text:
        raise ValueError("评论不能为空")
    row = CommunityComment(post_id=post_id, user_id=user_id, content=text)
    db.add(row)
    post.comment_count = int(post.comment_count or 0) + 1
    await db.commit()
    await db.refresh(row)
    return row


async def list_comments(db: AsyncSession, post_id: int) -> list[dict]:
    result = await db.execute(
        select(CommunityComment)
        .where(CommunityComment.post_id == post_id)
        .order_by(CommunityComment.created_at.asc(), CommunityComment.id.asc())
    )
    return [comment_dict(row) for row in result.scalars().all()]


async def _get_post_orm(db: AsyncSession, post_id: int) -> CommunityPost | None:
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    return result.scalar_one_or_none()


async def _author_map(db: AsyncSession, user_ids: list[str]) -> dict[str, dict]:
    ids = sorted({uid for uid in user_ids if uid})
    if not ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(ids)))
    return {
        row.id: {
            "name": row.name or row.username or "社区用户",
            "avatar_url": row.avatar_url or "",
        }
        for row in result.scalars().all()
    }


def post_dict(row: CommunityPost, liked_by_me: bool = False, favorited_by_me: bool = False, author: dict | None = None, include_images: bool = True) -> dict:
    author = author or {}
    return {
        "id": row.id,
        "user_id": row.user_id,
        "author": {
            "name": author.get("name") or "社区用户",
            "avatar_url": author.get("avatar_url") or "",
        },
        "title": row.title,
        "content": row.content,
        "category": row.category,
        "images": (row.images or []) if include_images else [],  # 列表不传图片，详情才传
        "recipe_payload": row.recipe_payload or {},
        "like_count": row.like_count or 0,
        "comment_count": row.comment_count or 0,
        "liked_by_me": liked_by_me,
        "favorited_by_me": favorited_by_me,
        "created_at": row.created_at.isoformat() if row.created_at else "",
        "updated_at": row.updated_at.isoformat() if row.updated_at else "",
    }


def comment_dict(row: CommunityComment) -> dict:
    return {
        "id": row.id,
        "post_id": row.post_id,
        "user_id": row.user_id,
        "content": row.content,
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }
