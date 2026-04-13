from dataclasses import dataclass

from youtube_transcript_api import (
    YouTubeTranscriptApi,
)


@dataclass
class Transcript:
    video_id: str
    text: str
    language_code: str
    duration: float  # total seconds


class TranscriptError(Exception):
    pass

class YouTubeTranscriptClient:
    def __init__(self, api: YouTubeTranscriptApi) -> None:
        self._api = api

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