#!/usr/bin/env bash
# 检查权限 → 若无权则提示 sudo → 自动录屏并复制到 docs/assets/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISAAC_CACHE="/mnt/sda1/leijh/miniconda3/envs/isaaclab/lib/python3.11/site-packages/isaacsim/kit/cache/shadercache/common"
TEST_FILE="$ISAAC_CACHE/.perm_check_$$"

check_perm() {
  mkdir -p "$ISAAC_CACHE" 2>/dev/null || return 1
  touch "$TEST_FILE" 2>/dev/null || return 1
  rm -f "$TEST_FILE"
  return 0
}

if ! check_perm; then
  echo ""
  echo "❌ Isaac Sim 缓存目录当前不可写（属主不是您），无法录屏。"
  echo ""
  echo "请在本 SSH 终端执行（会要求输入一次 sudo 密码）："
  echo "  cd $ROOT"
  echo "  sudo bash scripts/fix_isaac_permissions.sh"
  echo ""
  echo "完成后再执行："
  echo "  bash scripts/setup_and_record_g1.sh"
  echo ""
  exit 1
fi

echo "✅ 权限检查通过，开始录屏 …"
exec bash "$ROOT/scripts/record_isaac_g1_demo.sh"
