# 架构设计

## 设计原则

1. **同一套决策核心**：`CareOrchestrator` 在仿真与真机复用。
2. **适配器隔离硬件**：`SimulationAdapter` / `ROS2Adapter` 实现 `RobotAdapter`。
3. **可解释风险**：`RiskEngine` 输出分数、等级与原因列表，便于答辩与医疗合规沟通。
4. **边缘优先**：跌倒/情绪可在本地完成；大模型可切换 Mock 离线模式。

## 模块职责

| 模块 | 职责 |
|------|------|
| `perception/` | 传感融合输入，输出结构化 `PerceptionFrame` |
| `cognition/` | 风险评估、对话、主动照护规划 |
| `action/` | 将 `RobotAction` 下发到仿真或 ROS2 |
| `simulation/` | 桌面 GUI 与演示剧本 |

## 与 Isaac Lab / Unitree 的关系

本仓库提供 **决策与指令层**。若需高保真物理仿真，可将 `ROS2Adapter` 对接到：

- Isaac Lab 中 Unitree G1 等 humanoid 任务（见上级目录 `IsaacLab`）
- 真机 Unitree SDK2 / ROS2 驱动节点

机器人端只需订阅 `/care/robot_cmd` JSON，映射为语音、手势、导航等 SDK 调用。
