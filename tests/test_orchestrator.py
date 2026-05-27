import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator


def test_fall_triggers_emergency():
  cfg = load_config()
  orch = CareOrchestrator(cfg, SimulationAdapter())
  frame = PerceptionFrame(
    skeleton_aspect_ratio=0.3,
    skeleton_dy=-0.9,
    heart_rate=100,
    spo2=93,
    activity_level=0.01,
  )
  for _ in range(8):
    summary = orch.tick(frame)
  assert summary["risk"].level == "emergency"
  assert summary["fall"].detected


def test_chat_normal():
  cfg = load_config()
  orch = CareOrchestrator(cfg, SimulationAdapter())
  frame = PerceptionFrame(user_text="你好", heart_rate=70, spo2=99)
  summary = orch.tick(frame)
  assert summary["reply"]
  assert summary["risk"].level == "normal"
