from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, is_dataclass

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator
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
    self.adapter = SimulationAdapter()
    self.orch = CareOrchestrator(load_config(), self.adapter)
    self.chat_log: list[dict] = []

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
