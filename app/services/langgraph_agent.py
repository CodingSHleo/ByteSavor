"""
LangGraph Agent 适配层（当前为顺序调用版本，保持与真实 LangGraph 接口一致）。

后期替换为真实 LangGraph 时只需改此文件：
1. 安装 pip install langgraph
2. 用 StateGraph 定义 B→Y→T 状态流转
3. router 和 agent.py 接口不需要改
"""

from typing import TypedDict


class BYTEState(TypedDict):
    trace_id: str
    user_input: str
    image_url: str | None
    intent: dict
    ingredients: list
    recipes: list
    shopping_list: list
    stage_errors: list


async def run_byte_pipeline(
    user_input: str,
    sense_fn=None,
    decide_fn=None,
    task_fn=None,
    image_url: str | None = None,
) -> dict:
    """
    运行 BYTE 管道，返回完整结果。

    当前实现：顺序调用 sense → decide → task。
    后期 LangGraph 替换：编译 StateGraph，在每个 node 注入 provider 函数。

    StateGraph 伪代码：
        graph = StateGraph(BYTEState)
        graph.add_node("sense", sense_node)
        graph.add_node("decision", decision_node)
        graph.add_node("task", task_node)
        graph.add_edge("sense", "decision")
        graph.add_edge("decision", "task")
        graph.set_entry_point("sense")
        graph.add_conditional_edges("decision", has_error, {"yes": END, "no": "task"})
        app = graph.compile(checkpointer=MemorySaver())
        result = await app.ainvoke(initial_state)
    """
    from app.services.agent import execute
    return await execute(user_input, sense_fn, decide_fn, task_fn, image_url)
