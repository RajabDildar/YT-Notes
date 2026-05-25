import type { ChatMessage, SessionState } from "./api";

const STORAGE_KEY = "yt_notes_session";

export function createSessionId(): string {
  return crypto.randomUUID();
}

export async function loadSession(videoId: string): Promise<SessionState> {
  const key = `${STORAGE_KEY}:${videoId}`;
  const stored = await chrome.storage.session.get(key);
  const data = stored[key] as SessionState | undefined;
  if (data?.sessionId) {
    return data;
  }
  return { sessionId: createSessionId(), messages: [] };
}

export async function saveSession(
  videoId: string,
  session: SessionState
): Promise<void> {
  const key = `${STORAGE_KEY}:${videoId}`;
  await chrome.storage.session.set({ [key]: session });
}

export function appendMessage(
  session: SessionState,
  role: ChatMessage["role"],
  content: string
): SessionState {
  const messages = [...session.messages, { role, content }];
  const trimmed = messages.slice(-20);
  return { ...session, messages: trimmed };
}

export function clearSession(videoId: string): Promise<void> {
  const key = `${STORAGE_KEY}:${videoId}`;
  return chrome.storage.session.remove(key);
}
