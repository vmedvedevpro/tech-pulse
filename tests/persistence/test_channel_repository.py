import pytest

from tests.persistence.fakes import FakeChannelRepository


@pytest.fixture
def repo():
    return FakeChannelRepository()


class TestSubscribe:
    async def test_marks_user_as_subscribed_when_called(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        assert await repo.is_subscribed(user_id=1, handle="@fireship")

    async def test_stores_handle_when_subscribing(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        assert "@fireship" in await repo.get_subscriptions(user_id=1)

    async def test_subscribing_same_channel_twice_does_not_duplicate(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.subscribe(user_id=1, handle="@fireship")

        assert len(await repo.get_subscriptions(user_id=1)) == 1

    async def test_subscriptions_are_isolated_per_user(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=2, handle="@chan_b")

        assert await repo.get_subscriptions(user_id=1) == ["@chan_a"]
        assert await repo.get_subscriptions(user_id=2) == ["@chan_b"]


class TestUnsubscribe:
    async def test_removes_channel_when_user_is_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.unsubscribe(user_id=1, handle="@fireship")

        assert not await repo.is_subscribed(user_id=1, handle="@fireship")

    async def test_does_not_raise_when_channel_not_subscribed(self, repo):
        await repo.unsubscribe(user_id=1, handle="@unknown")

    async def test_only_removes_target_channel_when_multiple_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=1, handle="@chan_b")

        await repo.unsubscribe(user_id=1, handle="@chan_a")

        assert await repo.get_subscriptions(user_id=1) == ["@chan_b"]


class TestGetSubscriptions:
    async def test_returns_empty_list_when_no_subscriptions(self, repo):
        assert await repo.get_subscriptions(user_id=99) == []

    async def test_returns_all_subscribed_channels(self, repo):
        await repo.subscribe(user_id=1, handle="@chan_a")
        await repo.subscribe(user_id=1, handle="@chan_b")

        assert set(await repo.get_subscriptions(user_id=1)) == {"@chan_a", "@chan_b"}

    async def test_returns_strings(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")

        channels = await repo.get_subscriptions(user_id=1)
        assert isinstance(channels[0], str)


class TestIsSubscribed:
    async def test_returns_false_when_not_subscribed(self, repo):
        assert not await repo.is_subscribed(user_id=1, handle="@fireship")

    async def test_returns_true_when_subscribed(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        assert await repo.is_subscribed(user_id=1, handle="@fireship")

    async def test_returns_false_after_unsubscribe(self, repo):
        await repo.subscribe(user_id=1, handle="@fireship")
        await repo.unsubscribe(user_id=1, handle="@fireship")
        assert not await repo.is_subscribed(user_id=1, handle="@fireship")
