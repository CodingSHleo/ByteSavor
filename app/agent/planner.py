from dataclasses import dataclass

from app.agent.state import AgentState


@dataclass(frozen=True)
class AgentAction:
    kind: str
    tool: str | None = None
    reason: str = ""
    message: str = ""
    planner_source: str = "rule"
    candidate_tools: list[str] | None = None
    llm_reason: str = ""


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _field_has_value(state: AgentState, field: str) -> bool:
    if field == "intent":
        return bool(state.get("intent"))
    value = state.get(field)  # type: ignore[literal-required]
    return bool(value)


def build_candidate_actions(state: AgentState, skill_descriptors: list[dict]) -> list[dict]:
    text = state["user_input"]
    done = set(state["completed_tools"])
    has_image = bool(state["image_url"])
    candidates: list[dict] = []
    wants_nutrition = _has_any(text, ("营养", "热量", "蛋白质", "碳水", "脂肪"))
    wants_guide = _has_any(text, ("历史", "故事", "菜系", "文化", "探店", "怎么吃"))
    wants_quality = _has_any(text, ("品质", "新鲜", "好不好", "能不能买", "挑选"))
    wants_identify = _has_any(text, ("识别", "图片", "照片", "这张图", "拍照"))
    perception_first_tool = ""
    if has_image:
        if wants_nutrition and "nutrition" not in done:
            perception_first_tool = "nutrition"
        elif wants_guide and "guide" not in done:
            perception_first_tool = "guide"
        elif wants_quality and "quality" not in done:
            perception_first_tool = "quality"
        elif wants_identify and "sense" not in done:
            perception_first_tool = "sense"

    for descriptor in skill_descriptors:
        tool = descriptor.get("name")
        if not tool or tool in done:
            continue
        if perception_first_tool and tool != perception_first_tool:
            continue
        if descriptor.get("requires_image") and not has_image:
            continue

        input_fields = descriptor.get("input_fields") or []
        required_fields = [field for field in input_fields if field != "intent"]
        blocking_fields = [field for field in required_fields if field in {"recipes", "favorites"}]
        if any(not _field_has_value(state, field) for field in blocking_fields):
            continue
        has_inputs = all(
            _field_has_value(state, field)
            for field in required_fields
            if field in state
        )
        keywords = tuple(descriptor.get("intent_keywords") or [])
        keyword_match = _has_any(text, keywords) if keywords else False

        if descriptor.get("requires_user"):
            if not keyword_match:
                continue
        elif input_fields and required_fields and not has_inputs and not keyword_match:
            continue
        elif keywords and not keyword_match and not has_inputs:
            continue

        candidates.append({
            "kind": "tool",
            "tool": tool,
            "reason": descriptor.get("description", ""),
            "requires_image": bool(descriptor.get("requires_image", False)),
            "category": descriptor.get("category", "domain"),
        })

    return candidates


def plan_next_action(state: AgentState) -> AgentAction:
    text = state["user_input"]
    done = set(state["completed_tools"])
    has_image = bool(state["image_url"])

    if state["errors"]:
        return AgentAction("finish")

    wants_nutrition = _has_any(text, ("营养", "热量", "蛋白质", "碳水", "脂肪"))
    wants_guide = _has_any(text, ("历史", "故事", "菜系", "文化", "探店", "怎么吃"))
    wants_quality = _has_any(text, ("品质", "新鲜", "好不好", "能不能买", "挑选"))
    wants_identify = _has_any(text, ("识别", "图片", "照片", "这张图", "拍照"))
    wants_shopping = _has_any(text, ("购物清单", "采购清单", "买菜清单", "生成清单"))
    wants_recommend = _has_any(text, ("推荐", "做什么", "吃什么", "菜谱", "做一道", "做两道"))
    wants_inventory_check = _has_any(text, ("库存", "缺什么", "能不能做", "够不够", "已有食材", "清点"))
    wants_favorites = _has_any(text, ("收藏", "喜欢的菜", "我的菜谱"))

    if wants_inventory_check or wants_favorites:
        if "inventory" not in done:
            return AgentAction("tool", "inventory", "读取当前库存用于判断能否做菜")
        if wants_favorites and "favorites" not in done:
            return AgentAction("tool", "favorites", "读取用户收藏菜谱")
        if state.get("favorites") and state.get("recipe_check") is None and "recipe_check" not in done:
            return AgentAction("tool", "recipe_check", "清点收藏菜谱所需食材")
        if not state.get("favorites") and not state["recipes"] and "decision" not in done:
            return AgentAction("tool", "decision", "没有收藏目标时按库存推荐菜谱")
        if state["recipes"] and state.get("recipe_check") is None and "recipe_check" not in done:
            return AgentAction("tool", "recipe_check", "清点推荐菜谱所需食材")
        return AgentAction("finish")

    if wants_nutrition:
        if state["nutrition"] is not None:
            return AgentAction("finish")
        if not has_image:
            return AgentAction("ask_user", message="请上传需要分析的餐食图片。")
        if "nutrition" not in done:
            return AgentAction("tool", "nutrition", "用户需要营养分析")
        return AgentAction("finish")

    if wants_guide:
        if state["guide"] is not None:
            return AgentAction("finish")
        if not has_image:
            return AgentAction("ask_user", message="请上传需要讲解的菜品图片。")
        if "guide" not in done:
            return AgentAction("tool", "guide", "用户需要菜品文化向导")
        return AgentAction("finish")

    if wants_quality:
        if state["quality"] is not None:
            return AgentAction("finish")
        if not has_image:
            return AgentAction("ask_user", message="请上传需要鉴定品质的食材图片。")
        if "quality" not in done:
            return AgentAction("tool", "quality", "用户需要品质鉴定")
        return AgentAction("finish")

    if wants_identify and not has_image:
        return AgentAction("ask_user", message="请先上传图片，我会识别食材后继续处理。")

    if wants_identify and "sense" not in done:
        return AgentAction("tool", "sense", "先从图片提取食材")

    if (
        (wants_recommend or wants_shopping or wants_identify)
        and not state["recipes"]
        and "decision" not in done
    ):
        return AgentAction("tool", "decision", "根据食材和约束生成推荐")

    if wants_shopping and state["recipes"] and "task" not in done:
        return AgentAction("tool", "task", "把推荐菜谱转成购物清单")

    if state["recipes"] or state["shopping_list"]:
        return AgentAction("finish")

    if not done:
        return AgentAction("tool", "decision", "默认提供饮食推荐")

    return AgentAction("finish")
