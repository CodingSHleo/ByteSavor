from dataclasses import dataclass

from app.agent.state import AgentState


@dataclass(frozen=True)
class AgentAction:
    kind: str
    tool: str | None = None
    reason: str = ""
    message: str = ""


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def plan_next_action(state: AgentState) -> AgentAction:
    text = state["user_input"]
    done = set(state["completed_tools"])
    has_image = bool(state["image_url"])

    wants_nutrition = _has_any(text, ("营养", "热量", "蛋白质", "碳水", "脂肪"))
    wants_guide = _has_any(text, ("历史", "故事", "菜系", "文化", "探店", "怎么吃"))
    wants_quality = _has_any(text, ("品质", "新鲜", "好不好", "能不能买", "挑选"))
    wants_identify = _has_any(text, ("识别", "图片", "照片", "这张图", "拍照"))
    wants_shopping = _has_any(text, ("购物清单", "采购清单", "买菜清单", "生成清单"))
    wants_recommend = _has_any(text, ("推荐", "做什么", "吃什么", "菜谱", "做一道", "做两道"))

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
