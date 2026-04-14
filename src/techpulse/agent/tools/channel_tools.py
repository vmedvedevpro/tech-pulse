import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.persistence.channel_repository import ChannelRepository

_HANDLE_PARAM = {
    "type": "string",
    "description": "YouTube channel handle, e.g. '@nickchapsas'.",
}


class AddChannelTool(Tool):
    name = "add_channel"
    description = (
        "Saves a YouTube channel to the user's subscription list. "
        "Use this when the user asks to add, track, follow, or subscribe to a channel. "
        "Requires the channel handle (e.g. '@nickchapsas')."
    )
    input_schema = {
        "type": "object",
        "properties": {"channel_handle": _HANDLE_PARAM},
        "required": ["channel_handle"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ChannelRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        handle: str = tool_input["channel_handle"]
        log = logger.bind(user_id=self._user_id, handle=handle)
        log.debug("add_channel | checking")

        if await self._repo.is_subscribed(self._user_id, handle):
            log.debug("add_channel | already subscribed")
            return ToolResult(
                content=json.dumps({"status": "already_subscribed", "channel_handle": handle}, ensure_ascii=False)
            )

        await self._repo.subscribe(self._user_id, handle)
        log.info("add_channel | subscribed")
        return ToolResult(
            content=json.dumps({"status": "subscribed", "channel_handle": handle}, ensure_ascii=False)
        )


class ListChannelsTool(Tool):
    name = "list_channels"
    description = (
        "Returns the list of YouTube channels the user is currently subscribed to. "
        "Use this when the user asks to see, show, or list their channels."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: ChannelRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)
        log.debug("list_channels | fetching")

        channels = await self._repo.get_subscriptions(self._user_id)
        log.debug("list_channels | count={}", len(channels))

        payload = {"channels": [c.handle for c in channels]}
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))


class RemoveChannelTool(Tool):
    name = "remove_channel"
    description = (
        "Removes a YouTube channel from the user's subscription list. "
        "Use this when the user asks to remove, delete, unsubscribe, or stop tracking a channel. "
        "If uncertain about the handle, call list_channels first."
    )
    input_schema = {
        "type": "object",
        "properties": {"channel_handle": _HANDLE_PARAM},
        "required": ["channel_handle"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ChannelRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        handle: str = tool_input["channel_handle"]
        log = logger.bind(user_id=self._user_id, handle=handle)
        log.debug("remove_channel | checking")

        if not await self._repo.is_subscribed(self._user_id, handle):
            log.debug("remove_channel | not subscribed")
            return ToolResult(
                content=json.dumps({"status": "not_found", "channel_handle": handle}, ensure_ascii=False)
            )

        await self._repo.unsubscribe(self._user_id, handle)
        log.info("remove_channel | removed")
        return ToolResult(
            content=json.dumps({"status": "removed", "channel_handle": handle}, ensure_ascii=False)
        )
