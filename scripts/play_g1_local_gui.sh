#!/usr/bin/env bash
# 在本机有显示器时播放 G1（不录屏），用 OBS / Win+G 自行录制。
# 用法：在已安装 Isaac Lab 的机器上，接好显示器后执行。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-$ROOT/../IsaacLab}"
CHECKPOINT="${CHECKPOINT:-$ISAACLAB/checkpoints/g1_flat_checkpoint.pt}"
TASK="${TASK:-Isaac-Velocity-Flat-G1-Play-v0}"
GPU="${CUDA_VISIBLE_DEVICES:-0}"

if [[ ! -d "$ISAACLAB" ]]; then
  echo "❌ 未找到 Isaac Lab: $ISAACLAB"
  echo "   export ISAACLAB_PATH=/path/to/IsaacLab"
  exit 1
fi

NUCLEUS_LOCAL="$ISAACLAB/assets_nucleus"
G1_USD="$NUCLEUS_LOCAL/Isaac/IsaacLab/Robots/Unitree/G1/g1_minimal.usd"
HYDRA=()
if [[ -f "$G1_USD" ]]; then
  HYDRA+=("env.scene.robot.spawn.usd_path=$G1_USD")
  HYDRA+=("env.commands.base_velocity.debug_vis=false")
fi

export CUDA_VISIBLE_DEVICES="$GPU"
export ENABLE_CAMERAS=1

cd "$ISAACLAB"
echo "▶ 本地 GUI 播放 G1（关闭窗口或 Ctrl+C 结束）"
echo "   录屏：Windows Win+G / OBS；macOS QuickTime 屏幕录制"
echo ""

if [[ -x "./isaaclab.sh" ]]; then
  ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
    --task "$TASK" \
    --num_envs 1 \
    --checkpoint "$CHECKPOINT" \
    "${HYDRA[@]}"
else
  python scripts/reinforcement_learning/rsl_rl/play.py \
    --task "$TASK" \
    --num_envs 1 \
    --checkpoint "$CHECKPOINT" \
    "${HYDRA[@]}"
fi
