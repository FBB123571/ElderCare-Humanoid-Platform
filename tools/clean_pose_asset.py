#!/usr/bin/env python3
"""去除骨架演示图背景水印，铺纯白底并居中裁剪。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "assets" / "ppt_mediapipe_pose.png"
OUT = SRC


def clean_pose_image(src: Path, out: Path) -> bool:
  if not src.exists():
    return False
  arr = np.array(Image.open(src).convert("RGB"), dtype=np.uint8)
  r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

  pure_white = (r > 248) & (g > 248) & (b > 248)
  light = (r > 190) & (g > 190) & (b > 190)
  neutral = (np.abs(r.astype(int) - g) + np.abs(g.astype(int) - b) + np.abs(r.astype(int) - b)) < 28
  watermark = light & neutral & ~pure_white
  arr[watermark] = 255

  fg = ~((arr[..., 0] > 252) & (arr[..., 1] > 252) & (arr[..., 2] > 252))
  if not fg.any():
    Image.fromarray(arr).save(out)
    return True

  ys, xs = np.where(fg)
  pad = 24
  y0, y1 = max(0, ys.min() - pad), min(arr.shape[0], ys.max() + pad)
  x0, x1 = max(0, xs.min() - pad), min(arr.shape[1], xs.max() + pad)
  crop = arr[y0:y1, x0:x1]
  ch, cw = crop.shape[:2]
  target_w, target_h = 720, 960
  scale = min(target_w / cw, target_h / ch, 1.0)
  if scale < 1.0:
    im = Image.fromarray(crop).resize((int(cw * scale), int(ch * scale)), Image.Resampling.LANCZOS)
    crop = np.array(im)
    ch, cw = crop.shape[:2]

  canvas = np.full((target_h, target_w, 3), 255, dtype=np.uint8)
  y_off = (target_h - ch) // 2
  x_off = (target_w - cw) // 2
  canvas[y_off : y_off + ch, x_off : x_off + cw] = crop
  Image.fromarray(canvas).save(out, quality=95)
  return True


if __name__ == "__main__":
  tmp = SRC.with_suffix(".tmp.png")
  if clean_pose_image(SRC, tmp):
    tmp.replace(OUT)
    print(f"✅ 已清理: {OUT}")
  else:
    print(f"⚠️ 未找到: {SRC}")
