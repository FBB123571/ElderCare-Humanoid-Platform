#!/usr/bin/env bash
# 一次性修复 isaacsim 写权限（必须在本机 SSH 终端执行，会提示输入 sudo 密码）
set -euo pipefail

ISAAC_ROOT="/mnt/sda1/leijh/miniconda3/envs/isaaclab/lib/python3.11/site-packages/isaacsim"
USER_NAME="${SUDO_USER:-${USER:-leijh}}"

echo "▶ 修复 Isaac Sim 缓存目录权限 → $USER_NAME"
echo "   $ISAAC_ROOT"

sudo chown -R "$USER_NAME:$USER_NAME" "$ISAAC_ROOT/kit/cache" "$ISAAC_ROOT/kit/data" "$ISAAC_ROOT/kit/logs"
sudo chmod -R u+rwX "$ISAAC_ROOT/kit/cache" "$ISAAC_ROOT/kit/data" "$ISAAC_ROOT/kit/logs"
sudo mkdir -p "$ISAAC_ROOT/kit/cache/shadercache/common"
sudo mkdir -p "$ISAAC_ROOT/kit/data/Kit/Isaac-Sim/5.1/pip3-envs/default"
sudo chown -R "$USER_NAME:$USER_NAME" "$ISAAC_ROOT/kit/cache" "$ISAAC_ROOT/kit/data"

# 自检
sudo -u "$USER_NAME" touch "$ISAAC_ROOT/kit/cache/shadercache/common/.perm_ok"
rm -f "$ISAAC_ROOT/kit/cache/shadercache/common/.perm_ok"
echo "✅ 权限 OK，可录屏: bash scripts/record_isaac_g1_demo.sh"
