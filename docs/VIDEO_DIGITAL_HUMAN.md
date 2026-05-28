# 网络视频分析 · 数字人剧场

## 1. 网络视频 · 跌倒检测与预警

- 在 Web 控制台底部 **「网络视频分析」** 粘贴 **mp4 直链** 或上传文件
- 点击 **「分析并跌倒预警」**：逐帧 MediaPipe + 跌倒规则
- 若检测到跌倒：展示关键帧 + **自动触发 Orchestrator 紧急决策**（`call_emergency` 等）

推荐样片按钮来自 `config/video_samples.yaml`（公开测试片，**请替换为真实跌倒片段** 用于答辩）。

## 2. 网络视频 · 心情分析

- 切换 **「心情分析」** 标签，点击 **「分析心情轨迹」**
- 基于 **运动幅度 + 姿态宽高比 + 垂直速度** 的启发式情绪分布（非人脸表情识别）
- 结果同步到左侧情绪选择与数字人表情状态

## 3. 心情 · 数字人剧场（视频联动）

在 Web「网络视频分析」→ 标签 **「心情 · 数字人剧场」**：

1. 上传或选择样片（如 `docs/assets/samples/elder_fall_wechat.mp4`）
2. 点击 **「分析心情并开演」** → 先跑情绪轨迹，再按时间线自动演老人↔小护对话
3. **「重播心情剧」** 可仅重播对话（需已完成一次分析）

API：`GET /api/digital_human/mood_act`（SSE，依赖最近一次 `/api/video/analyze` 结果）

脚本生成：`care_companion/cognition/digital_human.py` → `build_mood_script_from_analysis`

## 4. 数字人陪护剧场（经典剧本）

- **发送对话**：老人话语 → 小护（Orchestrator + Mock/LLM）回复，头像随风险/情绪变化
- **开始情景剧**：SSE 演绎「倾诉 → 安抚 → 跌倒 → 紧急」完整剧本，与主仪表盘联动

## API

| 接口 | 说明 |
|------|------|
| `POST /api/video/analyze` | `mode=fall\|emotion\|both`，`url` 或 `file` |
| `GET /api/video/samples` | 推荐样片列表 |
| `POST /api/digital_human/chat` | 数字人单轮对话 |
| `GET /api/digital_human/act` | 情景剧 SSE |

## 启动

```bash
bash scripts/run_web.sh
# http://localhost:8765
```
