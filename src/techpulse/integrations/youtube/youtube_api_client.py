import re
import time
import urllib.request

import yt_dlp

from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import SubtitleTrack, Transcript, VideoMetadata

_TAG_RE = re.compile(r'<[^>]+>')
_TIMESTAMP_LINE_RE = re.compile(r'\d{1,2}:\d{2}:\d{2}[.,]\d+ --> ')
_TIMESTAMP_VALUE_RE = re.compile(r'(\d+):(\d{2}):(\d{2}[.,]\d+)')

_RETRY_DELAYS = (30, 60, 120)


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc)
    return '429' in msg or 'Too Many Requests' in msg


def _ts_to_seconds(ts: str) -> float:
    m = _TIMESTAMP_VALUE_RE.match(ts.replace(',', '.'))
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def _parse_vtt(content: str) -> tuple[str, float]:
    text_lines: list[str] = []
    duration = 0.0
    past_header = False

    for line in content.splitlines():
        line = line.strip()
        if not line:
            past_header = True
            continue
        if not past_header:
            continue
        if _TIMESTAMP_LINE_RE.match(line):
            end_ts = line.split('-->')[1].strip().split()[0]
            duration = max(duration, _ts_to_seconds(end_ts))
            continue
        if line.isdigit():
            continue
        clean = _TAG_RE.sub('', line).strip()
        if clean:
            text_lines.append(clean)

    result: list[str] = []
    for line in text_lines:
        if not result or result[-1] != line:
            result.append(line)
    return ' '.join(result), duration


class YouTubeTranscriptClient:
    _BASE_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'sleep_interval_requests': 3,
        'sleep_interval_subtitles': 3,
    }

    def __init__(self, cookie_file: str | None = None, ydl_class=None, urlopen=None) -> None:
        self._ydl_class = ydl_class or yt_dlp.YoutubeDL
        self._urlopen = urlopen or urllib.request.urlopen
        self._ydl_opts = {
            **self._BASE_OPTS,
            **(({'cookiefile': cookie_file}) if cookie_file else {}),
        }

    def _extract_info(self, video_id: str) -> dict:
        url = f'https://www.youtube.com/watch?v={video_id}'
        delays = iter(_RETRY_DELAYS)
        while True:
            try:
                with self._ydl_class(self._ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False, process=False)
            except Exception as exc:
                if not _is_rate_limited(exc):
                    raise
                delay = next(delays, None)
                if delay is None:
                    raise
                time.sleep(delay)

    def fetch_video_metadata(self, video_id: str) -> VideoMetadata:
        try:
            info = self._extract_info(video_id)
        except Exception as exc:
            raise TranscriptError(f"Failed to fetch metadata for {video_id!r}: {exc}") from exc
        return VideoMetadata(
            video_id=video_id,
            title=info.get('title', ''),
            channel=info.get('channel') or info.get('uploader', ''),
        )

    def get_transcript_metadata(self, video_id: str) -> list[SubtitleTrack]:
        try:
            info = self._extract_info(video_id)
        except Exception as exc:
            raise TranscriptError(
                f"Failed to fetch transcript metadata for {video_id!r}: {exc}"
            ) from exc

        tracks: list[SubtitleTrack] = []
        for lang_code, formats in info.get('subtitles', {}).items():
            name = formats[0].get('name', lang_code) if formats else lang_code
            tracks.append(SubtitleTrack(language_code=lang_code, language=name, is_generated=False))

        for lang_code, formats in info.get('automatic_captions', {}).items():
            if lang_code == 'live_chat':
                continue
            name = formats[0].get('name', lang_code) if formats else lang_code
            name = name.removesuffix(' (auto-generated)').strip()
            tracks.append(SubtitleTrack(language_code=lang_code, language=name, is_generated=True))

        tracks.sort(key=lambda t: t.is_generated)
        return tracks

    def fetch(self, video_id: str, language: str = None) -> Transcript:
        lang = language or 'en'
        try:
            info = self._extract_info(video_id)
        except Exception as exc:
            raise TranscriptError(
                f"Failed to fetch transcript for {video_id!r}: {exc}"
            ) from exc

        subtitles = info.get('subtitles', {})
        auto_captions = info.get('automatic_captions', {})

        if lang in subtitles:
            formats = subtitles[lang]
        elif lang in auto_captions:
            formats = auto_captions[lang]
        else:
            raise TranscriptError(
                f"No transcript available for {video_id!r} in language {lang!r}"
            )

        vtt_formats = [f for f in formats if f.get('ext') == 'vtt']
        fmt = (vtt_formats or formats)[0]

        try:
            with self._urlopen(fmt['url']) as resp:
                content = resp.read().decode('utf-8', errors='replace')
        except Exception as exc:
            raise TranscriptError(
                f"Failed to download subtitle for {video_id!r}: {exc}"
            ) from exc

        text, duration = _parse_vtt(content)
        return Transcript(video_id=video_id, text=text, language_code=lang, duration=duration)
