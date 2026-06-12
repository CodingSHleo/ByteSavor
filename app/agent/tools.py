from collections.abc import Awaitable, Callable

from app.agent.state import AgentState


Tool = Callable[[AgentState], Awaitable[dict]]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, tool: Tool) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Agent tool is not registered: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

