#!/usr/bin/env python3
"""把 ros2_cmd_timeline.jsonl 渲染成「ros2 topic echo」风格短视频（仅需 ffmpeg）。"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "docs" / "assets" / "ros2_cmd_timeline.jsonl"
OUT_MP4 = ROOT / "docs" / "assets" / "demo_ros2_cmd_echo.mp4"
TOPIC = "/care/robot_cmd"
FPS = 10
W, H = 1280, 720


def _load_records(path: Path) -> list[dict]:
  rows = []
  for line in path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
      rows.append(json.loads(line))
  return rows


def _escape_drawtext(s: str) -> str:
  return (
    s.replace("\\", "\\\\")
    .replace(":", "\\:")
    .replace("'", "\\'")
    .replace("%", "\\%")
    .replace("\n", " ")
  )


def _build_vf(records: list[dict], topic: str) -> tuple[str, float]:
  parts: list[str] = []
  header = _escape_drawtext(f"$ ros2 topic echo {topic}")
  parts.append(f"drawtext=text='{header}':fontsize=22:fontcolor=0x78B4FF:x=40:y=40")
  t_end = 0.0
  line_idx = 0
  for r in records:
    t0 = float(r.get("t_rel_s", 0))
    t_end = max(t_end, t0 + 1.2)
    cmd = r["data"].get("command", "?")
    color = "0xFFC850" if cmd == "call_emergency" else "0x64DC8C" if cmd in ("speak", "gesture") else "0xDCE6F0"
    chunks = textwrap.wrap(r["json"], width=95) or [r["json"]]
    for ci, chunk in enumerate(chunks[:2]):
      raw = _escape_drawtext(f"[{t0:.2f}s] {chunk}")
      y = 88 + line_idx * 26
      line_idx += 1
      if y > H - 48:
        break
      parts.append(
        f"drawtext=text='{raw}':fontsize=16:fontcolor={color}:x=40:y={y}:"
        f"enable='gte(t\\,{t0:.2f})'"
      )
  dur = max(7.0, min(11.0, t_end + 1.8))
  return ",".join(parts), dur


def render() -> None:
  if not JSONL.exists():
    raise SystemExit(f"缺少 {JSONL}，请先运行 scripts/run_scenario_drama.py")
  records = _load_records(JSONL)
  if not records:
    raise SystemExit("JSONL 为空")

  vf, dur = _build_vf(records, TOPIC)
  OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
  cmd = [
    "ffmpeg", "-y", "-nostdin",
    "-f", "lavfi", "-i", f"color=c=0x0C1018:s={W}x{H}:d={dur:.3f}:r={FPS}",
    "-vf", vf,
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-an", str(OUT_MP4),
  ]
  r = subprocess.run(cmd, capture_output=True, text=True)
  if r.returncode != 0:
    print(r.stderr[-2500:], file=sys.stderr)
    raise SystemExit(f"ffmpeg 失败 ({r.returncode})")
  print(f"✅ {OUT_MP4}  ({dur:.1f}s, {len(records)} msgs)")


if __name__ == "__main__":
  render()
