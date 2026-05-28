#!/usr/bin/env python3
"""录制「心情 · 数字人剧场」演示片（上传样片 → 分析 → 老人↔小护演戏）。"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "assets" / "demo_mood_digital_human.mp4"
SAMPLE = ROOT / "docs" / "assets" / "samples" / "elder_fall_wechat.mp4"
FPS = 20
VIEW_W, VIEW_H = 1920, 1080


def _ensure_web(port: int) -> None:
  import urllib.request

  url = f"http://127.0.0.1:{port}/api/health"
  for _ in range(50):
    try:
      with urllib.request.urlopen(url, timeout=2) as r:
        if r.status == 200 and b"digital_human" in r.read():
          return
    except Exception:
      time.sleep(0.5)
  subprocess.Popen(
    [str(ROOT / "scripts" / "run_web.sh"), str(port)],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  for _ in range(50):
    try:
      with urllib.request.urlopen(url, timeout=2) as r:
        if r.status == 200:
          return
    except Exception:
      time.sleep(0.5)
  raise RuntimeError("Web 未就绪: bash scripts/run_web.sh")


def _encode(frames_dir: Path, mp4: Path, fps: int) -> None:
  subprocess.run(
    [
      "ffmpeg", "-y", "-framerate", str(fps),
      "-i", str(frames_dir / "f_%06d.jpg"),
      "-c:v", "libx264", "-crf", "18", "-preset", "medium",
      "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", str(fps),
      str(mp4),
    ],
    check=True,
    capture_output=True,
  )


def record(port: int, out: Path, sample: Path) -> Path:
  from playwright.sync_api import sync_playwright

  if not sample.is_file():
    raise FileNotFoundError(f"缺少样片: {sample}")

  frames_dir = out.parent / "_mood_frames"
  shutil.rmtree(frames_dir, ignore_errors=True)
  frames_dir.mkdir(parents=True)

  class Cap:
    def __init__(self, page):
      self.page = page
      self.idx = 0

    def shot(self) -> None:
      self.page.screenshot(
        path=str(frames_dir / f"f_{self.idx:06d}.jpg"),
        type="jpeg",
        quality=86,
        animations="disabled",
      )
      self.idx += 1

    def hold(self, seconds: float) -> None:
      n = max(1, int(seconds * FPS))
      for _ in range(n):
        self.shot()
        time.sleep(seconds / n)

  print(f"录制心情数字人剧场 → {out}")

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": VIEW_W, "height": VIEW_H})
    cap = Cap(page)

    page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded", timeout=60000)
    cap.hold(2.0)

    page.locator('.video-tab[data-vtab="mood"]').click()
    cap.hold(1.2)

    page.locator("#videoMoodBlock").scroll_into_view_if_needed()
    cap.hold(0.8)

    page.locator("#videoFile").set_input_files(str(sample.resolve()))
    cap.hold(1.0)

    page.locator("#btnVideoMood").click()
    print("分析视频中，同步截帧…")

    t0 = time.time()
    last_n = 0
    stable = 0
    while time.time() - t0 < 200:
      cap.shot()
      time.sleep(0.4)
      try:
        txt = page.locator("#moodDhScript").inner_text(timeout=2000)
        n = page.locator("#moodDhScript .dh-line").count()
        if "情景剧结束" in txt:
          break
        if n == last_n:
          stable += 1
        else:
          stable = 0
          last_n = n
        if n >= 8 and stable > 15:
          break
      except Exception:
        pass

    cap.hold(6.0)
    browser.close()

  _encode(frames_dir, out, FPS)
  shutil.rmtree(frames_dir, ignore_errors=True)
  print(f"共 {cap.idx} 帧，约 {cap.idx / FPS:.0f}s")
  return out


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", type=int, default=8765)
  parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
  parser.add_argument("--sample", type=Path, default=SAMPLE)
  args = parser.parse_args()
  _ensure_web(args.port)
  path = record(args.port, args.output, args.sample)
  mb = path.stat().st_size / 1024 / 1024
  print(f"✅ {path} ({mb:.1f} MB)")


if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    print(f"❌ {exc}", file=sys.stderr)
    sys.exit(1)
