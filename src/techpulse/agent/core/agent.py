from collections.abc import AsyncIterator

import anthropic
from loguru import logger

from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.config import settings


class Agent:
    def __init__(self, registry: ToolRegistry, system: str | None = None):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._registry = registry
        self._messages: list[dict] = []
        self._system = system

    async def stream_chat(self, user_message: str) -> AsyncIterator[str]:
        self._messages.append({"role": "user", "content": user_message})

        while True:
            create_kwargs = dict(
                model=settings.anthropic_model,
                max_tokens=2048,
                tools=self._registry.get_schemas(),
                messages=self._messages,
            )
            if self._system:
                create_kwargs["system"] = self._system

            async with self._client.messages.stream(**create_kwargs) as stream:
                async for chunk in stream.text_stream:
                    yield chunk
                final_message = await stream.get_final_message()

            self._messages.append({"role": "assistant", "content": final_message.content})

            if final_message.stop_reason == "end_turn":
                logger.info("agent finished | output_tokens={}", final_message.usage.output_tokens)
                return

            if final_message.stop_reason == "tool_use":
                tool_results = []
                for block in final_message.content:
                    if isinstance(block, anthropic.types.ToolUseBlock):
                        result = await self._registry.run(block.name, block.input)
                        if result.is_error:
                            logger.warning("tool_result | {} | error | {}", block.name, result.content[:200])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content,
                            "is_error": result.is_error,
                        })
                self._messages.append({"role": "user", "content": tool_results})

    async def chat(self, user_message: str) -> str:
        chunks: list[str] = []
        async for chunk in self.stream_chat(user_message):
            chunks.append(chunk)
        return "".join(chunks)
