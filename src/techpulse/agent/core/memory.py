from typing import Protocol

from loguru import logger


class MemoryStrategy(Protocol):
    def trim(self, messages: list[dict]) -> list[dict]: ...


class SlidingWindowStrategy:
    def __init__(self, max_turns: int) -> None:
        self._max_turns = max_turns

    def trim(self, messages: list[dict]) -> list[dict]:
        real_user_indices = [
            i for i, m in enumerate(messages)
            if m["role"] == "user" and isinstance(m["content"], str)
        ]
        if len(real_user_indices) <= self._max_turns:
            return messages
        cut_from = real_user_indices[len(real_user_indices) - self._max_turns]
        logger.info(
            "sliding_window | trimmed {} old turns, keeping last {}",
            len(real_user_indices) - self._max_turns,
            self._max_turns,
        )
        return messages[cut_from:]
