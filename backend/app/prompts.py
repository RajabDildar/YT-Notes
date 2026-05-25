def build_system_prompt() -> str:
    return """You are YT Notes, a helpful assistant that answers questions about a single YouTube video.

Rules:
- Answer ONLY using the supplied transcript excerpts and session memory.
- Do not invent facts, quotes, or timestamps not supported by the context.
- If the answer is not in the transcript, say clearly that the transcript does not show it.
- Be clear and concise.
- Respond in the same language as the user's question when possible.
- For summaries, cover the main ideas without fluff."""


def build_user_prompt(
    *,
    video_title: str,
    video_id: str,
    session_summary: str,
    recent_conversation: str,
    retrieved_chunks: list[dict],
    user_question: str,
) -> str:
    chunk_blocks = []
    for i, ch in enumerate(retrieved_chunks, 1):
        start = ch.get("start")
        end = ch.get("end")
        ts = ""
        if start is not None and end is not None:
            ts = f" ({start:.0f}s–{end:.0f}s)"
        chunk_blocks.append(f"[Excerpt {i}{ts}]\n{ch['text']}")

    context = "\n\n".join(chunk_blocks) if chunk_blocks else "(no excerpts retrieved)"

    return f"""## Video
Title: {video_title}
ID: {video_id}

## Session summary
{session_summary or "(none)"}

## Recent conversation
{recent_conversation}

## Retrieved transcript excerpts
{context}

## User question
{user_question}

Answer the user question based on the excerpts above."""
