from datetime import datetime


class FakeChannelRepository:
    def __init__(self) -> None:
        self._subs: dict[int, set[str]] = {}

    async def subscribe(self, user_id: int, handle: str) -> None:
        self._subs.setdefault(user_id, set()).add(handle)

    async def unsubscribe(self, user_id: int, handle: str) -> None:
        self._subs.get(user_id, set()).discard(handle)

    async def get_subscriptions(self, user_id: int) -> list[str]:
        return sorted(self._subs.get(user_id, set()))

    async def is_subscribed(self, user_id: int, handle: str) -> bool:
        return handle in self._subs.get(user_id, set())


class FakeRepoRepository:
    def __init__(self) -> None:
        self._repos: dict[int, set[str]] = {}

    async def add_repo(self, user_id: int, repo: str) -> None:
        self._repos.setdefault(user_id, set()).add(repo)

    async def remove_repo(self, user_id: int, repo: str) -> None:
        self._repos.get(user_id, set()).discard(repo)

    async def get_repos(self, user_id: int) -> list[str]:
        return sorted(self._repos.get(user_id, set()))

    async def has_repo(self, user_id: int, repo: str) -> bool:
        return repo in self._repos.get(user_id, set())


class FakeInterestsRepository:
    def __init__(self) -> None:
        self._interests: dict[int, set[str]] = {}

    async def add_interest(self, user_id: int, interest: str) -> None:
        self._interests.setdefault(user_id, set()).add(interest)

    async def remove_interest(self, user_id: int, interest: str) -> None:
        self._interests.get(user_id, set()).discard(interest)

    async def get_interests(self, user_id: int) -> list[str]:
        return sorted(self._interests.get(user_id, set()))

    async def has_interest(self, user_id: int, interest: str) -> bool:
        return interest in self._interests.get(user_id, set())


class FakeDigestSubscriptionRepository:
    def __init__(self) -> None:
        self._subs: dict[int, datetime | None] = {}

    async def subscribe(self, user_id: int) -> None:
        self._subs.setdefault(user_id, None)

    async def unsubscribe(self, user_id: int) -> None:
        self._subs.pop(user_id, None)

    async def is_subscribed(self, user_id: int) -> bool:
        return user_id in self._subs

    async def list_due(self, threshold: datetime) -> list[int]:
        return sorted(
            uid
            for uid, sent_at in self._subs.items()
            if sent_at is None or sent_at < threshold
        )

    async def mark_sent(self, user_id: int, sent_at: datetime) -> None:
        if user_id in self._subs:
            self._subs[user_id] = sent_at


class FakeSeenItemsRepository:
    def __init__(self) -> None:
        self._seen: dict[int, set[str]] = {}

    async def filter_unseen(self, user_id: int, ids: list[str]) -> list[str]:
        seen = self._seen.get(user_id, set())
        return [i for i in ids if i not in seen]

    async def mark_many_seen(self, user_id: int, ids: list[str]) -> None:
        self._seen.setdefault(user_id, set()).update(ids)


class FakeVideoRepository:
    def __init__(self) -> None:
        self._videos: dict[str, dict] = {}

    async def upsert_metadata(
            self,
            video_id: str,
            title: str | None = None,
            channel_id: str | None = None,
            channel_title: str | None = None,
            published_at: datetime | None = None,
    ) -> None:
        v = self._videos.setdefault(video_id, {})
        v["title"] = title
        v["channel_id"] = channel_id
        v["channel_title"] = channel_title
        v["published_at"] = published_at

    async def get_metadata(self, video_id: str) -> tuple[str, str] | None:
        v = self._videos.get(video_id)
        if not v or v.get("title") is None or v.get("channel_title") is None:
            return None
        return v["title"], v["channel_title"]

    async def get_transcript(self, video_id: str) -> tuple[str, str] | None:
        v = self._videos.get(video_id)
        if not v or v.get("transcript") is None:
            return None
        return v["transcript"], v["transcript_language"]

    async def set_transcript(self, video_id: str, transcript: str, language: str) -> None:
        v = self._videos.setdefault(video_id, {})
        v["transcript"] = transcript
        v["transcript_language"] = language

    async def get_summary(self, video_id: str) -> str | None:
        v = self._videos.get(video_id)
        return v.get("summary") if v else None

    async def set_summary(self, video_id: str, summary: str) -> None:
        v = self._videos.setdefault(video_id, {})
        v["summary"] = summary
