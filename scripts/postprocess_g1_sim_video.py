#!/usr/bin/env python3
"""将 Isaac 原始录屏拉伸到答辩时长：固定观感、居家背景合成、轻微去抖。"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
DEFAULT_IN = ROOT / "docs/assets/demo_isaac_g1_locomotion_raw.mp4"
DEFAULT_OUT = ROOT / "docs/assets/demo_isaac_g1_locomotion.mp4"
DEFAULT_BG = ROOT / "docs/assets/scene_living_room.jpg"


def _probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def _label(text: str) -> str:
    if FONT.is_file():
        t = text.replace("'", "\\'")
        return (
            f"drawtext=fontfile={FONT}:text='{t}':fontsize=28:"
            "fontcolor=white:borderw=2:bordercolor=black@0.6:x=44:y=40"
        )
    return f"drawtext=text='{text}':fontsize=28:fontcolor=white:x=44:y=40"


def _fg_chain(slow: float, title: str, use_colorkey: bool) -> str:
    parts: list[str] = [f"setpts={slow:.4f}*PTS"]
    parts.append("tmix=frames=3:weights='1 2 1'")
    parts.append("scale=1280:720:force_original_aspect_ratio=decrease")
    parts.append("pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black")
    if use_colorkey:
        parts.append("colorkey=0x909090:0.22:0.08,format=rgba")
    parts.append("eq=brightness=0.03:saturation=1.1")
    parts.append(_label(title))
    return ",".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--bg", type=Path, default=Path(os.environ.get("G1_HOME_BG", str(DEFAULT_BG))))
    ap.add_argument("--no-bg", action="store_true", help="不合成居家照片背景（推荐，避免透视错位）")
    ap.add_argument("--target-dur", type=float, default=float(os.environ.get("G1_TARGET_DUR", "14")))
    ap.add_argument("--title", default="④ 居家场景·G1 搀扶老人站起（全仿真）")
    args = ap.parse_args()
    if not args.inp.is_file():
        raise SystemExit(f"缺少输入: {args.inp}")
    if not shutil.which("ffmpeg"):
        raise SystemExit("需要 ffmpeg")

    src_dur = _probe_duration(args.inp)
    slow = max(1.0, args.target_dur / max(0.5, src_dur))
    slow = min(slow, 3.5)

    use_bg = not args.no_bg and args.bg.is_file()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fg = _fg_chain(slow, args.title, use_colorkey=use_bg)

    if use_bg:
        fc = (
            f"[0:v]scale=1280:720,setsar=1[bg];"
            f"[1:v]{fg}[v];"
            f"[bg][v]overlay=shortest=1:format=auto[out]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-loop",
            "1",
            "-i",
            str(args.bg),
            "-i",
            str(args.inp),
            "-filter_complex",
            fc,
            "-map",
            "[out]",
            "-t",
            str(args.target_dur),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(args.out),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-i",
            str(args.inp),
            "-vf",
            fg,
            "-t",
            str(args.target_dur),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(args.out),
        ]
    subprocess.run(cmd, check=True)
    out_dur = _probe_duration(args.out)
    mode = "居家背景合成" if use_bg else "仅调色"
    print(f"✅ {args.out} ({out_dur:.1f}s, slow×{slow:.2f}, {mode})")


if __name__ == "__main__":
    main()
