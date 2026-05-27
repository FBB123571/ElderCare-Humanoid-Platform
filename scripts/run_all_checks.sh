#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
source .venv/bin/activate 2>/dev/null || bash scripts/setup_env.sh && source .venv/bin/activate

echo "========== 单元测试 =========="
python -m pytest tests/ -v

echo ""
echo "========== 无头演示 =========="
python scripts/run_headless_demo.py

echo ""
echo "========== 跌倒评测 =========="
python scripts/eval_fall_detection.py

echo ""
echo "✅ 全部检查通过"
