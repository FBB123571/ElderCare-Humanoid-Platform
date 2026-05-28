#!/usr/bin/env python3
"""G1 + 仿真老人 同场景录屏：室内 → 老人跌倒 → G1 赶赴 → 靠近停步（全仿真）。"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISAACLAB = Path(os.environ.get("ISAACLAB_PATH", ROOT.parent / "IsaacLab")).resolve()
RSL_RL = ISAACLAB / "scripts/reinforcement_learning/rsl_rl"
os.chdir(ISAACLAB)
sys.path.insert(0, str(RSL_RL))

import cli_args  # noqa: E402

from isaaclab.app import AppLauncher  # noqa: E402

parser = argparse.ArgumentParser(description="Record G1 + elder humanoid rescue in Isaac Sim.")
parser.add_argument("--video", action="store_true", default=True)
parser.add_argument("--video_length", type=int, default=int(os.environ.get("VIDEO_LEN", "360")))
parser.add_argument("--disable_fabric", action="store_true", default=False)
parser.add_argument("--num_envs", type=int, default=None)
parser.add_argument("--task", type=str, default="Isaac-Velocity-Flat-G1-Play-v0")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--seed", type=int, default=None)
parser.add_argument("--use_pretrained_checkpoint", action="store_true")
parser.add_argument("--real-time", action="store_true", default=False)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
args_cli.enable_cameras = True
args_cli.headless = True

sys.argv = [sys.argv[0]] + hydra_args
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym  # noqa: E402
import imageio  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from isaaclab.assets import ArticulationCfg, AssetBaseCfg  # noqa: E402
from isaaclab.utils import configclass  # noqa: E402
from isaaclab_assets import HUMANOID_CFG  # noqa: E402
from rsl_rl.runners import DistillationRunner, OnPolicyRunner  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.envs import (  # noqa: E402
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    ViewerCfg,
    multi_agent_to_single_agent,
)
from isaaclab.utils.assets import retrieve_file_path  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper  # noqa: E402
from isaaclab_rl.utils.pretrained_checkpoint import get_published_pretrained_checkpoint  # noqa: E402

import isaaclab_tasks  # noqa: F401, E402
from isaaclab_tasks.manager_based.locomotion.velocity.config.g1.flat_env_cfg import (  # noqa: E402
    G1FlatEnvCfg_PLAY,
)
from isaaclab_tasks.utils import get_checkpoint_path  # noqa: E402
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402

# —— 时间轴（仿真步）——
HOLD_STEPS = int(os.environ.get("ISAAC_HOLD_STEPS", "55"))
FALL_START = int(os.environ.get("ISAAC_ELDER_FALL_STEP", "55"))
FALL_DUR = int(os.environ.get("ISAAC_ELDER_FALL_STEPS", "55"))
WALK_DELAY = int(os.environ.get("ISAAC_WALK_DELAY", "95"))
STOP_DIST = float(os.environ.get("ISAAC_STOP_DIST", "1.05"))
LIFT_DUR = int(os.environ.get("ISAAC_LIFT_DUR", "90"))
LIFT_MIN_FALL_DONE = int(os.environ.get("ISAAC_LIFT_MIN_FALL_DONE", "1"))  # 跌倒动画结束后再扶

ELDER_X = float(os.environ.get("ISAAC_ELDER_X", "2.2"))
ELDER_Y = float(os.environ.get("ISAAC_ELDER_Y", "0.0"))
G1_START_X = float(os.environ.get("ISAAC_G1_START_X", "-3.2"))
LIN_X = float(os.environ.get("ISAAC_CMD_VEL_X", "1.15"))
ELDER_SCALE = float(os.environ.get("ISAAC_ELDER_SCALE", "0.93"))

# 老人姿态：躺 → 坐 → 扶起站立（分两段插值，避免一步飞天）
ELDER_STAND_Z = 1.28
ELDER_FALLEN_PITCH = 1.18
ELDER_FALLEN_ROLL = 0.92
ELDER_FALLEN_Z = 0.34
ELDER_SIT_PITCH = 0.50
ELDER_SIT_ROLL = 0.20
ELDER_SIT_Z = 0.62
LIFT_SIT_FRAC = float(os.environ.get("ISAAC_LIFT_SIT_FRAC", "0.38"))  # 扶起前半：坐起
G1_KNEEL_Z = 0.50
G1_STAND_Z = 0.74


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _quat_from_pitch_roll(pitch: float, roll: float) -> tuple[float, float, float, float]:
    cy, sy = math.cos(roll * 0.5), math.sin(roll * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    qw = cp * cy
    qx = sp * cy
    qy = cp * sy
    qz = -sp * sy
    return (qw, qx, qy, qz)


@configclass
class G1ElderRescuePlayCfg(G1FlatEnvCfg_PLAY):
    """G1 Play + 老人形 + 室内 USD / HDR 光照。"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.scene.num_envs = 1
        self.scene.env_spacing = 6.0

        humanoid_usd = os.environ.get("ISAAC_ELDER_USD", "")
        elder_spawn = HUMANOID_CFG.spawn
        if humanoid_usd and Path(humanoid_usd).is_file():
            elder_spawn = elder_spawn.replace(
                usd_path=humanoid_usd,
                scale=(ELDER_SCALE, ELDER_SCALE, ELDER_SCALE),
            )

        self.scene.elder = HUMANOID_CFG.replace(
            prim_path="{ENV_REGEX_NS}/Elder",
            spawn=elder_spawn,
            init_state=ArticulationCfg.InitialStateCfg(
                pos=(ELDER_X, ELDER_Y, 1.34),
                joint_pos={".*": 0.0},
            ),
        )

        indoor_usd = os.environ.get("ISAAC_INDOOR_USD", "")
        if indoor_usd and Path(indoor_usd).is_file():
            rtx = float(os.environ.get("ISAAC_ROOM_TX", "0.0"))
            rty = float(os.environ.get("ISAAC_ROOM_TY", "0.0"))
            rtz = float(os.environ.get("ISAAC_ROOM_TZ", "0.0"))
            self.scene.indoor = AssetBaseCfg(
                prim_path="/World/IndoorScene",
                spawn=sim_utils.UsdFileCfg(usd_path=indoor_usd),
                init_state=AssetBaseCfg.InitialStateCfg(pos=(rtx, rty, rtz)),
            )
            # 与房间木地板接近，避免双层地面穿帮
            self.scene.terrain.visual_material = sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.38, 0.34, 0.30),
                roughness=0.9,
            )

        hdr = os.environ.get("ISAAC_INDOOR_HDR", "")
        if hdr and Path(hdr).is_file():
            self.scene.rescue_dome = AssetBaseCfg(
                prim_path="/World/RescueDomeLight",
                spawn=sim_utils.DomeLightCfg(
                    intensity=float(os.environ.get("ISAAC_DOME_INTENSITY", "1500")),
                    color=(1.0, 0.97, 0.92),
                    texture_file=hdr,
                ),
            )

        self.scene.robot.init_state.pos = (G1_START_X, ELDER_Y, 0.74)
        self.scene.robot.init_state.rot = (1.0, 0.0, 0.0, 0.0)

        self.events.reset_base.params = {
            "pose_range": {
                "x": (G1_START_X, G1_START_X),
                "y": (0.0, 0.0),
                "yaw": (0.0, 0.0),
            },
            "velocity_range": {
                "x": (0.0, 0.0),
                "y": (0.0, 0.0),
                "z": (0.0, 0.0),
                "roll": (0.0, 0.0),
                "pitch": (0.0, 0.0),
                "yaw": (0.0, 0.0),
            },
        }


def _configure_play(env_cfg: ManagerBasedRLEnvCfg) -> None:
    env_cfg.scene.num_envs = 1
    cmd = env_cfg.commands.base_velocity
    cmd.resampling_time_range = (1.0e9, 1.0e9)
    cmd.rel_standing_envs = 0.0
    cmd.rel_heading_envs = 0.0
    cmd.heading_command = False
    cmd.debug_vis = False
    cmd.ranges.lin_vel_x = (LIN_X, LIN_X)
    cmd.ranges.lin_vel_y = (0.0, 0.0)
    cmd.ranges.ang_vel_z = (0.0, 0.0)


def _configure_viewer(env_cfg: ManagerBasedRLEnvCfg) -> None:
    w, h = (int(x) for x in os.environ.get("ISAAC_VIEWER_RES", "1280,720").split(","))
    env_cfg.viewer = ViewerCfg(
        eye=(0.5, -6.8, 2.6),
        lookat=(0.3, 0.0, 0.95),
        resolution=(w, h),
        origin_type="world",
        env_index=0,
    )


def _robot_elder_dist(robot, elder) -> float:
    return torch.norm(robot.data.root_pos_w[0, :2] - elder.data.root_pos_w[0, :2]).item()


def _fallen_progress(step: int) -> float:
    if step < FALL_START:
        return 0.0
    return _smoothstep(min(1.0, (step - FALL_START) / max(1, FALL_DUR)))


def _lift_progress(step: int, robot, elder, env) -> float | None:
    """抵达后进入扶起阶段，返回 0..1；否则 None。"""
    if step < FALL_START + FALL_DUR and LIFT_MIN_FALL_DONE:
        return None
    base = env.unwrapped
    if getattr(base, "_lift_begin_step", None) is None:
        if _robot_elder_dist(robot, elder) <= STOP_DIST + 0.12:
            base._lift_begin_step = step  # noqa: SLF001
        return None
    t = (step - base._lift_begin_step) / max(1, LIFT_DUR)  # type: ignore[attr-defined]
    return min(1.0, _smoothstep(t))


def _g1_cmd_speed(step: int, robot, elder, env) -> float:
    if _lift_progress(step, robot, elder, env) is not None:
        return 0.0
    if step < WALK_DELAY:
        return 0.0
    dist = _robot_elder_dist(robot, elder)
    if dist < STOP_DIST:
        return 0.0
    if dist < STOP_DIST + 0.5:
        return LIN_X * 0.55
    return LIN_X


def _force_forward_command(env: gym.Env, lin_x: float) -> None:
    term = env.unwrapped.command_manager.get_term("base_velocity")
    term.vel_command_b[:, 0] = lin_x
    term.vel_command_b[:, 1] = 0.0
    term.vel_command_b[:, 2] = 0.0
    term.is_standing_env[:] = lin_x <= 1.0e-4


def _apply_fixed_camera(env: gym.Env) -> None:
    """世界坐标固定机位，整段录屏不跟随角色（避免画面抖动）。"""
    base = env.unwrapped
    if getattr(base, "_fixed_cam_applied", False):
        return
    eye = np.array(
        [
            float(os.environ.get("ISAAC_CAM_EYE_X", "2.2")),
            float(os.environ.get("ISAAC_CAM_EYE_Y", "-5.8")),
            float(os.environ.get("ISAAC_CAM_EYE_Z", "2.35")),
        ],
        dtype=np.float64,
    )
    lookat = np.array(
        [
            float(os.environ.get("ISAAC_CAM_LOOK_X", "0.2")),
            float(os.environ.get("ISAAC_CAM_LOOK_Y", "0.0")),
            float(os.environ.get("ISAAC_CAM_LOOK_Z", "0.88")),
        ],
        dtype=np.float64,
    )
    base.sim.set_camera_view(eye=eye, target=lookat)
    vcc = getattr(base, "viewport_camera_controller", None)
    if vcc is not None:
        vcc.cfg.origin_type = "world"
        vcc.viewer_origin = torch.zeros(3, device=base.device)
        vcc.default_cam_eye = eye - vcc.viewer_origin.detach().cpu().numpy()
        vcc.default_cam_lookat = lookat - vcc.viewer_origin.detach().cpu().numpy()
    base._fixed_cam_applied = True  # noqa: SLF001


def _frame_ok(frame: np.ndarray | None) -> bool:
    if frame is None or frame.size == 0:
        return False
    return float(frame.std()) > 5.0


def _grab_frame(env: gym.Env, robot, elder, step: int) -> np.ndarray | None:
    _apply_fixed_camera(env)
    base = env.unwrapped
    base.sim.render()
    frame = base.render(recompute=True)
    if frame is None:
        return None
    if isinstance(frame, torch.Tensor):
        frame = frame.detach().cpu().numpy()
    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255).astype(np.uint8)
    return frame[..., :3]


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _write_elder_pose(
    elder, pitch: float, roll: float, x: float, y: float, z: float, curl: float, z_max: float = 1.32
) -> None:
    z = max(0.30, min(z_max, z))
    root = elder.data.default_root_state.clone()
    root[0, 0] = x
    root[0, 1] = y
    root[0, 2] = z
    qw, qx, qy, qz = _quat_from_pitch_roll(pitch, roll)
    root[0, 3:7] = torch.tensor([qw, qx, qy, qz], device=root.device, dtype=root.dtype)
    root[0, 7:13] = 0.0
    elder.write_root_pose_to_sim(root[:, :7])
    elder.write_root_velocity_to_sim(root[:, 7:13])
    jpos = elder.data.joint_pos.clone()
    for name_idx, jn in enumerate(elder.data.joint_names):
        if "knee" in jn or "shin" in jn:
            jpos[0, name_idx] = -0.72 * curl
        elif "hip" in jn:
            jpos[0, name_idx] = 0.22 * curl
        elif "upper_arm" in jn:
            jpos[0, name_idx] = 0.45 * curl
        elif "lower_arm" in jn:
            jpos[0, name_idx] = 0.15 * curl
    elder.write_joint_state_to_sim(jpos, torch.zeros_like(jpos))


def _animate_elder_fall(elder, step: int) -> None:
    if step < FALL_START:
        return
    u = _fallen_progress(step)
    _write_elder_pose(
        elder,
        pitch=_lerp(0.0, ELDER_FALLEN_PITCH, u),
        roll=_lerp(0.0, ELDER_FALLEN_ROLL, u),
        x=_lerp(ELDER_X, ELDER_X - 0.22, u),
        y=_lerp(ELDER_Y, ELDER_Y + 0.16, u),
        z=_lerp(ELDER_STAND_Z, ELDER_FALLEN_Z, u),
        curl=u,
    )


def _lift_sit_stand_u(lift_t: float) -> tuple[float, float, float]:
    """返回 (总进度 u, 坐起段 0-1, 站立段 0-1)。"""
    u = _smoothstep(lift_t)
    if u <= LIFT_SIT_FRAC:
        return u, u / max(1e-6, LIFT_SIT_FRAC), 0.0
    stand_u = _smoothstep((u - LIFT_SIT_FRAC) / max(1e-6, 1.0 - LIFT_SIT_FRAC))
    return u, 1.0, stand_u


def _animate_elder_lift(elder, lift_t: float) -> None:
    """躺地 → 坐起 → 扶起站立。"""
    _u, sit_u, stand_u = _lift_sit_stand_u(lift_t)
    if stand_u <= 0.0:
        _write_elder_pose(
            elder,
            pitch=_lerp(ELDER_FALLEN_PITCH, ELDER_SIT_PITCH, sit_u),
            roll=_lerp(ELDER_FALLEN_ROLL, ELDER_SIT_ROLL, sit_u),
            x=_lerp(ELDER_X - 0.22, ELDER_X - 0.08, sit_u),
            y=_lerp(ELDER_Y + 0.16, ELDER_Y + 0.12, sit_u),
            z=_lerp(ELDER_FALLEN_Z, ELDER_SIT_Z, sit_u),
            curl=_lerp(1.0, 0.45, sit_u),
            z_max=ELDER_SIT_Z + 0.08,
        )
    else:
        _write_elder_pose(
            elder,
            pitch=_lerp(ELDER_SIT_PITCH, 0.06, stand_u),
            roll=_lerp(ELDER_SIT_ROLL, 0.0, stand_u),
            x=_lerp(ELDER_X - 0.08, ELDER_X, stand_u),
            y=_lerp(ELDER_Y + 0.12, ELDER_Y + 0.06, stand_u),
            z=_lerp(ELDER_SIT_Z, ELDER_STAND_Z, stand_u),
            curl=_lerp(0.45, 0.06, stand_u),
            z_max=ELDER_STAND_Z + 0.05,
        )


def _animate_g1_assist(robot, elder, lift_t: float) -> None:
    """跪地托肩 → 协同站起（机器人始终贴地，不腾空）。"""
    e = elder.data.root_pos_w[0]
    ex, ey, ez = float(e[0]), float(e[1]), float(e[2])
    _u, sit_u, stand_u = _lift_sit_stand_u(lift_t)

    approach_u = min(1.0, sit_u / 0.55) if sit_u < 0.55 else 1.0

    root = robot.data.root_state_w.clone()
    root[0, 0] = _lerp(ex - 0.42, ex - 0.26, approach_u)
    root[0, 1] = ey + 0.20
    if stand_u <= 0.0:
        root[0, 2] = _lerp(G1_STAND_Z, G1_KNEEL_Z, approach_u)
    else:
        root[0, 2] = _lerp(G1_KNEEL_Z, G1_STAND_Z, stand_u)
    root[0, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=root.device, dtype=root.dtype)
    root[0, 7:13] = 0.0
    robot.write_root_pose_to_sim(root[:, :7])
    robot.write_root_velocity_to_sim(root[:, 7:13])

    arm_hold = min(1.0, sit_u * 0.7 + stand_u * 0.3)
    jpos = robot.data.default_joint_pos.clone()
    for name_idx, jn in enumerate(robot.data.joint_names):
        if "torso" in jn:
            jpos[0, name_idx] = _lerp(0.0, -0.28, approach_u) if stand_u <= 0 else _lerp(-0.28, 0.0, stand_u)
        elif "hip_pitch" in jn:
            if stand_u <= 0:
                jpos[0, name_idx] = _lerp(0.0, 0.78, approach_u)
            else:
                jpos[0, name_idx] = _lerp(0.78, 0.0, stand_u)
        elif "knee" in jn:
            if stand_u <= 0:
                jpos[0, name_idx] = _lerp(0.0, 1.08, approach_u)
            else:
                jpos[0, name_idx] = _lerp(1.08, 0.08, stand_u)
        elif "ankle_pitch" in jn:
            if stand_u <= 0:
                jpos[0, name_idx] = _lerp(0.0, -0.58, approach_u)
            else:
                jpos[0, name_idx] = _lerp(-0.58, 0.0, stand_u)
        elif "shoulder_pitch" in jn:
            jpos[0, name_idx] = _lerp(0.35, 0.72, arm_hold) if stand_u <= 0 else _lerp(0.72, 0.42, stand_u)
        elif "shoulder_roll" in jn:
            sign = 1.0 if "left" in jn else -1.0
            jpos[0, name_idx] = sign * _lerp(0.12, 0.28, arm_hold)
        elif "elbow" in jn:
            jpos[0, name_idx] = _lerp(0.48, 0.22, arm_hold) if stand_u <= 0 else _lerp(0.22, 0.38, stand_u)
        elif "wrist" in jn or "five" in jn or "three" in jn:
            jpos[0, name_idx] = 0.06 * arm_hold
    robot.write_joint_state_to_sim(jpos, torch.zeros_like(jpos))


def _sim_step(env, policy, policy_nn, obs, robot, elder, step: int):
    lift_t = _lift_progress(step, robot, elder, env)
    if lift_t is not None:
        _animate_elder_lift(elder, lift_t)
        _animate_g1_assist(robot, elder, lift_t)
        _force_forward_command(env, 0.0)
    else:
        _animate_elder_fall(elder, step)
        _force_forward_command(env, _g1_cmd_speed(step, robot, elder, env))
    actions = policy(obs)
    obs, _, dones, _ = env.step(actions)
    policy_nn.reset(dones)
    if lift_t is not None:
        _animate_elder_lift(elder, lift_t)
        _animate_g1_assist(robot, elder, lift_t)
    return obs


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    task_name = args_cli.task.split(":")[-1]
    train_task_name = task_name.replace("-Play", "")

    rescue_cfg = G1ElderRescuePlayCfg()
    env_cfg.scene = rescue_cfg.scene
    env_cfg.events = rescue_cfg.events
    env_cfg.viewer = rescue_cfg.viewer

    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    if args_cli.num_envs is not None:
        env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    _configure_play(env_cfg)
    _configure_viewer(env_cfg)

    log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
    if args_cli.use_pretrained_checkpoint:
        resume_path = get_published_pretrained_checkpoint("rsl_rl", train_task_name)
        if not resume_path:
            print("[INFO] 无预训练 checkpoint")
            return
    elif args_cli.checkpoint:
        resume_path = retrieve_file_path(args_cli.checkpoint)
    else:
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)

    log_dir = os.path.dirname(resume_path)
    env_cfg.log_dir = log_dir

    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array")
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    print(f"[INFO]: Loading checkpoint: {resume_path}")
    if agent_cfg.class_name == "OnPolicyRunner":
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    elif agent_cfg.class_name == "DistillationRunner":
        runner = DistillationRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    else:
        raise ValueError(agent_cfg.class_name)
    runner.load(resume_path)
    policy = runner.get_inference_policy(device=env.unwrapped.device)
    policy_nn = runner.alg.policy if hasattr(runner.alg, "policy") else runner.alg.actor_critic

    video_dir = os.path.join(log_dir, "videos", "play")
    os.makedirs(video_dir, exist_ok=True)
    out_mp4 = os.path.join(video_dir, "rl-video-elder-rescue.mp4")
    frames: list[np.ndarray] = []

    warmup = int(os.environ.get("ISAAC_RENDER_WARMUP", "70"))
    obs, _ = env.reset()
    env.unwrapped._lift_begin_step = None  # noqa: SLF001
    robot = env.unwrapped.scene["robot"]
    elder = env.unwrapped.scene["elder"]
    _apply_fixed_camera(env)
    pos0 = robot.data.root_pos_w[0, :2].clone()
    dt = env.unwrapped.step_dt
    fps = max(1, int(round(1.0 / dt)))

    print(
        f"[INFO] 双角色 | G1@{G1_START_X}→老人@{ELDER_X} | "
        f"hold<{WALK_DELAY} fall@{FALL_START}+{FALL_DUR} "
        f"stop<{STOP_DIST}m 扶起{LIFT_DUR}步 vx={LIN_X}"
    )

    global_step = 0
    with torch.inference_mode():
        for _ in range(warmup):
            obs = _sim_step(env, policy, policy_nn, obs, robot, elder, global_step)
            global_step += 1
            _grab_frame(env, robot, elder, global_step)

    print(f"[INFO] 录屏 {args_cli.video_length} 步 → {out_mp4} (fps={fps})")
    with torch.inference_mode():
        for timestep in range(1, args_cli.video_length + 1):
            t0 = time.time()
            obs = _sim_step(env, policy, policy_nn, obs, robot, elder, global_step)
            global_step += 1
            frame = _grab_frame(env, robot, elder, global_step)
            if _frame_ok(frame):
                frames.append(frame)  # type: ignore[arg-type]
            if timestep % 60 == 0:
                dxy = (robot.data.root_pos_w[0, :2] - pos0).norm().item()
                dist = torch.norm(robot.data.root_pos_w[0, :2] - elder.data.root_pos_w[0, :2]).item()
                print(
                    f"[INFO] {timestep}/{args_cli.video_length} frames={len(frames)} "
                    f"Δxy={dxy:.2f}m dist={dist:.2f}m"
                )
            if args_cli.real_time:
                time.sleep(max(0.0, dt - (time.time() - t0)))

    env.close()
    if len(frames) < 10:
        raise RuntimeError(f"有效帧过少 ({len(frames)})")
    imageio.mimsave(out_mp4, frames, fps=fps, macro_block_size=1)
    print(f"[INFO] 已写入: {out_mp4} ({len(frames)} 帧)")


if __name__ == "__main__":
    main()
    simulation_app.close()
