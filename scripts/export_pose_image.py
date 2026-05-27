#!/usr/bin/env python3
"""将照片分析为带 MediaPipe 骨架叠加的 JPG（答辩/PPT 用）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2

from care_companion.core.config import load_config
from care_companion.perception.pose_pipeline import PosePipeline


def main():
  parser = argparse.ArgumentParser(description="导出 MediaPipe 骨架叠加图")
  parser.add_argument("image", type=Path, help="输入照片路径")
  parser.add_argument(
    "-o",
    "--output",
    type=Path,
    default=ROOT / "docs" / "assets" / "pose_export.jpg",
    help="输出 JPG 路径",
  )
  args = parser.parse_args()
  if not args.image.is_file():
    print(f"❌ 找不到图片: {args.image}")
    sys.exit(1)

  img = cv2.imread(str(args.image))
  if img is None:
    print(f"❌ 无法读取: {args.image}")
    sys.exit(1)

  pipe = PosePipeline(load_config().get("fall", {}))
  metrics, fall_r, annotated = pipe.analyze_bgr(img)
  if annotated is None:
    print("❌ 分析失败")
    sys.exit(1)

  args.output.parent.mkdir(parents=True, exist_ok=True)
  cv2.imwrite(str(args.output), annotated)
  print(f"✅ 已保存: {args.output}")
  print(f"   检测到人体: {metrics.visible} · 原因: {fall_r.reason} · 宽高比: {metrics.aspect_ratio:.2f}")


if __name__ == "__main__":
  main()
