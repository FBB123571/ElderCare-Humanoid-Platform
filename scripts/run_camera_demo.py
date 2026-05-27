#!/usr/bin/env python3
"""本地摄像头 + MediaPipe 跌倒检测演示（需摄像头与显示器）。"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2

from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator
from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.perception.pose_pipeline import PosePipeline


def main():
  cfg = load_config()
  pose = PosePipeline(cfg.get("fall", {}))
  orch = CareOrchestrator(cfg, SimulationAdapter())
  cap = cv2.VideoCapture(0)
  if not cap.isOpened():
    print("❌ 无法打开摄像头")
    return 1
  print("按 q 退出。画面叠加姿态与风险状态。")
  t_prev = time.time()
  while True:
    ok, frame = cap.read()
    if not ok:
      break
    dt = max(time.time() - t_prev, 1e-3)
    t_prev = time.time()
    metrics, fall_r, annotated = pose.analyze_bgr(frame, dt)
    vis = annotated if annotated is not None else frame
    summary = orch.tick(
      PerceptionFrame(
        skeleton_aspect_ratio=metrics.aspect_ratio,
        skeleton_dy=metrics.dy,
        fall_detected=fall_r.detected,
        fall_score=fall_r.score,
      )
    )
    label = f"{summary['state'].upper()} risk={summary['risk'].score:.2f} fall={fall_r.detected}"
    cv2.putText(vis, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 180), 2)
    cv2.imshow("CareCompanion Camera Demo", vis)
    if cv2.waitKey(1) & 0xFF == ord("q"):
      break
  cap.release()
  cv2.destroyAllWindows()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
