#!/usr/bin/env bash
# A 档：合成约 30s 情景剧总片 — Web 跌倒段 + ROS2 echo + G1 行走
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$ROOT/docs/assets"
OUT="$ASSETS/demo_full_scenario.mp4"

WEB_SRC="${WEB_SRC:-$ASSETS/demo_carecompanion.mp4}"
G1_SRC="${G1_SRC:-$ASSETS/demo_isaac_g1_locomotion.mp4}"
ECHO_SRC="${ECHO_SRC:-$ASSETS/demo_ros2_cmd_echo.mp4}"

# Web 中取跌倒相关片段（可按实际录屏调整）
WEB_START="${WEB_START:-38}"
WEB_LEN="${WEB_LEN:-12}"
ECHO_LEN="${ECHO_LEN:-8}"
G1_LEN="${G1_LEN:-8}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

need() {
  [[ -f "$1" ]] || { echo "❌ 缺少: $1"; exit 1; }
}

need "$WEB_SRC"
need "$G1_SRC"

echo "▶ 裁剪 Web 段 ${WEB_START}s + ${WEB_LEN}s"
ffmpeg -y -nostdin -ss "$WEB_START" -t "$WEB_LEN" -i "$WEB_SRC" \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,drawtext=text='Web · 跌倒紧急':fontsize=28:fontcolor=white:x=40:y=40" \
  -c:v libx264 -pix_fmt yuv420p -an "$TMP/01_web.mp4" 2>/dev/null

if [[ -f "$ECHO_SRC" ]]; then
  echo "▶ 裁剪 ROS2 echo ${ECHO_LEN}s"
  ffmpeg -y -nostdin -t "$ECHO_LEN" -i "$ECHO_SRC" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
    -c:v libx264 -pix_fmt yuv420p -an "$TMP/02_ros2.mp4" 2>/dev/null
else
  echo "⚠️ 无 $ECHO_SRC，跳过 ROS2 段（先运行 render_ros2_echo_video.py）"
fi

echo "▶ 裁剪 G1 ${G1_LEN}s"
ffmpeg -y -nostdin -t "$G1_LEN" -i "$G1_SRC" \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,drawtext=text='Isaac Lab · G1 执行层':fontsize=28:fontcolor=white:x=40:y=40" \
  -c:v libx264 -pix_fmt yuv420p -an "$TMP/03_g1.mp4" 2>/dev/null

LIST="$TMP/concat.txt"
: >"$LIST"
[[ -f "$TMP/01_web.mp4" ]] && echo "file '01_web.mp4'" >>"$LIST"
[[ -f "$TMP/02_ros2.mp4" ]] && echo "file '02_ros2.mp4'" >>"$LIST"
[[ -f "$TMP/03_g1.mp4" ]] && echo "file '03_g1.mp4'" >>"$LIST"

echo "▶ 拼接 → $OUT"
ffmpeg -y -nostdin -f concat -safe 0 -i "$LIST" -c:v libx264 -pix_fmt yuv420p -an "$OUT" 2>/dev/null

ls -lh "$OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" | xargs -I{} echo "时长: {}s"
