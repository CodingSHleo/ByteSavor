from app.agent.planner import plan_next_action
from app.agent.state import new_agent_state


def test_planner_routes_nutrition_without_recipe_pipeline():
    state = new_agent_state(
        user_input="分析这顿饭的热量和蛋白质",
        conversation_id="conv_nutrition",
        image_url="data:image/jpeg;base64,dGVzdA==",
    )

    action = plan_next_action(state)

    assert action.tool == "nutrition"


def test_planner_routes_food_guide_without_shopping():
    state = new_agent_state(
        user_input="这道东坡肉有什么历史故事",
        conversation_id="conv_guide",
        image_url="data:image/jpeg;base64,dGVzdA==",
    )

    action = plan_next_action(state)

    assert action.tool == "guide"


def test_planner_stops_after_requested_result_exists():
    state = new_agent_state(
        user_input="推荐一道菜",
        conversation_id="conv_done",
    )
    state["recipes"] = [{"recipe_id": "r_001"}]

    action = plan_next_action(state)

    assert action.kind == "finish"
