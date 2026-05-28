# Isaac Lab · Unitree G1 仿真录屏（竞赛备片）

## 选型结论

- **引擎**：Isaac Lab（本机 `/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab`）
- **机器人**：Unitree G1 官方任务 `Isaac-Velocity-Flat-G1-Play-v0`
- **GPU**：录屏用 **1×3090** 即可（`CUDA_VISIBLE_DEVICES=0`）
- **现场答辩**：仍以 Web 为主；本视频仅作 PPT/备片，不 live 开 Isaac

## 一键录制

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
bash scripts/record_isaac_g1_demo.sh
```

输出：`docs/assets/demo_isaac_g1_locomotion.mp4`

### 常用参数

```bash
# 指定 GPU、加长录屏步数
CUDA_VISIBLE_DEVICES=2 VIDEO_LEN=600 bash scripts/record_isaac_g1_demo.sh

# 有显示器时可关 headless（默认 HEADLESS=1）
HEADLESS=0 bash scripts/record_isaac_g1_demo.sh

# 粗糙地形备选
TASK=Isaac-Velocity-Rough-G1-Play-v0 bash scripts/record_isaac_g1_demo.sh
```

## 与 CareCompanion 的关系

```
Web / 剧本 / 跌倒检测  →  CareOrchestrator  →  RobotAction (JSON)
                              ↓
                    ROS2 /care/robot_cmd（部署接口）
                              ↓
              Isaac G1 仿真（本录屏，展示人形执行层）
```

赛前剪辑建议：Web 跌倒紧急（15s）+ 本 G1 片段（15～30s），旁白强调「同一套决策可下发人形」。

## 故障排查

| 现象 | 处理 |
|------|------|
| 找不到 isaaclab.sh | `export ISAACLAB_PATH=...` |
| 无预训练权重 | 本地权重：`bash scripts/download_g1_checkpoint.sh` |
| 无 mp4 | 看 `logs/isaac_record/*.log`，确认 `--enable_cameras` |
| X11 报错 | 保持 `HEADLESS=1`；**不要用 xvfb**（本机易出现 `VK_ERROR_INCOMPATIBLE_DRIVER`） |
| 卡在「平地场景」>10 分钟 | 多为 **Vulkan/RTX 未起来** 或 **GPU 被占满**；`pkill -f isaac_g1_play_record` 后重试 |
| `no suitable CUDA GPU` | 勿多开 Isaac；`pkill -f isaac_g1`；换空闲卡或取消 `CUDA_VISIBLE_DEVICES` |
| `/mnt/sda1/.../isaacsim` Permission denied | isaacsim 装在他人目录；需 **本用户自建 conda 环境** 或请管理员改缓存目录权限 |
| 录屏锁占用 | `rm -f /tmp/carecompanion_isaac_g1_record.lock` 并结束残留 `tee`/`bash` |

### 本机实测结论（2026-05-28）

- **仿真加载 G1 可行**（本地 USD + checkpoint + `isaac_g1_play_record.py` 预热）。
- **headless 自动录 mp4 未成功**：RTX/Replicator 抓帧失败或场景初始化挂死。
- **答辩建议**：主片用 `docs/assets/demo_carecompanion.mp4`；G1 作「架构可对接 Isaac/ROS2」说明，或换 **有显示器 / 本用户 isaacsim 环境** 的机器再录。

### 推荐重试命令（单实例）

```bash
pkill -f isaac_g1_play_record || true
rm -f /tmp/carecompanion_isaac_g1_record.lock
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
# 选空闲 GPU，例如 7
CUDA_VISIBLE_DEVICES=7 USE_XVFB=0 HEADLESS=1 VIDEO_LEN=200 \
  CHECKPOINT=/mnt/sdb1/leijh/EnergySnake1/robot/IsaacLab/checkpoints/g1_flat_checkpoint.pt \
  bash scripts/record_isaac_g1_demo.sh
```

有桌面时：`HEADLESS=0 USE_XVFB=0`（需真实 `DISPLAY`，且能访问扩展仓库或本地 kit 依赖齐全）。
