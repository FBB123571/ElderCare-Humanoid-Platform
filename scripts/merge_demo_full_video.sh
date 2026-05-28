#!/usr/bin/env bash
# 完整流程总片：心情情景演绎 → 跌倒分析 → ROS2 → G1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$ROOT/docs/assets"
OUT="$ASSETS/demo_full_scenario.mp4"
FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

FALL="${FALL_SRC:-$ASSETS/demo_elder_fall_analysis.mp4}"
MOOD="${MOOD_SRC:-$ASSETS/demo_mood_digital_human.mp4}"
G1="${G1_SRC:-$ASSETS/demo_isaac_g1_locomotion.mp4}"
ECHO="${ECHO_SRC:-$ASSETS/demo_ros2_cmd_echo.mp4}"

FALL_LEN="${FALL_LEN:-9}"
MOOD_LEN="${MOOD_LEN:-14}"
ECHO_LEN="${ECHO_LEN:-8}"
G1_LEN="${G1_LEN:-14}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

_label() {
  local text="$1"
  if [[ -f "$FONT" ]]; then
    echo "drawtext=fontfile=${FONT}:text='${text}':fontsize=26:fontcolor=white:x=40:y=36"
  else
    echo "drawtext=text='${text}':fontsize=26:fontcolor=white:x=40:y=36"
  fi
}

need() { [[ -f "$1" ]] || { echo "❌ 缺少: $1"; exit 1; }; }

need "$FALL"
need "$G1"

VF_SCALE="scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"

if [[ -f "$MOOD" ]]; then
  echo "▶ [1] 心情情景演绎 ${MOOD_LEN}s"
  VF_MOOD="${VF_SCALE},$(_label '① 双数字人情景演绎')"
  ffmpeg -y -nostdin -t "$MOOD_LEN" -i "$MOOD" -vf "$VF_MOOD" \
    -c:v libx264 -pix_fmt yuv420p -an "$TMP/01_mood.mp4" 2>/dev/null
else
  echo "⚠️ 无 $MOOD，跳过情景演绎（先运行 render_mood_theater_video.py）"
fi

echo "▶ [2] 跌倒分析 ${FALL_LEN}s"
VF_FALL="${VF_SCALE},$(_label '② 跌倒视觉分析')"
ffmpeg -y -nostdin -t "$FALL_LEN" -i "$FALL" -vf "$VF_FALL" \
  -c:v libx264 -pix_fmt yuv420p -an "$TMP/02_fall.mp4" 2>/dev/null

if [[ -f "$ECHO" ]]; then
  echo "▶ [3] ROS2 指令 ${ECHO_LEN}s"
  ffmpeg -y -nostdin -t "$ECHO_LEN" -i "$ECHO" -vf "$VF_SCALE,$(_label '③ ROS2 决策下发')" \
    -c:v libx264 -pix_fmt yuv420p -an "$TMP/03_ros2.mp4" 2>/dev/null
fi

echo "▶ [4] G1 执行层 ${G1_LEN}s"
ffmpeg -y -nostdin -t "$G1_LEN" -i "$G1" -vf "$VF_SCALE,$(_label '④ G1 搀扶老人站起（全仿真）')" \
  -c:v libx264 -pix_fmt yuv420p -an "$TMP/04_g1.mp4" 2>/dev/null

LIST="$TMP/concat.txt"
: >"$LIST"
[[ -f "$TMP/01_mood.mp4" ]] && echo "file '01_mood.mp4'" >>"$LIST"
[[ -f "$TMP/02_fall.mp4" ]] && echo "file '02_fall.mp4'" >>"$LIST"
[[ -f "$TMP/03_ros2.mp4" ]] && echo "file '03_ros2.mp4'" >>"$LIST"
[[ -f "$TMP/04_g1.mp4" ]] && echo "file '04_g1.mp4'" >>"$LIST"

echo "▶ 拼接 → $OUT"
ffmpeg -y -nostdin -f concat -safe 0 -i "$LIST" -c:v libx264 -pix_fmt yuv420p -an "$OUT" 2>/dev/null
ls -lh "$OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" | xargs -I{} echo "时长: {}s"
