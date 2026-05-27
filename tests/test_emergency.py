import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.action.emergency_notifier import EmergencyNotifier
from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame, RobotAction, RobotCommand
from care_companion.core.orchestrator import CareOrchestrator


def test_emergency_notifier_writes_log(tmp_path):
  n = EmergencyNotifier(log_dir=tmp_path)
  rec = n.trigger(["跌倒事件"], {"hr": 100})
  assert rec.channels
  assert (tmp_path / "emergency_calls.jsonl").exists()


def test_simulation_adapter_emergency():
  adapter = SimulationAdapter()
  adapter.execute(RobotAction(RobotCommand.CALL_EMERGENCY, {"reasons": ["test"]}))
  assert adapter.history[-1]["command"] == "call_emergency"
  assert adapter.notifier.history


def test_orchestrator_emergency_chain():
  cfg = load_config()
  adapter = SimulationAdapter()
  orch = CareOrchestrator(cfg, adapter)
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
  assert any(h["command"] == "call_emergency" for h in adapter.history)
