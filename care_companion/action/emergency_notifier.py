from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EmergencyRecord:
  timestamp: str
  reasons: list[str]
  channels: list[str]
  payload: dict = field(default_factory=dict)


class EmergencyNotifier:
  """紧急呼叫模拟：记录家属/120/云端推送（真机可替换为 VoIP / 4G / App SDK）。"""

  def __init__(self, log_dir: str | Path = "logs"):
    self.log_dir = Path(log_dir)
    self.log_dir.mkdir(parents=True, exist_ok=True)
    self.history: list[EmergencyRecord] = []

  def trigger(self, reasons: list[str], context: dict | None = None) -> EmergencyRecord:
    channels = ["family_app_push", "sms_backup", "local_alarm"]
    record = EmergencyRecord(
      timestamp=datetime.now().isoformat(timespec="seconds"),
      reasons=reasons,
      channels=channels,
      payload=context or {},
    )
    self.history.append(record)
    path = self.log_dir / "emergency_calls.jsonl"
    with path.open("a", encoding="utf-8") as f:
      f.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")
    logger.warning("[EMERGENCY] %s -> %s", reasons, channels)
    return record
