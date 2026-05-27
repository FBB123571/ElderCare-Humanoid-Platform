#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .venv/bin/activate ]; then
  echo "ℹ️ 未找到 .venv，请先运行: bash scripts/setup_env.sh"
  exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate

if ! python -c "import tkinter" 2>/dev/null; then
  echo "❌ 缺少 tkinter（GUI 需要）。请执行: sudo apt install -y python3-tk"
  exit 1
fi

run_gui() {
  python scripts/run_simulation.py "$@"
}

if [ -z "${DISPLAY:-}" ]; then
  if [ "${1:-}" = "--real" ]; then
    echo "❌ 已指定 --real 但 DISPLAY 为空。请在服务器桌面终端运行，或："
    echo "   export DISPLAY=:1   # 若本机已登录图形界面"
    exit 1
  fi
  if ! command -v xvfb-run >/dev/null 2>&1; then
    echo "❌ SSH 无 DISPLAY，且未安装 xvfb。请执行:"
    echo "   sudo apt install -y xvfb"
    echo "   或在本机图形界面终端运行: bash scripts/run_gui.sh --real"
    exit 1
  fi
  echo "ℹ️ SSH 无显示器，使用 xvfb 虚拟屏做 GUI 冒烟测试（约 12 秒）…"
  echo "   若要在屏幕上看到窗口，请在服务器本机桌面终端执行: bash scripts/run_gui.sh --real"
  xvfb-run -a python scripts/run_simulation.py --smoke-test
  echo "✅ GUI 冒烟测试完成"
  exit 0
fi

run_gui "$@"
