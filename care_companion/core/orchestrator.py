from __future__ import annotations

import logging
from time import time

from care_companion.action.robot_adapter import RobotAdapter
from care_companion.cognition.care_planner import CarePlanner
from care_companion.cognition.dialogue_manager import DialogueManager
from care_companion.cognition.risk_engine import RiskEngine
from care_companion.core.events import PerceptionFrame, RobotState
from care_companion.perception.emotion_recognizer import EmotionRecognizer
from care_companion.perception.fall_detector import FallDetector
from care_companion.perception.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


class CareOrchestrator:
  """感知-决策-执行主循环，仿真与真机共用。"""

  def __init__(self, cfg: dict, robot: RobotAdapter):
    self.cfg = cfg
    self.robot = robot
    self.state = RobotState.MONITOR
    self.fall = FallDetector(cfg.get("fall", {}))
    self.emotion = EmotionRecognizer()
    self.health = HealthMonitor(cfg.get("health", {}))
    self.risk_engine = RiskEngine(cfg.get("risk", {}))
    self.dialogue = DialogueManager(cfg.get("dialogue", {}))
    self.planner = CarePlanner()
    self._last_tick = time()
    self.logs: list[str] = []

  def tick(self, frame: PerceptionFrame) -> dict:
    dt = max(time() - self._last_tick, 1e-3)
    self._last_tick = time()

    fall_r = self.fall.from_metrics(
      frame.skeleton_aspect_ratio,
      frame.skeleton_dy,
      dt,
    )
    frame.fall_score = fall_r.score
    frame.fall_detected = fall_r.detected

    emo_r = self.emotion.fuse(
      visual=frame.emotion if frame.emotion != "neutral" else None,
      text=frame.user_text,
    )
    frame.emotion = emo_r.label
    frame.emotion_score = emo_r.score

    health = self.health.update(
      frame.heart_rate, frame.spo2, frame.activity_level
    )
    risk = self.risk_engine.assess(frame, health.risk_flags)

    if risk.level == "emergency":
      self.state = RobotState.EMERGENCY
    elif risk.level == "alert":
      self.state = RobotState.ALERT
    elif frame.user_text:
      self.state = RobotState.CONVERSE
    else:
      self.state = RobotState.MONITOR

    ctx = {
      "risk_level": risk.level,
      "risk_score": risk.score,
      "emotion": frame.emotion,
      "reasons": risk.reasons,
    }
    reply = None
    if frame.user_text or risk.level != "normal":
      reply = self.dialogue.respond(frame.user_text, ctx)
    actions = self.planner.plan(risk.level, risk.reasons, reply)

    for act in actions:
      self.robot.execute(act)

    summary = {
      "state": self.state.value,
      "risk": risk,
      "fall": fall_r,
      "health_flags": health.risk_flags,
      "reply": reply,
      "actions": [a.command.value for a in actions],
    }
    line = (
      f"[{self.state.value}] risk={risk.score:.2f} fall={fall_r.detected} "
      f"emo={frame.emotion} hr={frame.heart_rate}"
    )
    self.logs.append(line)
    logger.debug(line)
    summary["reply"] = reply or ""
    return summary
