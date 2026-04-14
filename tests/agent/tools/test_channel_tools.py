import json
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.channel_tools import (
    AddChannelTool,
    ListChannelsTool,
    RemoveChannelTool,
)
from techpulse.persistence.channel_repository import ChannelInfo

_USER_ID = 42
_HANDLE = "@nickchapsas"


def _make_repo(**overrides) -> AsyncMock:
    return AsyncMock(**overrides)


class TestAddChannelTool:
    @pytest.mark.asyncio
    async def test_run_returns_subscribed_when_channel_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = AddChannelTool(repo, _USER_ID)

        # Act
        result = await tool.run({"channel_handle": _HANDLE})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "subscribed", "channel_handle": _HANDLE}

    @pytest.mark.asyncio
    async def test_run_calls_subscribe_when_channel_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = AddChannelTool(repo, _USER_ID)

        # Act
        await tool.run({"channel_handle": _HANDLE})

        # Assert
        repo.subscribe.assert_awaited_once_with(_USER_ID, _HANDLE)

    @pytest.mark.asyncio
    async def test_run_returns_already_subscribed_when_duplicate(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = AddChannelTool(repo, _USER_ID)

        # Act
        result = await tool.run({"channel_handle": _HANDLE})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "already_subscribed", "channel_handle": _HANDLE}

    @pytest.mark.asyncio
    async def test_run_does_not_call_subscribe_when_already_subscribed(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = AddChannelTool(repo, _USER_ID)

        # Act
        await tool.run({"channel_handle": _HANDLE})

        # Assert
        repo.subscribe.assert_not_awaited()


class TestListChannelsTool:
    @pytest.mark.asyncio
    async def test_run_returns_empty_list_when_no_subscriptions(self):
        # Arrange
        repo = _make_repo()
        repo.get_subscriptions.return_value = []
        tool = ListChannelsTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"channels": []}

    @pytest.mark.asyncio
    async def test_run_returns_channel_handles_when_subscriptions_exist(self):
        # Arrange
        repo = _make_repo()
        repo.get_subscriptions.return_value = [
            ChannelInfo(handle="@chan_a"),
            ChannelInfo(handle="@chan_b"),
        ]
        tool = ListChannelsTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"channels": ["@chan_a", "@chan_b"]}

    @pytest.mark.asyncio
    async def test_run_passes_user_id_to_repository(self):
        # Arrange
        repo = _make_repo()
        repo.get_subscriptions.return_value = []
        tool = ListChannelsTool(repo, _USER_ID)

        # Act
        await tool.run({})

        # Assert
        repo.get_subscriptions.assert_awaited_once_with(_USER_ID)


class TestRemoveChannelTool:
    @pytest.mark.asyncio
    async def test_run_returns_removed_when_channel_exists(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = RemoveChannelTool(repo, _USER_ID)

        # Act
        result = await tool.run({"channel_handle": _HANDLE})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "removed", "channel_handle": _HANDLE}

    @pytest.mark.asyncio
    async def test_run_calls_unsubscribe_when_channel_exists(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = True
        tool = RemoveChannelTool(repo, _USER_ID)

        # Act
        await tool.run({"channel_handle": _HANDLE})

        # Assert
        repo.unsubscribe.assert_awaited_once_with(_USER_ID, _HANDLE)

    @pytest.mark.asyncio
    async def test_run_returns_not_found_when_channel_not_subscribed(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = RemoveChannelTool(repo, _USER_ID)

        # Act
        result = await tool.run({"channel_handle": _HANDLE})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "not_found", "channel_handle": _HANDLE}

    @pytest.mark.asyncio
    async def test_run_does_not_call_unsubscribe_when_not_subscribed(self):
        # Arrange
        repo = _make_repo()
        repo.is_subscribed.return_value = False
        tool = RemoveChannelTool(repo, _USER_ID)

        # Act
        await tool.run({"channel_handle": _HANDLE})

        # Assert
        repo.unsubscribe.assert_not_awaited()
