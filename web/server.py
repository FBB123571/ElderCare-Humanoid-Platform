from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from web.session import SESSION

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="CareCompanion", version="1.1.0")
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
  use_vision: bool = False


class DigitalHumanChatRequest(BaseModel):
  message: str = ""
  emotion: str = "neutral"


@app.get("/")
def index():
  return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
  return {
    "ok": True,
    "service": "CareCompanion Web",
    "features": ["video_url", "digital_human", "mood_acting"],
  }


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
    "dh_log": SESSION.dh_log[-50:],
    "system_logs": SESSION.orch.logs[-20:],
    "dh_avatar": SESSION.dh_avatar,
    "last_video": SESSION.last_video is not None,
  }


@app.post("/api/tick")
def tick(body: TickRequest):
  payload = body.model_dump()
  use_vision = payload.pop("use_vision", False)
  return SESSION.tick_with_vision(payload, use_vision=use_vision)


@app.post("/api/vision/analyze")
async def vision_analyze(file: UploadFile = File(...)):
  data = await file.read()
  return SESSION.analyze_vision(data)


@app.get("/api/vision/last")
def vision_last():
  return {"ok": SESSION.last_vision is not None, "metrics": SESSION.last_vision}


@app.get("/api/video/samples")
def video_samples():
  return SESSION.list_video_samples()


@app.post("/api/video/analyze")
async def video_analyze(
  mode: str = Form("both"),
  url: Optional[str] = Form(None),
  max_frames: int = Form(120),
  frame_stride: int = Form(2),
  auto_alert: bool = Form(True),
  file: Optional[UploadFile] = File(None),
):
  upload_bytes = None
  if file and file.filename:
    upload_bytes = await file.read()
  return SESSION.analyze_video(
    url=url,
    upload_bytes=upload_bytes,
    mode=mode,
    max_frames=max_frames,
    frame_stride=frame_stride,
    auto_alert=auto_alert,
  )


@app.get("/api/video/last")
def video_last():
  return {"ok": SESSION.last_video is not None, "result": SESSION.last_video}


@app.post("/api/digital_human/chat")
def digital_human_chat(body: DigitalHumanChatRequest):
  return SESSION.digital_human_chat(body.message, body.emotion)


@app.get("/api/digital_human/act")
async def digital_human_act():
  SESSION.reset()

  async def event_gen():
    async for item in SESSION.stream_acting():
      yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

  return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/api/digital_human/mood_act")
async def digital_human_mood_act():
  """根据最近一次视频心情分析结果，驱动老人↔小护情景剧（SSE）。"""

  async def event_gen():
    async for item in SESSION.stream_mood_acting():
      yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

  return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/api/demo/stream")
async def demo_stream():
  SESSION.reset()

  async def event_gen():
    async for item in SESSION.stream_demo():
      yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

  return StreamingResponse(event_gen(), media_type="text/event-stream")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
