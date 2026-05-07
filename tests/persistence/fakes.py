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


class FakeReleaseRepository:
    def __init__(self) -> None:
        self._seen: dict[int, set[str]] = {}

    async def filter_unseen(self, user_id: int, release_ids: list[str]) -> list[str]:
        seen = self._seen.get(user_id, set())
        return [rid for rid in release_ids if rid not in seen]

    async def mark_many_seen(self, user_id: int, release_ids: list[str]) -> None:
        self._seen.setdefault(user_id, set()).update(release_ids)


class FakeVideoRepository:
    def __init__(self) -> None:
        self._seen: dict[int, set[str]] = {}

    async def filter_unseen(self, user_id: int, video_ids: list[str]) -> list[str]:
        seen = self._seen.get(user_id, set())
        return [vid for vid in video_ids if vid not in seen]

    async def mark_many_seen(self, user_id: int, video_ids: list[str]) -> None:
        self._seen.setdefault(user_id, set()).update(video_ids)
