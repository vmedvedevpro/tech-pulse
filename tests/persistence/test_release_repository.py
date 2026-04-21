import fakeredis.aioredis
import pytest

from techpulse.persistence.release_repository import ReleaseRepository

_ID_A = "owner/repo@v1.0"
_ID_B = "owner/repo@v1.1"


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def repo(redis):
    return ReleaseRepository(redis)


class TestFilterUnseen:
    @pytest.mark.asyncio
    async def test_returns_all_ids_when_none_seen(self, repo):
        result = await repo.filter_unseen(user_id=1, release_ids=[_ID_A, _ID_B])

        assert sorted(result) == sorted([_ID_A, _ID_B])

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_seen(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])

        result = await repo.filter_unseen(user_id=1, release_ids=[_ID_A])

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_only_unseen_ids(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])

        result = await repo.filter_unseen(user_id=1, release_ids=[_ID_A, _ID_B])

        assert result == [_ID_B]

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_input(self, repo):
        result = await repo.filter_unseen(user_id=1, release_ids=[])

        assert result == []

    @pytest.mark.asyncio
    async def test_seen_is_isolated_per_user(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])

        result = await repo.filter_unseen(user_id=2, release_ids=[_ID_A])

        assert result == [_ID_A]


class TestMarkManySeen:
    @pytest.mark.asyncio
    async def test_marks_ids_as_seen(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])

        unseen = await repo.filter_unseen(user_id=1, release_ids=[_ID_A])
        assert unseen == []

    @pytest.mark.asyncio
    async def test_marks_multiple_ids_at_once(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A, _ID_B])

        unseen = await repo.filter_unseen(user_id=1, release_ids=[_ID_A, _ID_B])
        assert unseen == []

    @pytest.mark.asyncio
    async def test_does_not_raise_for_empty_input(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[])

    @pytest.mark.asyncio
    async def test_marking_same_id_twice_is_idempotent(self, repo):
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])
        await repo.mark_many_seen(user_id=1, release_ids=[_ID_A])

        unseen = await repo.filter_unseen(user_id=1, release_ids=[_ID_A])
        assert unseen == []
