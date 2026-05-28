#!/usr/bin/env bash
# 下载 Isaac Lab Unitree G1 平地行走预训练权重（约 2MB）
set -euo pipefail
ISAACLAB="${ISAACLAB_PATH:-/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab}"
OUT="$ISAACLAB/checkpoints/g1_flat_checkpoint.pt"
URL="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/Isaac-Velocity-Flat-G1-v0/checkpoint.pt"
mkdir -p "$(dirname "$OUT")"
curl --noproxy '*' -fsSL --max-time 300 -o "$OUT" "$URL"
ls -lh "$OUT"
echo "✅ 已保存: $OUT"
