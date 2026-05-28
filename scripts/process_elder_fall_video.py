#!/usr/bin/env python3
"""分析自采老人跌倒视频并生成带骨架/预警 HUD 的答辩录屏。"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.perception.video_analyzer import VideoAnalyzer

SAMPLES_DIR = ROOT / "docs" / "assets" / "samples"
DEFAULT_NAMES = (
  "elder_fall_wechat.mp4",
  "a42f27767beb9dab9d03d40327faffe3_raw.mp4",
)
OUT_MP4 = ROOT / "docs" / "assets" / "demo_elder_fall_analysis.mp4"
OUT_JSON = ROOT / "docs" / "assets" / "elder_fall_analysis.json"
ARCHIVE_SAMPLE = SAMPLES_DIR / "elder_fall_wechat.mp4"


def _resolve_input(explicit: str | None) -> Path | None:
  if explicit:
    p = Path(explicit).expanduser()
    if p.is_file():
      return p.resolve()
    print(f"❌ 指定路径不存在: {p}", file=sys.stderr)
    return None
  for name in DEFAULT_NAMES:
    candidate = SAMPLES_DIR / name
    if candidate.is_file():
      return candidate.resolve()
  return None


def _load_cfg() -> dict:
  cfg_path = ROOT / "config" / "default.yaml"
  return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def main() -> int:
  parser = argparse.ArgumentParser(description="老人跌倒视频：分析 + 标注录屏")
  parser.add_argument(
    "input",
    nargs="?",
    help="mp4 路径（默认查找 docs/assets/samples/elder_fall_wechat.mp4）",
  )
  parser.add_argument("--max-frames", type=int, default=0, help="0=全片")
  parser.add_argument("--stride", type=int, default=1)
  parser.add_argument("--no-merge", action="store_true", help="不更新 30s 总片")
  args = parser.parse_args()

  src = _resolve_input(args.input)
  if src is None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("未找到跌倒样片。请先将微信视频复制到服务器，例如：", file=sys.stderr)
    print(f"  mkdir -p {SAMPLES_DIR}", file=sys.stderr)
    print(f"  scp \".../a42f27767beb9dab9d03d40327faffe3_raw.mp4\" \\")
    print(f"      user@host:{ARCHIVE_SAMPLE}", file=sys.stderr)
    print("或在 Windows 本机执行后重新运行：", file=sys.stderr)
    print(f"  python {Path(__file__).name} /path/to/a42f27767beb9dab9d03d40327faffe3_raw.mp4", file=sys.stderr)
    return 1

  if src != ARCHIVE_SAMPLE.resolve() and ARCHIVE_SAMPLE.parent.exists():
    shutil.copy2(src, ARCHIVE_SAMPLE)
    print(f"▶ 已归档样片 → {ARCHIVE_SAMPLE}")

  cfg = _load_cfg()
  analyzer = VideoAnalyzer(cfg)
  max_frames = args.max_frames if args.max_frames > 0 else None

  print(f"▶ 分析: {src}")
  analysis = analyzer.analyze_file(
    src,
    max_frames=max_frames or 900,
    frame_stride=max(1, args.stride),
  )
  if not analysis.get("ok"):
    print(f"❌ 分析失败: {analysis.get('error')}", file=sys.stderr)
    return 1

  OUT_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"▶ 分析 JSON → {OUT_JSON}")
  fall = analysis.get("fall", {})
  print(
    f"   跌倒检测: {'是' if fall.get('detected') else '否'} "
    f"max_score={fall.get('max_score')} first_t={fall.get('first_alert_t_s')}s"
  )

  print(f"▶ 渲染标注视频 → {OUT_MP4}")
  render = analyzer.render_annotated_video(
    src,
    OUT_MP4,
    max_frames=max_frames,
    frame_stride=max(1, args.stride),
  )
  if not render.get("ok"):
    print(f"❌ 渲染失败: {render.get('error')}", file=sys.stderr)
    return 1
  print(f"   帧数={render.get('frames_rendered')} 时长≈{render.get('duration_s')}s")

  if not args.no_merge:
    import subprocess

    web_len = min(14, max(8, int(render.get("duration_s", 10) + 2)))
    env = {
      **dict(__import__("os").environ),
      "WEB_SRC": str(OUT_MP4),
      "WEB_START": "0",
      "WEB_LEN": str(web_len),
    }
    print("▶ 用跌倒分析段更新 demo_full_scenario.mp4 …")
    subprocess.run(
      ["bash", str(ROOT / "scripts" / "merge_demo_full_video.sh")],
      cwd=str(ROOT),
      env=env,
      check=False,
    )

  print("✅ 完成")
  print(f"   标注视频: {OUT_MP4}")
  print(f"   总片(若已合成): {ROOT / 'docs/assets/demo_full_scenario.mp4'}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
