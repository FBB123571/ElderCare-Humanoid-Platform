"""数字人陪护：对话人设与情景剧脚本。"""
from __future__ import annotations

from dataclasses import dataclass

from care_companion.core.events import PerceptionFrame


@dataclass
class ActingLine:
  speaker: str  # elder | stage
  text: str | None = None
  frame: PerceptionFrame | None = None
  pause_s: float = 0.0


COMPANION_NAME = "小护"
COMPANION_GREETING = "您好，我是陪伴机器人小护，一直在您身边。"

# 自然交互情景剧：倾诉 → 安抚 → 突发跌倒 → 紧急响应
ACTING_SCRIPT: list[ActingLine] = [
  ActingLine("stage", "【场景】客厅午后，老人独坐沙发", pause_s=0.8),
  ActingLine("elder", "小护啊，这几天老是睡不踏实，心里空落落的。"),
  ActingLine("elder", "孩子们都忙，我也不想总打扰他们…"),
  ActingLine(
    "elder",
    None,
    frame=PerceptionFrame(
      user_text="就是有点孤单",
      emotion="sad",
      heart_rate=78,
      activity_level=0.15,
    ),
  ),
  ActingLine("stage", "【转折】老人起身时不稳", pause_s=1.0),
  ActingLine(
    "elder",
    "哎哟——！",
    frame=PerceptionFrame(
      skeleton_aspect_ratio=0.32,
      skeleton_dy=-0.85,
      activity_level=0.04,
      emotion="anxious",
      heart_rate=102,
      fall_detected=True,
      fall_score=0.96,
    ),
  ),
  ActingLine(
    "elder",
    None,
    frame=PerceptionFrame(
      skeleton_aspect_ratio=0.28,
      skeleton_dy=0.0,
      activity_level=0.02,
      emotion="anxious",
      heart_rate=108,
      fall_detected=True,
      fall_score=0.98,
      user_text="",
    ),
  ),
  ActingLine("stage", "【系统】风险融合 → 紧急指令下发", pause_s=0.6),
]


def companion_avatar_state(risk_level: str, emotion: str) -> str:
  if risk_level == "emergency":
    return "emergency"
  if risk_level == "alert":
    return "alert"
  if emotion in ("sad", "anxious", "happy", "neutral"):
    return emotion
  return "neutral"
