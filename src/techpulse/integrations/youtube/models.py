from dataclasses import dataclass
from datetime import datetime


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    channel: str


@dataclass
class VideoInfo:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: datetime
    description: str


@dataclass
class Transcript:
    video_id: str
    text: str
    language_code: str
    duration: float  # total seconds
