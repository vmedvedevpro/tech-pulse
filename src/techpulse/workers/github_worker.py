from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from techpulse.integrations.github.github_client import GitHubClient, GitHubError
from techpulse.persistence.release_repository import ReleaseRepository
from techpulse.persistence.repo_repository import RepoRepository


@dataclass
class ReleaseDigestItem:
    release_id: str  # "owner/repo@tag"
    repo: str
    tag: str
    name: str
    body: str
    published_at: datetime
    url: str


class GitHubWorker:
    def __init__(
            self,
            github: GitHubClient,
            repo_repo: RepoRepository,
            release_repo: ReleaseRepository,
            user_id: int,
    ) -> None:
        self._github = github
        self._repo_repo = repo_repo
        self._release_repo = release_repo
        self._user_id = user_id

    async def collect(self, max_per_repo: int = 3) -> list[ReleaseDigestItem]:
        repos = await self._repo_repo.get_repos(self._user_id)
        if not repos:
            logger.info("no watched repos | user_id={}", self._user_id)
            return []

        all_releases = []
        for repo in repos:
            try:
                releases = await self._github.get_releases(repo, max_results=max_per_repo)
                all_releases.extend(releases)
                logger.debug("repo={} fetched={}", repo, len(releases))
            except GitHubError as exc:
                logger.warning("repo={} error | {}", repo, exc)

        if not all_releases:
            return []

        release_ids = [f"{r.repo}@{r.tag}" for r in all_releases]
        unseen_ids = set(await self._release_repo.filter_unseen(self._user_id, release_ids))
        new_releases = [r for r, rid in zip(all_releases, release_ids) if rid in unseen_ids]

        logger.info("user_id={} total={} new={}", self._user_id, len(all_releases), len(new_releases))

        if not new_releases:
            return []

        await self._release_repo.mark_many_seen(self._user_id, [f"{r.repo}@{r.tag}" for r in new_releases])

        return [
            ReleaseDigestItem(
                release_id=f"{r.repo}@{r.tag}",
                repo=r.repo,
                tag=r.tag,
                name=r.name,
                body=r.body,
                published_at=r.published_at,
                url=r.url,
            )
            for r in new_releases
        ]
