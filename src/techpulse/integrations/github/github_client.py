import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from github import Auth, Github
from github.GithubException import GithubException
from loguru import logger

from techpulse.integrations.github.models import ReleaseInfo


class GitHubError(Exception):
    pass


@dataclass(frozen=True)
class RepoInfo:
    full_name: str
    description: str
    language: str | None
    stars: int
    topics: list[str]
    url: str


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        auth = Auth.Token(token) if token else None
        self._gh = Github(auth=auth)

    async def get_repo_info(self, repo: str) -> RepoInfo:
        return await asyncio.to_thread(self._get_repo_info_sync, repo)

    def _get_repo_info_sync(self, repo: str) -> RepoInfo:
        try:
            gh_repo = self._gh.get_repo(repo)
        except GithubException as exc:
            raise GitHubError(f"GitHub API error for {repo}: {exc.status}") from exc

        logger.debug("github repo={} info fetched", repo)
        return RepoInfo(
            full_name=gh_repo.full_name,
            description=gh_repo.description or "",
            language=gh_repo.language,
            stars=gh_repo.stargazers_count,
            topics=gh_repo.get_topics(),
            url=gh_repo.html_url,
        )

    async def get_releases(self, repo: str, max_results: int = 5) -> list[ReleaseInfo]:
        return await asyncio.to_thread(self._get_releases_sync, repo, max_results)

    def _get_releases_sync(self, repo: str, max_results: int) -> list[ReleaseInfo]:
        try:
            gh_repo = self._gh.get_repo(repo)
            releases = gh_repo.get_releases()
        except GithubException as exc:
            raise GitHubError(f"GitHub API error for {repo}: {exc.status}") from exc

        result = []
        for release in releases:
            if len(result) >= max_results:
                break
            if release.draft or release.prerelease:
                continue
            published_at = release.published_at
            if published_at and published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            result.append(ReleaseInfo(
                repo=repo,
                tag=release.tag_name,
                name=release.title or release.tag_name,
                body=(release.body or "").strip(),
                published_at=published_at or datetime.now(timezone.utc),
                url=release.html_url,
            ))

        logger.debug("github repo={} releases_fetched={}", repo, len(result))
        return result

    async def get_latest_release(self, repo: str) -> ReleaseInfo | None:
        return await asyncio.to_thread(self._get_latest_release_sync, repo)

    def _get_latest_release_sync(self, repo: str) -> ReleaseInfo | None:
        try:
            gh_repo = self._gh.get_repo(repo)
            releases = gh_repo.get_releases()
        except GithubException as exc:
            raise GitHubError(f"GitHub API error for {repo}: {exc.status}") from exc

        for release in releases:
            if release.draft or release.prerelease:
                continue
            published_at = release.published_at
            if published_at and published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            logger.debug("github repo={} latest_release={}", repo, release.tag_name)
            return ReleaseInfo(
                repo=repo,
                tag=release.tag_name,
                name=release.title or release.tag_name,
                body=(release.body or "").strip(),
                published_at=published_at or datetime.now(timezone.utc),
                url=release.html_url,
            )

        return None

    def close(self) -> None:
        self._gh.close()
