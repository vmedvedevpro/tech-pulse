import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

import anthropic
from anthropic.types import CacheControlEphemeralParam, MessageParam, TextBlockParam, ToolResultBlockParam
from loguru import logger

from techpulse.agent.core.events import AgentEvent, TextDelta
from techpulse.agent.core.memory import MemoryStrategy
from techpulse.agent.core.tool_registry import ToolRegistry

_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 5.0  # seconds; multiplied by attempt number


class Agent:
    def __init__(
            self,
            registry: ToolRegistry,
            api_key: str,
            model: str,
            system: str,
            user_context_loader: Callable[[], Awaitable[str]],
            memory_strategy: MemoryStrategy,
    ):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._registry = registry
        self._messages: list[MessageParam] = []
        self._system = system
        self._user_context_loader = user_context_loader
        self._memory_strategy = memory_strategy

    async def stream_chat(self, user_message: str) -> AsyncIterator[AgentEvent]:
        self._messages.append(MessageParam(role="user", content=user_message))

        while True:
            user_context = await self._user_context_loader()
            final_message: anthropic.types.Message | None = None

            for attempt in range(_MAX_RETRIES):
                try:
                    async with self._open_stream(user_context) as stream:
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
            self._messages.append(MessageParam(role="assistant", content=final_message.content))

            if final_message.stop_reason == "end_turn":
                u = final_message.usage
                logger.info(
                    "finished | output={} input={} cache_read={} cache_write={}",
                    u.output_tokens,
                    u.input_tokens,
                    u.cache_read_input_tokens,
                    u.cache_creation_input_tokens,
                )
                self._messages = self._memory_strategy.trim(self._messages)
                return

            if final_message.stop_reason == "tool_use":
                tool_results: list[ToolResultBlockParam] = []
                tool_blocks = [b for b in final_message.content if isinstance(b, anthropic.types.ToolUseBlock)]

                for block in tool_blocks:
                    logger.debug("tool_call {} input={}", block.name, block.input)

                if len(tool_blocks) > 1:
                    logger.warning("multiple tool_calls in a single message")

                results = await asyncio.gather(*(self._registry.run(block.name, block.input) for block in tool_blocks))

                for block, result in zip(tool_blocks, results):
                    if result.is_error:
                        logger.warning("tool_result {} error | {}", block.name, result.content[:200])
                    else:
                        logger.debug("tool_result {} ok | {}", block.name, result.content[:200])
                    tool_results.append(ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id=block.id,
                        content=result.content,
                        is_error=result.is_error,
                    ))
                self._messages.append(MessageParam(role="user", content=tool_results))

    def _open_stream(self, user_context: str):
        return self._client.messages.stream(
            model=self._model,
            max_tokens=2048,
            tools=self._registry.get_schemas(),
            messages=self._messages,
            system=[
                TextBlockParam(type="text", text=self._system,
                               cache_control=CacheControlEphemeralParam(type="ephemeral")),
                TextBlockParam(type="text", text=user_context),
            ],
        )
