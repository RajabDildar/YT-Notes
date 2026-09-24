from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings


class EmbeddingClient:
    """Gemini Embedding 2 via LangChain Google GenAI integration."""

    def __init__(self) -> None:
        self.model = settings.google_embedding_model
        self._doc_embedder: GoogleGenerativeAIEmbeddings | None = None
        self._query_embedder: GoogleGenerativeAIEmbeddings | None = None
        if settings.google_api_key:
            common_kwargs = {
                "model": self.model,
                "google_api_key": settings.google_api_key,
            }
            self._doc_embedder = GoogleGenerativeAIEmbeddings(
                **common_kwargs,
                task_type="RETRIEVAL_DOCUMENT",
            )
            self._query_embedder = GoogleGenerativeAIEmbeddings(
                **common_kwargs,
                task_type="RETRIEVAL_QUERY",
            )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self._doc_embedder:
            raise RuntimeError("Embedding service is not configured.")

        try:
            return self._doc_embedder.embed_documents(texts)
        except Exception as e:
            raise RuntimeError(
                "Embedding service failed. Please try again later."
            ) from e

    def embed_query(self, query: str) -> list[float]:
        if not self._query_embedder:
            raise RuntimeError("Embedding service is not configured.")

        try:
            return self._query_embedder.embed_query(query)
        except Exception as e:
            raise RuntimeError(
                "Embedding service failed. Please try again later."
            ) from e


embedding_client = EmbeddingClient()
