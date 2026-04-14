import fakeredis.aioredis
import pytest

from techpulse.persistence.channel_repository import ChannelInfo, ChannelRepository


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def repo(redis):
    return ChannelRepository(redis)


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_marks_user_as_subscribed_when_called(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        assert await repo.is_subscribed(user_id=1, handle="@fireship")

    @pytest.mark.asyncio
    async def test_stores_handle_when_subscribing(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        channels = await repo.get_subscriptions(user_id=1)
        assert channels[0].handle == "@fireship"

    @pytest.mark.asyncio
    async def test_subscribing_same_channel_twice_does_not_duplicate(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.subscribe(user_id=1, handle="@fireship")

        channels = await repo.get_subscriptions(user_id=1)
        assert len(channels) == 1

    @pytest.mark.asyncio
    async def test_subscriptions_are_isolated_per_user(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=2, handle="@chan_b")

        user1_channels = await repo.get_subscriptions(user_id=1)
        user2_channels = await repo.get_subscriptions(user_id=2)

        assert len(user1_channels) == 1
        assert user1_channels[0].handle == "@chan_a"
        assert len(user2_channels) == 1
        assert user2_channels[0].handle == "@chan_b"


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_removes_channel_when_user_is_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.unsubscribe(user_id=1, handle="@fireship")

        assert not await repo.is_subscribed(user_id=1, handle="@fireship")

    @pytest.mark.asyncio
    async def test_does_not_raise_when_channel_not_subscribed(self, repo):
        await repo.unsubscribe(user_id=1, handle="@unknown")

    @pytest.mark.asyncio
    async def test_only_removes_target_channel_when_multiple_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=1, handle="@chan_b")

        await repo.unsubscribe(user_id=1, handle="@chan_a")

        channels = await repo.get_subscriptions(user_id=1)
        assert len(channels) == 1
        assert channels[0].handle == "@chan_b"


class TestGetSubscriptions:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_subscriptions(self, repo):
        result = await repo.get_subscriptions(user_id=99)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_subscribed_channels(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=1, handle="@chan_b")

        channels = await repo.get_subscriptions(user_id=1)
        handles = {c.handle for c in channels}

        assert handles == {"@chan_a", "@chan_b"}

    @pytest.mark.asyncio
    async def test_returns_channel_info_dataclass(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        channels = await repo.get_subscriptions(user_id=1)

        assert isinstance(channels[0], ChannelInfo)


class TestIsSubscribed:
    @pytest.mark.asyncio
    async def test_returns_false_when_not_subscribed(self, repo):
        assert not await repo.is_subscribed(user_id=1, handle="@fireship")

    @pytest.mark.asyncio
    async def test_returns_true_when_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        assert await repo.is_subscribed(user_id=1, handle="@fireship")

    @pytest.mark.asyncio
    async def test_returns_false_after_unsubscribe(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.unsubscribe(user_id=1, handle="@fireship")
        assert not await repo.is_subscribed(user_id=1, handle="@fireship")
