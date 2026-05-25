from huggingface_hub import InferenceClient

from app.config import settings


class EmbeddingClient:
    """Hugging Face Inference API feature-extraction for BGE-M3."""

    def __init__(self) -> None:
        self.model = settings.hf_embedding_model
        self._client: InferenceClient | None = None
        if settings.huggingface_api_key:
            self._client = InferenceClient(token=settings.huggingface_api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self._client:
            raise RuntimeError("Hugging Face API key is not configured.")

        try:
            result = self._client.feature_extraction(texts, model=self.model)
        except Exception as e:
            raise RuntimeError(
                "Embedding service failed. Please try again later."
            ) from e

        vectors = self._to_vectors(result, len(texts))
        return vectors

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    @staticmethod
    def _to_vectors(result: object, expected: int) -> list[list[float]]:
        """Convert numpy array or list responses into list[list[float]]."""
        if hasattr(result, "tolist"):
            arr = result.tolist()
        elif isinstance(result, list):
            arr = result
        else:
            raise RuntimeError("Invalid embedding response.")

        if expected == 1:
            if isinstance(arr[0], (int, float)):
                return [arr]  # type: ignore[list-item]
            return [arr[0]]  # type: ignore[index]

        if isinstance(arr[0], (int, float)):
            return [arr]  # type: ignore[list-item]

        return arr  # type: ignore[return-value]


embedding_client = EmbeddingClient()
