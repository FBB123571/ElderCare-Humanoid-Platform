from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from care_companion.perception.fall_detector import FallDetector, FallResult

logger = logging.getLogger(__name__)

_MP = None
_POSE = None


def _ensure_mediapipe():
  global _MP, _POSE
  if _POSE is not None:
    return True
  try:
    import mediapipe as mp

    _MP = mp
    _POSE = mp.solutions.pose.Pose(
      static_image_mode=True,
      model_complexity=1,
      enable_segmentation=False,
      min_detection_confidence=0.5,
      min_tracking_confidence=0.5,
    )
    return True
  except ImportError:
    logger.warning("mediapipe 未安装，视觉分析不可用。pip install mediapipe")
    return False


@dataclass
class PoseMetrics:
  aspect_ratio: float
  dy: float
  visible: bool
  landmarks_norm: np.ndarray | None


class PosePipeline:
  """MediaPipe 姿态 → 跌倒几何特征。"""

  def __init__(self, fall_cfg: dict):
    self._fall_cfg = fall_cfg
    self.fall = FallDetector(fall_cfg)
    self._prev_center_y: float | None = None

  def reset(self) -> None:
    self.fall = FallDetector(self._fall_cfg)
    self._prev_center_y = None

  def metrics_from_landmarks(self, landmarks_norm: np.ndarray, dt: float = 0.1) -> PoseMetrics:
    """landmarks_norm: (N, 2) 归一化 x,y。"""
    ys = landmarks_norm[:, 1]
    xs = landmarks_norm[:, 0]
    h = max(float(ys.max() - ys.min()), 1e-3)
    w = max(float(xs.max() - xs.min()), 1e-3)
    aspect = w / h
    cy = float(ys.mean())
    dy = 0.0
    if self._prev_center_y is not None and dt > 0:
      dy = (cy - self._prev_center_y) / dt
    self._prev_center_y = cy
    return PoseMetrics(aspect_ratio=aspect, dy=dy, visible=True, landmarks_norm=landmarks_norm)

  def analyze_bgr(self, image_bgr: np.ndarray, dt: float = 0.1) -> tuple[PoseMetrics, FallResult, np.ndarray | None]:
    if not _ensure_mediapipe():
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "mediapipe 未安装"),
        None,
      )

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    result = _POSE.process(rgb)
    annotated = image_bgr.copy()

    if not result.pose_landmarks:
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "未检测到人体"),
        annotated,
      )

    lm = result.pose_landmarks.landmark
    pts = np.array([[p.x, p.y] for p in lm if p.visibility > 0.5])
    if len(pts) < 4:
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "关键点不足"),
        annotated,
      )

    metrics = self.metrics_from_landmarks(pts, dt)
    fall_r = self.fall.from_metrics(metrics.aspect_ratio, metrics.dy, dt)

    import mediapipe as mp

    mp.solutions.drawing_utils.draw_landmarks(
      annotated,
      result.pose_landmarks,
      mp.solutions.pose.POSE_CONNECTIONS,
    )
    return metrics, fall_r, annotated

  def decode_upload(self, raw: bytes) -> np.ndarray | None:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img
