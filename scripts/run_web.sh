#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

if [ ! -f .venv/bin/activate ]; then
  bash scripts/setup_env.sh
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install -q fastapi "uvicorn[standard]" 2>/dev/null || pip install fastapi "uvicorn[standard]"

PORT="${1:-8765}"

if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "✅ Web 控制台已在运行: http://127.0.0.1:${PORT}"
  echo "   Cursor → 查看 → 端口 → 8765 →「在浏览器中打开」"
  echo "   或浏览器访问: http://localhost:${PORT}"
  exit 0
fi

if ss -tln 2>/dev/null | grep -q ":${PORT} " || netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
  echo "⚠️ 端口 ${PORT} 被占用但服务无响应，尝试结束旧进程..."
  fuser -k "${PORT}/tcp" 2>/dev/null || true
  sleep 1
fi

echo "启动 Web 控制台，端口 ${PORT} ..."
echo "浏览器访问: http://localhost:${PORT} （Cursor 需转发端口 ${PORT}）"
exec python scripts/run_web.py "${PORT}"
