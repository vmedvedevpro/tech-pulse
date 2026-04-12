from typing import Any

from techpulse.agent.tools.base import ToolResult, Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def run(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        if tool_name not in self._tools:
            return ToolResult(content=f"Unknown tool: {tool_name}", is_error=True)
        return self._tools[tool_name].run(tool_input)

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]
