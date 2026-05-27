# 软件著作权材料清单

## 软件名称建议

**CareCompanion 智能养老人形陪伴机器人系统 V1.0**

## 源程序提交

- 核心：`care_companion/` 全部 `.py`
- 界面：`simulation/desktop_gui.py`
- 入口：`scripts/run_simulation.py`、`scripts/run_headless_demo.py`

## 文档材料

- 本仓库 `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- 操作手册：运行 GUI 截图 + 演示剧本说明

## 功能说明（与规划书对应）

| 规划功能 | 实现文件 |
|----------|----------|
| 语音对话 | `cognition/dialogue_manager.py` |
| 情绪识别 | `perception/emotion_recognizer.py` |
| 跌倒检测 | `perception/fall_detector.py` |
| 健康监测 | `perception/health_monitor.py` |
| 仿真界面 | `simulation/desktop_gui.py` |
| 机器人部署 | `action/robot_adapter.py` (ROS2) |
