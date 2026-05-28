#!/usr/bin/env python3
"""高清演示视频：逐帧截图 + ffmpeg，流程紧凑、时长约 2.5～3 分钟。"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "assets" / "demo_carecompanion.mp4"
FPS = 24
VIEW_W, VIEW_H = 1280, 720


def _ensure_web(port: int) -> None:
  import urllib.request

  url = f"http://127.0.0.1:{port}/api/health"
  try:
    with urllib.request.urlopen(url, timeout=2) as r:
      if r.status == 200:
        return
  except Exception:
    pass
  print("正在启动 Web 服务…")
  subprocess.Popen(
    [str(ROOT / "scripts" / "run_web.sh"), str(port)],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  for _ in range(40):
    try:
      with urllib.request.urlopen(url, timeout=2) as r:
        if r.status == 200:
          return
    except Exception:
      time.sleep(0.5)
  raise RuntimeError("Web 启动超时，请先 bash scripts/run_web.sh")


def _find_upload_image() -> Path:
  for p in (
    ROOT / "data" / "test_fullbody.png",
    ROOT / "web" / "static" / "samples" / "pose_demo.jpg",
  ):
    if p.is_file():
      return p
  raise FileNotFoundError("请提供样图：data/test_fullbody.png 或 web/static/samples/pose_demo.jpg")


class FrameCapture:
  def __init__(self, page, out_dir: Path, fps: int = FPS):
    self.page = page
    self.out_dir = out_dir
    self.fps = fps
    self.idx = 0
    out_dir.mkdir(parents=True, exist_ok=True)

  def shot(self) -> None:
    path = self.out_dir / f"f_{self.idx:06d}.jpg"
    self.page.screenshot(path=str(path), type="jpeg", quality=88, animations="disabled")
    self.idx += 1

  def hold(self, seconds: float) -> None:
    n = max(1, int(seconds * self.fps))
    dt = seconds / n
    for _ in range(n):
      self.shot()
      time.sleep(dt)

  def until(
    self,
    js_ok: str,
    timeout_s: float = 30.0,
    poll_s: float = 0.18,
    min_hold_s: float = 1.0,
  ) -> None:
    """轮询截帧直到条件成立，避免干等画面卡住。"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
      self.shot()
      if self.page.evaluate(js_ok):
        break
      time.sleep(poll_s)
    self.hold(min_hold_s)


def _encode(frames_dir: Path, mp4: Path, fps: int) -> None:
  if shutil.which("ffmpeg") is None:
    raise RuntimeError("需要 ffmpeg")
  subprocess.run(
    [
      "ffmpeg",
      "-y",
      "-framerate",
      str(fps),
      "-i",
      str(frames_dir / "f_%06d.jpg"),
      "-c:v",
      "libx264",
      "-crf",
      "16",
      "-preset",
      "slow",
      "-pix_fmt",
      "yuv420p",
      "-movflags",
      "+faststart",
      "-r",
      str(fps),
      str(mp4),
    ],
    check=True,
    capture_output=True,
  )


def record(port: int, out: Path, upload_image: Path | None) -> Path:
  from playwright.sync_api import sync_playwright

  upload_image = upload_image or _find_upload_image()
  frames_dir = out.parent / "_demo_frames"
  if frames_dir.exists():
    shutil.rmtree(frames_dir)

  print(f"录制 {VIEW_W}×{VIEW_H} @ {FPS}fps → {out}")

  with sync_playwright() as p:
    browser = p.chromium.launch(
      headless=True,
      args=["--disable-dev-shm-usage", "--no-sandbox"],
    )
    page = browser.new_page(viewport={"width": VIEW_W, "height": VIEW_H})
    cap = FrameCapture(page, frames_dir, FPS)

    page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
    cap.until(
      "() => (document.getElementById('connBadge')?.textContent || '').includes('在线')",
      timeout_s=20,
      min_hold_s=2.5,
    )

    # ① 上传照片 → 骨架
    page.locator("#visionFile").set_input_files(str(upload_image.resolve()))
    cap.until(
      """() => {
        const v = document.getElementById('visionPreview');
        return v && !v.classList.contains('hidden');
      }""",
      timeout_s=60,
      poll_s=0.15,
      min_hold_s=5.0,
    )

    # ② 老人倾诉
    page.locator('[data-preset="chat"]').click()
    cap.hold(1.0)
    page.locator("#btnTick").click()
    cap.until(
      "() => (document.getElementById('replyText')?.textContent || '').length > 4",
      timeout_s=15,
      min_hold_s=6.0,
    )

    # ③ 模拟跌倒（单步，立刻看到紧急状态）
    page.locator('[data-preset="fall"]').click()
    cap.hold(1.0)
    page.locator("#btnTick").click()
    cap.until(
      """() => {
        const t = document.getElementById('stateText')?.textContent || '';
        return t.includes('紧急');
      }""",
      timeout_s=12,
      min_hold_s=5.0,
    )

    page.locator("#robotLog").scroll_into_view_if_needed()
    cap.until(
      "() => document.querySelectorAll('#robotLog .cmd-item').length >= 3",
      timeout_s=10,
      min_hold_s=8.0,
    )

    # ④ 完整演示剧本（重置后跑全流程，录制中持续截帧）
    page.locator("#btnReset").click()
    cap.hold(2.0)
    page.locator("#btnDemo").click()
    cap.until(
      "() => (document.getElementById('scenarioName')?.textContent || '').includes('日常')",
      timeout_s=8,
      min_hold_s=1.0,
    )
    cap.until(
      "() => (document.getElementById('scenarioName')?.textContent || '').includes('倾诉')",
      timeout_s=15,
      poll_s=0.15,
      min_hold_s=1.0,
    )
    cap.until(
      "() => (document.getElementById('scenarioName')?.textContent || '').includes('跌倒')",
      timeout_s=20,
      poll_s=0.15,
      min_hold_s=1.0,
    )
    cap.until(
      "() => (document.getElementById('chatLog')?.textContent || '').includes('演示完成')",
      timeout_s=25,
      poll_s=0.15,
      min_hold_s=10.0,
    )

    page.locator("#chatLog").scroll_into_view_if_needed()
    cap.hold(4.0)
    page.locator(".risk-hero").scroll_into_view_if_needed()
    cap.hold(3.0)

    # ⑤ 网络视频 · 跌倒分析（自采样片）
    elder = ROOT / "docs" / "assets" / "samples" / "elder_fall_wechat.mp4"
    if elder.is_file():
      page.locator(".feature-row").scroll_into_view_if_needed()
      cap.hold(1.0)
      page.locator('.video-tab[data-vtab="fall"]').click()
      cap.hold(0.8)
      page.locator("#videoFile").set_input_files(str(elder.resolve()))
      cap.hold(0.6)
      page.locator("#btnVideoFall").click()
      cap.until(
        """() => {
          const a = document.getElementById('videoAlert');
          return a && !a.classList.contains('hidden');
        }""",
        timeout_s=120,
        poll_s=0.35,
        min_hold_s=5.0,
      )

    # ⑥ 心情 · 数字人剧场（缩略展示）
    if elder.is_file():
      page.locator('.video-tab[data-vtab="mood"]').click()
      cap.hold(1.0)
      page.locator("#videoFile").set_input_files(str(elder.resolve()))
      page.locator("#btnVideoMood").click()
      cap.until(
        """() => (document.querySelectorAll('#moodDhScript .dh-line').length >= 4)""",
        timeout_s=150,
        poll_s=0.35,
        min_hold_s=8.0,
      )
      page.locator("#videoMoodTheater").scroll_into_view_if_needed()
      cap.hold(4.0)

    browser.close()

  n = len(list(frames_dir.glob("f_*.jpg")))
  print(f"共 {n} 帧，成片约 {n / FPS:.0f} 秒")
  _encode(frames_dir, out, FPS)
  shutil.rmtree(frames_dir, ignore_errors=True)
  return out


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", type=int, default=8765)
  parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
  parser.add_argument("--image", type=Path)
  args = parser.parse_args()

  _ensure_web(args.port)
  path = record(args.port, args.output, args.image)
  mb = path.stat().st_size / 1024 / 1024
  print(f"✅ 已生成: {path} ({mb:.1f} MB)")


if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    print(f"❌ {exc}", file=sys.stderr)
    sys.exit(1)
