import time
import uuid
import re
import logging
from app.services.providers import SenseProvider, DecisionProvider, TaskProvider

logger = logging.getLogger("agent")

FOOD_NAMES = ["牛肉", "鸡肉", "猪肉", "鸡蛋", "番茄", "西红柿", "西兰花", "南瓜", "豆腐", "鱼", "虾", "土豆", "牛奶", "酸奶", "生菜", "黄瓜", "胡萝卜", "洋葱"]


async def _get_intent(user_input: str) -> dict:
    """三级降级: DeepSeek → Ollama本地 → 正则"""
    # 1. DeepSeek
    from app.services.llm_deepseek import parse_intent as ds_parse
    result = await ds_parse(user_input)
    if result:
        logger.info("intent_deepseek", extra={"input": user_input[:60], "intent": result})
        return result
    # 2. Ollama 本地
    from app.services.llm import parse_intent as ollama_parse
    result = await ollama_parse(user_input)
    if result:
        logger.info("intent_ollama", extra={"input": user_input[:60], "intent": result})
        return result
    # 3. 正则降级
    fallback = _parse_intent_regex(user_input)
    logger.info("intent_regex", extra={"input": user_input[:60], "intent": fallback})
    return fallback


async def execute(
    user_input: str,
    sense_fn: SenseProvider | None = None,
    decide_fn: DecisionProvider | None = None,
    task_fn: TaskProvider | None = None,
    image_url: str | None = None,
) -> dict:
    trace_id = uuid.uuid4().hex[:12]
    stages = []
    intent = await _get_intent(user_input)

    # ---- Sense 阶段 ----
    t0 = time.time()
    sense_result = None
    stage_sense = {"stage": "sense", "status": "skipped", "latency_ms": 0}
    if image_url and sense_fn:
        try:
            sense_result = await sense_fn(image_url)
            stage_sense["status"] = "success" if sense_result else "failed"
            stage_sense["data"] = sense_result
        except Exception as e:
            stage_sense["status"] = "error"
            stage_sense["error"] = str(e)
            logger.warning("sense_failed", extra={"error": str(e), "trace_id": trace_id})
    stage_sense["latency_ms"] = round((time.time() - t0) * 1000)
    stages.append(stage_sense)

    # ---- Decision 阶段 ----
    t0 = time.time()
    ingredients = list(intent["ingredients"])
    if sense_result and sense_result.get("ingredients"):
        vlm_names = [i["name"] for i in sense_result["ingredients"]]
        ingredients = list(set(ingredients + vlm_names))

    constraints = {"time_limit": intent["time_limit"], "goal": intent["goal"], "taste": intent.get("taste", "")}
    recipes = []
    stage_dec = {"stage": "decision", "status": "skipped", "latency_ms": 0}
    if decide_fn:
        try:
            recipes = await decide_fn(ingredients, constraints, [])
            stage_dec["status"] = "success" if recipes else "empty"
            stage_dec["data"] = recipes
        except Exception as e:
            stage_dec["status"] = "error"
            stage_dec["error"] = str(e)
            logger.warning("decision_failed", extra={"error": str(e), "trace_id": trace_id})
    stage_dec["latency_ms"] = round((time.time() - t0) * 1000)
    stages.append(stage_dec)

    # ---- Task 阶段 ----
    t0 = time.time()
    shop_list = []
    stage_task = {"stage": "task", "status": "skipped", "latency_ms": 0}
    if task_fn and recipes:
        try:
            recipe_ids = [r["recipe_id"] for r in recipes[:3]]
            shop_list = await task_fn(recipe_ids)
            stage_task["status"] = "success" if shop_list else "empty"
            stage_task["data"] = shop_list
        except Exception as e:
            stage_task["status"] = "error"
            stage_task["error"] = str(e)
            logger.warning("task_failed", extra={"error": str(e), "trace_id": trace_id})
    stage_task["latency_ms"] = round((time.time() - t0) * 1000)
    stages.append(stage_task)

    logger.info("agent_pipeline", extra={
        "trace_id": trace_id, "input": user_input[:80],
        "stages": [(s["stage"], s["status"], s["latency_ms"]) for s in stages],
    })

    has_error = any(s["status"] in {"error", "failed"} for s in stages)
    return {
        "trace_id": trace_id,
        "stages": stages,
        "parsed_intent": intent,
        "ingredients": [{"name": i, "from": "text" if i in intent["ingredients"] else "vlm"} for i in ingredients],
        "recipes": recipes,
        "shopping_list": shop_list,
        "degraded": has_error,
    }


def _parse_intent_regex(text: str) -> dict:
    goal = "balanced"
    time_limit = 30
    taste = ""
    ingredients = []

    if "减脂" in text or "减肥" in text:
        goal = "fat_loss"
    elif "增肌" in text:
        goal = "muscle_gain"

    m = re.search(r"(\d+)\s*分钟", text)
    if m:
        time_limit = int(m.group(1))

    if "辣" in text:
        taste = "spicy"
    elif "清淡" in text:
        taste = "light"

    for k in FOOD_NAMES:
        if k in text:
            ingredients.append(k)

    return {"goal": goal, "time_limit": time_limit, "taste": taste, "ingredients": ingredients}
