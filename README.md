# CareCompanion · 智能养老人形陪伴机器人平台

[![GitHub](https://img.shields.io/badge/GitHub-FBB123571%2FElderCare--Humanoid--Platform-181717?logo=github)](https://github.com/FBB123571/ElderCare-Humanoid-Platform)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)]()
[![ROS2](https://img.shields.io/badge/Deploy-ROS2%20%7C%20Simulation-223344)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **仿真验证 → 边缘感知 → 人形机器人部署** 一体化养老陪伴系统。  
> 面向 **中国机器人及人工智能大赛 · 机器人创新赛道**：多模态融合、主动式照护、可解释风险决策、MediaPipe 视觉感知。

---

## 核心能力（除真机外均已实现）

| 模块 | 说明 |
|------|------|
| 多模态风险引擎 | 跌倒 + 情绪 + 健康 → 可解释评分与状态机 |
| MediaPipe 视觉 | 浏览器/摄像头骨架提取 + 跌倒特征 |
| Web 控制台 | 实时仪表盘、对话、指令流、演示剧本 |
| 紧急呼叫链路 | 告警音 / 语音 / `call_emergency` / 家属通知日志 |
| 评测体系 | 合成场景 F1=100%，pytest + 无头压测 |
| ROS2 接口 | `/care/robot_cmd` JSON（真机 SDK 待对接） |
| 答辩材料 | 技术报告 + **答辩 PPT**（见 `docs/`） |

---

## 快速开始

```bash
git clone https://github.com/FBB123571/ElderCare-Humanoid-Platform.git
cd ElderCare-Humanoid-Platform

bash scripts/setup_env.sh          # 安装依赖
bash scripts/run_web.sh            # Web 控制台 → http://localhost:8765
bash scripts/run_all_checks.sh     # 测试 + 无头演示 + 跌倒评测
```

**生成答辩 PPT：**

```bash
python tools/generate_presentation.py
# 输出: docs/答辩_CareCompanion.pptx
```

---

## 系统架构

```
感知 (Fall / Emotion / Health / Pose)
        ↓
CareOrchestrator + RiskEngine
        ↓
CarePlanner → RobotAdapter → 仿真 / ROS2 / 人形
        ↑
Web 控制台 / 桌面 GUI
```

---

## 脚本一览

| 命令 | 用途 |
|------|------|
| `bash scripts/run_web.sh` | **Web 控制台（推荐答辩演示）** |
| `bash scripts/run_headless.sh` | 无头自动剧本验证 |
| `bash scripts/run_gui.sh` | 桌面 GUI（需显示器） |
| `python scripts/eval_fall_detection.py` | 跌倒检测评测报告 |
| `python scripts/run_camera_demo.py` | 本地摄像头 + MediaPipe |
| `python scripts/run_ros2_bridge.py` | ROS2 指令发布演示 |
| `bash scripts/run_all_checks.sh` | 一键回归检查 |

---

## 评测结果（摘要）

详见 [docs/evaluation/METRICS.md](docs/evaluation/METRICS.md)

| 指标 | 结果 |
|------|------|
| 跌倒检测 F1（合成 6 场景） | **100%** |
| 端到端紧急呼叫 | **100%** |
| 单 tick 延迟 | < 50ms（CPU，无云端 LLM） |

---

## 目录结构

```
ElderCare-Humanoid-Platform/
├── care_companion/       # 决策核心
├── web/                  # FastAPI + 前端
├── simulation/           # 桌面 GUI
├── data/evaluation/      # 评测场景与结果
├── docs/                 # 技术报告、答辩 PPT、竞赛材料
├── tools/                # PPT 生成等
├── scripts/
└── tests/
```

---

## 文档

- [技术报告（竞赛版）](docs/TECHNICAL_REPORT.md)
- [答辩 PPT](docs/答辩_CareCompanion.pptx)（运行 `tools/generate_presentation.py` 生成）
- [架构说明](docs/ARCHITECTURE.md)
- [部署指南](docs/DEPLOYMENT.md)
- [竞赛答辩要点](docs/COMPETITION.md)
- [评测指标](docs/evaluation/METRICS.md)

---

## 作者

[FBB123571](https://github.com/FBB123571)
