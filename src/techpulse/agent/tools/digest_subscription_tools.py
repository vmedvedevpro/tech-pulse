import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.persistence.repositories.protocols import DigestSubscriptionRepositoryProtocol


class SubscribeWeeklyDigestTool(Tool):
    name = "subscribe_weekly_digest"
    description = (
        "Enables automatic weekly digest delivery for the user. "
        "Once subscribed, the user will receive a digest of new YouTube videos and "
        "GitHub releases once per week at a fixed server-defined day and time. "
        "Use this when the user asks to enable, turn on, or start receiving regular digests."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: DigestSubscriptionRepositoryProtocol, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)

        if await self._repo.is_subscribed(self._user_id):
            log.debug("already subscribed")
            return ToolResult(content=json.dumps({"status": "already_subscribed"}))

        await self._repo.subscribe(self._user_id)
        log.info("subscribed to weekly digest")
        return ToolResult(content=json.dumps({"status": "subscribed"}))


class UnsubscribeWeeklyDigestTool(Tool):
    name = "unsubscribe_weekly_digest"
    description = (
        "Disables automatic weekly digest delivery for the user. "
        "Use this when the user asks to disable, turn off, stop, or unsubscribe from regular digests."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: DigestSubscriptionRepositoryProtocol, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)

        if not await self._repo.is_subscribed(self._user_id):
            log.debug("not subscribed")
            return ToolResult(content=json.dumps({"status": "not_subscribed"}))

        await self._repo.unsubscribe(self._user_id)
        log.info("unsubscribed from weekly digest")
        return ToolResult(content=json.dumps({"status": "unsubscribed"}))


class GetWeeklyDigestStatusTool(Tool):
    name = "get_weekly_digest_status"
    description = (
        "Returns whether the user is currently subscribed to the automatic weekly digest. "
        "Use this when the user asks about their digest schedule, status, or whether digests are enabled."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: DigestSubscriptionRepositoryProtocol, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)
        subscribed = await self._repo.is_subscribed(self._user_id)
        log.debug("status | subscribed={}", subscribed)
        return ToolResult(content=json.dumps({"subscribed": subscribed}))
