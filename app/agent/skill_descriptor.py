"""
SkillDescriptor 轻量元数据：描述每个 Agent 工具的输入/输出/完成条件。
用于减少 planner 中的硬编码，支持后续配置化。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import asdict

SKILL_DESCRIPTORS: dict[str, "SkillDescriptor"] = {}


@dataclass
class SkillDescriptor:
    name: str                           # 工具名
    description: str                    # 一句话描述
    requires_image: bool = False        # 是否需要图片
    requires_user: bool = False         # 是否需要登录
    input_fields: list[str] = field(default_factory=list)  # 依赖的 AgentState 字段
    output_fields: list[str] = field(default_factory=list)  # 写入的 AgentState 字段
    intent_keywords: list[str] = field(default_factory=list)  # 触发意图关键词
    completion_criteria: str = ""       # 完成条件描述
    timeout_ms: int = 8000              # 单个 skill 最大执行时间
    max_retries: int = 0                # 当前允许 0 或 1
    retryable_errors: list[str] = field(default_factory=list)  # 可重试错误码
    degrade_on_error: bool = True       # 出错后是否降级
    category: str = "domain"           # skill 分类

    def to_dict(self) -> dict:
        return asdict(self)


def register_skill(
    name: str,
    description: str,
    requires_image: bool = False,
    requires_user: bool = False,
    input_fields: list[str] | None = None,
    output_fields: list[str] | None = None,
    intent_keywords: list[str] | None = None,
    completion_criteria: str = "",
    timeout_ms: int = 8000,
    max_retries: int = 0,
    retryable_errors: list[str] | None = None,
    degrade_on_error: bool = True,
    category: str = "domain",
) -> SkillDescriptor:
    sd = SkillDescriptor(
        name=name,
        description=description,
        requires_image=requires_image,
        requires_user=requires_user,
        input_fields=input_fields or [],
        output_fields=output_fields or [],
        intent_keywords=intent_keywords or [],
        completion_criteria=completion_criteria,
        timeout_ms=timeout_ms,
        max_retries=max_retries,
        retryable_errors=retryable_errors or [],
        degrade_on_error=degrade_on_error,
        category=category,
    )
    SKILL_DESCRIPTORS[name] = sd
    return sd


def get_skill(name: str) -> SkillDescriptor | None:
    return SKILL_DESCRIPTORS.get(name)


# ── 注册所有 Agent 工具元数据 ──

register_skill(
    name="sense",
    description="用 VLM 识别图片中的食材，返回食材列表、新鲜度、分量估计",
    requires_image=True,
    requires_user=False,
    input_fields=["image_url"],
    output_fields=["ingredients", "sense_result"],
    intent_keywords=["识别", "图片", "拍照", "这是什么"],
    completion_criteria="成功识别到至少 1 个食材",
    timeout_ms=12000,
    max_retries=1,
    retryable_errors=["VLM_UNAVAILABLE", "TimeoutError"],
    category="perception",
)

register_skill(
    name="decision",
    description="根据已有食材、用户偏好、健康目标推荐菜谱",
    requires_image=False,
    requires_user=False,
    input_fields=["ingredients", "intent", "preferences", "memory_context"],
    output_fields=["recipes"],
    intent_keywords=["推荐", "做什么", "吃什么", "菜谱", "减脂", "增肌"],
    completion_criteria="返回至少 1 个菜谱推荐",
    timeout_ms=10000,
    category="decision",
)

register_skill(
    name="task",
    description="根据推荐菜谱生成合并后的购物清单",
    requires_image=False,
    requires_user=False,
    input_fields=["recipes"],
    output_fields=["shopping_list"],
    intent_keywords=["购物", "清单", "采购", "需要买"],
    completion_criteria="生成至少 1 项购物清单",
    timeout_ms=6000,
    category="task",
)

register_skill(
    name="nutrition",
    description="分析一餐的营养成分（热量、蛋白、碳水、脂肪）",
    requires_image=True,
    requires_user=False,
    input_fields=["image_url", "intent"],
    output_fields=["nutrition"],
    intent_keywords=["营养", "热量", "卡路里", "蛋白质"],
    completion_criteria="返回非 0 的营养数据",
    timeout_ms=12000,
    max_retries=1,
    retryable_errors=["VLM_UNAVAILABLE", "TimeoutError"],
    category="perception",
)

register_skill(
    name="quality",
    description="鉴定食材品质，包括新鲜度、外观、保质期判断",
    requires_image=True,
    requires_user=False,
    input_fields=["image_url"],
    output_fields=["quality"],
    intent_keywords=["鉴定", "品质", "新鲜", "坏了"],
    completion_criteria="返回品质评估结果",
    timeout_ms=12000,
    max_retries=1,
    retryable_errors=["VLM_UNAVAILABLE", "TimeoutError"],
    category="perception",
)

register_skill(
    name="guide",
    description="菜品文化讲解与探店向导",
    requires_image=True,
    requires_user=False,
    input_fields=["image_url"],
    output_fields=["guide"],
    intent_keywords=["探店", "是什么菜", "讲解", "介绍"],
    completion_criteria="返回菜品识别和文化讲解",
    timeout_ms=12000,
    max_retries=1,
    retryable_errors=["VLM_UNAVAILABLE", "TimeoutError"],
    category="perception",
)

register_skill(
    name="inventory",
    description="读取用户当前食材库存",
    requires_image=False,
    requires_user=True,
    input_fields=[],
    output_fields=["inventory"],
    intent_keywords=["库存", "有什么", "还有多少"],
    completion_criteria="成功读取库存列表",
    timeout_ms=5000,
    category="memory",
)

register_skill(
    name="favorites",
    description="读取用户收藏的菜谱",
    requires_image=False,
    requires_user=True,
    input_fields=[],
    output_fields=["favorites"],
    intent_keywords=["收藏", "喜欢", "常做"],
    completion_criteria="成功读取收藏列表",
    timeout_ms=5000,
    category="memory",
)

register_skill(
    name="recipe_check",
    description="检查菜谱与库存匹配度，计算已有/缺失食材",
    requires_image=False,
    requires_user=True,
    input_fields=["recipes", "favorites"],
    output_fields=["recipe_check", "shopping_list"],
    intent_keywords=["能做吗", "检查", "缺什么", "够不够", "清点"],
    completion_criteria="返回 fit_ratio 和缺失列表",
    timeout_ms=7000,
    category="decision",
)
