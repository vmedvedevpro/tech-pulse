from datetime import datetime, timezone

import pytest

from tests.persistence.fakes import FakeDigestSubscriptionRepository


@pytest.fixture
def repo():
    return FakeDigestSubscriptionRepository()


class TestSubscribe:
    async def test_marks_user_as_subscribed_when_called(self, repo):
        await repo.subscribe(user_id=1)

        assert await repo.is_subscribed(user_id=1)

    async def test_subscribing_twice_is_idempotent(self, repo):
        await repo.subscribe(user_id=1)
        await repo.mark_sent(user_id=1, sent_at=datetime(2026, 5, 4, 9, tzinfo=timezone.utc))
        await repo.subscribe(user_id=1)

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == [1]

    async def test_subscriptions_are_isolated_per_user(self, repo):
        await repo.subscribe(user_id=1)

        assert await repo.is_subscribed(user_id=1)
        assert not await repo.is_subscribed(user_id=2)


class TestUnsubscribe:
    async def test_removes_subscription_when_present(self, repo):
        await repo.subscribe(user_id=1)
        await repo.unsubscribe(user_id=1)

        assert not await repo.is_subscribed(user_id=1)

    async def test_does_not_raise_when_user_not_subscribed(self, repo):
        await repo.unsubscribe(user_id=99)


class TestListDue:
    async def test_returns_user_with_no_last_sent(self, repo):
        await repo.subscribe(user_id=1)

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == [1]

    async def test_returns_user_when_last_sent_before_threshold(self, repo):
        await repo.subscribe(user_id=1)
        await repo.mark_sent(user_id=1, sent_at=datetime(2026, 5, 4, 9, tzinfo=timezone.utc))

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == [1]

    async def test_excludes_user_when_last_sent_at_or_after_threshold(self, repo):
        await repo.subscribe(user_id=1)
        await repo.mark_sent(user_id=1, sent_at=datetime(2026, 5, 11, 9, tzinfo=timezone.utc))

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == []

    async def test_returns_only_subscribed_users(self, repo):
        await repo.subscribe(user_id=1)
        await repo.subscribe(user_id=2)
        await repo.unsubscribe(user_id=2)

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == [1]


class TestMarkSent:
    async def test_updates_last_sent_at(self, repo):
        await repo.subscribe(user_id=1)
        sent_at = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        await repo.mark_sent(user_id=1, sent_at=sent_at)

        threshold = datetime(2026, 5, 11, 9, tzinfo=timezone.utc)
        assert await repo.list_due(threshold) == []

    async def test_silently_skips_when_user_not_subscribed(self, repo):
        await repo.mark_sent(user_id=1, sent_at=datetime(2026, 5, 11, 9, tzinfo=timezone.utc))

        assert not await repo.is_subscribed(user_id=1)
