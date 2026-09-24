from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.prompts import build_system_prompt, build_user_prompt


def _extract_text(response: object) -> str:
    if hasattr(response, "text"):
        text = getattr(response, "text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                txt = block.get("text") or block.get("content")
                if isinstance(txt, str):
                    parts.append(txt)
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts).strip()
    return str(content).strip() if content is not None else ""


class ChatService:
    def __init__(self) -> None:
        self._primary: ChatGoogleGenerativeAI | None = None
        self._fallback: ChatGoogleGenerativeAI | None = None
        if settings.google_api_key:
            common_kwargs = {
                "google_api_key": settings.google_api_key,
                "max_retries": 1,
            }
            self._primary = ChatGoogleGenerativeAI(
                model=settings.google_chat_model,
                temperature=0.3,
                max_tokens=1024,
                **common_kwargs,
            )
            self._fallback = ChatGoogleGenerativeAI(
                model=settings.google_chat_model_fallback,
                temperature=0.3,
                max_tokens=1024,
                **common_kwargs,
            )

    def generate(
        self,
        *,
        video_title: str,
        video_id: str,
        session_summary: str,
        recent_conversation: str,
        retrieved_chunks: list[dict],
        user_question: str,
    ) -> str:
        if not self._primary or not self._fallback:
            raise RuntimeError("The answer service is temporarily unavailable.")

        user_prompt = build_user_prompt(
            video_title=video_title,
            video_id=video_id,
            session_summary=session_summary,
            recent_conversation=recent_conversation,
            retrieved_chunks=retrieved_chunks,
            user_question=user_question,
        )

        messages = [
            ("system", build_system_prompt()),
            ("human", user_prompt),
        ]

        models = [self._primary, self._fallback]
        last_error: Exception | None = None

        for model in models:
            try:
                response = model.invoke(messages)
                content = _extract_text(response)
                if content:
                    return content
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(
            "The answer service is temporarily unavailable."
        ) from last_error


chat_service = ChatService()
