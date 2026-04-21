import fakeredis.aioredis
import pytest

from techpulse.persistence.user_interests_repository import InterestsRepository


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def repo(redis):
    return InterestsRepository(redis)


class TestAddInterest:
    @pytest.mark.asyncio
    async def test_marks_interest_as_known_when_called(self, repo):
        await repo.add_interest(user_id=1, interest="rust")

        assert await repo.has_interest(user_id=1, interest="rust")

    @pytest.mark.asyncio
    async def test_stores_interest_when_added(self, repo):
        await repo.add_interest(user_id=1, interest="rust")

        interests = await repo.get_interests(user_id=1)
        assert interests == ["rust"]

    @pytest.mark.asyncio
    async def test_adding_same_interest_twice_does_not_duplicate(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="rust")

        interests = await repo.get_interests(user_id=1)
        assert len(interests) == 1

    @pytest.mark.asyncio
    async def test_interests_are_isolated_per_user(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=2, interest="golang")

        user1 = await repo.get_interests(user_id=1)
        user2 = await repo.get_interests(user_id=2)

        assert user1 == ["rust"]
        assert user2 == ["golang"]


class TestRemoveInterest:
    @pytest.mark.asyncio
    async def test_removes_interest_when_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.remove_interest(user_id=1, interest="rust")

        assert not await repo.has_interest(user_id=1, interest="rust")

    @pytest.mark.asyncio
    async def test_does_not_raise_when_interest_absent(self, repo):
        await repo.remove_interest(user_id=1, interest="unknown")

    @pytest.mark.asyncio
    async def test_only_removes_target_when_multiple_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="llm agents")

        await repo.remove_interest(user_id=1, interest="rust")

        interests = await repo.get_interests(user_id=1)
        assert interests == ["llm agents"]


class TestGetInterests:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_interests(self, repo):
        result = await repo.get_interests(user_id=99)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_interests_sorted(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.add_interest(user_id=1, interest="llm agents")

        interests = await repo.get_interests(user_id=1)

        assert interests == ["llm agents", "rust"]


class TestHasInterest:
    @pytest.mark.asyncio
    async def test_returns_false_when_absent(self, repo):
        assert not await repo.has_interest(user_id=1, interest="rust")

    @pytest.mark.asyncio
    async def test_returns_true_when_present(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        assert await repo.has_interest(user_id=1, interest="rust")

    @pytest.mark.asyncio
    async def test_returns_false_after_remove(self, repo):
        await repo.add_interest(user_id=1, interest="rust")
        await repo.remove_interest(user_id=1, interest="rust")
        assert not await repo.has_interest(user_id=1, interest="rust")
