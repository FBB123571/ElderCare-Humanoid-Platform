#!/usr/bin/env bash
# 加长总片（与 demo_full_scenario 相同四段，可单独导出备份）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export FALL_LEN="${FALL_LEN:-10}"
export MOOD_LEN="${MOOD_LEN:-16}"
export ECHO_LEN="${ECHO_LEN:-8}"
export G1_LEN="${G1_LEN:-8}"
bash "$ROOT/scripts/merge_demo_full_video.sh"
cp -f "$ROOT/docs/assets/demo_full_scenario.mp4" "$ROOT/docs/assets/demo_full_extended.mp4"
ls -lh "$ROOT/docs/assets/demo_full_extended.mp4"
