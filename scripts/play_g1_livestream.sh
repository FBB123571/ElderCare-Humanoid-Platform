#!/usr/bin/env bash
# 在服务器 headless 下开 WebRTC 直播，你在本机 WebRTC 客户端观看并录屏。
# Cursor 端口转发 49100 → 49100，本机连 127.0.0.1:49100
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab}"
CHECKPOINT="${CHECKPOINT:-$ISAACLAB/checkpoints/g1_flat_checkpoint.pt}"
TASK="${TASK:-Isaac-Velocity-Flat-G1-Play-v0}"
GPU="${CUDA_VISIBLE_DEVICES:-4}"
PUBLIC_IP="${PUBLIC_IP:-127.0.0.1}"
LIVESTREAM="${LIVESTREAM:-1}"
# livestream 时必须用 headless.rendering.kit，否则会加载需联网的 rendering.kit 并报错
EXPERIENCE="${EXPERIENCE:-$ISAACLAB/apps/isaaclab.python.headless.rendering.kit}"

NUCLEUS_LOCAL="$ISAACLAB/assets_nucleus"
G1_USD="$NUCLEUS_LOCAL/Isaac/IsaacLab/Robots/Unitree/G1/g1_minimal.usd"
HYDRA=()
if [[ -f "$G1_USD" ]]; then
  HYDRA+=("env.scene.robot.spawn.usd_path=$G1_USD")
  HYDRA+=("env.commands.base_velocity.debug_vis=false")
fi

export CUDA_VISIBLE_DEVICES="$GPU"
export ENABLE_CAMERAS=1
export PUBLIC_IP
export OMNI_USER_DATA="${OMNI_USER_DATA:-/tmp/omni_user_${USER:-leijh}}"
export OMNI_CACHE_DIR="${OMNI_CACHE_DIR:-/tmp/omni_cache_${USER:-leijh}}"
export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/nvidia_icd.json}"
mkdir -p "$OMNI_USER_DATA" "$OMNI_CACHE_DIR"

LOCK_FILE="/tmp/carecompanion_isaac_g1_livestream.lock"
if [[ -f "$LOCK_FILE" ]]; then
  OLD_PID="$(cat "$LOCK_FILE" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "❌ 直播已在运行 (pid=$OLD_PID)，请先: kill $OLD_PID"
    exit 1
  fi
  rm -f "$LOCK_FILE"
fi
echo "$$" >"$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

cd "$ISAACLAB"
ISAAC_PYTHON="/home/leijh/miniconda3/envs/isaaclab/bin/python"
if [[ ! -x "$ISAAC_PYTHON" ]]; then
  ISAAC_PYTHON="$(command -v python)"
fi

if [[ ! -f "$EXPERIENCE" ]]; then
  echo "❌ 未找到 experience: $EXPERIENCE"
  exit 1
fi

echo "▶ G1 WebRTC 直播  GPU=$GPU  livestream=$LIVESTREAM"
echo "   experience: $EXPERIENCE"
echo "   1. Cursor → 端口 → 转发 49100"
echo "   2. 本机安装 Isaac Sim WebRTC Streaming Client"
echo "   3. 连接: $PUBLIC_IP:49100"
echo "   4. OBS / Win+G 录客户端窗口"
echo ""

unset PYTHONPATH
export PYTHONNOUSERSITE=1

NUCLEUS_URI="file://${NUCLEUS_LOCAL}"
USER_CFG="${OMNI_USER_DATA}/isaac_sim_user.config.json"

"$ISAAC_PYTHON" scripts/reinforcement_learning/rsl_rl/play.py \
  --headless \
  --livestream "$LIVESTREAM" \
  --enable_cameras \
  --experience "$EXPERIENCE" \
  --task "$TASK" \
  --num_envs 1 \
  --checkpoint "$CHECKPOINT" \
  --kit_args="--/persistent/isaac/asset_root/cloud=${NUCLEUS_URI} --/app/userConfigPath=${USER_CFG}" \
  "${HYDRA[@]}"
