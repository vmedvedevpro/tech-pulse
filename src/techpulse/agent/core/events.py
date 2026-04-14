from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


@dataclass(frozen=True, slots=True)
class ToolUseStarted:
    name: str


@dataclass(frozen=True, slots=True)
class ToolUseCompleted:
    name: str
    ok: bool


AgentEvent = TextDelta | ToolUseStarted | ToolUseCompleted
