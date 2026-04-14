from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


AgentEvent = TextDelta
