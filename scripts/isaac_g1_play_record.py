#!/usr/bin/env python3
"""G1 录屏：世界坐标固定机位（地面会动、人能看出在走）+ 固定前进速度。"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISAACLAB = Path(os.environ.get("ISAACLAB_PATH", ROOT.parent / "IsaacLab")).resolve()
RSL_RL = ISAACLAB / "scripts/reinforcement_learning/rsl_rl"
os.chdir(ISAACLAB)
sys.path.insert(0, str(RSL_RL))

from isaaclab.app import AppLauncher  # noqa: E402

import cli_args  # noqa: E402

parser = argparse.ArgumentParser(description="Record G1 locomotion video with RSL-RL.")
parser.add_argument("--video", action="store_true", default=True)
parser.add_argument("--video_length", type=int, default=200)
parser.add_argument("--disable_fabric", action="store_true", default=False)
parser.add_argument("--num_envs", type=int, default=None)
parser.add_argument("--task", type=str, default=None)
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
from rsl_rl.runners import DistillationRunner, OnPolicyRunner  # noqa: E402

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
from isaaclab_tasks.utils import get_checkpoint_path  # noqa: E402
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402


def _configure_play(env_cfg: ManagerBasedRLEnvCfg) -> None:
    lin_x = float(os.environ.get("ISAAC_CMD_VEL_X", "0.75"))
    env_cfg.scene.num_envs = 1
    env_cfg.scene.env_spacing = 2.5
    cmd = env_cfg.commands.base_velocity
    cmd.resampling_time_range = (1.0e9, 1.0e9)
    cmd.rel_standing_envs = 0.0
    cmd.rel_heading_envs = 0.0
    cmd.heading_command = False
    cmd.debug_vis = False
    cmd.ranges.lin_vel_x = (lin_x, lin_x)
    cmd.ranges.lin_vel_y = (0.0, 0.0)
    cmd.ranges.ang_vel_z = (0.0, 0.0)


def _configure_viewer(env_cfg: ManagerBasedRLEnvCfg) -> None:
    w, h = (int(x) for x in os.environ.get("ISAAC_VIEWER_RES", "1280,720").split(","))
    # 世界坐标固定机位初值；录屏时用 _update_world_camera 只更新 lookat
    env_cfg.viewer = ViewerCfg(
        eye=(-6.0, -5.0, 3.2),
        lookat=(0.0, 0.0, 0.9),
        resolution=(w, h),
        origin_type="world",
        env_index=0,
    )


def _force_forward_command(env: gym.Env, lin_x: float) -> None:
    term = env.unwrapped.command_manager.get_term("base_velocity")
    term.vel_command_b[:, 0] = lin_x
    term.vel_command_b[:, 1] = 0.0
    term.vel_command_b[:, 2] = 0.0
    term.is_standing_env[:] = False


def _setup_world_camera(env: gym.Env, robot) -> np.ndarray:
    """机位固定在 reset 时世界坐标，不随机器人平移（才能看出在走）。"""
    root = robot.data.root_pos_w[0].detach().cpu().numpy()
    off = np.array(
        [
            float(os.environ.get("ISAAC_CAM_BACK", "-6.0")),
            float(os.environ.get("ISAAC_CAM_SIDE", "-5.0")),
            float(os.environ.get("ISAAC_CAM_UP", "3.2")),
        ],
        dtype=np.float64,
    )
    cam_eye = root + off
    env.unwrapped._record_cam_eye = cam_eye  # noqa: SLF001
    return cam_eye


def _update_world_camera(env: gym.Env, robot) -> None:
    """仅把 lookat 对准机器人躯干，eye 保持世界固定。"""
    base = env.unwrapped
    cam_eye = getattr(base, "_record_cam_eye", None)
    if cam_eye is None:
        cam_eye = _setup_world_camera(env, robot)
    root = robot.data.root_pos_w[0].detach().cpu().numpy()
    lookat = root + np.array([0.0, 0.0, 0.9], dtype=np.float64)
    base.sim.set_camera_view(eye=cam_eye, target=lookat)
    vcc = getattr(base, "viewport_camera_controller", None)
    if vcc is not None:
        vcc.cfg.origin_type = "world"
        vcc.viewer_origin = torch.zeros(3, device=base.device)
        vcc.default_cam_eye = cam_eye - vcc.viewer_origin.detach().cpu().numpy()
        vcc.default_cam_lookat = lookat - vcc.viewer_origin.detach().cpu().numpy()


def _frame_ok(frame: np.ndarray | None) -> bool:
    if frame is None or frame.size == 0:
        return False
    return float(frame.std()) > 5.0


def _grab_frame(env: gym.Env, robot) -> np.ndarray | None:
    _update_world_camera(env, robot)
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


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    task_name = args_cli.task.split(":")[-1]
    train_task_name = task_name.replace("-Play", "")

    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    if args_cli.num_envs is not None:
        env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    _configure_play(env_cfg)
    _configure_viewer(env_cfg)
    lin_x = float(os.environ.get("ISAAC_CMD_VEL_X", "0.75"))

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
    out_mp4 = os.path.join(video_dir, "rl-video-step-0.mp4")
    frames: list[np.ndarray] = []

    warmup = int(os.environ.get("ISAAC_RENDER_WARMUP", "80"))
    obs, _ = env.reset()
    _force_forward_command(env, lin_x)
    robot = env.unwrapped.scene["robot"]
    _setup_world_camera(env, robot)
    pos0 = robot.data.root_pos_w[0, :2].clone()
    joint0 = robot.data.joint_pos[0].clone()
    dt = env.unwrapped.step_dt
    fps = max(1, int(round(1.0 / dt)))

    print(f"[INFO] 前进 vx={lin_x} m/s | 世界固定机位（非跟随）| 预热 {warmup} 步")
    with torch.inference_mode():
        for _ in range(warmup):
            _force_forward_command(env, lin_x)
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            policy_nn.reset(dones)
            _grab_frame(env, robot)

    pos_warm = robot.data.root_pos_w[0, :2] - pos0
    joint_delta = (robot.data.joint_pos[0] - joint0).abs().max().item()
    print(f"[INFO] 预热后 Δxy={pos_warm.norm().item():.2f} m, 关节最大变化={joint_delta:.3f} rad")

    print(f"[INFO] 录屏 {args_cli.video_length} 步 → {out_mp4} (fps={fps})")
    with torch.inference_mode():
        for timestep in range(1, args_cli.video_length + 1):
            t0 = time.time()
            _force_forward_command(env, lin_x)
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            policy_nn.reset(dones)
            frame = _grab_frame(env, robot)
            if _frame_ok(frame):
                frames.append(frame)  # type: ignore[arg-type]
            if timestep % 50 == 0:
                dxy = (robot.data.root_pos_w[0, :2] - pos0).norm().item()
                jd = (robot.data.joint_pos[0] - joint0).abs().max().item()
                print(f"[INFO] step {timestep}/{args_cli.video_length} frames={len(frames)} Δxy={dxy:.2f}m jointΔ={jd:.3f}")
            if args_cli.real_time:
                time.sleep(max(0.0, dt - (time.time() - t0)))

    pos_end = robot.data.root_pos_w[0, :2] - pos0
    joint_end = (robot.data.joint_pos[0] - joint0).abs().max().item()
    print(f"[INFO] 录屏段 Δxy={pos_end.norm().item():.2f} m, 关节最大变化={joint_end:.3f} rad")
    env.close()
    if len(frames) < 10:
        raise RuntimeError(f"有效帧过少 ({len(frames)})")
    if pos_end.norm().item() < 0.5:
        raise RuntimeError(f"位移过小 (Δxy={pos_end.norm().item():.2f}m)，checkpoint/策略异常")
    if joint_end < 0.05:
        raise RuntimeError(f"关节几乎不动 (max Δ={joint_end:.3f} rad)，画面会像站着")
    imageio.mimsave(out_mp4, frames, fps=fps, macro_block_size=1)
    print(f"[INFO] 已写入: {out_mp4} ({len(frames)} 帧)")


if __name__ == "__main__":
    main()
    simulation_app.close()
