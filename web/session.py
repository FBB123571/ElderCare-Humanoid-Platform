from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path

import base64

import yaml

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.cognition.digital_human import (
  ACTING_SCRIPT,
  COMPANION_GREETING,
  COMPANION_NAME,
  companion_avatar_state,
)
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator
from care_companion.perception.pose_pipeline import PosePipeline
from care_companion.perception.video_analyzer import VideoAnalyzer
from care_companion.perception.video_fetch import cleanup_path, resolve_video_source
from simulation.scenarios import demo_scenarios

ROOT = Path(__file__).resolve().parents[1]


def _serialize(obj):
  if is_dataclass(obj):
    return asdict(obj)
  if isinstance(obj, list):
    return [_serialize(x) for x in obj]
  return obj


class CareSession:
  """单用户 Web 会话，复用 CareOrchestrator 核心逻辑。"""

  def __init__(self):
    self.reset()

  def reset(self) -> None:
    self.cfg = load_config()
    self.adapter = SimulationAdapter()
    self.orch = CareOrchestrator(self.cfg, self.adapter)
    self.pose = PosePipeline(self.cfg.get("fall", {}))
    self.video = VideoAnalyzer(self.cfg)
    self.chat_log: list[dict] = []
    self.dh_log: list[dict] = []
    self.last_vision: dict | None = None
    self.last_video: dict | None = None
    self.dh_avatar = "neutral"

  def analyze_vision(self, image_bytes: bytes, dt: float = 0.1) -> dict:
    try:
      return self._analyze_vision_impl(image_bytes, dt)
    except Exception as exc:
      return {"ok": False, "error": f"视觉分析异常: {exc}"}

  def _analyze_vision_impl(self, image_bytes: bytes, dt: float = 0.1) -> dict:
    img = self.pose.decode_upload(image_bytes)
    if img is None:
      return {"ok": False, "error": "无法解码图像"}
    metrics, fall_r, annotated = self.pose.analyze_bgr(img, dt)
    preview_b64 = None
    if annotated is not None:
      import cv2

      _, buf = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
      preview_b64 = base64.b64encode(buf).decode("ascii")
    self.last_vision = {
      "aspect_ratio": metrics.aspect_ratio,
      "dy": metrics.dy,
      "visible": metrics.visible,
      "fall": _serialize(fall_r),
    }
    if metrics.visible:
      message = f"已检测到人体骨架 · 宽高比 {metrics.aspect_ratio:.2f}"
    else:
      message = fall_r.reason or "未检测到人体（请上传含头、肩、髋、手臂的上半身照片）"

    return {
      "ok": True,
      "metrics": self.last_vision,
      "preview_jpeg_b64": preview_b64,
      "message": message,
      "mediapipe_available": self.pose.mediapipe_ready()
      or fall_r.reason not in ("mediapipe 未安装", "缺少姿态模型，请运行 bash scripts/download_mediapipe_models.sh"),
    }

  def tick_with_vision(self, payload: dict, use_vision: bool = False) -> dict:
    if use_vision and self.last_vision:
      payload = {
        **payload,
        "skeleton_aspect_ratio": self.last_vision["aspect_ratio"],
        "skeleton_dy": self.last_vision["dy"],
      }
    return self.tick(payload)

  def tick(self, payload: dict) -> dict:
    user_text = (payload.get("user_text") or "").strip() or None
    if user_text:
      self.chat_log.append({"role": "user", "text": user_text})

    frame = PerceptionFrame(
      heart_rate=int(payload.get("heart_rate", 72)),
      spo2=int(payload.get("spo2", 98)),
      activity_level=float(payload.get("activity_level", 0.4)),
      skeleton_aspect_ratio=float(payload.get("skeleton_aspect_ratio", 1.1)),
      skeleton_dy=float(payload.get("skeleton_dy", 0.0)),
      emotion=str(payload.get("emotion", "neutral")),
      user_text=user_text,
    )
    summary = self.orch.tick(frame)
    result = {
      "state": summary["state"],
      "risk": _serialize(summary["risk"]),
      "fall": _serialize(summary["fall"]),
      "health_flags": summary["health_flags"],
      "reply": summary["reply"] or "",
      "actions": summary["actions"],
      "timestamp": time.time(),
    }
    if result["reply"]:
      self.chat_log.append({"role": "robot", "text": result["reply"]})
    return result

  def list_video_samples(self) -> dict:
    path = ROOT / "config" / "video_samples.yaml"
    if not path.is_file():
      return {"fall": [], "mood": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {"fall": data.get("fall", []), "mood": data.get("mood", [])}

  def analyze_video(
    self,
    *,
    url: str | None = None,
    upload_bytes: bytes | None = None,
    mode: str = "both",
    max_frames: int = 120,
    frame_stride: int = 2,
    auto_alert: bool = True,
  ) -> dict:
    path = None
    try:
      path, source = resolve_video_source(url=url, upload_bytes=upload_bytes)
      raw = self.video.analyze_file(path, max_frames=max_frames, frame_stride=frame_stride)
      if not raw.get("ok"):
        return raw
      out = {"ok": True, "source": source, **raw}
      self.last_video = out

      if mode in ("fall", "both") and raw["fall"]["detected"] and auto_alert:
        tick_payload = {
          "heart_rate": 102,
          "spo2": 93,
          "activity_level": 0.03,
          "skeleton_aspect_ratio": 0.3,
          "skeleton_dy": 0.0,
          "emotion": "anxious",
          "user_text": "【视频分析】检测到跌倒事件",
        }
        alert = self.tick(tick_payload)
        out["alert"] = alert
        self.dh_log.append({
          "role": "system",
          "text": f"⚠️ 视频跌倒预警：t≈{raw['fall'].get('first_alert_t_s')}s，已触发紧急决策",
        })

      if mode in ("emotion", "both"):
        emo = raw["emotion"]["dominant"]
        self.dh_avatar = companion_avatar_state("normal", emo)

      return out
    except ValueError as exc:
      return {"ok": False, "error": str(exc)}
    except Exception as exc:
      return {"ok": False, "error": f"视频分析失败: {exc}"}
    finally:
      cleanup_path(path)

  def digital_human_chat(self, message: str, emotion: str | None = None) -> dict:
    text = (message or "").strip()
    if not text:
      return {"ok": False, "error": "请输入对话"}
    self.dh_log.append({"role": "elder", "text": text, "speaker": "老人"})
    payload = {
      "heart_rate": 78,
      "spo2": 97,
      "activity_level": 0.25,
      "skeleton_aspect_ratio": 1.0,
      "skeleton_dy": 0.0,
      "emotion": emotion or "neutral",
      "user_text": text,
    }
    result = self.tick(payload)
    reply = result.get("reply") or "我在听，您慢慢说。"
    self.dh_log.append({
      "role": "companion",
      "text": reply,
      "speaker": COMPANION_NAME,
      "avatar": companion_avatar_state(result["risk"]["level"], emotion or "neutral"),
    })
    self.dh_avatar = companion_avatar_state(result["risk"]["level"], emotion or "neutral")
    return {
      "ok": True,
      "reply": reply,
      "tick": result,
      "avatar": self.dh_avatar,
      "companion_name": COMPANION_NAME,
    }

  async def stream_acting(self):
    yield {
      "type": "stage",
      "text": COMPANION_GREETING,
      "speaker": COMPANION_NAME,
      "avatar": "neutral",
    }
    self.dh_log.append({"role": "companion", "text": COMPANION_GREETING, "speaker": COMPANION_NAME})

    for line in ACTING_SCRIPT:
      if line.pause_s > 0:
        yield {"type": "pause", "seconds": line.pause_s}
        await asyncio.sleep(line.pause_s)

      if line.speaker == "stage":
        yield {"type": "stage", "text": line.text, "speaker": "旁白"}
        self.dh_log.append({"role": "system", "text": line.text})
        continue

      if line.speaker == "elder" and line.text and line.frame is None:
        yield {"type": "elder", "text": line.text, "speaker": "老人"}
        self.dh_log.append({"role": "elder", "text": line.text, "speaker": "老人"})
        result = self.tick({
          "heart_rate": 76,
          "spo2": 97,
          "activity_level": 0.2,
          "skeleton_aspect_ratio": 1.0,
          "skeleton_dy": 0.0,
          "emotion": "sad",
          "user_text": line.text,
        })
        self.dh_avatar = companion_avatar_state(result["risk"]["level"], "sad")
        reply = result.get("reply") or ""
        if reply:
          yield {
            "type": "companion",
            "text": reply,
            "speaker": COMPANION_NAME,
            "avatar": self.dh_avatar,
          }
          self.dh_log.append({"role": "companion", "text": reply, "speaker": COMPANION_NAME})
        await asyncio.sleep(0.8)
        continue

      if line.frame is not None:
        f = line.frame
        payload = {
          "heart_rate": f.heart_rate,
          "spo2": f.spo2,
          "activity_level": f.activity_level,
          "skeleton_aspect_ratio": f.skeleton_aspect_ratio,
          "skeleton_dy": f.skeleton_dy,
          "emotion": f.emotion,
          "user_text": f.user_text or "",
        }
        if f.fall_detected:
          payload["skeleton_aspect_ratio"] = min(payload["skeleton_aspect_ratio"], 0.35)
        result = self.tick(payload)
        self.dh_avatar = companion_avatar_state(result["risk"]["level"], f.emotion)
        if line.text:
          yield {"type": "elder", "text": line.text, "speaker": "老人"}
        yield {
          "type": "companion",
          "text": result.get("reply") or "",
          "speaker": COMPANION_NAME,
          "avatar": self.dh_avatar,
          "tick": _serialize(result),
        }
        if result.get("reply"):
          self.dh_log.append({
            "role": "companion",
            "text": result["reply"],
            "speaker": COMPANION_NAME,
          })
        await asyncio.sleep(0.5)

    yield {"type": "done", "avatar": self.dh_avatar}

  async def stream_demo(self):
    for step in demo_scenarios():
      yield {"type": "scenario", "name": step.name, "duration_s": step.duration_s}
      t0 = time.time()
      while time.time() - t0 < step.duration_s:
        result = self.tick(
          {
            "heart_rate": step.frame.heart_rate,
            "spo2": step.frame.spo2,
            "activity_level": step.frame.activity_level,
            "skeleton_aspect_ratio": step.frame.skeleton_aspect_ratio,
            "skeleton_dy": step.frame.skeleton_dy,
            "emotion": step.frame.emotion,
            "user_text": step.frame.user_text or "",
          }
        )
        yield {"type": "tick", **result}
        await asyncio.sleep(0.45)
    yield {
      "type": "done",
      "robot_commands": len(self.adapter.history),
      "emergency": any(h.get("command") == "call_emergency" for h in self.adapter.history),
    }


SESSION = CareSession()
