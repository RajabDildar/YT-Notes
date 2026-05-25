from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.transcript import TranscriptData, TranscriptSegment


@dataclass
class TranscriptChunk:
    video_id: str
    video_title: str
    chunk_index: int
    start_timestamp: float
    end_timestamp: float
    source_language: str
    transcript_text: str


def _format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _segment_time_range(segments: list[TranscriptSegment], start_idx: int, end_idx: int) -> tuple[float, float]:
    start = segments[start_idx].start
    last = segments[end_idx]
    end = last.start + last.duration
    return start, end


def build_chunks(
    data: TranscriptData,
    video_title: str,
) -> list[TranscriptChunk]:
    """Split transcript into overlapping chunks with timestamp metadata."""
    lines: list[str] = []
    line_segments: list[tuple[int, int]] = []

    for i, seg in enumerate(data.segments):
        ts = _format_timestamp(seg.start)
        lines.append(f"[{ts}] {seg.text}")
        line_segments.append((i, i))

    full_text = "\n".join(lines)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n", ". ", " ", ""],
    )
    texts = splitter.split_text(full_text)

    chunks: list[TranscriptChunk] = []
    search_from = 0

    for idx, text in enumerate(texts):
        cleaned = text.strip()
        if not cleaned:
            continue

        pos = full_text.find(cleaned, search_from)
        if pos == -1:
            pos = full_text.find(cleaned)
        search_from = max(0, pos) + len(cleaned)

        start_ts = data.segments[0].start
        end_ts = data.segments[-1].start + data.segments[-1].duration

        if pos >= 0:
            prefix = full_text[:pos]
            line_count = prefix.count("\n")
            end_line = line_count + cleaned.count("\n")
            start_idx = min(line_count, len(data.segments) - 1)
            end_idx = min(end_line, len(data.segments) - 1)
            start_ts, end_ts = _segment_time_range(data.segments, start_idx, end_idx)

        chunks.append(
            TranscriptChunk(
                video_id=data.video_id,
                video_title=video_title,
                chunk_index=len(chunks),
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                source_language=data.language,
                transcript_text=cleaned,
            )
        )

    return chunks
