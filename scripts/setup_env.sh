#!/usr/bin/env bash
# 安装依赖。本机若配置了失效的 http_proxy，pip 会连不上，需先取消代理。
set -euo pipefail
cd "$(dirname "$0")/.."

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt

echo ""
echo "✅ 依赖安装完成。接下来可运行："
echo "   bash scripts/run_web.sh        # Web 控制台（推荐，浏览器访问）"
echo "   bash scripts/run_headless.sh"
echo "   bash scripts/run_gui.sh"
