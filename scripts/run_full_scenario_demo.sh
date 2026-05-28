#!/usr/bin/env bash
# 一键：情景剧 ROS2 录制 → echo 视频 → 合成 30s 总片
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

echo "=== [1/3] 跑通剧本并录制 robot_cmd JSONL ==="
"$PY" scripts/run_scenario_drama.py

echo ""
echo "=== [2/3] 渲染 ros2 topic echo 风格视频 ==="
"$PY" scripts/render_ros2_echo_video.py

echo ""
echo "=== [3/3] 合成 demo_full_scenario.mp4 ==="
bash scripts/merge_demo_full_video.sh

echo ""
echo "✅ 完成"
echo "   JSONL: docs/assets/ros2_cmd_timeline.jsonl"
echo "   Echo:  docs/assets/demo_ros2_cmd_echo.mp4"
echo "   总片:  docs/assets/demo_full_scenario.mp4"
