# CareCompanion 答辩 PPT — 待办清单

## 已完成

- [x] 6 张 Web 截图已放入 `docs/assets/ppt_*.png`
- [x] `tools/generate_presentation.py` 已自动插入截图页
- [x] Web 演示录屏 `docs/assets/demo_carecompanion.mp4`
- [x] Isaac G1 行走录屏 `docs/assets/demo_isaac_g1_locomotion.mp4`（2026-05-28）
- [x] PPT 嵌入双演示视频页 + 海报帧 `ppt_isaac_g1_poster.png`
- [x] 进度规划 `docs/答辩进度规划.md`
- [x] 输出文件：`docs/答辩_CareCompanion.pptx`（约 30 页，以生成脚本为准）

### 截图与幻灯片对应

| 文件 | 幻灯片标题 |
|------|------------|
| `ppt_emotion_input.png` | （界面）情感倾诉交互 |
| `ppt_full_dashboard.png` | 系统界面：老人倾诉场景 |
| `ppt_risk_panel.png` | 系统界面：风险决策仪表盘 |
| `ppt_header_perception.png` | 系统界面：紧急状态监测 |
| `ppt_chat_emergency.png` | 系统界面：跌倒紧急对话日志 |
| `ppt_robot_commands.png` | 系统界面：机器人指令流 |

重新生成 PPT：

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
python tools/generate_presentation.py
```

---

## 仍需你补充（建议优先级）

### 高优先级（答辩前必做）

1. **填写封面信息**  
   打开 `docs/答辩_CareCompanion.pptx`，修改：团队名称、学校、指导教师、队员、日期。

2. **软著 / 知识产权**  
   在「开源与知识产权」页填写软著登记号（若已申请）；无则写「申请中」并附材料截图。

3. **MediaPipe 骨架截图**（当前摄像头区域为黑屏）  
   - 启动：`bash scripts/run_web.sh`  
   - 浏览器打开 `http://localhost:8765`（Cursor 端口转发 8765）  
   - 点击「打开摄像头」→「分析当前帧」  
   - 截一张带骨架叠加的画面，保存为 `docs/assets/ppt_mediapipe_pose.png`  
   - 在 `tools/generate_presentation.py` 的 Web 小节增加一页 `_screenshot_slide(..., "ppt_mediapipe_pose.png", ...)` 后重新生成。

4. **演示视频 + 二维码**  
   - 录屏 3–5 分钟：日常监测 → 老人倾诉 → 模拟跌倒 → 紧急流程  
   - 上传 B 站 / 网盘 / GitHub Release  
   - 用 [草料二维码](https://cli.im/) 生成二维码图片 → `docs/assets/ppt_demo_qr.png`  
   - 在 PPT「致谢」前加一页「现场演示 / 扫码观看」。

### 中优先级（冲国奖加分）

5. **跌倒场景全屏截图**  
   运行「模拟跌倒」剧本后，风险仪表盘显示 **紧急** 且分数升高时截一张，命名 `ppt_fall_emergency.png`。

6. **真机 / 仿真视频**  
   - [x] Isaac G1 已录：`docs/assets/demo_isaac_g1_locomotion.mp4`（PPT 已嵌入）  
   - [ ] 可选：Unitree 实拍 30 秒「举手 + 语音」替换或补充

7. **对比实验一页**  
   若有时间：纯规则 vs 融合引擎的误报/漏报对比表（可用现有 `fall_eval_report.json`）。

### 低优先级 / 现场准备

8. **答辩话术**  
   对照 `docs/COMPETITION.md` 练 8–10 分钟：问题背景 → 创新 → 演示 → 评测 → 展望。

9. **现场环境**  
   - 笔记本 + 热点备用  
   - 提前 `run_web.sh`，确认 8765 端口转发  
   - 备用：无网时用无头剧本 `bash scripts/run_headless.sh`

10. **推送到 GitHub**（可选）  
    ```bash
    git add docs/assets docs/答辩_CareCompanion.pptx tools/generate_presentation.py docs/PPT_待办清单.md
    git commit -m "docs: embed Web screenshots in defense PPT"
    git -c http.proxy= -c https.proxy= push
    ```

---

## 截图操作速查

```bash
# 1. 启动 Web
bash scripts/run_web.sh

# 2. 本机浏览器（SSH 需在 Cursor Ports 里转发 8765）
# http://localhost:8765

# 3. 演示顺序
# 日常监测 → 老人倾诉（单步推理）→ 运行演示剧本 → 模拟跌倒

# 4. 新截图放入 docs/assets/ 后重新生成 PPT
python tools/generate_presentation.py
```

如有新截图，按 `ppt_描述.png` 命名并告知，可继续写入生成脚本。
