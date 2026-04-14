from dataclasses import dataclass


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    channel: str


@dataclass
class Transcript:
    video_id: str
    text: str
    language_code: str
    duration: float  # total seconds
