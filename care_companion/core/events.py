from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any


class RobotState(str, Enum):
  IDLE = "idle"
  MONITOR = "monitor"
  CONVERSE = "converse"
  ALERT = "alert"
  EMERGENCY = "emergency"


class RobotCommand(str, Enum):
  SPEAK = "speak"
  GESTURE = "gesture"
  APPROACH = "approach"
  ALERT_SOUND = "alert_sound"
  CALL_EMERGENCY = "call_emergency"
  LOG = "log"


@dataclass
class PerceptionFrame:
  timestamp: float = field(default_factory=time)
  fall_score: float = 0.0
  fall_detected: bool = False
  emotion: str = "neutral"
  emotion_score: float = 0.0
  heart_rate: int = 72
  spo2: int = 98
  activity_level: float = 0.5
  user_text: str | None = None
  skeleton_aspect_ratio: float = 1.2
  skeleton_dy: float = 0.0


@dataclass
class RiskAssessment:
  score: float
  level: str
  reasons: list[str] = field(default_factory=list)


@dataclass
class RobotAction:
  command: RobotCommand
  payload: dict[str, Any] = field(default_factory=dict)
