#!/usr/bin/env python3
"""ROS2 桥接演示：将演示剧本动作发布到 /care/robot_cmd。"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.action.robot_adapter import ROS2Adapter
from care_companion.core.config import load_config
from care_companion.core.orchestrator import CareOrchestrator
from simulation.scenarios import demo_scenarios


def main():
  cfg = load_config()
  robot = ROS2Adapter(cfg.get("ros2", {}))
  orch = CareOrchestrator(cfg, robot)
  print("ROS2 bridge demo — 订阅方请监听", cfg["ros2"]["cmd_topic"])
  for step in demo_scenarios():
    print("场景:", step.name)
    t0 = time.time()
    while time.time() - t0 < step.duration_s:
      orch.tick(step.frame)
      time.sleep(0.5)
  robot.shutdown()
  print("完成")


if __name__ == "__main__":
  main()
