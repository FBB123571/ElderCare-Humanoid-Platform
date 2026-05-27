from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass
class HealthSnapshot:
  heart_rate: int
  spo2: int
  activity_level: float
  risk_flags: list[str]


class HealthMonitor:
  def __init__(self, cfg: dict):
    self.hr_min = cfg.get("hr_min", 50)
    self.hr_max = cfg.get("hr_max", 120)
    self.spo2_min = cfg.get("spo2_min", 92)
    self.inactivity_limit = cfg.get("inactivity_minutes", 45) * 60
    self._last_active = time()

  def update(
    self,
    heart_rate: int,
    spo2: int,
    activity_level: float,
  ) -> HealthSnapshot:
    flags: list[str] = []
    if heart_rate < self.hr_min or heart_rate > self.hr_max:
      flags.append("心率异常")
    if spo2 < self.spo2_min:
      flags.append("血氧偏低")
    if activity_level > 0.15:
      self._last_active = time()
    elif time() - self._last_active > self.inactivity_limit:
      flags.append("长时间无活动")

    return HealthSnapshot(heart_rate, spo2, activity_level, flags)
