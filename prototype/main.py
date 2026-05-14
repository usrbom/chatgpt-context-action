import uuid
import os
from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database as db
import agent

db.init_db()

app = FastAPI(title="ChatGPT Contextual Action Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> {"messages": [...], "state": {...}}
_sessions: dict = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str = "demo_user_01"


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_calls: list


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.session_id not in _sessions:
        _sessions[req.session_id] = {"messages": [], "state": None}

    session = _sessions[req.session_id]
    session["messages"].append({"role": "user", "content": req.message})

    today = date.today().isoformat()
    response_text, tool_calls, new_state = agent.run_agent(
        messages=list(session["messages"]),
        user_id=req.user_id,
        today=today,
        session_id=req.session_id,
        state=session["state"],
    )

    session["messages"].append({"role": "assistant", "content": response_text})
    session["state"] = new_state

    return ChatResponse(
        session_id=req.session_id,
        message=response_text,
        tool_calls=tool_calls,
    )


@app.get("/session/new")
async def new_session():
    return {"session_id": str(uuid.uuid4())}


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "mock-agent (no API key required)"}


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
