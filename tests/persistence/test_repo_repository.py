import pytest

from tests.persistence.fakes import FakeRepoRepository


@pytest.fixture
def repo():
    return FakeRepoRepository()


class TestAddRepo:
    async def test_marks_repo_as_known_when_added(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")

        assert await repo.has_repo(user_id=1, repo="owner/repo")

    async def test_stores_repo_in_list(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")

        assert await repo.get_repos(user_id=1) == ["owner/repo"]

    async def test_adding_same_repo_twice_does_not_duplicate(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")
        await repo.add_repo(user_id=1, repo="owner/repo")

        assert len(await repo.get_repos(user_id=1)) == 1

    async def test_repos_are_isolated_per_user(self, repo):
        await repo.add_repo(user_id=1, repo="owner/a")
        await repo.add_repo(user_id=2, repo="owner/b")

        assert await repo.get_repos(user_id=1) == ["owner/a"]
        assert await repo.get_repos(user_id=2) == ["owner/b"]


class TestRemoveRepo:
    async def test_removes_repo_when_present(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")
        await repo.remove_repo(user_id=1, repo="owner/repo")

        assert not await repo.has_repo(user_id=1, repo="owner/repo")

    async def test_does_not_raise_when_repo_absent(self, repo):
        await repo.remove_repo(user_id=1, repo="unknown/repo")

    async def test_only_removes_target_when_multiple_present(self, repo):
        await repo.add_repo(user_id=1, repo="owner/a")
        await repo.add_repo(user_id=1, repo="owner/b")

        await repo.remove_repo(user_id=1, repo="owner/a")

        assert await repo.get_repos(user_id=1) == ["owner/b"]


class TestGetRepos:
    async def test_returns_empty_list_when_no_repos(self, repo):
        assert await repo.get_repos(user_id=99) == []

    async def test_returns_repos_sorted(self, repo):
        await repo.add_repo(user_id=1, repo="owner/z")
        await repo.add_repo(user_id=1, repo="owner/a")

        assert await repo.get_repos(user_id=1) == ["owner/a", "owner/z"]


class TestHasRepo:
    async def test_returns_false_when_absent(self, repo):
        assert not await repo.has_repo(user_id=1, repo="owner/repo")

    async def test_returns_true_when_present(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")
        assert await repo.has_repo(user_id=1, repo="owner/repo")

    async def test_returns_false_after_remove(self, repo):
        await repo.add_repo(user_id=1, repo="owner/repo")
        await repo.remove_repo(user_id=1, repo="owner/repo")
        assert not await repo.has_repo(user_id=1, repo="owner/repo")
