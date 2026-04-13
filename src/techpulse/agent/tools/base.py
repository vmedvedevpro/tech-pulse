from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


class Tool(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]

    async def run(self, tool_input: dict[str, Any]) -> ToolResult: ...
