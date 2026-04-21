import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.persistence.repo_repository import RepoRepository

_REPO_PARAM = {
    "type": "string",
    "description": "GitHub repository in 'owner/repo' format, e.g. 'microsoft/vscode'.",
}


class AddRepoTool(Tool):
    name = "add_repo"
    description = (
        "Saves a GitHub repository to the user's watch list. "
        "Use this when the user asks to add, track, or follow a repository. "
        "Requires the repository in 'owner/repo' format."
    )
    input_schema = {
        "type": "object",
        "properties": {"repo": _REPO_PARAM},
        "required": ["repo"],
        "additionalProperties": False,
    }

    def __init__(self, repository: RepoRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        repo: str = tool_input["repo"]
        log = logger.bind(user_id=self._user_id, repo=repo)

        if await self._repo.has_repo(self._user_id, repo):
            log.debug("already watching")
            return ToolResult(content=json.dumps({"status": "already_watching", "repo": repo}))

        await self._repo.add_repo(self._user_id, repo)
        log.info("watching")
        return ToolResult(content=json.dumps({"status": "added", "repo": repo}))


class ListReposTool(Tool):
    name = "list_repos"
    description = (
        "Returns the list of GitHub repositories the user is currently watching. "
        "Use this when the user asks to see or list their tracked repositories."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, repository: RepoRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(user_id=self._user_id)
        repos = await self._repo.get_repos(self._user_id)
        log.debug("count={}", len(repos))
        return ToolResult(content=json.dumps({"repos": repos}))


class RemoveRepoTool(Tool):
    name = "remove_repo"
    description = (
        "Removes a GitHub repository from the user's watch list. "
        "Use this when the user asks to remove, untrack, or stop following a repository. "
        "If uncertain about the exact name, call list_repos first."
    )
    input_schema = {
        "type": "object",
        "properties": {"repo": _REPO_PARAM},
        "required": ["repo"],
        "additionalProperties": False,
    }

    def __init__(self, repository: RepoRepository, user_id: int) -> None:
        self._repo = repository
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        repo: str = tool_input["repo"]
        log = logger.bind(user_id=self._user_id, repo=repo)

        if not await self._repo.has_repo(self._user_id, repo):
            log.debug("not watching")
            return ToolResult(content=json.dumps({"status": "not_found", "repo": repo}))

        await self._repo.remove_repo(self._user_id, repo)
        log.info("removed")
        return ToolResult(content=json.dumps({"status": "removed", "repo": repo}))
