#!/usr/bin/env python3
"""离线渲染「心情·数字人剧场」：双全身数字人 + 中文对白气泡。"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import cv2
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.perception.video_analyzer import VideoAnalyzer
from care_companion.visual.character_renderer import render_dual_character_frame
from web.session import CareSession

OUT = ROOT / "docs" / "assets" / "demo_mood_digital_human.mp4"
SAMPLE = ROOT / "docs" / "assets" / "samples" / "elder_fall_wechat.mp4"
FPS = 12
TITLE = "CareCompanion · 心情 · 双数字人互动剧场"


def _infer_elder_mood(text: str, default: str = "neutral") -> str:
  if not text:
    return default
  if any(w in text for w in ("哎哟", "跌", "慌", "怕")):
    return "anxious"
  if any(w in text for w in ("孤单", "闷", "睡不", "空落")):
    return "sad"
  if any(w in text for w in ("暖和", "挺好", "踏实")):
    return "happy"
  return default


async def _collect_events(session: CareSession) -> list[dict]:
  events: list[dict] = []
  async for item in session.stream_mood_acting():
    events.append(item)
  return events


def main() -> int:
  if not SAMPLE.is_file():
    print(f"❌ 缺少 {SAMPLE}", file=sys.stderr)
    return 1

  cfg = yaml.safe_load((ROOT / "config" / "default.yaml").read_text(encoding="utf-8"))
  print("▶ 分析视频…")
  analysis = VideoAnalyzer(cfg).analyze_file(SAMPLE, max_frames=900, frame_stride=1)
  if not analysis.get("ok"):
    print("❌ 分析失败", analysis.get("error"), file=sys.stderr)
    return 1

  session = CareSession()
  session.last_video = analysis

  print("▶ 生成双数字人对话…")
  events = asyncio.run(_collect_events(session))

  frames_dir = ROOT / "docs" / "assets" / "_mood_render_frames"
  frames_dir.mkdir(parents=True, exist_ok=True)
  for f in frames_dir.glob("*.jpg"):
    f.unlink()

  dialogue: list[tuple[str, str, str]] = []
  elder_mood = "neutral"
  companion_mood = "neutral"
  active: str | None = None
  idx = 0
  hold = int(FPS * 1.6)

  def emit(extra: int = 0) -> None:
    nonlocal idx
    frame = render_dual_character_frame(
      TITLE,
      dialogue,
      elder_mood=elder_mood,
      companion_mood=companion_mood,
      active_speaker=active,
    )
    for _ in range(hold + extra):
      cv2.imwrite(str(frames_dir / f"f_{idx:06d}.jpg"), frame)
      idx += 1

  emit(2)

  for ev in events:
    t = ev.get("type")
    if t == "stage":
      active = None
      dialogue.append(("stage", "", ev.get("text", "")))
      emit(1)
    elif t == "elder":
      active = "elder"
      txt = ev.get("text", "") or ""
      elder_mood = _infer_elder_mood(txt, elder_mood)
      dialogue.append(("elder", "老人", txt))
      emit(2)
    elif t == "companion":
      active = "companion"
      companion_mood = ev.get("avatar") or companion_mood
      dialogue.append(("companion", "小护", ev.get("text", "")))
      emit(2)
    elif t == "done":
      active = None
      companion_mood = ev.get("avatar") or companion_mood
      dialogue.append(("stage", "", "情景剧结束 · 感谢观看"))
      emit(4)

  tmp = OUT.with_suffix(".raw.mp4")
  subprocess.run(
    [
      "ffmpeg", "-y", "-framerate", str(FPS),
      "-i", str(frames_dir / "f_%06d.jpg"),
      "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an",
      str(tmp),
    ],
    check=True,
    capture_output=True,
  )
  subprocess.run(
    ["ffmpeg", "-y", "-i", str(tmp), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
    check=True,
    capture_output=True,
  )
  tmp.unlink(missing_ok=True)
  for f in frames_dir.glob("*.jpg"):
    f.unlink()
  frames_dir.rmdir()

  print(f"✅ {OUT} ({OUT.stat().st_size / 1024 / 1024:.1f} MB, {idx / FPS:.0f}s)")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
