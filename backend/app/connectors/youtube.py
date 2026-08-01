import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    AgeRestricted,
    InvalidVideoId,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
)


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
YOUTUBE_SHORT_HOSTS = {"youtu.be", "www.youtu.be"}


class InvalidYouTubeUrlError(ValueError):
    pass


class YouTubeVideoUnavailableError(Exception):
    pass


class YouTubeTranscriptUnavailableError(Exception):
    pass


@dataclass
class YouTubeTranscript:
    video_id: str
    source_url: str
    filename: str
    text_content: str


def extract_video_id(url: str) -> str:
    parsed_url = urlparse(url.strip())
    host = (parsed_url.hostname or "").lower()

    if host in YOUTUBE_SHORT_HOSTS:
        video_id = parsed_url.path.strip("/").split("/")[0]
        return validate_video_id(video_id)

    if host in YOUTUBE_HOSTS:
        if parsed_url.path == "/watch":
            video_id = parse_qs(parsed_url.query).get("v", [""])[0]
            return validate_video_id(video_id)

        path_parts = [part for part in parsed_url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            return validate_video_id(path_parts[1])

    raise InvalidYouTubeUrlError("Only youtube.com and youtu.be URLs are supported")


def validate_video_id(video_id: str) -> str:
    if not video_id or not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise InvalidYouTubeUrlError("YouTube URL must contain a valid video ID")

    return video_id


def normalize_source_url(video_id: str) -> str:
    return f"https://youtu.be/{video_id}"


def download_transcript(url: str) -> YouTubeTranscript:
    video_id = extract_video_id(url)

    try:
        fetched_transcript = YouTubeTranscriptApi().fetch(video_id)
    except (AgeRestricted, InvalidVideoId, VideoUnavailable, VideoUnplayable) as exc:
        raise YouTubeVideoUnavailableError("YouTube video is unavailable") from exc
    except (NoTranscriptFound, TranscriptsDisabled) as exc:
        raise YouTubeTranscriptUnavailableError(
            "Transcript is unavailable for this YouTube video"
        ) from exc

    text_content = "\n".join(
        snippet.text.strip()
        for snippet in fetched_transcript.snippets
        if snippet.text.strip()
    )
    if not text_content:
        raise YouTubeTranscriptUnavailableError(
            "Transcript is unavailable for this YouTube video"
        )

    return YouTubeTranscript(
        video_id=video_id,
        source_url=normalize_source_url(video_id),
        filename=video_id,
        text_content=text_content,
    )
