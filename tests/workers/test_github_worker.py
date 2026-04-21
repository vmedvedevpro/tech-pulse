from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from techpulse.integrations.github.github_client import GitHubError
from techpulse.integrations.github.models import ReleaseInfo
from techpulse.workers.github_worker import GitHubWorker

_USER_ID = 5
_NOW = datetime(2024, 6, 1, tzinfo=timezone.utc)


def _release(repo: str, tag: str) -> ReleaseInfo:
    return ReleaseInfo(
        repo=repo,
        tag=tag,
        name=tag,
        body=f"Notes for {tag}",
        published_at=_NOW,
        url=f"https://github.com/{repo}/releases/tag/{tag}",
    )


def _make_worker(
        repos: list[str],
        releases_map: dict[str, list[ReleaseInfo]] | None = None,
        unseen_ids: list[str] | None = None,
) -> tuple[GitHubWorker, AsyncMock, AsyncMock, AsyncMock]:
    github = AsyncMock()
    repo_repo = AsyncMock()
    release_repo = AsyncMock()

    repo_repo.get_repos.return_value = repos

    async def get_releases(repo: str, max_results: int = 3) -> list[ReleaseInfo]:
        return (releases_map or {}).get(repo, [])

    github.get_releases.side_effect = get_releases
    release_repo.filter_unseen.return_value = unseen_ids if unseen_ids is not None else []

    worker = GitHubWorker(github, repo_repo, release_repo, _USER_ID)
    return worker, github, repo_repo, release_repo


class TestCollectNoRepos:
    @pytest.mark.asyncio
    async def test_returns_empty_when_user_has_no_repos(self):
        worker, *_ = _make_worker(repos=[])

        result = await worker.collect()

        assert result == []

    @pytest.mark.asyncio
    async def test_does_not_call_github_when_no_repos(self):
        worker, github, *_ = _make_worker(repos=[])

        await worker.collect()

        github.get_releases.assert_not_called()


class TestCollectNewReleases:
    @pytest.mark.asyncio
    async def test_returns_new_releases(self):
        rel = _release("owner/a", "v1.0")
        worker, *_ = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel]},
            unseen_ids=["owner/a@v1.0"],
        )

        result = await worker.collect()

        assert len(result) == 1
        assert result[0].repo == "owner/a"
        assert result[0].tag == "v1.0"
        assert result[0].release_id == "owner/a@v1.0"

    @pytest.mark.asyncio
    async def test_returns_releases_from_multiple_repos(self):
        rel_a = _release("owner/a", "v1.0")
        rel_b = _release("owner/b", "v2.0")
        worker, *_ = _make_worker(
            repos=["owner/a", "owner/b"],
            releases_map={"owner/a": [rel_a], "owner/b": [rel_b]},
            unseen_ids=["owner/a@v1.0", "owner/b@v2.0"],
        )

        result = await worker.collect()

        assert len(result) == 2
        release_ids = {r.release_id for r in result}
        assert release_ids == {"owner/a@v1.0", "owner/b@v2.0"}

    @pytest.mark.asyncio
    async def test_marks_new_releases_as_seen(self):
        rel = _release("owner/a", "v1.0")
        worker, _, _, release_repo = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel]},
            unseen_ids=["owner/a@v1.0"],
        )

        await worker.collect()

        release_repo.mark_many_seen.assert_awaited_once_with(_USER_ID, ["owner/a@v1.0"])

    @pytest.mark.asyncio
    async def test_digest_item_contains_correct_fields(self):
        rel = _release("owner/a", "v1.0")
        worker, *_ = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel]},
            unseen_ids=["owner/a@v1.0"],
        )

        result = await worker.collect()

        item = result[0]
        assert item.repo == "owner/a"
        assert item.tag == "v1.0"
        assert item.name == "v1.0"
        assert item.body == "Notes for v1.0"
        assert item.published_at == _NOW
        assert item.url == "https://github.com/owner/a/releases/tag/v1.0"


class TestCollectSeenReleases:
    @pytest.mark.asyncio
    async def test_returns_empty_when_all_releases_already_seen(self):
        rel = _release("owner/a", "v1.0")
        worker, *_ = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel]},
            unseen_ids=[],
        )

        result = await worker.collect()

        assert result == []

    @pytest.mark.asyncio
    async def test_does_not_mark_seen_when_nothing_new(self):
        rel = _release("owner/a", "v1.0")
        worker, _, _, release_repo = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel]},
            unseen_ids=[],
        )

        await worker.collect()

        release_repo.mark_many_seen.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_filters_seen_and_returns_only_new(self):
        rel_old = _release("owner/a", "v1.0")
        rel_new = _release("owner/a", "v1.1")
        worker, *_ = _make_worker(
            repos=["owner/a"],
            releases_map={"owner/a": [rel_old, rel_new]},
            unseen_ids=["owner/a@v1.1"],
        )

        result = await worker.collect()

        assert len(result) == 1
        assert result[0].tag == "v1.1"


class TestCollectGitHubErrors:
    @pytest.mark.asyncio
    async def test_skips_repo_on_github_error(self):
        rel_b = _release("owner/b", "v2.0")

        github = AsyncMock()
        repo_repo = AsyncMock()
        release_repo = AsyncMock()

        repo_repo.get_repos.return_value = ["owner/a", "owner/b"]

        async def get_releases(repo: str, max_results: int = 3) -> list[ReleaseInfo]:
            if repo == "owner/a":
                raise GitHubError("rate limit exceeded")
            return [rel_b]

        github.get_releases.side_effect = get_releases
        release_repo.filter_unseen.return_value = ["owner/b@v2.0"]

        worker = GitHubWorker(github, repo_repo, release_repo, _USER_ID)
        result = await worker.collect()

        assert len(result) == 1
        assert result[0].repo == "owner/b"

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_repos_fail(self):
        github = AsyncMock()
        repo_repo = AsyncMock()
        release_repo = AsyncMock()

        repo_repo.get_repos.return_value = ["owner/a"]
        github.get_releases.side_effect = GitHubError("server error")

        worker = GitHubWorker(github, repo_repo, release_repo, _USER_ID)
        result = await worker.collect()

        assert result == []


class TestCollectMaxPerRepo:
    @pytest.mark.asyncio
    async def test_passes_max_per_repo_to_github_client(self):
        worker, github, *_ = _make_worker(repos=["owner/a"], releases_map={}, unseen_ids=[])

        await worker.collect(max_per_repo=5)

        github.get_releases.assert_awaited_once_with("owner/a", max_results=5)

    @pytest.mark.asyncio
    async def test_default_max_per_repo_is_three(self):
        worker, github, *_ = _make_worker(repos=["owner/a"], releases_map={}, unseen_ids=[])

        await worker.collect()

        github.get_releases.assert_awaited_once_with("owner/a", max_results=3)
