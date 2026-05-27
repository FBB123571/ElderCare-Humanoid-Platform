# CareCompanion 技术报告（竞赛版）

## 1. 项目概述

**CareCompanion** 是面向居家养老场景的智能养老人形陪伴机器人软件平台，实现「多模态感知 → 可解释风险决策 → 主动照护执行」闭环，支持 Web 仿真验证、MediaPipe 视觉感知与 ROS2 人形机器人部署接口。

- 仓库：https://github.com/FBB123571/ElderCare-Humanoid-Platform
- 许可：MIT

## 2. 需求分析

| 需求 | 实现 |
|------|------|
| 跌倒检测与告警 | FallDetector + PosePipeline |
| 情感陪伴对话 | DialogueManager |
| 生理健康监测 | HealthMonitor |
| 紧急呼叫 | EmergencyNotifier + call_emergency |
| 人形机器人控制 | RobotAdapter / ROS2 |
| 可视化演示 | Web 控制台 |

## 3. 系统架构

详见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 4. 关键算法

### 4.1 跌倒检测

输入：骨架宽高比 \(R = w/h\)，垂直速度 \(v_y\)，时间步 \(\Delta t\)。

特征：

- 快速下落：\(v_y < -v_{th}\)
- 躺倒：\(R < R_{lying}\)
- 静止：躺倒后 \(|v_y| < 0.05\) 持续 \(\geq T_{still}\)

融合得分并判定快速/慢速跌倒（见 `fall_detector.py`）。

### 4.2 风险融合

\[
S = w_f S_{fall} + w_e S_{emo} + w_h S_{health}
\]

默认权重 0.45 / 0.25 / 0.30，阈值划分 normal / alert / emergency。

### 4.3 对话与规划

- Mock 离线对话（默认）或 OpenAI 兼容 API
- CarePlanner 根据风险等级生成 RobotAction 序列

## 5. 实验评测

见 [evaluation/METRICS.md](evaluation/METRICS.md)。

- 合成跌倒场景：Precision/Recall/F1 = 100%
- 端到端紧急链路：100% 触发

## 6. 部署方案

见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 7. 创新点总结

1. 多模态可解释风险引擎，非黑盒 LLM
2. 紧急事件硬优先级状态机
3. 仿真—Web—ROS2 统一 Orchestrator
4. 边缘视觉（MediaPipe）+ 离线对话能力

## 8. 不足与展望

- 真机动作视频待补充
- 公开跌倒数据集泛化评测待开展
- 多用户与隐私合规待深化
