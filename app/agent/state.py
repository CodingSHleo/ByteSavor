from __future__ import annotations

import re
import uuid
from typing import Any, TypedDict

from app.services.intent_keywords import FOOD_NAMES


class AgentState(TypedDict):
    conversation_id: str
    trace_id: str
    user_input: str
    image_url: str | None
    intent: dict[str, Any]
    ingredients: list[str]
    recipes: list[dict]
    shopping_list: list[dict]
    inventory: list[dict]
    favorites: list[dict]
    recipe_check: dict | None
    nutrition: dict | None
    quality: dict | None
    guide: dict | None
    preferences: list[str]
    completed_tools: list[str]
    events: list[dict]
    errors: list[dict]
    step_count: int
    memory_context: dict[str, Any]  # MemoryContext 四层记忆
    memory_used: list[dict[str, Any]]  # 本次参考的记忆摘要
    sense_result: dict | None  # sense 工具的原始返回（含置信度）


def _parse_basic_intent(text: str) -> dict[str, Any]:
    goal = "balanced"
    if "减脂" in text or "减肥" in text:
        goal = "fat_loss"
    elif "增肌" in text:
        goal = "muscle_gain"

    time_limit = 30
    match = re.search(r"(\d+)\s*分钟", text)
    if match:
        time_limit = int(match.group(1))

    taste = "spicy" if "辣" in text else "light" if "清淡" in text else ""
    ingredients = [name for name in FOOD_NAMES if name in text]
    return {
        "goal": goal,
        "time_limit": time_limit,
        "taste": taste,
        "ingredients": ingredients,
    }


def new_agent_state(
    user_input: str,
    conversation_id: str,
    image_url: str | None = None,
    preferences: list[str] | None = None,
    memory_context: dict[str, Any] | None = None,
) -> AgentState:
    intent = _parse_basic_intent(user_input)
    return {
        "conversation_id": conversation_id,
        "trace_id": uuid.uuid4().hex[:12],
        "user_input": user_input,
        "image_url": image_url,
        "intent": intent,
        "ingredients": list(intent["ingredients"]),
        "recipes": [],
        "shopping_list": [],
        "inventory": [],
        "favorites": [],
        "recipe_check": None,
        "nutrition": None,
        "quality": None,
        "guide": None,
        "preferences": list(preferences or []),
        "completed_tools": [],
        "events": [],
        "errors": [],
        "step_count": 0,
        "memory_context": memory_context or {},
        "memory_used": [],
        "sense_result": None,
    }
