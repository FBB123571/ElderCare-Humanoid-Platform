# 评测指标

## 跌倒检测（合成场景）

评测脚本：`python scripts/eval_fall_detection.py`  
场景定义：`data/evaluation/fall_scenarios.yaml`

| 指标 | 数值 |
|------|------|
| 场景数 | 6 |
| Precision | **100%** |
| Recall | **100%** |
| F1 | **100%** |
| Accuracy | **100%** |

### 场景说明

| 场景 | 标签 | 说明 |
|------|------|------|
| standing_normal | normal | 站立 |
| walking_normal | normal | 行走 |
| sit_down | near_fall | 坐下（易误报，当前未触发） |
| sudden_fall | fall | 快速跌倒 |
| lying_still | fall | 躺倒静止 |
| bend_pickup | near_fall | 弯腰捡物 |

### 算法要点

- 快速下落 + 躺倒姿态融合
- **躺倒静止 ≥2s** 触发慢速跌倒（养老场景）

## 端到端紧急链路

`run_headless_demo.py`：演示剧本 **100%** 触发 `call_emergency`。

## 响应时延

单帧 `CareOrchestrator.tick` 在 CPU 上通常 **< 50ms**（无大模型 API 调用）。

## 视觉感知

- MediaPipe Pose 提取骨架
- Web 端浏览器摄像头 → `/api/vision/analyze`
- 本地演示：`python scripts/run_camera_demo.py`

## 待实机补充

- 人形机器人动作执行视频
- 公开跌倒数据集（UR Fall 等）泛化评测
- 多房间 / 遮挡场景
