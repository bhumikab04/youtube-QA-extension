import os
import re
from dotenv import load_dotenv
load_dotenv()  # reads .env and sets OPENAI_API_KEY etc.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import answer_question

app = FastAPI(title="YouTube Video Q&A API")

# Allow the Chrome extension (and local testing) to call this API.
# Chrome extensions send requests with an origin like chrome-extension://<id>
# During development "*" is simplest; lock this down before publishing widely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    video_url_or_id: str
    question: str


def extract_video_id(url_or_id: str) -> str:
    """Accepts a raw video ID or a full YouTube URL and returns the ID."""
    patterns = [
        r"(?:v=|/)([0-9A-Za-z_-]{11}).*",  # watch?v=ID or youtu.be/ID
        r"^([0-9A-Za-z_-]{11})$",           # already just an ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise HTTPException(status_code=400, detail="Could not extract a video ID from that input.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(req: AskRequest):
    video_id = extract_video_id(req.video_url_or_id)
    try:
        answer = answer_question(video_id, req.question)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")
    return {"video_id": video_id, "answer": answer}
