#!/usr/bin/env bash
# 下载 MediaPipe Pose Landmarker 模型（答辩视觉分析必需）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/data/models/pose_landmarker_lite.task"
URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

mkdir -p "$(dirname "$DEST")"
if [[ -f "$DEST" && "$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")" -gt 100000 ]]; then
  echo "✅ 模型已存在: $DEST"
  exit 0
fi

echo "⬇️  正在下载 pose_landmarker_lite.task …"
# 避免失效代理
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  curl -fsSL "$URL" -o "$DEST"
echo "✅ 已保存: $DEST ($(du -h "$DEST" | cut -f1))"
