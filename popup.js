// Change this to your deployed backend URL once you host it (see README).
const BACKEND_URL = "http://localhost:8000";

const videoInfoEl = document.getElementById("videoInfo");
const questionEl = document.getElementById("question");
const askBtn = document.getElementById("askBtn");
const statusEl = document.getElementById("status");
const answerEl = document.getElementById("answer");
const loaderEl = document.getElementById("loader");
const loaderTextEl = document.getElementById("loaderText");

let currentVideoId = null;

function extractVideoId(url) {
  const match = url.match(/(?:v=|youtu\.be\/)([0-9A-Za-z_-]{11})/);
  return match ? match[1] : null;
}

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || !tab.url.includes("youtube.com/watch")) {
    videoInfoEl.textContent = "Open a YouTube video to use this.";
    askBtn.disabled = true;
    return;
  }
  currentVideoId = extractVideoId(tab.url);
  if (!currentVideoId) {
    videoInfoEl.textContent = "Couldn't detect a video ID on this page.";
    askBtn.disabled = true;
    return;
  }
  videoInfoEl.textContent = `Video ID: ${currentVideoId}`;
}

async function ask() {
  const question = questionEl.value.trim();
  if (!question || !currentVideoId) return;

  askBtn.disabled = true;
  statusEl.textContent = "";
  answerEl.textContent = "";
  loaderTextEl.textContent = "Thinking…";
  loaderEl.style.display = "flex";

  try {
    const res = await fetch(`${BACKEND_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_url_or_id: currentVideoId,
        question,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      statusEl.textContent = "Error";
      answerEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    answerEl.textContent = data.answer;
  } catch (err) {
    statusEl.textContent = "Error";
    answerEl.textContent = "Could not reach the backend. Is it running?";
  } finally {
    askBtn.disabled = false;
    loaderEl.style.display = "none";
  }
}

askBtn.addEventListener("click", ask);
init();