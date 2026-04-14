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
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship")

        assert await repo.is_subscribed(user_id=1, channel_id="UC123")

    @pytest.mark.asyncio
    async def test_stores_channel_name_when_subscribing(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship")

        channels = await repo.get_subscriptions(user_id=1)
        assert channels[0].name == "Fireship"

    @pytest.mark.asyncio
    async def test_subscribing_same_channel_twice_does_not_duplicate(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship")
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship Updated")

        channels = await repo.get_subscriptions(user_id=1)
        assert len(channels) == 1

    @pytest.mark.asyncio
    async def test_subscriptions_are_isolated_per_user(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Chan A")
        await repo.subscribe(user_id=2, channel_id="UC456", channel_name="Chan B")

        user1_channels = await repo.get_subscriptions(user_id=1)
        user2_channels = await repo.get_subscriptions(user_id=2)

        assert len(user1_channels) == 1
        assert user1_channels[0].channel_id == "UC123"
        assert len(user2_channels) == 1
        assert user2_channels[0].channel_id == "UC456"


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_removes_channel_when_user_is_subscribed(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship")
        await repo.unsubscribe(user_id=1, channel_id="UC123")

        assert not await repo.is_subscribed(user_id=1, channel_id="UC123")

    @pytest.mark.asyncio
    async def test_does_not_raise_when_channel_not_subscribed(self, repo):
        await repo.unsubscribe(user_id=1, channel_id="UC_UNKNOWN")

    @pytest.mark.asyncio
    async def test_only_removes_target_channel_when_multiple_subscribed(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Chan A")
        await repo.subscribe(user_id=1, channel_id="UC456", channel_name="Chan B")

        await repo.unsubscribe(user_id=1, channel_id="UC123")

        channels = await repo.get_subscriptions(user_id=1)
        assert len(channels) == 1
        assert channels[0].channel_id == "UC456"


class TestGetSubscriptions:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_subscriptions(self, repo):
        result = await repo.get_subscriptions(user_id=99)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_subscribed_channels(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Chan A")
        await repo.subscribe(user_id=1, channel_id="UC456", channel_name="Chan B")

        channels = await repo.get_subscriptions(user_id=1)
        channel_ids = {c.channel_id for c in channels}

        assert channel_ids == {"UC123", "UC456"}

    @pytest.mark.asyncio
    async def test_returns_channel_info_dataclass(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Fireship")

        channels = await repo.get_subscriptions(user_id=1)

        assert isinstance(channels[0], ChannelInfo)


class TestIsSubscribed:
    @pytest.mark.asyncio
    async def test_returns_false_when_not_subscribed(self, repo):
        assert not await repo.is_subscribed(user_id=1, channel_id="UC123")

    @pytest.mark.asyncio
    async def test_returns_true_when_subscribed(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Chan")
        assert await repo.is_subscribed(user_id=1, channel_id="UC123")

    @pytest.mark.asyncio
    async def test_returns_false_after_unsubscribe(self, repo):
        await repo.subscribe(user_id=1, channel_id="UC123", channel_name="Chan")
        await repo.unsubscribe(user_id=1, channel_id="UC123")
        assert not await repo.is_subscribed(user_id=1, channel_id="UC123")
