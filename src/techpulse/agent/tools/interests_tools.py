import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.persistence.user_interests_repository import InterestsRepository

_INTEREST_PARAM = {
    "type": "string",
    "description": "A topic the user is interested in, e.g. 'rust', 'distributed systems', 'LLM agents'.",
}


class AddInterestTool(Tool):
    name = "add_interest"
    description = (
        "Saves a topic to the user's interests list. "
        "Use this when the user asks to add, track, or follow a topic. "
        "Requires the topic name."
    )
    input_schema = {
        "type": "object",
        "properties": {"interest": _INTEREST_PARAM},
        "required": ["interest"],
        "additionalProperties": False,
    }

    def __init__(self, repository: InterestsRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        interest: str = tool_input["interest"]
        log = logger.bind(user_id=self._user_id, interest=interest)
        log.debug("checking interest")

        if await self._repo.has_interest(self._user_id, interest):
            log.debug("already present")
            return ToolResult(
                content=json.dumps({"status": "already_present", "interest": interest}, ensure_ascii=False)
            )

        await self._repo.add_interest(self._user_id, interest)
        log.info("added")
        return ToolResult(
            content=json.dumps({"status": "added", "interest": interest}, ensure_ascii=False)
        )


class ListInterestsTool(Tool):
    name = "list_interests"
    description = (
        "Returns the list of topics the user is currently interested in. "
        "Use this when the user asks to see, show, or list their interests."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: InterestsRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)
        log.debug("fetching interests")

        interests = await self._repo.get_interests(self._user_id)
        log.debug("count={}", len(interests))

        return ToolResult(content=json.dumps({"interests": interests}, ensure_ascii=False))


class RemoveInterestTool(Tool):
    name = "remove_interest"
    description = (
        "Removes a topic from the user's interests list. "
        "Use this when the user asks to remove, delete, or drop a topic. "
        "If uncertain about the exact name, call list_interests first."
    )
    input_schema = {
        "type": "object",
        "properties": {"interest": _INTEREST_PARAM},
        "required": ["interest"],
        "additionalProperties": False,
    }

    def __init__(self, repository: InterestsRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        interest: str = tool_input["interest"]
        log = logger.bind(user_id=self._user_id, interest=interest)
        log.debug("checking interest")

        if not await self._repo.has_interest(self._user_id, interest):
            log.debug("not present")
            return ToolResult(
                content=json.dumps({"status": "not_found", "interest": interest}, ensure_ascii=False)
            )

        await self._repo.remove_interest(self._user_id, interest)
        log.info("removed")
        return ToolResult(
            content=json.dumps({"status": "removed", "interest": interest}, ensure_ascii=False)
        )
