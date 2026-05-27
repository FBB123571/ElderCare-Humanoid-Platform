from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from web.session import SESSION

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="CareCompanion", version="1.0.0")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)


class TickRequest(BaseModel):
  heart_rate: int = Field(72, ge=40, le=160)
  spo2: int = Field(98, ge=85, le=100)
  activity_level: float = Field(0.4, ge=0.0, le=1.0)
  skeleton_aspect_ratio: float = Field(1.1, ge=0.2, le=2.0)
  skeleton_dy: float = Field(0.0, ge=-1.5, le=1.0)
  emotion: str = "neutral"
  user_text: str = ""


@app.get("/")
def index():
  return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
  return {"ok": True, "service": "CareCompanion Web"}


@app.post("/api/reset")
def reset():
  SESSION.reset()
  return {"ok": True}


@app.get("/api/status")
def status():
  return {
    "state": SESSION.orch.state.value,
    "robot_history": SESSION.adapter.history[-30:],
    "chat_log": SESSION.chat_log[-40:],
    "system_logs": SESSION.orch.logs[-20:],
  }


@app.post("/api/tick")
def tick(body: TickRequest):
  return SESSION.tick(body.model_dump())


@app.get("/api/demo/stream")
async def demo_stream():
  SESSION.reset()

  async def event_gen():
    async for item in SESSION.stream_demo():
      yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

  return StreamingResponse(event_gen(), media_type="text/event-stream")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
