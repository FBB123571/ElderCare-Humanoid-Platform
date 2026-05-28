# 情景剧总片（Web + ROS2 + G1）

## 一键生成

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
bash scripts/run_full_scenario_demo.sh
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `docs/assets/ros2_cmd_timeline.jsonl` | `/care/robot_cmd` 等价载荷（带时间戳） |
| `docs/assets/ros2_cmd_summary.json` | 条数、是否含 `call_emergency` |
| `docs/assets/demo_ros2_cmd_echo.mp4` | 终端 echo 风格录屏（~11s） |
| `docs/assets/demo_full_scenario.mp4` | **30s 总片**：Web 跌倒段 → ROS2 → G1 |

## 叙事结构（约 29s）

1. **Web · 跌倒紧急**（12s，来自 `demo_carecompanion.mp4` 38s 起）
2. **ROS2 指令流**（8s，`call_emergency` / `gesture` 等 JSON）
3. **Isaac G1 行走**（8s，执行层示意）

## 答辩话术

> 跌倒检测与紧急决策在 Web 平台完成；Orchestrator 通过标准话题 `/care/robot_cmd` 下发 JSON 指令；人形执行层用 Isaac G1 仿真展示 locomotion 能力。三者为**分层架构**，非单点 walking demo。

## 调参

```bash
# 调整 Web 片段起点（若跌倒画面不在 38s）
WEB_START=40 WEB_LEN=12 bash scripts/merge_demo_full_video.sh

# 仅重跑 ROS2 段
python3 scripts/run_scenario_drama.py
python3 scripts/render_ros2_echo_video.py
```

## ROS2 真机/真话题（可选）

本机若已装 `rclpy`，`run_scenario_drama.py` 会同时 **publish** 到 `/care/robot_cmd`；否则 JSONL 与日志模式载荷一致，答辩可展示 JSONL + echo 视频。

```bash
# 另一终端监听（需 ROS2 环境）
ros2 topic echo /care/robot_cmd
```
