# 人形机器人部署指南

## 推荐硬件架构

```
老人房间相机/麦克风/可穿戴
        ↓
  NUC / Jetson (care_companion)
        ↓ ROS2 DDS
  人形机器人机载电脑 (厂商 SDK)
        ↓
  语音播报 / 手臂动作 / 移动底盘
```

## ROS2 话题约定

| 话题 | 类型 | 说明 |
|------|------|------|
| `/care/robot_cmd` | `std_msgs/String` (JSON) | 下行指令 |
| `/care/status` | `std_msgs/String` | 上行状态（可自行扩展发布） |

### JSON 指令示例

```json
{"command": "speak", "text": "请不要动，援助正在赶来。"}
{"command": "gesture", "name": "raise_hand"}
{"command": "call_emergency", "reasons": ["跌倒事件"]}
```

## 部署步骤

1. 在边缘设备安装依赖：`pip install -r requirements.txt`
2. 配置 `config/default.yaml` 中阈值与 `dialogue.provider`
3. 启动感知节点（相机/OpenCV 或厂商驱动）
4. 启动决策：`python scripts/run_ros2_bridge.py` 或自写循环调用 `CareOrchestrator.tick`
5. 机器人端编写订阅节点，解析 JSON 并调用 SDK

## Unitree G1 / 其他人形

- 将 `gesture` 映射到预设动作 ID
- 将 `approach` 映射到导航目标点（相对老人坐标）
- `call_emergency` 触发 VoIP / 4G 模块 / 家属 App 推送

## 仿真先行

答辩前务必运行：

```bash
python scripts/run_headless_demo.py
python scripts/run_simulation.py
```

确认跌倒 → 紧急呼叫链路完整。
