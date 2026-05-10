from typing import Any

from anthropic.types import ToolParam

from techpulse.agent.tools.base import Tool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    async def run(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        if tool_name not in self._tools:
            return ToolResult(content=f"Unknown tool: {tool_name}", is_error=True)
        return await self._tools[tool_name].run(tool_input)

    def get_schemas(self) -> list[ToolParam]:
        return [
            ToolParam(name=tool.name, description=tool.description, input_schema=tool.input_schema, strict=True)
            for tool in self._tools.values()
        ]
