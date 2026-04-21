import json
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.interests_tools import (
    AddInterestTool,
    ListInterestsTool,
    RemoveInterestTool,
)

_USER_ID = 42
_INTEREST = "rust"


def _make_repo(**overrides) -> AsyncMock:
    return AsyncMock(**overrides)


class TestAddInterestTool:
    @pytest.mark.asyncio
    async def test_run_returns_added_when_interest_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = False
        tool = AddInterestTool(repo, _USER_ID)

        # Act
        result = await tool.run({"interest": _INTEREST})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "added", "interest": _INTEREST}

    @pytest.mark.asyncio
    async def test_run_calls_add_interest_when_interest_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = False
        tool = AddInterestTool(repo, _USER_ID)

        # Act
        await tool.run({"interest": _INTEREST})

        # Assert
        repo.add_interest.assert_awaited_once_with(_USER_ID, _INTEREST)

    @pytest.mark.asyncio
    async def test_run_returns_already_present_when_duplicate(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = True
        tool = AddInterestTool(repo, _USER_ID)

        # Act
        result = await tool.run({"interest": _INTEREST})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "already_present", "interest": _INTEREST}

    @pytest.mark.asyncio
    async def test_run_does_not_call_add_when_already_present(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = True
        tool = AddInterestTool(repo, _USER_ID)

        # Act
        await tool.run({"interest": _INTEREST})

        # Assert
        repo.add_interest.assert_not_awaited()


class TestListInterestsTool:
    @pytest.mark.asyncio
    async def test_run_returns_empty_list_when_no_interests(self):
        # Arrange
        repo = _make_repo()
        repo.get_interests.return_value = []
        tool = ListInterestsTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"interests": []}

    @pytest.mark.asyncio
    async def test_run_returns_interests_when_present(self):
        # Arrange
        repo = _make_repo()
        repo.get_interests.return_value = ["llm agents", "rust"]
        tool = ListInterestsTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"interests": ["llm agents", "rust"]}

    @pytest.mark.asyncio
    async def test_run_passes_user_id_to_repository(self):
        # Arrange
        repo = _make_repo()
        repo.get_interests.return_value = []
        tool = ListInterestsTool(repo, _USER_ID)

        # Act
        await tool.run({})

        # Assert
        repo.get_interests.assert_awaited_once_with(_USER_ID)


class TestRemoveInterestTool:
    @pytest.mark.asyncio
    async def test_run_returns_removed_when_interest_exists(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = True
        tool = RemoveInterestTool(repo, _USER_ID)

        # Act
        result = await tool.run({"interest": _INTEREST})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "removed", "interest": _INTEREST}

    @pytest.mark.asyncio
    async def test_run_calls_remove_interest_when_interest_exists(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = True
        tool = RemoveInterestTool(repo, _USER_ID)

        # Act
        await tool.run({"interest": _INTEREST})

        # Assert
        repo.remove_interest.assert_awaited_once_with(_USER_ID, _INTEREST)

    @pytest.mark.asyncio
    async def test_run_returns_not_found_when_interest_absent(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = False
        tool = RemoveInterestTool(repo, _USER_ID)

        # Act
        result = await tool.run({"interest": _INTEREST})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "not_found", "interest": _INTEREST}

    @pytest.mark.asyncio
    async def test_run_does_not_call_remove_when_interest_absent(self):
        # Arrange
        repo = _make_repo()
        repo.has_interest.return_value = False
        tool = RemoveInterestTool(repo, _USER_ID)

        # Act
        await tool.run({"interest": _INTEREST})

        # Assert
        repo.remove_interest.assert_not_awaited()
