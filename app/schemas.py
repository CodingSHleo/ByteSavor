from pydantic import BaseModel, Field
from typing import List, Any, Dict
import uuid

# ---------- 全局响应 ----------
def generate_trace_id():
    return uuid.uuid4().hex

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any
    trace_id: str = Field(default_factory=generate_trace_id)

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail
    trace_id: str = Field(default_factory=generate_trace_id)

# ---------- Perception ----------
class Ingredient(BaseModel):
    name: str
    confidence: float
    freshness: str
    state: str

class SenseRequest(BaseModel):
    task_id: str
    image_url: str
    context: dict = Field(default={"scene": "kitchen"})

# ---------- Decision ----------
class RecipeBrief(BaseModel):
    recipe_id: str
    title: str
    match_score: float

class DecisionRequest(BaseModel):
    ingredients: List[str] = Field(default=[])
    constraints: dict = Field(default={"time_limit": 30, "taste": "spicy", "goal": "fat_loss"})

class RecipeDetail(BaseModel):
    recipe_id: str
    title: str
    steps: List[str]

# ---------- Task ----------
class ShoppingItem(BaseModel):
    name: str
    amount: str

class MergeRequest(BaseModel):
    recipes: List[str]
    people: int = 2

# ---------- Agent & Feedback ----------
class AgentRequest(BaseModel):
    input: str
    mode: str = "full"
    image_url: str | None = None
    conversation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

class FeedbackRequest(BaseModel):
    recipe_id: str
    rating: int = Field(..., ge=1, le=5)

# ---------- Auth ----------
class RegisterRequest(BaseModel):
    openid: str = Field(..., min_length=1)

class LoginRequest(BaseModel):
    openid: str = Field(..., min_length=1)

# ---------- User ----------
class NutritionStatus(BaseModel):
    score: int
    deficits: List[str]

class UserProfile(BaseModel):
    user_id: str
    name: str
    goal: str
    preferences: List[str]

class ProfileUpdate(BaseModel):
    goal: str | None = None
    preferences: List[str] | None = None

# ---------- 结构化数量 ----------
class Quantity(BaseModel):
    value: float | None = None       # 数值，少许/适量时为空
    unit: str = ""                   # g / ml / 个 / 勺 / 瓣 / 根 / 少许 / 适量
    display: str = ""                # 前端展示用: "300g" / "少许"

# ---------- Agent 编排 ----------
class StageResult(BaseModel):
    stage: str                       # sense / decision / task
    status: str                      # success / skipped / failed
    latency_ms: int = 0
    data: Any = None
    error: str | None = None

class AgentResponse(BaseModel):
    trace_id: str
    stages: List[StageResult]
    parsed_intent: dict
    ingredients: list = []
    recipes: list = []
    shopping_list: list = []
