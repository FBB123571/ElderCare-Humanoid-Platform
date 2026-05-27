from __future__ import annotations

from dataclasses import dataclass

from care_companion.core.events import PerceptionFrame


@dataclass
class ScenarioStep:
  name: str
  duration_s: float
  frame: PerceptionFrame


def demo_scenarios() -> list[ScenarioStep]:
  """答辩演示剧本：正常 → 情绪低落 → 跌倒紧急。"""
  return [
    ScenarioStep(
      "日常监测",
      2.0,
      PerceptionFrame(
        heart_rate=72,
        spo2=98,
        activity_level=0.4,
        skeleton_aspect_ratio=1.1,
        skeleton_dy=0.0,
        emotion="neutral",
      ),
    ),
    ScenarioStep(
      "老人倾诉",
      3.0,
      PerceptionFrame(
        user_text="最近有点孤独，睡不太好",
        heart_rate=78,
        spo2=97,
        activity_level=0.2,
        emotion="sad",
        skeleton_aspect_ratio=1.0,
      ),
    ),
    ScenarioStep(
      "跌倒事件",
      2.5,
      PerceptionFrame(
        heart_rate=95,
        spo2=94,
        activity_level=0.05,
        skeleton_aspect_ratio=0.35,
        skeleton_dy=-0.8,
        emotion="anxious",
      ),
    ),
    ScenarioStep(
      "紧急维持",
      2.0,
      PerceptionFrame(
        heart_rate=102,
        spo2=93,
        activity_level=0.02,
        skeleton_aspect_ratio=0.3,
        skeleton_dy=0.0,
        fall_detected=True,
        fall_score=0.95,
      ),
    ),
  ]
