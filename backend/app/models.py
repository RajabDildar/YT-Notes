from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    video_id: str = Field(..., min_length=6, max_length=20)
    video_title: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    video_title: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    hf_configured: bool
