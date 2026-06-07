import json, httpx, logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import MergeRequest, SuccessResponse, ErrorResponse
from app.services.shopping import merge_shopping_list as do_merge
from app.services.ingredient_tips import enrich_shopping_list
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("task")


@router.post("/v1/task/merge-list", tags=["Task"])
async def merge_list(req: MergeRequest, db: AsyncSession = Depends(get_db)):
    if not req.recipes:
        return ErrorResponse(error={"code": "NO_RECIPES", "message": "未选择菜谱"})
    items = await do_merge(db, req.recipes)
    items = enrich_shopping_list(items)

    # 按人数调整数量
    if req.people != 2 and settings.llm_api_key:
        try:
            items = await adjust_by_people(items, req.people)
        except Exception as e:
            logger.warning("people_adjust_failed %s", e)

    return SuccessResponse(data={"shopping_list": items, "people": req.people})


async def adjust_by_people(items: list[dict], people: int) -> list[dict]:
    """用 DeepSeek 按人数调整食材数量"""
    item_list = ", ".join([f"{i['name']} {i['display']}" for i in items])
    prompt = f"""按{people}人用餐调整以下食材数量。每道菜默认是2人份。返回JSON数组:
[{{"name":"食材名","display":"调整后数量+单位"}}]
食材: {item_list}"""

    resp = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 500, "temperature": 0},
        timeout=30
    )
    content = resp.json()["choices"][0]["message"]["content"]
    if "```" in content:
        content = content.split("```")[1].split("```")[0]
        if content.startswith("json"): content = content[4:]
    adjusted = json.loads(content)

    result = []
    for orig in items:
        for adj in adjusted:
            if adj["name"] == orig["name"]:
                orig["display"] = adj["display"]
                break
        result.append(orig)
    return result
