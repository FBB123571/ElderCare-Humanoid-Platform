#!/usr/bin/env python3
"""无 GUI 自动跑通演示剧本，用于 CI / 答辩预演。"""
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.orchestrator import CareOrchestrator
from simulation.scenarios import demo_scenarios


def main():
  cfg = load_config()
  adapter = SimulationAdapter()
  orch = CareOrchestrator(cfg, adapter)

  print("CareCompanion headless demo")
  for step in demo_scenarios():
    print(f"\n=== {step.name} ({step.duration_s}s) ===")
    t0 = time.time()
    while time.time() - t0 < step.duration_s:
      s = orch.tick(step.frame)
      print(
        f"  state={s['state']} risk={s['risk'].score:.2f} "
        f"fall={s['fall'].detected} actions={s['actions']}"
      )
      time.sleep(0.3)

  print(f"\n完成。共执行机器人指令 {len(adapter.history)} 条。")
  emergency = [h for h in adapter.history if h.get("command") == "call_emergency"]
  if not emergency:
    raise SystemExit("预期演示中包含紧急呼叫，请检查跌倒场景逻辑")
  print("✅ 跌倒紧急流程验证通过")


if __name__ == "__main__":
  main()
