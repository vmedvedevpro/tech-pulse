from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReleaseInfo:
    repo: str  # "owner/repo"
    tag: str
    name: str
    body: str
    published_at: datetime
    url: str
