from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.chunking import TranscriptChunk
from app.config import settings
from app.embeddings import embedding_client


class VectorStore:
    def __init__(self) -> None:
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    def _collection_name(self, video_id: str) -> str:
        return f"video_{video_id}"

    def has_video(self, video_id: str) -> bool:
        name = self._collection_name(video_id)
        try:
            col = self._client.get_collection(name)
            return col.count() > 0
        except Exception:
            return False

    def index_chunks(self, chunks: list[TranscriptChunk]) -> None:
        if not chunks:
            return

        video_id = chunks[0].video_id
        name = self._collection_name(video_id)

        try:
            self._client.delete_collection(name)
        except Exception:
            pass

        collection = self._client.create_collection(name=name, metadata={"hnsw:space": "cosine"})
        texts = [c.transcript_text for c in chunks]
        embeddings = embedding_client.embed_texts(texts)

        ids = [f"{video_id}_{c.chunk_index}" for c in chunks]
        metadatas = [
            {
                "video_id": c.video_id,
                "video_title": c.video_title,
                "chunk_index": c.chunk_index,
                "start_timestamp": c.start_timestamp,
                "end_timestamp": c.end_timestamp,
                "source_language": c.source_language,
            }
            for c in chunks
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

    def retrieve(self, video_id: str, query: str, top_k: int | None = None) -> list[dict]:
        k = top_k or settings.retrieval_top_k
        name = self._collection_name(video_id)
        collection: Collection = self._client.get_collection(name)
        query_embedding = embedding_client.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        out: list[dict] = []
        for doc, meta in zip(docs, metas):
            out.append(
                {
                    "text": doc,
                    "start": meta.get("start_timestamp"),
                    "end": meta.get("end_timestamp"),
                    "language": meta.get("source_language"),
                }
            )
        return out


vector_store = VectorStore()
