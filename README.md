# CareCompanion · 智能养老人形陪伴机器人平台

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)]()
[![ROS2](https://img.shields.io/badge/Deploy-ROS2%20%7C%20Simulation-223344)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **仿真验证 → 边缘感知 → 人形机器人部署** 一体化养老陪伴系统。  
> 面向创新创业/软著/机器人竞赛：**多模态融合、主动式照护、可解释风险决策、真实机器人接口**。

---

## 为什么比「纯桌面 Demo」更适合获奖

| 维度 | 本方案 | 常见桌面仿真 |
|------|--------|--------------|
| 部署路径 | ROS2 / 人形机器人适配层，仿真与真机同一套 API | 仅 GUI，无法上机 |
| 感知融合 | 跌倒 + 情绪 + 生理指标 → **统一风险引擎** | 模块孤立 |
| 认知层 | 大模型对话 + **主动照护任务规划** | 仅聊天 |
| 安全合规 | 本地优先处理敏感视觉；紧急事件硬优先级 | 全云端 |
| 可演示性 | 桌面仿真 + 无头压测 + 场景剧本 | 单界面 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Simulation (GUI)                    │
│              场景剧本 · 实时面板 · 告警与对话日志              │
└────────────────────────────┬────────────────────────────────┘
                             │ RobotAdapter (统一接口)
┌────────────────────────────▼────────────────────────────────┐
│                     Care Orchestrator                          │
│   状态机: IDLE → MONITOR → CONVERSE → ALERT → EMERGENCY       │
└─┬──────────┬──────────┬──────────┬──────────┬───────────────┘
  │          │          │          │          │
  ▼          ▼          ▼          ▼          ▼
Fall      Emotion    Health     Dialogue   Risk
Detector  Recognizer Monitor    Manager    Engine
  │          │          │          │          │
  └──────────┴──────────┴────┬─────┴──────────┘
                               ▼
                    ┌──────────────────────┐
                    │  ROS2 Bridge (可选)   │
                    │  /care/* topics       │
                    └──────────┬───────────┘
                               ▼
                    Unitree / 其他人形机器人
```

---

## 功能模块

- **跌倒检测**：人体姿态宽高比 + 垂直速度 + 静止确认（MediaPipe 可选增强）
- **情绪识别**：面部 + 语音文本情感融合（离线可运行）
- **健康监测**：心率/血氧/活动量仿真或接入可穿戴设备 JSON
- **语音对话**：可插拔 LLM（默认内置 Mock，支持 OpenAI 兼容 API）
- **主动照护**：久坐提醒、用药提醒、情绪低落安抚、紧急呼叫
- **人形部署**：`RobotAdapter` → `SimulationAdapter` / `ROS2Adapter`

---

## 快速开始

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform

# 安装依赖（自动处理失效代理；勿直接 pip，否则会 ProxyError）
bash scripts/setup_env.sh

# 无头自动化演示（评委/CI，SSH 可用）
bash scripts/run_headless.sh

# Web 控制台（推荐：本机浏览器访问，Cursor 转发 8765 端口）
bash scripts/run_web.sh

# 桌面仿真（需本机显示器 + DISPLAY）
bash scripts/run_gui.sh
```

若坚持手动安装，请先取消代理再 pip：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_simulation.py
python scripts/run_headless_demo.py

# ROS2 桥接（需已安装 rclpy）
python scripts/run_ros2_bridge.py
```

---

## 部署到人形机器人

详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。核心思路：

1. 工控机/NUC 运行 `care_companion` 感知与决策节点  
2. `ROS2Adapter` 发布 `/care/robot_cmd`（语音、手势、导航意图）  
3. 机器人端订阅并映射到厂商 SDK（Unitree、智元等）

---

## 目录结构

```
ElderCare-Humanoid-Platform/
├── care_companion/       # 核心 Python 包
├── web/                  # Web 控制台（FastAPI + 前端）
├── simulation/           # 桌面仿真 GUI
├── deployment/ros2/      # ROS2 话题定义与桥接
├── config/               # 场景与阈值配置
├── docs/                 # 架构、部署、竞赛答辩材料
├── scripts/              # 启动脚本
└── tests/
```

---

## 文档

- [架构说明](docs/ARCHITECTURE.md)
- [人形机器人部署](docs/DEPLOYMENT.md)
- [竞赛/答辩要点](docs/COMPETITION.md)
- [软著材料清单](docs/SOFT_COPYRIGHT.md)

---

## 作者

[FBB123571](https://github.com/FBB123571)
