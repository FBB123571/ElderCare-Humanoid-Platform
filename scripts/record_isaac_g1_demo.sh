#!/usr/bin/env bash
# 使用旁路 Isaac Lab 录制 Unitree G1 仿真视频，并复制到本仓库 docs/assets/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab}"
OUT_DIR="$ROOT/docs/assets"
LOG_TAG="carecompanion_isaac_g1"
TASK="${TASK:-Isaac-Velocity-Flat-G1-Play-v0}"
VIDEO_LEN="${VIDEO_LEN:-500}"
# 不默认绑单卡，避免与 Omniverse 设备枚举冲突；需要时手动 export CUDA_VISIBLE_DEVICES=0
GPU="${CUDA_VISIBLE_DEVICES:-}"
# 录屏：默认无 xvfb（本机 xvfb 下 Vulkan 易失败）；无显示器时可 USE_XVFB=1
USE_XVFB="${USE_XVFB:-0}"
HEADLESS="${HEADLESS:-1}"
RENDER_MODE="${RENDER_MODE:-performance}"
RENDER_WARMUP="${RENDER_WARMUP:-100}"
CHECKPOINT="${CHECKPOINT:-}"
PLAY_SCRIPT="${PLAY_SCRIPT:-$ROOT/scripts/isaac_g1_play_record.py}"

mkdir -p "$OUT_DIR" "$ROOT/logs/isaac_record"
export ENABLE_CAMERAS="${ENABLE_CAMERAS:-1}"
# Isaac 缓存写到可写目录，避免 kit 目录 Permission denied
export OMNI_USER_DATA="${OMNI_USER_DATA:-/tmp/omni_user_${USER:-leijh}}"
export OMNI_CACHE_DIR="${OMNI_CACHE_DIR:-/tmp/omni_cache_${USER:-leijh}}"
mkdir -p "$OMNI_USER_DATA" "$OMNI_CACHE_DIR"

# 本地 Nucleus 镜像（避免 omni.client 拉不下 g1_minimal.usd）
NUCLEUS_LOCAL="$ISAACLAB/assets_nucleus"
G1_USD="$NUCLEUS_LOCAL/Isaac/IsaacLab/Robots/Unitree/G1/g1_minimal.usd"
G1_USD_URL="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/G1/g1_minimal.usd"
if [[ ! -f "$G1_USD" ]]; then
  echo "[INFO] 下载 G1 USD 到本地 Nucleus 镜像 …"
  mkdir -p "$(dirname "$G1_USD")"
  curl --noproxy '*' -fsSL --max-time 600 -o "$G1_USD" "$G1_USD_URL" || true
fi
if [[ ! -d "$ISAACLAB" ]]; then
  echo "❌ 未找到 Isaac Lab: $ISAACLAB"
  echo "   可设置: export ISAACLAB_PATH=/path/to/IsaacLab"
  exit 1
fi

if [[ ! -x "$ISAACLAB/isaaclab.sh" ]]; then
  echo "❌ 缺少 $ISAACLAB/isaaclab.sh"
  exit 1
fi

if [[ -n "$GPU" ]]; then
  export CUDA_VISIBLE_DEVICES="$GPU"
fi
# 强制 NVIDIA Vulkan，避免默认识别到不兼容驱动
export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/nvidia_icd.json}"
export __NV_PRIME_RENDER_OFFLOAD="${__NV_PRIME_RENDER_OFFLOAD:-1}"
export __GLX_VENDOR_LIBRARY_NAME="${__GLX_VENDOR_LIBRARY_NAME:-nvidia}"
echo "▶ Isaac Lab 录屏: task=$TASK gpu=${GPU:-all} headless=$HEADLESS xvfb=$USE_XVFB render=$RENDER_MODE length=$VIDEO_LEN"

RECORD_LOG="$ROOT/logs/isaac_record/${LOG_TAG}_$(date +%Y%m%d_%H%M%S).log"
EXTRA=()
if [[ "$HEADLESS" == "1" ]]; then
  EXTRA+=(--headless)
fi
export CARB_CACHE_PATH="${CARB_CACHE_PATH:-/tmp/carb_${USER:-leijh}}"
export ISAACSIM_CACHE_DIR="${ISAACSIM_CACHE_DIR:-$OMNI_CACHE_DIR/isaacsim}"
export ISAACSIM_USER_DIR="${ISAACSIM_USER_DIR:-$OMNI_USER_DATA/isaacsim}"
KIT_OGN_CACHE="${KIT_OGN_CACHE:-/tmp/isaacsim_ogn_${USER:-leijh}}"
mkdir -p "$CARB_CACHE_PATH" "$ISAACSIM_CACHE_DIR" "$ISAACSIM_USER_DIR" "$KIT_OGN_CACHE"
chmod 755 "$KIT_OGN_CACHE" 2>/dev/null || true

# 单实例锁，避免多开抢 GPU
LOCK_FILE="${LOCK_FILE:-/tmp/carecompanion_isaac_g1_record.lock}"
if [[ -f "$LOCK_FILE" ]]; then
  OLD_PID="$(cat "$LOCK_FILE" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "❌ 已有录屏任务在运行 (pid=$OLD_PID)，请先结束: pkill -f isaac_g1_play_record"
    exit 1
  fi
  rm -f "$LOCK_FILE"
fi
echo "$$" >"$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT
# 使用本地 USD（Hydra 覆盖，避免 --kit_args 与 argparse 冲突）
ENV_USD="$NUCLEUS_LOCAL/Isaac/Environments/Grid/default_environment.usd"
ENV_USD_URL="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Environments/Grid/default_environment.usd"
if [[ ! -f "$ENV_USD" ]]; then
  echo "[INFO] 下载平地场景 USD …"
  mkdir -p "$(dirname "$ENV_USD")"
  curl --noproxy '*' -fsSL --max-time 120 -o "$ENV_USD" "$ENV_USD_URL" || true
fi

HYDRA_USD=(
  "env.commands.base_velocity.debug_vis=false"
)
KIT_ARGS=()
if [[ -f "$G1_USD" ]]; then
  HYDRA_USD+=("env.scene.robot.spawn.usd_path=$G1_USD")
  echo "[INFO] 本地 G1 USD: $G1_USD"
fi
# 平地场景走 GroundPlaneCfg，不能用 env.scene.terrain.usd_path（plane 要求 None）
if [[ -d "$NUCLEUS_LOCAL" ]]; then
  NUCLEUS_URI="file://${NUCLEUS_LOCAL}"
  USER_CFG="${OMNI_USER_DATA}/isaac_sim_user.config.json"
  # 值以 -- 开头，必须用 --kit_args=... 否则 argparse 会当成新参数
  KIT_ARGS=(--kit_args="--/persistent/isaac/asset_root/cloud=${NUCLEUS_URI} --/app/userConfigPath=${USER_CFG} --/app/cache/ogn_generated=${KIT_OGN_CACHE}")
  echo "[INFO] 本地 Nucleus 根: $NUCLEUS_URI"
  echo "[INFO] kit ogn 缓存: $KIT_OGN_CACHE"
fi

CKPT_DEFAULT="$ISAACLAB/checkpoints/g1_flat_checkpoint.pt"
if [[ -z "$CHECKPOINT" && -f "$CKPT_DEFAULT" ]]; then
  CHECKPOINT="$CKPT_DEFAULT"
fi
if [[ -z "$CHECKPOINT" ]]; then
  echo "[INFO] 本地无权重，尝试下载 G1 预训练 checkpoint …"
  mkdir -p "$ISAACLAB/checkpoints"
  env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
    curl --noproxy '*' -fsSL --max-time 300 \
    -o "$CKPT_DEFAULT" \
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/Isaac-Velocity-Flat-G1-v0/checkpoint.pt" \
    && CHECKPOINT="$CKPT_DEFAULT" || echo "[WARN] 下载失败，将尝试 --use_pretrained_checkpoint"
fi

CKPT_ARGS=()
if [[ -n "$CHECKPOINT" && -f "$CHECKPOINT" ]]; then
  CKPT_ARGS=(--checkpoint "$CHECKPOINT")
  echo "[INFO] checkpoint: $CHECKPOINT"
else
  CKPT_ARGS=(--use_pretrained_checkpoint)
fi

cd "$ISAACLAB"
export TERM="${TERM:-xterm}"
export ISAACLAB_PATH="$ISAACLAB"

# 优先用 isaaclab 环境的 python，避免 isaaclab.sh 在非交互终端 tabs 报错
ISAAC_PYTHON="${ISAAC_PYTHON:-}"
if [[ -z "$ISAAC_PYTHON" && -x "${CONDA_PREFIX:-}/bin/python" ]]; then
  ISAAC_PYTHON="${CONDA_PREFIX}/bin/python"
fi
if [[ -x "/home/leijh/miniconda3/envs/isaaclab/bin/python" ]]; then
  ISAAC_PYTHON="/home/leijh/miniconda3/envs/isaaclab/bin/python"
elif [[ -z "$ISAAC_PYTHON" && -x "/home/leijh/miniconda3/envs/isaaclab/bin/python" ]]; then
  ISAAC_PYTHON="/home/leijh/miniconda3/envs/isaaclab/bin/python"
fi
if [[ -z "$ISAAC_PYTHON" && -x "$ISAACLAB/_isaac_sim/python.sh" ]]; then
  ISAAC_PYTHON="$ISAACLAB/_isaac_sim/python.sh"
fi

export ISAAC_RENDER_WARMUP="${ISAAC_RENDER_WARMUP:-$RENDER_WARMUP}"
export ISAAC_VIEWER_RES="${ISAAC_VIEWER_RES:-1280,720}"
export ISAAC_CMD_VEL_X="${ISAAC_CMD_VEL_X:-0.75}"

PLAY_ARGS=(
  "$PLAY_SCRIPT"
  "${EXTRA[@]}"
  --enable_cameras
  --task "$TASK"
  "${CKPT_ARGS[@]}"
  --num_envs 1
  --video
  --video_length "$VIDEO_LEN"
  --rendering_mode "$RENDER_MODE"
  "${KIT_ARGS[@]}"
  "${HYDRA_USD[@]}"
)
echo "[INFO] play script: $PLAY_SCRIPT (warmup=$RENDER_WARMUP)"

XVFB_CMD=()
if [[ "$USE_XVFB" == "1" ]]; then
  if ! command -v xvfb-run >/dev/null 2>&1; then
    echo "❌ 需要 xvfb-run 才能无物理显示器录屏: sudo apt install xvfb"
    exit 1
  fi
  XVFB_SCREEN="${XVFB_SCREEN:-1920x1080x24}"
  XVFB_CMD=(xvfb-run -a -s "-screen 0 ${XVFB_SCREEN} +extension GLX +render -noreset")
  echo "[INFO] 使用 xvfb 虚拟显示: ${XVFB_SCREEN}"
fi

set +e
if [[ -n "$ISAAC_PYTHON" && -x "$ISAAC_PYTHON" ]]; then
  if [[ ${#XVFB_CMD[@]} -gt 0 ]]; then
    "${XVFB_CMD[@]}" "$ISAAC_PYTHON" "${PLAY_ARGS[@]}" 2>&1 | tee "$RECORD_LOG"
  else
    "$ISAAC_PYTHON" "${PLAY_ARGS[@]}" 2>&1 | tee "$RECORD_LOG"
  fi
else
  if [[ ${#XVFB_CMD[@]} -gt 0 ]]; then
    "${XVFB_CMD[@]}" ./isaaclab.sh -p "${PLAY_ARGS[@]}" 2>&1 | tee "$RECORD_LOG"
  else
    ./isaaclab.sh -p "${PLAY_ARGS[@]}" 2>&1 | tee "$RECORD_LOG"
  fi
fi
PLAY_RC="${PIPESTATUS[0]:-1}"
set -e

if [[ "${PLAY_RC:-1}" -ne 0 ]]; then
  echo "❌ Isaac play 失败 (exit ${PLAY_RC})，日志: $RECORD_LOG"
  exit "${PLAY_RC}"
fi

# 查找最新 mp4（logs/rsl_rl 或 checkpoint 旁 videos/play/）
LATEST_MP4=""
SEARCH_ROOTS=("$ISAACLAB/logs/rsl_rl" "$ISAACLAB/checkpoints")
for _root in "${SEARCH_ROOTS[@]}"; do
  if [[ -d "$_root" ]]; then
    _found="$(find "$_root" -type f -path '*/videos/play/*.mp4' -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- || true)"
    if [[ -n "$_found" && -f "$_found" ]]; then
      LATEST_MP4="$_found"
    fi
  fi
done
# 最小体积过滤（避免灰屏空片 ~10KB）
if [[ -n "$LATEST_MP4" && -f "$LATEST_MP4" ]]; then
  _sz="$(stat -c%s "$LATEST_MP4" 2>/dev/null || echo 0)"
  if [[ "$_sz" -lt 8000 ]]; then
    echo "⚠️ mp4 过小 (${_sz} bytes)，可能为无效灰屏: $LATEST_MP4"
    LATEST_MP4=""
  fi
fi

if [[ -z "$LATEST_MP4" || ! -f "$LATEST_MP4" ]]; then
  echo "⚠️ 未找到 mp4，请检查日志: $RECORD_LOG"
  exit 1
fi

DEST="$OUT_DIR/demo_isaac_g1_locomotion.mp4"
cp -f "$LATEST_MP4" "$DEST"
echo "✅ 已复制: $DEST"
echo "   源文件: $LATEST_MP4"
ls -lh "$DEST"
