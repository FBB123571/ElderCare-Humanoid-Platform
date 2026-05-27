from __future__ import annotations

from care_companion.core.events import PerceptionFrame, RiskAssessment


class RiskEngine:
  def __init__(self, cfg: dict):
    self.w_fall = cfg.get("fall_weight", 0.45)
    self.w_emo = cfg.get("emotion_weight", 0.25)
    self.w_health = cfg.get("health_weight", 0.30)
    self.alert_th = cfg.get("alert_threshold", 0.65)
    self.emergency_th = cfg.get("emergency_threshold", 0.85)

  def assess(self, frame: PerceptionFrame, health_flags: list[str]) -> RiskAssessment:
    reasons: list[str] = []
    fall_s = frame.fall_score if frame.fall_detected else frame.fall_score * 0.5
    if frame.fall_detected:
      reasons.append("跌倒事件")

    emo_s = 0.0
    if frame.emotion in ("sad", "anxious"):
      emo_s = frame.emotion_score
      reasons.append(f"情绪低落({frame.emotion})")

    health_s = min(len(health_flags) * 0.35, 1.0)
    if health_flags:
      reasons.extend(health_flags)

    score = (
      self.w_fall * fall_s
      + self.w_emo * emo_s
      + self.w_health * health_s
    )
    score = min(max(score, 0.0), 1.0)

    if score >= self.emergency_th or frame.fall_detected:
      level = "emergency"
    elif score >= self.alert_th:
      level = "alert"
    else:
      level = "normal"

    return RiskAssessment(score=score, level=level, reasons=reasons)
