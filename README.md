# YT Notes

A Chrome extension that opens a side-panel chat to **summarize YouTube videos** and answer follow-up questions in **any language**. AI runs on a local FastAPI backend (RAG over transcripts with Google Gemini chat + embeddings + ChromaDB).

## Architecture


| Layer    | Stack                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------ |
| Frontend | Chrome MV3, React, Tailwind, Side Panel API                                                                 |
| Backend  | FastAPI, LangChain text splitters, ChromaDB, Gemini 3.1 Flash Lite chat, Gemini Embedding 2                 |


```
User → Side panel → POST /api/chat → Transcript → Chunk → Embed → ChromaDB
                                              ↓
                                    Retrieve top-k → Gemini → Answer
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- [Google AI (Gemini) API key](https://aistudio.google.com/app/apikey)

## Backend setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with GOOGLE_API_KEY

uvicorn app.main:app --reload --host 127.0.0.1 --port 3000
```

Verify: `http://127.0.0.1:3000/health`

## Extension setup

```bash
cd frontend
npm install
npm run build
```

Load in Chrome:

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select `frontend/dist`

## Usage

1. Open a YouTube **watch** page (video with captions/transcript).
2. Click the **YT Notes** extension icon → side panel opens.
3. Use quick actions or type a question in any language.
4. Follow-up questions stay in the same session until you click **New chat**.

## Configuration

See `backend/.env.example` for:

- Chat model and fallback (`GOOGLE_CHAT_MODEL`, `GOOGLE_CHAT_MODEL_FALLBACK`)
- Embedding model (`GOOGLE_EMBEDDING_MODEL`)
- Chunk size / overlap / `RETRIEVAL_TOP_K`
- Chroma persist path

The extension calls `http://127.0.0.1:3000` by default (`frontend/src/lib/api.ts`).

## v1 scope

Included: side panel chat, transcript RAG, session memory, multilingual Q&A.

Not included: login, user API keys in the browser, voice, local models, cross-session multi-video memory.

## License

See [LICENSE](LICENSE).