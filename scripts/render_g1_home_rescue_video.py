#!/usr/bin/env python3
"""同一客厅机位：老人跌倒→机器人赶赴→扶起（轻量抠图，约 2 分钟出片）。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FALL_VID = ROOT / "docs" / "assets" / "samples" / "elder_fall_wechat.mp4"
ROBOT_RAW = ROOT / "docs" / "assets" / "demo_isaac_g1_locomotion_raw.mp4"
ROOM_IMG = ROOT / "docs" / "assets" / "scene_living_room.jpg"
OUT = ROOT / "docs" / "assets" / "demo_isaac_g1_locomotion.mp4"
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
W, H = 1280, 720
FPS = 24
DUR = 14.0
FLOOR_Y = int(H * 0.88)


def _font(size: int) -> ImageFont.FreeTypeFont:
  return ImageFont.truetype(str(FONT_PATH), size)


def _load_bg() -> np.ndarray:
  bg = cv2.imread(str(ROOM_IMG))
  if bg is None:
    raise FileNotFoundError(ROOM_IMG)
  return cv2.resize(bg, (W, H), interpolation=cv2.INTER_AREA)


def _load_frames(path: Path, limit: int | None = None) -> list[np.ndarray]:
  cap = cv2.VideoCapture(str(path))
  out: list[np.ndarray] = []
  while cap.isOpened():
    ok, f = cap.read()
    if not ok:
      break
    out.append(f)
    if limit and len(out) >= limit:
      break
  cap.release()
  return out


def _mask_from_gray_bg(bgr: np.ndarray) -> np.ndarray:
  """Isaac 灰背景：色差抠图。"""
  bg = np.median(np.vstack([bgr[5:45, 5:45].reshape(-1, 3), bgr[5:45, -45:].reshape(-1, 3)]), axis=0)
  diff = np.linalg.norm(bgr.astype(np.float32) - bg.astype(np.float32), axis=2)
  m = (diff > 22).astype(np.uint8) * 255
  m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
  return cv2.GaussianBlur(m, (5, 5), 0)


def _mask_elder_fast(bgr: np.ndarray) -> np.ndarray:
  """跌倒视频：中心人物矩形 GrabCut（单次）。"""
  h, w = bgr.shape[:2]
  mask = np.zeros((h, w), np.uint8)
  rect = (int(w * 0.2), int(h * 0.08), int(w * 0.6), int(h * 0.88))
  bgd = np.zeros((1, 65), np.float64)
  fgd = np.zeros((1, 65), np.float64)
  cv2.grabCut(bgr, mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
  m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
  return cv2.GaussianBlur(m, (9, 9), 0)


def _paste(canvas: np.ndarray, bgr: np.ndarray, alpha: np.ndarray, x: int, y: int) -> None:
  h, w = bgr.shape[:2]
  x1, y1 = max(0, x), max(0, y)
  x2, y2 = min(W, x + w), min(H, y + h)
  if x2 <= x1 or y2 <= y1:
    return
  sx1, sy1 = x1 - x, y1 - y
  sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
  a = alpha[sy1:sy2, sx1:sx2].astype(np.float32) / 255.0
  a3 = np.stack([a, a, a], axis=2)
  roi = canvas[y1:y2, x1:x2].astype(np.float32)
  fg = bgr[sy1:sy2, sx1:sx2].astype(np.float32)
  canvas[y1:y2, x1:x2] = (fg * a3 + roi * (1 - a3)).astype(np.uint8)


def _subtitle(canvas: np.ndarray, text: str) -> None:
  pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
  d = ImageDraw.Draw(pil, "RGBA")
  f = _font(20)
  bbox = d.textbbox((0, 0), text, font=f)
  tw = bbox[2] - bbox[0]
  x, y = (W - tw) // 2, H - 52
  d.rounded_rectangle([x - 12, y - 4, x + tw + 12, y + 28], radius=8, fill=(0, 0, 0, 150))
  d.text((x, y), text, font=f, fill=(255, 248, 240, 255))
  canvas[:] = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


def _ease(t: float) -> float:
  t = max(0.0, min(1.0, t))
  return t * t * (3 - 2 * t)


def render() -> list[np.ndarray]:
  bg = _load_bg()
  fall = _load_frames(FALL_VID)
  robot = _load_frames(ROBOT_RAW, limit=80)
  if not fall or not robot:
    raise RuntimeError("缺少素材")

  print("  · 抠图（3 次）…", flush=True)
  i_down = min(len(fall) - 1, int(len(fall) * 0.52))
  i_up = max(5, int(len(fall) * 0.12))
  mask_fall = _mask_elder_fast(fall[i_down // 2])
  mask_down = _mask_elder_fast(fall[i_down])
  mask_up = _mask_elder_fast(fall[i_up])
  mask_robot = _mask_from_gray_bg(robot[len(robot) // 2])

  elder_w = int(W * 0.36)
  n = int(DUR * FPS)
  out_frames: list[np.ndarray] = []

  for i in range(n):
    t = i / FPS
    canvas = bg.copy()

    if t < 4.0:
      fi = min(i_down, int((t / 4.0) * i_down))
      f, m = fall[fi], mask_fall
      sc = elder_w / f.shape[1]
      nw, nh = int(f.shape[1] * sc), int(f.shape[0] * sc)
      _paste(canvas, cv2.resize(f, (nw, nh)), cv2.resize(m, (nw, nh)), int(W * 0.40) - nw // 2, FLOOR_Y - nh + 15)
      _subtitle(canvas, "同一客厅视角 · 老人跌倒")

    elif t < 5.0:
      f, m = fall[i_down], mask_down
      sc = elder_w / f.shape[1]
      nw, nh = int(f.shape[1] * sc), int(f.shape[0] * sc)
      _paste(canvas, cv2.resize(f, (nw, nh)), cv2.resize(m, (nw, nh)), int(W * 0.40) - nw // 2, FLOOR_Y - nh + 25)
      _subtitle(canvas, "跌倒预警 · 调度人形机器人")

    elif t < 9.5:
      f, m = fall[i_down], mask_down
      sc = elder_w / f.shape[1]
      nw, nh = int(f.shape[1] * sc), int(f.shape[0] * sc)
      _paste(canvas, cv2.resize(f, (nw, nh)), cv2.resize(m, (nw, nh)), int(W * 0.40) - nw // 2, FLOOR_Y - nh + 25)
      prog = _ease((t - 5.0) / 4.5)
      ri = min(len(robot) - 1, int(prog * (len(robot) - 1)))
      rb = cv2.resize(robot[ri], (int(320 + 120 * prog), int(420 + 160 * prog)))
      ra = cv2.resize(mask_robot, (rb.shape[1], rb.shape[0]))
      _paste(canvas, rb, ra, int(W * (0.88 - prog * 0.32)) - rb.shape[1] // 2, FLOOR_Y - rb.shape[0])
      _subtitle(canvas, "机器人入画赶赴")

    else:
      prog = _ease((t - 9.5) / 4.5)
      fi, m = (i_down, mask_down) if prog < 0.5 else (i_up, mask_up)
      lift = int(18 * (1 - prog))
      f = fall[fi]
      sc = elder_w / f.shape[1]
      nw, nh = int(f.shape[1] * sc), int(f.shape[0] * sc)
      _paste(canvas, cv2.resize(f, (nw, nh)), cv2.resize(m, (nw, nh)), int(W * 0.40) - nw // 2, FLOOR_Y - nh + 25 - lift)
      rb = cv2.resize(robot[len(robot) // 3], (380, 500))
      ra = cv2.resize(mask_robot, (rb.shape[1], rb.shape[0]))
      _paste(canvas, rb, ra, int(W * 0.50) - rb.shape[1] // 2, FLOOR_Y - rb.shape[0])
      _subtitle(canvas, "协助老人起身（示意）")

    out_frames.append(canvas)
  return out_frames


def main() -> int:
  for p in (FALL_VID, ROBOT_RAW, ROOM_IMG, FONT_PATH):
    if not Path(p).is_file():
      print(f"❌ 缺少 {p}", file=sys.stderr)
      return 1
  print("▶ 合成自然同机位短片…", flush=True)
  frames = render()
  tmp = OUT.with_suffix(".tmp.mp4")
  wr = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
  for f in frames:
    wr.write(f)
  wr.release()
  subprocess.run(
    ["ffmpeg", "-y", "-nostdin", "-i", str(tmp), "-c:v", "libx264", "-crf", "17",
     "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(OUT)],
    check=True, capture_output=True,
  )
  tmp.unlink(missing_ok=True)
  print(f"✅ {OUT} ({OUT.stat().st_size/1024/1024:.1f} MB, {DUR}s)")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
