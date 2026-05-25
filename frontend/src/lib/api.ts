const API_BASE = "http://127.0.0.1:3000";

export interface VideoContext {
  videoId: string;
  title: string;
  url: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SessionState {
  sessionId: string;
  messages: ChatMessage[];
}

export interface ChatRequest {
  message: string;
  video_id: string;
  video_title?: string;
  session_id?: string;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  video_title?: string;
  error?: string;
}

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = (await res.json()) as ChatResponse & { detail?: string };

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }

  return data;
}

export async function getActiveVideo(): Promise<VideoContext | null> {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: "GET_ACTIVE_VIDEO" }, (response) => {
      if (chrome.runtime.lastError || !response?.ok || !response.videoId) {
        resolve(null);
        return;
      }
      resolve({
        videoId: response.videoId,
        title: response.title || "YouTube Video",
        url: response.url,
      });
    });
  });
}
