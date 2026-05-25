import re
from dataclasses import dataclass

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


@dataclass
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass
class TranscriptData:
    video_id: str
    language: str
    segments: list[TranscriptSegment]


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([.!?])\1+", r"\1", text)
    return text


def _dedupe_segments(segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
    seen: set[str] = set()
    out: list[TranscriptSegment] = []
    for seg in segments:
        key = seg.text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(seg)
    return out


def fetch_transcript(video_id: str) -> TranscriptData:
    """Load YouTube captions using youtube-transcript-api v1.x instance API."""
    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
    except (VideoUnavailable, TranscriptsDisabled, NoTranscriptFound) as e:
        raise ValueError("The transcript could not be loaded for this video.") from e

    language_codes = [t.language_code for t in transcript_list]
    transcript = None

    if language_codes:
        try:
            transcript = transcript_list.find_manually_created_transcript(language_codes)
        except Exception:
            pass

    if transcript is None and language_codes:
        try:
            transcript = transcript_list.find_generated_transcript(language_codes)
        except Exception:
            pass

    if transcript is None:
        try:
            transcript = next(iter(transcript_list))
        except StopIteration as e:
            raise ValueError("The transcript could not be loaded for this video.") from e

    fetched = transcript.fetch()
    language = fetched.language_code

    segments = [
        TranscriptSegment(
            text=_normalize_text(snippet.text),
            start=float(snippet.start),
            duration=float(snippet.duration),
        )
        for snippet in fetched.snippets
        if snippet.text.strip()
    ]
    segments = _dedupe_segments(segments)

    if not segments:
        raise ValueError("The transcript could not be loaded for this video.")

    return TranscriptData(video_id=video_id, language=language, segments=segments)


def segments_to_plain_text(data: TranscriptData) -> str:
    return " ".join(s.text for s in data.segments)
