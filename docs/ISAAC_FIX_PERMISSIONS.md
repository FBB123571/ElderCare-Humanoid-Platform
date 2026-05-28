# Isaac Sim 权限问题（直播/录屏失败根因）

## 现象

终端里出现：

- `Permission denied: .../isaacsim/kit/cache/...`
- `Permission denied: .../isaacsim/kit/data/Kit/Isaac-Sim/5.1/pip3-envs`
- `Failed to initialize rtx::shaderdb`
- 或 `dependency solver failure`（直播误用 rendering.kit 时）

## 原因

当前 `isaaclab` conda 环境里的 **isaacsim 安装在 `/mnt/sda1/...`，属主为 `yaozq`**，用户 `leijh` 无法写入缓存目录，导致 RTX/直播/录屏异常。

## 一次性修复（需管理员或有 sudo 密码）

在服务器执行：

```bash
sudo chown -R leijh:leijh /mnt/sda1/leijh/miniconda3/envs/isaaclab/lib/python3.11/site-packages/isaacsim/kit/cache
sudo chown -R leijh:leijh /mnt/sda1/leijh/miniconda3/envs/isaaclab/lib/python3.11/site-packages/isaacsim/kit/data
```

然后重新运行：

```bash
cd /mnt/sdb1/leijh/EnergySnake1/robot/ElderCare-Humanoid-Platform
bash scripts/play_g1_livestream.sh
```

## 已修复的脚本问题

- `play_g1_livestream.sh`：强制使用 `isaaclab.python.headless.rendering.kit`（避免联网 extension 校验失败）
- `record_isaac_g1_demo.sh`：录屏锁、Vulkan ICD、PIPESTATUS 异常

## 答辩备选

在权限修好前，请使用 **`docs/assets/demo_carecompanion.mp4`** 作为演示视频。
