from dataclasses import dataclass, field
from uuid import uuid4

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class SessionMemory:
    session_id: str
    video_id: str
    summary: str = ""
    recent_turns: list[Turn] = field(default_factory=list)

    def add_turn(self, role: str, content: str, max_turns: int = 6) -> None:
        self.recent_turns.append(Turn(role=role, content=content))
        if len(self.recent_turns) > max_turns:
            self.recent_turns = self.recent_turns[-max_turns:]

    def format_recent(self) -> str:
        if not self.recent_turns:
            return "(none)"
        lines = []
        for t in self.recent_turns:
            label = "User" if t.role == "user" else "Assistant"
            lines.append(f"{label}: {t.content}")
        return "\n".join(lines)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionMemory] = {}

    def get_or_create(self, session_id: str | None, video_id: str) -> SessionMemory:
        if session_id and session_id in self._sessions:
            mem = self._sessions[session_id]
            if mem.video_id != video_id:
                mem = SessionMemory(session_id=str(uuid4()), video_id=video_id)
                self._sessions[mem.session_id] = mem
            return mem

        new_id = session_id or str(uuid4())
        mem = SessionMemory(session_id=new_id, video_id=video_id)
        self._sessions[new_id] = mem
        return mem

    @staticmethod
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

    def update_summary(self, memory: SessionMemory, user_msg: str, assistant_msg: str) -> None:
        if not settings.google_api_key:
            return

        prompt = f"""Compress this conversation into a short session summary (max 120 words).
Keep facts and topics needed for follow-up questions.

Previous summary:
{memory.summary or "(empty)"}

Latest exchange:
User: {user_msg}
Assistant: {assistant_msg}

Return only the updated summary."""

        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.google_chat_model_fallback,
                google_api_key=settings.google_api_key,
                temperature=0.2,
                max_tokens=256,
                max_retries=1,
            )
            response = llm.invoke([("user", prompt)])
            memory.summary = self._extract_text(response)
        except Exception:
            memory.summary = f"{memory.summary}\nUser asked: {user_msg[:200]}".strip()[:500]


session_store = SessionStore()
