from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.chat import chat_service
from app.config import settings
from app.memory import session_store
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.rag import ensure_video_indexed, retrieve_context

app = FastAPI(title="YT Notes API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        groq_configured=bool(settings.groq_api_key),
        hf_configured=bool(settings.huggingface_api_key),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:

    if not settings.groq_api_key or not settings.huggingface_api_key:
        raise HTTPException(
            status_code=503,
            detail="The answer service is temporarily unavailable.",
        )

    memory = session_store.get_or_create(req.session_id, req.video_id)
    video_title = req.video_title or f"YouTube video {req.video_id}"

    try:
        video_title = ensure_video_indexed(req.video_id, video_title)
        chunks = retrieve_context(req.video_id, req.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="The answer service is temporarily unavailable.",
        ) from e

    try:
        answer = chat_service.generate(
            video_title=video_title,
            video_id=req.video_id,
            session_summary=memory.summary,
            recent_conversation=memory.format_recent(),
            retrieved_chunks=chunks,
            user_question=req.message,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    memory.add_turn("user", req.message)
    memory.add_turn("assistant", answer)
    session_store.update_summary(memory, req.message, answer)

    return ChatResponse(
        answer=answer,
        session_id=memory.session_id,
        video_title=video_title,
    )
