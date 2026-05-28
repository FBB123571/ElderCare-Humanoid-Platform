#!/usr/bin/env bash
# 一键生成答辩用全部 mp4（跌倒分析 / 心情数字人 / Web 总演示 / 30s 情景剧）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
PORT="${PORT:-8765}"

echo "========== [1/5] 确保 Web 运行 =========="
bash scripts/run_web.sh "$PORT" || true
sleep 1

echo ""
echo "========== [2/5] 老人跌倒分析录屏 =========="
"$PY" scripts/process_elder_fall_video.py --no-merge

echo ""
echo "========== [3/5] 心情·数字人剧场演示片 =========="
"$PY" scripts/render_mood_theater_video.py || "$PY" scripts/record_mood_theater_video.py -p "$PORT" || {
  echo "⚠️ 心情剧场视频失败，跳过"
}

echo ""
echo "========== [4/5] CareCompanion Web 全流程录屏 =========="
"$PY" scripts/record_demo_video.py -p "$PORT" || {
  echo "⚠️ Web 全流程录屏失败，保留旧 demo_carecompanion.mp4"
}

echo ""
echo "========== [5/5] 合成 30s 情景剧总片 =========="
export WEB_SRC="${WEB_SRC:-$ROOT/docs/assets/demo_elder_fall_analysis.mp4}"
export WEB_START=0
export WEB_LEN=10
"$PY" scripts/render_mood_theater_video.py
"$PY" scripts/render_g1_home_rescue_video.py 2>/dev/null || true
bash scripts/merge_demo_full_video.sh
bash scripts/merge_demo_extended.sh 2>/dev/null || true

echo ""
echo "✅ 全部视频："
ls -lh docs/assets/demo_*.mp4 docs/assets/samples/elder_fall_wechat.mp4 2>/dev/null
