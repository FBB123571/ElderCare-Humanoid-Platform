from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FallResult:
  score: float
  detected: bool
  reason: str


class FallDetector:
  """基于骨架几何与运动学的跌倒检测（可接 MediaPipe 关键点）。"""

  def __init__(self, cfg: dict):
    self.aspect_lying = cfg.get("aspect_ratio_lying", 0.55)
    self.velocity_th = cfg.get("velocity_threshold", 0.35)
    self.still_seconds = cfg.get("still_seconds", 2.0)
    self._prev_dy = 0.0
    self._still_time = 0.0

  def update(self, aspect_ratio: float, dy: float, dt: float) -> FallResult:
    fast_drop = dy < -self.velocity_th
    lying = aspect_ratio < self.aspect_lying

    if lying and abs(dy) < 0.05:
      self._still_time += dt
    else:
      self._still_time = 0.0

    score = 0.0
    reasons: list[str] = []
    if fast_drop:
      score += 0.45
      reasons.append("快速下落")
    if lying:
      score += 0.35
      reasons.append("躺倒姿态")
    if self._still_time >= self.still_seconds:
      score += 0.2
      reasons.append("倒地后静止")

    # 快速跌倒：高分 + 下落/躺倒；慢速倒地：躺倒且静止超过阈值（养老场景常见）
    detected = score >= 0.7 and (lying or fast_drop)
    if lying and self._still_time >= self.still_seconds:
      detected = score >= 0.55
    self._prev_dy = dy
    reason = "、".join(reasons) if reasons else "正常"
    return FallResult(score=min(score, 1.0), detected=detected, reason=reason)

  def from_metrics(self, aspect_ratio: float, dy: float, dt: float) -> FallResult:
    """仿真/真机直接注入宽高比与垂直速度（每秒）。"""
    return self.update(aspect_ratio, dy, dt)

  def from_pose_landmarks(self, landmarks: np.ndarray | None, dt: float) -> FallResult:
    """landmarks: (N, 2) 归一化坐标，无相机时由仿真注入。"""
    if landmarks is None or len(landmarks) < 2:
      return FallResult(0.0, False, "无姿态")
    ys = landmarks[:, 1]
    xs = landmarks[:, 0]
    h = max(float(ys.max() - ys.min()), 1e-3)
    w = max(float(xs.max() - xs.min()), 1e-3)
    aspect = w / h
    dy = float(ys.mean() - getattr(self, "_prev_y", ys.mean()))
    self._prev_y = float(ys.mean())
    return self.update(aspect, dy / max(dt, 1e-3), dt)
