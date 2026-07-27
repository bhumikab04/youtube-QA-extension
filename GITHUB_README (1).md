# 🎥 YouTube Video Q&A

Ask questions about any YouTube video and get answers grounded in what's actually said in it — powered by Google Gemini, LangChain, and a Retrieval-Augmented Generation (RAG) pipeline.

Ask things like:
- "Summarize this video"
- "Does this video talk about nuclear fusion? What did they say?"
- "What did the speaker say about DeepMind?"

## How it works

1. **Fetch** — pulls the video's transcript/captions using `youtube-transcript-api`.
2. **Chunk** — splits the transcript into overlapping chunks with LangChain's `RecursiveCharacterTextSplitter`.
3. **Embed** — converts each chunk into a vector using Gemini's embedding model, stored in a FAISS vector index.
4. **Retrieve** — for a given question, finds the most relevant chunks via similarity search.
5. **Answer** — feeds those chunks + the question to `gemini-2.5-flash`, instructed to answer **only** from the provided context.

```
Chrome Extension (popup UI)  →  FastAPI backend  →  Gemini API
                                       ↓
                            YouTube Transcript API
```

## Tech stack

- **Backend:** Python, FastAPI, LangChain, FAISS, Google Generative AI (Gemini)
- **Frontend:** Chrome Extension (Manifest V3) — vanilla HTML/CSS/JS
- **Transcript fetching:** `youtube-transcript-api`

## Project structure

```
.
├── main.py               # FastAPI app — exposes the /ask endpoint
├── rag.py                # Core RAG logic (transcript → chunks → FAISS → LLM)
├── requirements.txt      # Python dependencies
├── .env.example          # Template for required environment variables
└── .gitignore
```

*(The Chrome extension code — `manifest.json`, `popup.html/css/js` — lives alongside this backend and talks to it over HTTP.)*

## Getting started

```bash
# 1. Clone this repo
git clone https://github.com/bhumikab04/youtube-QA-extension.git
cd youtube-QA-extension

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# then open .env and add your Gemini API key (get one free at https://aistudio.google.com/apikey)

# 5. Run the server
uvicorn main:app --reload --port 8000
```

Test it:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"video_url_or_id": "Gfr50f6ZBvo", "question": "What is this video about?"}'
```

## Chrome Extension

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder
4. Make sure the backend server (above) is running
5. Open any YouTube video and click the extension icon to ask questions

## API

### `POST /ask`

**Request body:**
```json
{
  "video_url_or_id": "https://www.youtube.com/watch?v=VIDEO_ID",
  "question": "What is this video about?"
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "answer": "..."
}
```

### `GET /health`
Simple healthcheck — returns `{"status": "ok"}`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) |

## Notes & limitations

- Currently runs locally — the backend needs to be running on your machine for the extension to work.
- The in-memory retriever cache resets whenever the server restarts.
- Only fetches English-language captions by default.

## License

MIT
