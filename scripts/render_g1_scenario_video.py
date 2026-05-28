#!/usr/bin/env python3
"""将 Isaac G1 原始录屏场景化为「养老紧急响应 · 执行层」演示片。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "docs" / "assets" / "demo_isaac_g1_locomotion_raw.mp4"
SRC = ROOT / "docs" / "assets" / "demo_isaac_g1_locomotion.mp4"
OUT = ROOT / "docs" / "assets" / "demo_isaac_g1_locomotion.mp4"
FONT = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
W, H = 1280, 720
DUR = 10.0


def _font_esc(p: Path) -> str:
  return str(p).replace("\\", "\\\\").replace(":", "\\:")


def main() -> int:
  import shutil

  if RAW.is_file():
    src = RAW
  elif SRC.is_file():
    shutil.copy2(SRC, RAW)
    print(f"▶ 已备份原始片 → {RAW}")
    src = RAW
  else:
    print(f"❌ 缺少 {SRC}", file=sys.stderr)
    return 1
  tmp = OUT.with_suffix(".tmp.mp4")

  if not FONT.is_file():
    print(f"❌ 缺少中文字体 {FONT}", file=sys.stderr)
    return 1

  ff = _font_esc(FONT)
  # 右侧机器人画面：放慢、裁切居中、调色、轻微暗角
  robot = (
    f"[0:v]trim=duration={DUR},setpts=PTS-STARTPTS,"
    "setpts=1.35*PTS,"
    "fps=24,"
    "scale=980:720:force_original_aspect_ratio=increase,"
    "crop=980:720,"
    "eq=contrast=1.06:brightness=0.03:saturation=1.12,"
    "vignette=angle=PI/5:mode=forward,"
    "unsharp=5:5:0.4:5:5:0.0"
    "[rv];"
  )
  # 左侧任务面板 + 文案
  panel = (
    f"color=c=0x0b1220:s={W}x{H}:d={DUR}[bg];"
    f"[bg]drawbox=x=0:y=0:w=300:h={H}:color=0x111827:t=fill,"
    f"drawbox=x=0:y=0:w=4:h={H}:color=0x0ea5e9:t=fill[bar];"
    f"[bar]drawtext=fontfile={ff}:text='CareCompanion':fontsize=22:fontcolor=0x7dd3fc:x=28:y=36,"
    f"drawtext=fontfile={ff}:text='执行层 · 人形机器人':fontsize=18:fontcolor=0xe2e8f0:x=28:y=72,"
    f"drawtext=fontfile={ff}:text='紧急任务':fontsize=16:fontcolor=0xfbbf24:x=28:y=118,"
    f"drawtext=fontfile={ff}:text='收到跌倒预警指令':fontsize=15:fontcolor=0xfde68a:x=28:y=148,"
    f"drawtext=fontfile={ff}:text='目标：老人起居区':fontsize=15:fontcolor=0xcbd5e1:x=28:y=178,"
    f"drawtext=fontfile={ff}:text='状态：赶赴现场中':fontsize=15:fontcolor=0x6ee7b7:x=28:y=218,"
    f"drawtext=fontfile={ff}:text='策略：平地稳定行走':fontsize=14:fontcolor=0x94a3b8:x=28:y=248,"
    f"drawtext=fontfile={ff}:text='Isaac Lab · Unitree G1':fontsize=13:fontcolor=0x64748b:x=28:y=580,"
    f"drawtext=fontfile={ff}:text='仿真验证执行链路':fontsize=13:fontcolor=0x64748b:x=28:y=602"
    f"[ui];"
  )
  comp = (
    "[ui][rv]overlay=x=300:y=0:format=auto[base];"
    f"[base]drawtext=fontfile={ff}:text='④ 执行层响应':fontsize=24:fontcolor=white:"
    "x=320:y=24:box=1:boxcolor=0x00000066:boxborderw=8,"
    f"drawtext=fontfile={ff}:text='决策已下发 → 人形本体出动':fontsize=16:fontcolor=0xe2e8f0:"
    "x=320:y=58:box=1:boxcolor=0x00000044:boxborderw=6"
    "[vout]"
  )
  vf = robot + panel + comp

  cmd = [
    "ffmpeg", "-y", "-nostdin",
    "-i", str(src.resolve()),
    "-filter_complex", vf,
    "-map", "[vout]",
    "-t", str(DUR),
    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
    str(tmp),
  ]
  print("▶ 场景化渲染 G1 执行层视频…")
  r = subprocess.run(cmd, capture_output=True, text=True)
  if r.returncode != 0:
    print(r.stderr[-2000:] if r.stderr else r.stdout, file=sys.stderr)
    return 1
  tmp.replace(OUT)
  mb = OUT.stat().st_size / 1024 / 1024
  print(f"✅ {OUT} ({mb:.1f} MB, {DUR}s)")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
