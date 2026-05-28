#!/usr/bin/env python3
"""情景剧：跑通 demo_scenarios，录制 /care/robot_cmd 等价 JSONL（B 档 ROS2 证据）。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.action.recording_ros2_adapter import RecordingROS2Adapter
from care_companion.core.config import load_config
from care_companion.core.orchestrator import CareOrchestrator
from simulation.scenarios import demo_scenarios

OUT_JSONL = ROOT / "docs" / "assets" / "ros2_cmd_timeline.jsonl"
OUT_SUMMARY = ROOT / "docs" / "assets" / "ros2_cmd_summary.json"


def main() -> None:
  cfg = load_config()
  topic = cfg.get("ros2", {}).get("cmd_topic", "/care/robot_cmd")
  adapter = RecordingROS2Adapter(cfg.get("ros2", {}), OUT_JSONL)
  orch = CareOrchestrator(cfg, adapter)

  print("=" * 60)
  print("CareCompanion 情景剧 — ROS2 指令录制")
  print(f"话题: {topic}")
  print(f"输出: {OUT_JSONL}")
  print("=" * 60)

  timeline: list[dict] = []
  for step in demo_scenarios():
    print(f"\n▶ 场景: {step.name} ({step.duration_s}s)")
    t_scene = time.time()
    ticks = 0
    while time.time() - t_scene < step.duration_s:
      s = orch.tick(step.frame)
      ticks += 1
      timeline.append({
        "scene": step.name,
        "state": s["state"],
        "risk": round(s["risk"].score, 3),
        "risk_level": s["risk"].level,
        "fall": s["fall"].detected,
        "n_actions": len(s["actions"]),
      })
      time.sleep(0.35)

  adapter.shutdown()

  emergency = [r for r in adapter.records if r["data"].get("command") == "call_emergency"]
  summary = {
    "topic": topic,
    "total_commands": len(adapter.records),
    "scenes": [st.name for st in demo_scenarios()],
    "emergency_commands": len(emergency),
    "commands": [r["data"]["command"] for r in adapter.records],
    "rclpy_published": adapter._pub is not None,  # noqa: SLF001
  }
  OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

  print(f"\n共记录 {len(adapter.records)} 条 robot_cmd")
  print(f"其中 call_emergency: {len(emergency)} 条")
  print(f"ROS2 实发: {'是' if summary['rclpy_published'] else '否（已写 JSONL，与话题载荷一致）'}")
  print(f"摘要: {OUT_SUMMARY}")

  if not emergency:
    raise SystemExit("❌ 未触发 call_emergency，请检查跌倒场景")
  print("✅ 情景剧 ROS2 录制完成")


if __name__ == "__main__":
  main()
