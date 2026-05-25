from app.chunking import build_chunks
from app.config import settings
from app.memory import session_store
from app.transcript import fetch_transcript
from app.vector_store import vector_store


def ensure_video_indexed(video_id: str, video_title: str) -> str:
    """Load transcript, chunk, embed, and store if not already indexed."""
    if vector_store.has_video(video_id):
        return video_title

    data = fetch_transcript(video_id)
    title = video_title or f"YouTube video {video_id}"
    chunks = build_chunks(data, title)
    vector_store.index_chunks(chunks)
    return chunks[0].video_title if chunks else title


def retrieve_context(video_id: str, question: str) -> list[dict]:
    if not vector_store.has_video(video_id):
        return []
    return vector_store.retrieve(video_id, question, settings.retrieval_top_k)
