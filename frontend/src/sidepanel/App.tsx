import { useCallback, useEffect, useRef, useState } from "react";
import { getActiveVideo, sendChat, type VideoContext } from "../lib/api";
import type { SessionState } from "../lib/api";
import {
  appendMessage,
  clearSession,
  loadSession,
  saveSession,
} from "../lib/session";

const QUICK_ACTIONS = [
  {
    label: "Summarize video",
    message: "Please summarize this video concisely.",
  },
  { label: "Main point?", message: "What is the main point of this video?" },
  {
    label: "Key takeaways",
    message: "List the key takeaways from this video.",
  },
];

function formatError(err: unknown): string {
  const msg = err instanceof Error ? err.message : String(err);
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
    return "The answer service is temporarily unavailable. Server is temporarily unavailable.";
  }
  if (msg.toLowerCase().includes("transcript")) {
    return "The transcript could not be loaded for this video.";
  }
  return msg || "Something went wrong. Please try again.";
}

export default function App() {
  const [video, setVideo] = useState<VideoContext | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const refreshVideo = useCallback(async () => {
    const ctx = await getActiveVideo();
    setVideo(ctx);
    if (ctx) {
      const s = await loadSession(ctx.videoId);
      setSession(s);
      setError(null);
    } else {
      setSession(null);
      setError("Open a YouTube watch page to use YT Notes.");
    }
  }, []);

  useEffect(() => {
    refreshVideo();
    const onChanged = (msg: { type?: string }) => {
      if (msg.type === "VIDEO_CHANGED") refreshVideo();
    };
    chrome.runtime.onMessage.addListener(onChanged);
    return () => chrome.runtime.onMessage.removeListener(onChanged);
  }, [refreshVideo]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages, loading]);

  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading || !video || !session) return;

    setError(null);
    setLoading(true);
    setInput("");

    let next = appendMessage(session, "user", trimmed);
    setSession(next);
    await saveSession(video.videoId, next);

    try {
      const res = await sendChat({
        message: trimmed,
        video_id: video.videoId,
        video_title: video.title,
        session_id: session.sessionId,
      });

      next = appendMessage(next, "assistant", res.answer);
      setSession({ ...next, sessionId: res.session_id || next.sessionId });
      await saveSession(video.videoId, {
        ...next,
        sessionId: res.session_id || next.sessionId,
      });

      if (res.video_title && video.title !== res.video_title) {
        setVideo({ ...video, title: res.video_title });
      }
    } catch (e) {
      setError(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    if (!video) return;
    await clearSession(video.videoId);
    const s = await loadSession(video.videoId);
    setSession(s);
    setError(null);
  };

  return (
    <div className="flex h-full flex-col bg-yt-dark text-gray-100">
      <header className="shrink-0 border-b border-yt-border bg-yt-surface px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-lg font-semibold tracking-tight">
            <span className="text-yt-red">YT</span> Notes
          </h1>
          <button
            type="button"
            onClick={handleNewChat}
            disabled={!video}
            className="text-xs text-yt-muted hover:text-white disabled:opacity-40"
          >
            New chat
          </button>
        </div>
        <p className="mt-1 truncate text-xs text-yt-muted" title={video?.title}>
          {video?.title ?? "No video detected"}
        </p>
      </header>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-3">
        {session?.messages.length === 0 && !loading && (
          <div className="rounded-lg border border-yt-border bg-yt-surface p-4 text-sm text-yt-muted">
            Ask anything about the current video. Summaries and follow-ups work
            in any language.
          </div>
        )}

        {session?.messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[95%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
              m.role === "user"
                ? "ml-auto bg-yt-red/90 text-white"
                : "mr-auto bg-yt-surface border border-yt-border"
            }`}
          >
            <p className="whitespace-pre-wrap">{m.content}</p>
          </div>
        ))}

        {loading && (
          <div className="mr-auto flex items-center gap-2 rounded-xl border border-yt-border bg-yt-surface px-3 py-2 text-sm text-yt-muted">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-yt-red" />
            Thinking…
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="shrink-0 border-t border-yt-border bg-yt-surface px-3 py-2">
        <div className="mb-2 flex flex-wrap gap-1.5">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.label}
              type="button"
              disabled={!video || loading}
              onClick={() => handleSend(a.message)}
              className="rounded-full border border-yt-border px-2.5 py-1 text-xs text-yt-muted transition hover:border-yt-red/50 hover:text-white disabled:opacity-40"
            >
              {a.label}
            </button>
          ))}
        </div>

        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(input);
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              video ? "Ask about this video…" : "Open a YouTube video first"
            }
            disabled={!video || loading}
            className="min-w-0 flex-1 rounded-lg border border-yt-border bg-yt-dark px-3 py-2 text-sm outline-none focus:border-yt-red/60 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!video || loading || !input.trim()}
            className="rounded-lg bg-yt-red px-4 py-2 text-sm font-medium text-white transition hover:bg-red-600 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
