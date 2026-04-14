import asyncio
from collections.abc import AsyncIterator

import anthropic
from loguru import logger

from techpulse.agent.core.events import (
    AgentEvent,
    TextDelta,
    ToolUseCompleted,
    ToolUseStarted,
)
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.config import settings

_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 5.0  # seconds; multiplied by attempt number


class Agent:
    def __init__(self, registry: ToolRegistry, system: str | None = None):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._registry = registry
        self._messages: list[dict] = []
        self._system = system

    async def stream_chat(self, user_message: str) -> AsyncIterator[AgentEvent]:
        self._messages.append({"role": "user", "content": user_message})

        while True:
            final_message = None
            for attempt in range(_MAX_RETRIES):
                try:
                    async with self._open_stream() as stream:
                        async for delta in stream.text_stream:
                            yield TextDelta(delta)
                        final_message = await stream.get_final_message()
                    break
                except anthropic.APIStatusError as exc:
                    if exc.status_code != 529 or attempt == _MAX_RETRIES - 1:
                        raise
                    delay = _RETRY_BASE_DELAY * (attempt + 1)
                    logger.warning(
                        "anthropic overloaded | attempt={}/{} | retrying in {}s",
                        attempt + 1, _MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)

            assert final_message is not None
            self._messages.append({"role": "assistant", "content": final_message.content})

            if final_message.stop_reason == "end_turn":
                logger.info("finished | output_tokens={}", final_message.usage.output_tokens)
                return

            if final_message.stop_reason == "tool_use":
                tool_results: list[dict] = []
                for block in final_message.content:
                    if not isinstance(block, anthropic.types.ToolUseBlock):
                        continue
                    logger.debug("tool_call {} input={}", block.name, block.input)
                    yield ToolUseStarted(block.name)
                    result = await self._registry.run(block.name, block.input)
                    yield ToolUseCompleted(block.name, ok=not result.is_error)
                    if result.is_error:
                        logger.warning("tool_result {} error | {}", block.name, result.content[:200])
                    else:
                        logger.debug("tool_result {} ok | {}", block.name, result.content[:200])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.content,
                        "is_error": result.is_error,
                    })
                self._messages.append({"role": "user", "content": tool_results})

    def _open_stream(self):
        kwargs = dict(
            model=settings.anthropic_model,
            max_tokens=2048,
            tools=self._registry.get_schemas(),
            messages=self._messages,
        )
        if self._system:
            kwargs["system"] = self._system
        return self._client.messages.stream(**kwargs)
