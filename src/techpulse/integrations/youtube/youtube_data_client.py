from datetime import datetime, timezone

import httpx

from techpulse.integrations.youtube.exceptions import YouTubeAPIError
from techpulse.integrations.youtube.models import VideoInfo


class YouTubeDataClient:
    def __init__(self, api_key: str, base_url: str, http_client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._http = http_client or httpx.AsyncClient(timeout=10.0)

    async def get_channel_id(self, handle: str) -> str:
        """Resolve a @handle (with or without @) to a channel ID."""
        clean = handle.lstrip("@")
        params = {
            "part": "id",
            "forHandle": clean,
            "key": self._api_key,
        }
        data = await self._get("/channels", params)
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError(f"Channel not found for handle: {handle!r}")
        return items[0]["id"]

    async def get_recent_videos(self, channel_id: str, max_results: int = 10) -> list[VideoInfo]:
        """Return the most recent uploads for a channel, newest first."""
        playlist_id = await self._get_uploads_playlist_id(channel_id)
        return await self._get_playlist_videos(playlist_id, max_results)

    async def _get_uploads_playlist_id(self, channel_id: str) -> str:
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self._api_key,
        }
        data = await self._get("/channels", params)
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError(f"Channel not found: {channel_id!r}")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    async def _get_playlist_videos(self, playlist_id: str, max_results: int) -> list[VideoInfo]:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": min(max_results, 50),
            "key": self._api_key,
        }
        data = await self._get("/playlistItems", params)
        videos = []
        for item in data.get("items", []):
            snippet = item["snippet"]
            resource = snippet["resourceId"]
            if resource.get("kind") != "youtube#video":
                continue
            published_at = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            videos.append(VideoInfo(
                video_id=resource["videoId"],
                title=snippet["title"],
                channel_id=snippet["channelId"],
                channel_title=snippet["channelTitle"],
                published_at=published_at,
                description=snippet.get("description", ""),
            ))
        return videos

    async def _get(self, path: str, params: dict) -> dict:
        try:
            response = await self._http.get(self._base_url + path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:300]
            raise YouTubeAPIError(
                f"YouTube API {exc.response.status_code} on {path}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise YouTubeAPIError(f"Request failed for {path}: {exc}") from exc

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "YouTubeDataClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self.aclose()
