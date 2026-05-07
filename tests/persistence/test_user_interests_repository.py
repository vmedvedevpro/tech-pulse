import pytest

from tests.persistence.fakes import FakeInterestsRepository


@pytest.fixture
def repo():
    return FakeInterestsRepository()


class TestAddInterest:
    async def test_marks_interest_as_known_when_called(self, repo):
        await repo.add_interest(user_id=1, interest="rust")

        assert await repo.has_interest(user_id=1, interest="rust")

    async def test_stores_interest_when_added(self, repo):
        await repo.add_interest(user_id=1, interest="rust")

        assert await repo.get_interests(user_id=1) == ["rust"]

    async def test_adding_same_interest_twice_does_not_duplicate(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="rust")

        assert len(await repo.get_interests(user_id=1)) == 1

    async def test_interests_are_isolated_per_user(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=2, interest="golang")

        assert await repo.get_interests(user_id=1) == ["rust"]
        assert await repo.get_interests(user_id=2) == ["golang"]


class TestRemoveInterest:
    async def test_removes_interest_when_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.remove_interest(user_id=1, interest="rust")

        assert not await repo.has_interest(user_id=1, interest="rust")

    async def test_does_not_raise_when_interest_absent(self, repo):
        await repo.remove_interest(user_id=1, interest="unknown")

    async def test_only_removes_target_when_multiple_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="llm agents")

        await repo.remove_interest(user_id=1, interest="rust")

        assert await repo.get_interests(user_id=1) == ["llm agents"]


class TestGetInterests:
    async def test_returns_empty_list_when_no_interests(self, repo):
        assert await repo.get_interests(user_id=99) == []

    async def test_returns_all_interests_sorted(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="llm agents")

        assert await repo.get_interests(user_id=1) == ["llm agents", "rust"]


class TestHasInterest:
    async def test_returns_false_when_absent(self, repo):
        assert not await repo.has_interest(user_id=1, interest="rust")

    async def test_returns_true_when_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        assert await repo.has_interest(user_id=1, interest="rust")

    async def test_returns_false_after_remove(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.remove_interest(user_id=1, interest="rust")
        assert not await repo.has_interest(user_id=1, interest="rust")
