#!/usr/bin/env bash
# 下载 MediaPipe Pose Landmarker 模型（答辩视觉分析必需）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/data/models/pose_landmarker_lite.task"
URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

# 清除失效本地代理（常见于 Cursor/Clash 关闭后仍残留）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy no_proxy NO_PROXY

mkdir -p "$(dirname "$DEST")"
if [[ -f "$DEST" && "$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")" -gt 100000 ]]; then
  echo "✅ 模型已存在: $DEST"
  exit 0
fi

echo "⬇️  正在下载 pose_landmarker_lite.task …"
if command -v curl >/dev/null 2>&1; then
  curl --noproxy '*' -fsSL "$URL" -o "$DEST"
elif command -v wget >/dev/null 2>&1; then
  wget --no-proxy -q -O "$DEST" "$URL"
else
  echo "❌ 需要 curl 或 wget"
  exit 1
fi

if [[ ! -f "$DEST" ]] || [[ "$(stat -c%s "$DEST")" -lt 100000 ]]; then
  echo "❌ 下载失败或文件过小，请检查网络后重试"
  rm -f "$DEST"
  exit 1
fi

echo "✅ 已保存: $DEST ($(du -h "$DEST" | cut -f1))"
