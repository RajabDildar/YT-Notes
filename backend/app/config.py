from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str = ""

    google_chat_model: str = "gemini-3.1-flash-lite"
    google_chat_model_fallback: str = "gemini-3.5-flash"
    google_embedding_model: str = "gemini-embedding-2"

    retrieval_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 120

    chroma_persist_dir: str = "./data/chroma"
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
