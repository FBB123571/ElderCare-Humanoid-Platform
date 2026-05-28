# 老人跌倒样片

将微信导出的原始 mp4 放到本目录，任选文件名：

- `elder_fall_wechat.mp4`（推荐）
- `a42f27767beb9dab9d03d40327faffe3_raw.mp4`

## 从 Windows 复制到服务器

在 **Windows PowerShell**（替换 `user` 与服务器 IP）：

```powershell
scp "C:\Users\刘小凡\xwechat_files\wxid_cuzz2serr6kg22_3950\msg\video\2026-05\a42f27767beb9dab9d03d40327faffe3_raw.mp4" `
  user@<服务器IP>:/mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform/docs/assets/samples/elder_fall_wechat.mp4
```

## 一键分析 + 录屏 + 更新 30s 总片

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
bash scripts/run_elder_fall_demo.sh
# 或指定路径：
.venv/bin/python scripts/process_elder_fall_video.py /path/to/video.mp4
```

输出：

- `docs/assets/demo_elder_fall_analysis.mp4` — 带 MediaPipe 骨架与 FALL ALERT 条
- `docs/assets/elder_fall_analysis.json` — 时间线指标
- `docs/assets/demo_full_scenario.mp4` — 总片 Web 段自动替换为上述分析视频
