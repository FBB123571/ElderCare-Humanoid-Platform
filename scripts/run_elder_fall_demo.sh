#!/usr/bin/env bash
# 老人跌倒样片：分析 + 标注 mp4 + 更新 demo_full_scenario
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

INPUT="${1:-}"
if [[ -n "$INPUT" ]]; then
  exec "$PY" scripts/process_elder_fall_video.py "$INPUT"
else
  exec "$PY" scripts/process_elder_fall_video.py
fi
