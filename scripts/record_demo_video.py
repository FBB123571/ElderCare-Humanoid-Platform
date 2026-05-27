#!/usr/bin/env python3
"""无头浏览器自动录制的答辩演示视频（约 3～4 分钟）。"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "assets" / "demo_carecompanion.mp4"
WEB_URL = "http://127.0.0.1:8765"


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
          print("Web 已就绪")
          return
    except Exception:
      time.sleep(0.5)
  raise RuntimeError("Web 启动超时，请先手动 bash scripts/run_web.sh")


def _find_upload_image() -> Path:
  candidates = [
    ROOT / "web" / "static" / "samples" / "pose_demo.jpg",
    ROOT / "data" / "test_fullbody.png",
    ROOT / "docs" / "assets" / "ppt_mediapipe_pose.png",
  ]
  for p in candidates:
    if p.is_file():
      return p
  raise FileNotFoundError("找不到用于上传的样图，请放一张到 web/static/samples/pose_demo.jpg")


def _to_mp4(webm: Path, mp4: Path) -> None:
  if shutil.which("ffmpeg") is None:
    shutil.copy2(webm, mp4.with_suffix(".webm"))
    print(f"未安装 ffmpeg，保留 WebM: {webm}")
    return
  subprocess.run(
    [
      "ffmpeg",
      "-y",
      "-i",
      str(webm),
      "-c:v",
      "libx264",
      "-pix_fmt",
      "yuv420p",
      "-movflags",
      "+faststart",
      str(mp4),
    ],
    check=True,
    capture_output=True,
  )


def record(port: int, out: Path, upload_image: Path | None) -> Path:
  from playwright.sync_api import sync_playwright

  upload_image = upload_image or _find_upload_image()
  out.parent.mkdir(parents=True, exist_ok=True)
  tmp_dir = out.parent / "_record_tmp"
  tmp_dir.mkdir(exist_ok=True)

  base = f"http://127.0.0.1:{port}"
  print(f"录制中 → {out}")
  print(f"上传样图: {upload_image}")

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
      viewport={"width": 1280, "height": 720},
      record_video_dir=str(tmp_dir),
      record_video_size={"width": 1280, "height": 720},
    )
    page = context.new_page()
    page.goto(base, wait_until="networkidle")
    page.wait_for_selector("#connBadge", timeout=15000)
    time.sleep(1.2)

    # 1. 上传照片分析
    page.locator("#visionFile").set_input_files(str(upload_image.resolve()))
    page.wait_for_function(
      """() => {
        const st = document.getElementById('visionStatus')?.textContent || '';
        return st.includes('骨架') || st.includes('宽高比');
      }""",
      timeout=60000,
    )
    time.sleep(2.5)

    # 2. 老人倾诉
    page.locator('[data-preset="chat"]').click()
    time.sleep(0.8)
    page.locator("#btnTick").click()
    page.wait_for_function(
      """() => (document.getElementById('replyText')?.textContent || '').length > 2""",
      timeout=15000,
    )
    time.sleep(2.5)

    # 3. 运行完整演示剧本（含跌倒紧急）
    page.locator("#btnDemo").click()
    page.wait_for_selector("#scenarioBar:not(.hidden)", timeout=10000)
    time.sleep(18)

    # 4. 滚到指令流
    page.locator("#robotLog").scroll_into_view_if_needed()
    time.sleep(3)
    page.locator("#chatLog").scroll_into_view_if_needed()
    time.sleep(2)

    context.close()
    browser.close()

  videos = sorted(tmp_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime)
  if not videos:
    raise RuntimeError("未生成录屏文件")
  webm = videos[-1]
  _to_mp4(webm, out)
  shutil.rmtree(tmp_dir, ignore_errors=True)
  return out


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", type=int, default=8765)
  parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
  parser.add_argument("--image", type=Path, help="上传分析用的照片")
  args = parser.parse_args()

  _ensure_web(args.port)
  path = record(args.port, args.output, args.image)
  print(f"✅ 演示视频已生成: {path}")
  print(f"   大小: {path.stat().st_size / 1024 / 1024:.1f} MB")
  print("   下一步: 上传 B 站/网盘 → 做二维码 → 放入 docs/assets/ppt_demo_qr.png")


if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    print(f"❌ {exc}", file=sys.stderr)
    sys.exit(1)
