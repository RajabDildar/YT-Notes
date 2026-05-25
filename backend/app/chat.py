from groq import Groq

from app.config import settings
from app.prompts import build_system_prompt, build_user_prompt


class ChatService:
    def __init__(self) -> None:
        self._client: Groq | None = None
        if settings.groq_api_key:
            self._client = Groq(api_key=settings.groq_api_key)

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
        if not self._client:
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
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ]

        models = [settings.groq_chat_model, settings.groq_chat_model_fallback]
        last_error: Exception | None = None

        for model in models:
            try:
                completion = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1024,
                    reasoning_format="hidden",
                )
                content = completion.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(
            "The answer service is temporarily unavailable."
        ) from last_error


chat_service = ChatService()
