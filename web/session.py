from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, is_dataclass

import base64

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator
from care_companion.perception.pose_pipeline import PosePipeline
from simulation.scenarios import demo_scenarios


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
    self.chat_log: list[dict] = []
    self.last_vision: dict | None = None

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
