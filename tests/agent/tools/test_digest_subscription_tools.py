import json
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.digest_subscription_tools import (
    GetWeeklyDigestStatusTool,
    SubscribeWeeklyDigestTool,
    UnsubscribeWeeklyDigestTool,
)

_USER_ID = 42


def _make_repo(**overrides) -> AsyncMock:
    return AsyncMock(**overrides)


class TestSubscribeWeeklyDigestTool:
    @pytest.mark.asyncio
    async def test_run_returns_subscribed_when_user_is_new(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = SubscribeWeeklyDigestTool(repo, _USER_ID)

        result = await tool.run({})

        assert not result.is_error
        assert json.loads(result.content) == {"status": "subscribed"}

    @pytest.mark.asyncio
    async def test_run_calls_subscribe_when_user_is_new(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = SubscribeWeeklyDigestTool(repo, _USER_ID)

        await tool.run({})

        repo.subscribe.assert_awaited_once_with(_USER_ID)

    @pytest.mark.asyncio
    async def test_run_returns_already_subscribed_when_duplicate(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = SubscribeWeeklyDigestTool(repo, _USER_ID)

        result = await tool.run({})

        assert json.loads(result.content) == {"status": "already_subscribed"}

    @pytest.mark.asyncio
    async def test_run_does_not_call_subscribe_when_already_subscribed(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = SubscribeWeeklyDigestTool(repo, _USER_ID)

        await tool.run({})

        repo.subscribe.assert_not_awaited()


class TestUnsubscribeWeeklyDigestTool:
    @pytest.mark.asyncio
    async def test_run_returns_unsubscribed_when_user_is_subscribed(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = UnsubscribeWeeklyDigestTool(repo, _USER_ID)

        result = await tool.run({})

        assert json.loads(result.content) == {"status": "unsubscribed"}

    @pytest.mark.asyncio
    async def test_run_calls_unsubscribe_when_user_is_subscribed(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = UnsubscribeWeeklyDigestTool(repo, _USER_ID)

        await tool.run({})

        repo.unsubscribe.assert_awaited_once_with(_USER_ID)

    @pytest.mark.asyncio
    async def test_run_returns_not_subscribed_when_user_is_absent(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = UnsubscribeWeeklyDigestTool(repo, _USER_ID)

        result = await tool.run({})

        assert json.loads(result.content) == {"status": "not_subscribed"}

    @pytest.mark.asyncio
    async def test_run_does_not_call_unsubscribe_when_user_is_absent(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = UnsubscribeWeeklyDigestTool(repo, _USER_ID)

        await tool.run({})

        repo.unsubscribe.assert_not_awaited()


class TestGetWeeklyDigestStatusTool:
    @pytest.mark.asyncio
    async def test_run_returns_true_when_subscribed(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = GetWeeklyDigestStatusTool(repo, _USER_ID)

        result = await tool.run({})

        assert json.loads(result.content) == {"subscribed": True}

    @pytest.mark.asyncio
    async def test_run_returns_false_when_not_subscribed(self):
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = GetWeeklyDigestStatusTool(repo, _USER_ID)

        result = await tool.run({})

        assert json.loads(result.content) == {"subscribed": False}
