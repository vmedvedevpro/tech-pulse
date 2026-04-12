import anthropic

from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.config import settings


class Agent:
    def __init__(self, registry: ToolRegistry):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._registry = registry
        self._messages: list[dict] = []

    # noinspection PyTypeChecker
    def chat(self, user_message: str) -> str:
        self._messages.append({"role": "user", "content": user_message})

        while True:
            response: anthropic.types.Message = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                tools=self._registry.get_schemas(),
                messages=self._messages
            )

            if response.stop_reason == "end_turn":
                # noinspection PyUnresolvedReferences
                answer = response.content[0].text
                self._messages.append({"role": "assistant", "content": answer})
                return answer

            if response.stop_reason == "tool_use":
                self._messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if isinstance(block, anthropic.types.ToolUseBlock):
                        result = self._registry.run(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content,
                            "is_error": result.is_error,
                        })

                self._messages.append({"role": "user", "content": tool_results})
