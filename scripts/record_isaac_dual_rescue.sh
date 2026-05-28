#!/usr/bin/env bash
# 全仿真双角色：家庭室内 simple_room + 居家 HDR + 分镜 + 后处理到 14s
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab}"
OUT_DIR="$ROOT/docs/assets"
NUCLEUS_LOCAL="$ISAACLAB/assets_nucleus"
PLAY_SCRIPT="$ROOT/scripts/isaac_g1_elder_rescue_record.py"
BASE_URL="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1"

export PLAY_SCRIPT DUAL_SIM=1 SKIP_DUAL_POST=1
export VIDEO_LEN="${VIDEO_LEN:-520}"
export ISAAC_LIFT_DUR="${ISAAC_LIFT_DUR:-170}"
export ISAAC_LIFT_SIT_FRAC=0.38
export ISAAC_RENDER_WARMUP="${ISAAC_RENDER_WARMUP:-90}"
export RENDER_MODE="${RENDER_MODE:-balanced}"
export ISAAC_CMD_VEL_X="${ISAAC_CMD_VEL_X:-1.15}"
export ISAAC_HOLD_STEPS=45
export ISAAC_WALK_DELAY=75
export ISAAC_ELDER_FALL_STEP=45
export ISAAC_ELDER_FALL_STEPS=50
export ISAAC_STOP_DIST=0.95
export G1_TARGET_DUR=14
# 默认不用照片抠图合成（与仿真透视不一致会穿帮）；仅保留 Isaac 房间
export G1_USE_PHOTO_BG="${G1_USE_PHOTO_BG:-0}"
HOME_BG="$ROOT/docs/assets/scene_living_room.jpg"

HUMANOID_USD="$NUCLEUS_LOCAL/Isaac/Robots/IsaacSim/Humanoid/humanoid_instanceable.usd"
HOME_ROOM_USD="$NUCLEUS_LOCAL/Isaac/Environments/Simple_Room/simple_room.usd"
WAREHOUSE_USD="$NUCLEUS_LOCAL/Isaac/Environments/Simple_Warehouse/warehouse.usd"
HOSPITAL_USD="$NUCLEUS_LOCAL/Isaac/Environments/Hospital/hospital.usd"
INDOOR_HDR="$NUCLEUS_LOCAL/NVIDIA/Assets/Skies/Indoor/small_empty_house_4k.hdr"

mkdir -p "$(dirname "$HUMANOID_USD")" "$(dirname "$HOME_ROOM_USD")" "$(dirname "$INDOOR_HDR")"

_fetch() {
  local out="$1" url="$2" t="${3:-300}"
  [[ -f "$out" && "$(stat -c%s "$out" 2>/dev/null || echo 0)" -gt 1000 ]] && return 0
  echo "[INFO] 下载 $(basename "$out") …"
  curl --noproxy '*' -fsSL --max-time "$t" -o "$out" "$url" || return 1
}

_fetch "$HUMANOID_USD" "$BASE_URL/Isaac/Robots/IsaacSim/Humanoid/humanoid_instanceable.usd" 300 || exit 1
_fetch "$INDOOR_HDR" "$BASE_URL/NVIDIA/Assets/Skies/Indoor/small_empty_house_4k.hdr" 180 || echo "[WARN] HDR 下载失败，使用默认光照"
if [[ ! -f "$HOME_BG" ]]; then
  echo "[INFO] 下载居家客厅参考图（后处理背景）…"
  curl --noproxy '*' -fsSL --max-time 120 -o "$HOME_BG" \
    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1280&h=720&fit=crop&q=85" \
    || true
fi

if [[ "${DOWNLOAD_HOME_ROOM:-1}" == "1" ]]; then
  _fetch "$HOME_ROOM_USD" "$BASE_URL/Isaac/Environments/Simple_Room/simple_room.usd" 300 || true
fi
if [[ "${DOWNLOAD_WAREHOUSE:-0}" == "1" ]]; then
  _fetch "$WAREHOUSE_USD" "$BASE_URL/Isaac/Environments/Simple_Warehouse/warehouse.usd" 600 || true
fi
if [[ "${DOWNLOAD_HOSPITAL:-0}" == "1" ]]; then
  _fetch "$HOSPITAL_USD" "$BASE_URL/Isaac/Environments/Hospital/hospital.usd" 900 || true
fi

export ISAAC_ELDER_USD="$HUMANOID_USD"
export ISAAC_INDOOR_HDR="$INDOOR_HDR"
if [[ -f "$HOME_ROOM_USD" ]]; then
  export ISAAC_INDOOR_USD="$HOME_ROOM_USD"
  # 房间中央空地：老人靠前、G1 从门口侧走来；斜向固定机位
  export ISAAC_ROOM_TX=0.0 ISAAC_ROOM_TY=0.0 ISAAC_ROOM_TZ=0.0
  export ISAAC_CAM_EYE_X=2.6 ISAAC_CAM_EYE_Y=-3.4 ISAAC_CAM_EYE_Z=1.65
  export ISAAC_CAM_LOOK_X=-0.15 ISAAC_CAM_LOOK_Y=-0.35 ISAAC_CAM_LOOK_Z=0.82
  export ISAAC_ELDER_X=0.85 ISAAC_ELDER_Y=-0.35 ISAAC_G1_START_X=-1.35
  export ISAAC_STOP_DIST=0.75
  echo "[INFO] 家庭场景 (Simple Room): $HOME_ROOM_USD"
elif [[ -f "$HOSPITAL_USD" && "${PREFER_HOSPITAL:-0}" == "1" ]]; then
  export ISAAC_INDOOR_USD="$HOSPITAL_USD"
  export ISAAC_CAM_EYE_X=-4.5 ISAAC_CAM_EYE_Y=-8.0 ISAAC_CAM_EYE_Z=3.0
  export ISAAC_ELDER_X=1.0 ISAAC_G1_START_X=-4.0
  echo "[INFO] 医院场景: $HOSPITAL_USD"
elif [[ -f "$WAREHOUSE_USD" ]]; then
  export ISAAC_INDOOR_USD="$WAREHOUSE_USD"
  export ISAAC_CAM_EYE_X=1.0 ISAAC_CAM_EYE_Y=-7.0 ISAAC_CAM_EYE_Z=2.5
  export ISAAC_ELDER_X=1.8 ISAAC_G1_START_X=-2.8
  echo "[INFO] 仓库室内: $WAREHOUSE_USD"
else
  echo "[WARN] 无室内 USD，使用平地 + 居家 HDR"
fi

[[ -f "$INDOOR_HDR" ]] && echo "[INFO] 室内 HDR: $INDOOR_HDR"
echo "[INFO] 老人模型: $HUMANOID_USD"

bash "$ROOT/scripts/record_isaac_g1_demo.sh"

RAW="$OUT_DIR/demo_isaac_g1_locomotion_raw.mp4"
DEST="$OUT_DIR/demo_isaac_g1_locomotion.mp4"
if [[ -f "$RAW" ]]; then
  POST_ARGS=()
  [[ "$G1_USE_PHOTO_BG" == "1" ]] || POST_ARGS+=(--no-bg)
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    "$ROOT/.venv/bin/python" "$ROOT/scripts/postprocess_g1_sim_video.py" --in "$RAW" --out "$DEST" "${POST_ARGS[@]}"
  else
    python3 "$ROOT/scripts/postprocess_g1_sim_video.py" --in "$RAW" --out "$DEST" "${POST_ARGS[@]}"
  fi
  ls -lh "$RAW" "$DEST"
  bash "$ROOT/scripts/merge_demo_full_video.sh"
fi
