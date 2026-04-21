import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.github_tools import GetLatestReleaseTool, GetRepoInfoTool
from techpulse.integrations.github.github_client import GitHubError, RepoInfo
from techpulse.integrations.github.models import ReleaseInfo

_REPO = "owner/repo"
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

_REPO_INFO = RepoInfo(
    full_name=_REPO,
    description="A code editor",
    language="TypeScript",
    stars=150_000,
    topics=["editor", "ide"],
    url="https://github.com/owner/repo",
)

_RELEASE_INFO = ReleaseInfo(
    repo=_REPO,
    tag="v1.2.3",
    name="Release 1.2.3",
    body="Bug fixes and improvements",
    published_at=_NOW,
    url="https://github.com/owner/repo/releases/tag/v1.2.3",
)


def _make_client(**overrides) -> AsyncMock:
    return AsyncMock(**overrides)


class TestGetRepoInfoTool:
    @pytest.mark.asyncio
    async def test_returns_repo_info_on_success(self):
        # Arrange
        client = _make_client()
        client.get_repo_info.return_value = _REPO_INFO
        tool = GetRepoInfoTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["full_name"] == _REPO
        assert payload["stars"] == 150_000
        assert payload["topics"] == ["editor", "ide"]
        assert payload["language"] == "TypeScript"

    @pytest.mark.asyncio
    async def test_returns_error_on_github_error(self):
        # Arrange
        client = _make_client()
        client.get_repo_info.side_effect = GitHubError("API error: 404")
        tool = GetRepoInfoTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert result.is_error
        assert "API error: 404" in result.content

    @pytest.mark.asyncio
    async def test_passes_repo_to_client(self):
        # Arrange
        client = _make_client()
        client.get_repo_info.return_value = _REPO_INFO
        tool = GetRepoInfoTool(client)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        client.get_repo_info.assert_awaited_once_with(_REPO)

    @pytest.mark.asyncio
    async def test_returns_url_in_payload(self):
        # Arrange
        client = _make_client()
        client.get_repo_info.return_value = _REPO_INFO
        tool = GetRepoInfoTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        payload = json.loads(result.content)
        assert payload["url"] == "https://github.com/owner/repo"


class TestGetLatestReleaseTool:
    @pytest.mark.asyncio
    async def test_returns_release_info_on_success(self):
        # Arrange
        client = _make_client()
        client.get_latest_release.return_value = _RELEASE_INFO
        tool = GetLatestReleaseTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["tag"] == "v1.2.3"
        assert payload["repo"] == _REPO
        assert payload["published_at"] == _NOW.isoformat()

    @pytest.mark.asyncio
    async def test_returns_no_releases_status_when_none_found(self):
        # Arrange
        client = _make_client()
        client.get_latest_release.return_value = None
        tool = GetLatestReleaseTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "no_releases", "repo": _REPO}

    @pytest.mark.asyncio
    async def test_returns_error_on_github_error(self):
        # Arrange
        client = _make_client()
        client.get_latest_release.side_effect = GitHubError("Not found: 404")
        tool = GetLatestReleaseTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        assert result.is_error
        assert "Not found: 404" in result.content

    @pytest.mark.asyncio
    async def test_passes_repo_to_client(self):
        # Arrange
        client = _make_client()
        client.get_latest_release.return_value = None
        tool = GetLatestReleaseTool(client)

        # Act
        await tool.run({"repo": _REPO})

        # Assert
        client.get_latest_release.assert_awaited_once_with(_REPO)

    @pytest.mark.asyncio
    async def test_release_body_included_in_payload(self):
        # Arrange
        client = _make_client()
        client.get_latest_release.return_value = _RELEASE_INFO
        tool = GetLatestReleaseTool(client)

        # Act
        result = await tool.run({"repo": _REPO})

        # Assert
        payload = json.loads(result.content)
        assert payload["body"] == "Bug fixes and improvements"
