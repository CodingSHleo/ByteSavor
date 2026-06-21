from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.agent.skill_descriptor import SKILL_DESCRIPTORS, SkillDescriptor
from app.agent.state import AgentState


Tool = Callable[[AgentState], Awaitable[dict]]


@dataclass
class SkillExecutionResult:
    output: dict
    status: str
    latency_ms: int
    retry_count: int
    error_code: str | None = None
    message: str = ""
    descriptor: dict | None = None


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, tool: Tool) -> None:
        if name not in SKILL_DESCRIPTORS:
            raise ValueError(f"Unknown skill descriptor: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Agent tool is not registered: {name}")
        return self._tools[name]

    def descriptor(self, name: str) -> SkillDescriptor:
        if name not in SKILL_DESCRIPTORS:
            raise ValueError(f"Unknown skill descriptor: {name}")
        return SKILL_DESCRIPTORS[name]

    def describe(self) -> list[dict]:
        return [self.descriptor(name).to_dict() for name in self.names()]

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)


def _normalize_error_code(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "TimeoutError"
    message = str(exc)
    if message in {"VLM_NOT_CONFIGURED", "VLM_UNAVAILABLE"}:
        return message
    if isinstance(exc, ValueError) and message:
        return message
    return type(exc).__name__


async def execute_tool(registry: ToolRegistry, name: str, state: AgentState) -> SkillExecutionResult:
    descriptor = registry.descriptor(name)
    descriptor_dict = descriptor.to_dict()
    max_retries = max(0, min(descriptor.max_retries, 1))
    attempts = max_retries + 1
    started = time.perf_counter()
    last_error_code: str | None = None
    last_message = ""

    for attempt in range(attempts):
        try:
            tool = registry.get(name)
            output = await asyncio.wait_for(tool(state), timeout=descriptor.timeout_ms / 1000)
            return SkillExecutionResult(
                output=output,
                status="success",
                latency_ms=round((time.perf_counter() - started) * 1000),
                retry_count=attempt,
                descriptor=descriptor_dict,
            )
        except Exception as exc:
            last_error_code = _normalize_error_code(exc)
            last_message = str(exc)[:200]
            should_retry = attempt < max_retries and last_error_code in descriptor.retryable_errors
            if should_retry:
                continue
            return SkillExecutionResult(
                output={},
                status="error",
                latency_ms=round((time.perf_counter() - started) * 1000),
                retry_count=attempt,
                error_code=last_error_code,
                message=last_message,
                descriptor=descriptor_dict,
            )

    return SkillExecutionResult(
        output={},
        status="error",
        latency_ms=round((time.perf_counter() - started) * 1000),
        retry_count=max_retries,
        error_code=last_error_code or "UnknownError",
        message=last_message,
        descriptor=descriptor_dict,
    )
