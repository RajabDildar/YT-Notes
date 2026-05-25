from dataclasses import dataclass, field
from uuid import uuid4

from groq import Groq

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

    def update_summary(self, memory: SessionMemory, user_msg: str, assistant_msg: str) -> None:
        if not settings.groq_api_key:
            return

        client = Groq(api_key=settings.groq_api_key)
        prompt = f"""Compress this conversation into a short session summary (max 120 words).
Keep facts and topics needed for follow-up questions.

Previous summary:
{memory.summary or "(empty)"}

Latest exchange:
User: {user_msg}
Assistant: {assistant_msg}

Return only the updated summary."""

        try:
            completion = client.chat.completions.create(
                model=settings.groq_chat_model_fallback,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256,
            )
            memory.summary = (completion.choices[0].message.content or "").strip()
        except Exception:
            memory.summary = f"{memory.summary}\nUser asked: {user_msg[:200]}".strip()[:500]


session_store = SessionStore()
