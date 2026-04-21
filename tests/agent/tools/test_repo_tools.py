import json
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.repo_tools import AddRepoTool, ListReposTool, RemoveRepoTool

_USER_ID = 7
_REPO = "microsoft/vscode"


def _make_repo(**overrides) -> AsyncMock:
    return AsyncMock(**overrides)


class TestAddRepoTool:
    @pytest.mark.asyncio
    async def test_returns_added_when_repo_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = False
        tool = AddRepoTool(repo, _USER_ID)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "added", "repo": _REPO}

    @pytest.mark.asyncio
    async def test_calls_add_repo_when_repo_is_new(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = False
        tool = AddRepoTool(repo, _USER_ID)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        repo.add_repo.assert_awaited_once_with(_USER_ID, _REPO)

    @pytest.mark.asyncio
    async def test_returns_already_watching_when_duplicate(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = True
        tool = AddRepoTool(repo, _USER_ID)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "already_watching", "repo": _REPO}

    @pytest.mark.asyncio
    async def test_does_not_call_add_when_already_watching(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = True
        tool = AddRepoTool(repo, _USER_ID)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        repo.add_repo.assert_not_awaited()


class TestListReposTool:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_repos(self):
        # Arrange
        repo = _make_repo()
        repo.get_repos.return_value = []
        tool = ListReposTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"repos": []}

    @pytest.mark.asyncio
    async def test_returns_repos_when_present(self):
        # Arrange
        repo = _make_repo()
        repo.get_repos.return_value = ["facebook/react", "microsoft/vscode"]
        tool = ListReposTool(repo, _USER_ID)

        # Act
        result = await tool.run({})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"repos": ["facebook/react", "microsoft/vscode"]}

    @pytest.mark.asyncio
    async def test_passes_user_id_to_repository(self):
        # Arrange
        repo = _make_repo()
        repo.get_repos.return_value = []
        tool = ListReposTool(repo, _USER_ID)

        # Act
        await tool.run({})

        # Assert
        repo.get_repos.assert_awaited_once_with(_USER_ID)


class TestRemoveRepoTool:
    @pytest.mark.asyncio
    async def test_returns_removed_when_present(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = True
        tool = RemoveRepoTool(repo, _USER_ID)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "removed", "repo": _REPO}

    @pytest.mark.asyncio
    async def test_calls_remove_repo_when_present(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = True
        tool = RemoveRepoTool(repo, _USER_ID)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        repo.remove_repo.assert_awaited_once_with(_USER_ID, _REPO)

    @pytest.mark.asyncio
    async def test_returns_not_found_when_absent(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = False
        tool = RemoveRepoTool(repo, _USER_ID)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"status": "not_found", "repo": _REPO}

    @pytest.mark.asyncio
    async def test_does_not_call_remove_when_absent(self):
        # Arrange
        repo = _make_repo()
        repo.has_repo.return_value = False
        tool = RemoveRepoTool(repo, _USER_ID)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        repo.remove_repo.assert_not_awaited()
