import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.integrations.github.github_client import GitHubClient, GitHubError

_REPO_PARAM = {
    "type": "string",
    "description": "GitHub repository in 'owner/repo' format, e.g. 'microsoft/vscode'.",
}


class GetRepoInfoTool(Tool):
    name = "get_repo_info"
    description = (
        "Fetches basic information about a GitHub repository: description, "
        "primary language, star count, and topics. "
        "Use this when the user shares a GitHub repo link or asks what a project is about."
    )
    input_schema = {
        "type": "object",
        "properties": {"repo": _REPO_PARAM},
        "required": ["repo"],
        "additionalProperties": False,
    }

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        repo: str = tool_input["repo"]
        logger.debug("get_repo_info repo={}", repo)
        try:
            info = await self._client.get_repo_info(repo)
        except GitHubError as exc:
            return ToolResult(content=str(exc), is_error=True)

        payload = {
            "full_name": info.full_name,
            "description": info.description,
            "language": info.language,
            "stars": info.stars,
            "topics": info.topics,
            "url": info.url,
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))


class GetLatestReleaseTool(Tool):
    name = "get_latest_release"
    description = (
        "Fetches the latest stable release of a GitHub repository: tag, title, "
        "release notes, and publication date. Skips drafts and pre-releases. "
        "Use this when the user asks about the latest release or recent changes in a repo."
    )
    input_schema = {
        "type": "object",
        "properties": {"repo": _REPO_PARAM},
        "required": ["repo"],
        "additionalProperties": False,
    }

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        repo: str = tool_input["repo"]
        logger.debug("get_latest_release repo={}", repo)
        try:
            release = await self._client.get_latest_release(repo)
        except GitHubError as exc:
            return ToolResult(content=str(exc), is_error=True)

        if release is None:
            return ToolResult(content=json.dumps({"status": "no_releases", "repo": repo}))

        payload = {
            "repo": release.repo,
            "tag": release.tag,
            "name": release.name,
            "body": release.body,
            "published_at": release.published_at.isoformat(),
            "url": release.url,
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
