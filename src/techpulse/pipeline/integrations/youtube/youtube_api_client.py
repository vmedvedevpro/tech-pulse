import json
import urllib.request

from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.pipeline.integrations.youtube.exceptions import TranscriptError
from techpulse.pipeline.integrations.youtube.models import Transcript, VideoMetadata


class YouTubeTranscriptClient:
    def __init__(self, api: YouTubeTranscriptApi, urlopen=urllib.request.urlopen) -> None:
        self._api = api
        self._urlopen = urlopen

    def fetch_video_metadata(self, video_id: str) -> VideoMetadata:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        try:
            with self._urlopen(url) as response:
                data = json.loads(response.read())
        except Exception as exc:
            raise TranscriptError(f"Failed to fetch metadata for {video_id!r}: {exc}") from exc
        return VideoMetadata(
            video_id=video_id,
            title=data["title"],
            channel=data["author_name"],
        )

    def get_transcript_metadata(self, video_id: str):
        try:
            transcript_meta = self._api.list(video_id)
            return transcript_meta
        except Exception as exc:
            raise TranscriptError(
                f"Failed to fetch transcript metadata for {video_id!r}: {exc}"
            ) from exc

    def fetch(self, video_id: str, language: str = None) -> Transcript:
        try:
            transcript = self._api.fetch(video_id, languages=(language,) if language else ('en',))
        except Exception as exc:
            raise TranscriptError(
                f"Failed to fetch transcript for {video_id!r}: {exc}"
            ) from exc

        text = " ".join(snippet.text for snippet in transcript.snippets)
        duration = sum(snippet.duration for snippet in transcript.snippets)

        return Transcript(
            video_id=video_id,
            text=text,
            language_code=transcript.language_code,
            duration=duration,
        )
