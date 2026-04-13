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

    async def chat(self, user_message: str) -> str:
        self._messages.append({"role": "user", "content": user_message})

        while True:
            create_kwargs = dict(
                model=settings.anthropic_model,
                max_tokens=1024,
                tools=self._registry.get_schemas(),
                messages=self._messages,
            )
            if self._system:
                create_kwargs["system"] = self._system

            response: anthropic.types.Message = await self._client.messages.create(**create_kwargs)

            if response.stop_reason == "end_turn":
                # noinspection PyUnresolvedReferences
                answer = response.content[0].text
                self._messages.append({"role": "assistant", "content": answer})
                logger.info("agent finished | answer length: {} chars", len(answer))
                return answer

            if response.stop_reason == "tool_use":
                self._messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
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
