from __future__ import annotations

import json
import time
from pathlib import Path

from care_companion.action.robot_adapter import ROS2Adapter
from care_companion.core.events import RobotAction


class RecordingROS2Adapter(ROS2Adapter):
  """在 ROS2Adapter 基础上，将每条指令写入 JSONL（等同 /care/robot_cmd 载荷）。"""

  def __init__(self, cfg: dict, log_path: str | Path):
    super().__init__(cfg)
    self._log_path = Path(log_path)
    self._log_path.parent.mkdir(parents=True, exist_ok=True)
    self._fp = self._log_path.open("w", encoding="utf-8")
    self._topic = cfg.get("cmd_topic", "/care/robot_cmd")
    self._t0 = time.time()
    self.records: list[dict] = []

  def execute(self, action: RobotAction) -> None:
    payload = {"command": action.command.value, **action.payload}
    text = json.dumps(payload, ensure_ascii=False)
    rec = {
      "t_rel_s": round(time.time() - self._t0, 3),
      "topic": self._topic,
      "data": payload,
      "json": text,
    }
    self.records.append(rec)
    self._fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
    self._fp.flush()
    super().execute(action)

  def shutdown(self) -> None:
    self._fp.close()
    super().shutdown()
