from __future__ import annotations

import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from care_companion.perception.fall_detector import FallDetector, FallResult

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "data" / "models" / "pose_landmarker_lite.task"
MODEL_URL = (
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
  "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

_LEGACY_POSE = None
_TASKS_LANDMARKER = None


@dataclass
class PoseMetrics:
  aspect_ratio: float
  dy: float
  visible: bool
  landmarks_norm: np.ndarray | None


def _model_path(fall_cfg: dict) -> Path:
  raw = fall_cfg.get("mediapipe_model") or fall_cfg.get("pose_model")
  return Path(raw) if raw else DEFAULT_MODEL_PATH


def _urlopen_no_proxy(req: urllib.request.Request, timeout: int = 120):
  """绕过失效的 HTTP_PROXY（如 127.0.0.1:17897）。"""
  opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
  return opener.open(req, timeout=timeout)


def ensure_pose_model(path: Path | None = None) -> Path:
  """确保本地存在 MediaPipe Tasks 模型文件。"""
  target = path or DEFAULT_MODEL_PATH
  if target.is_file() and target.stat().st_size > 100_000:
    return target
  target.parent.mkdir(parents=True, exist_ok=True)
  logger.info("正在下载 MediaPipe 姿态模型 → %s", target)
  req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "CareCompanion/1.0"})
  with _urlopen_no_proxy(req) as resp, open(target, "wb") as f:
    f.write(resp.read())
  if target.stat().st_size < 100_000:
    target.unlink(missing_ok=True)
    raise RuntimeError("姿态模型下载失败，请运行: bash scripts/download_mediapipe_models.sh")
  return target


def _ensure_legacy_pose():
  global _LEGACY_POSE
  if _LEGACY_POSE is not None:
    return True
  try:
    import mediapipe as mp

    if not hasattr(mp, "solutions"):
      return False
    _LEGACY_POSE = mp.solutions.pose.Pose(
      static_image_mode=True,
      model_complexity=1,
      enable_segmentation=False,
      min_detection_confidence=0.5,
      min_tracking_confidence=0.5,
    )
    return True
  except Exception as exc:
    logger.debug("legacy mediapipe pose 不可用: %s", exc)
    return False


def _ensure_tasks_landmarker(model_path: Path):
  global _TASKS_LANDMARKER
  if _TASKS_LANDMARKER is not None:
    return True
  if not model_path.is_file():
    return False
  try:
    import mediapipe as mp
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

    opts = PoseLandmarkerOptions(
      base_options=BaseOptions(model_asset_path=str(model_path.resolve())),
      running_mode=RunningMode.IMAGE,
      min_pose_detection_confidence=0.5,
      min_pose_presence_confidence=0.5,
      min_tracking_confidence=0.5,
    )
    _TASKS_LANDMARKER = PoseLandmarker.create_from_options(opts)
    return True
  except Exception as exc:
    logger.warning("MediaPipe Tasks Pose 初始化失败: %s", exc)
    return False


def _draw_tasks_pose(image_bgr: np.ndarray, landmarks) -> np.ndarray:
  from mediapipe.tasks.python.vision import PoseLandmarksConnections, drawing_utils

  annotated = image_bgr.copy()
  drawing_utils.draw_landmarks(
    annotated,
    landmarks,
    PoseLandmarksConnections.POSE_LANDMARKS,
    drawing_utils.DrawingSpec(color=(0, 220, 120), thickness=2, circle_radius=2),
    drawing_utils.DrawingSpec(color=(80, 160, 255), thickness=2, circle_radius=1),
  )
  return annotated


def _landmarks_to_array(landmarks) -> np.ndarray:
  pts = []
  for p in landmarks:
    vis = getattr(p, "visibility", None)
    if vis is not None and vis < 0.5:
      continue
    pts.append([p.x, p.y])
  return np.array(pts, dtype=np.float32) if pts else np.empty((0, 2))


class PosePipeline:
  """MediaPipe 姿态 → 跌倒几何特征（兼容 solutions 与 Tasks API）。"""

  def __init__(self, fall_cfg: dict):
    self._fall_cfg = fall_cfg
    self.fall = FallDetector(fall_cfg)
    self._prev_center_y: float | None = None
    self._model_path = _model_path(fall_cfg)
    self._backend: str | None = None

  def reset(self) -> None:
    self.fall = FallDetector(self._fall_cfg)
    self._prev_center_y = None

  def mediapipe_ready(self) -> bool:
    if _ensure_legacy_pose():
      return True
    return _ensure_tasks_landmarker(self._model_path)

  def metrics_from_landmarks(self, landmarks_norm: np.ndarray, dt: float = 0.1) -> PoseMetrics:
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

  def _analyze_legacy(self, image_bgr: np.ndarray, dt: float) -> tuple[PoseMetrics, FallResult, np.ndarray | None]:
    import mediapipe as mp

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    result = _LEGACY_POSE.process(rgb)
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
    mp.solutions.drawing_utils.draw_landmarks(
      annotated,
      result.pose_landmarks,
      mp.solutions.pose.POSE_CONNECTIONS,
    )
    self._backend = "legacy"
    return metrics, fall_r, annotated

  def _analyze_tasks(self, image_bgr: np.ndarray, dt: float) -> tuple[PoseMetrics, FallResult, np.ndarray | None]:
    import mediapipe as mp

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = _TASKS_LANDMARKER.detect(mp_image)
    annotated = image_bgr.copy()
    if not result.pose_landmarks:
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "未检测到人体"),
        annotated,
      )
    landmarks = result.pose_landmarks[0]
    pts = _landmarks_to_array(landmarks)
    if len(pts) < 4:
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "关键点不足（请包含肩、髋、手臂）"),
        annotated,
      )
    metrics = self.metrics_from_landmarks(pts, dt)
    fall_r = self.fall.from_metrics(metrics.aspect_ratio, metrics.dy, dt)
    annotated = _draw_tasks_pose(annotated, landmarks)
    self._backend = "tasks"
    return metrics, fall_r, annotated

  def analyze_bgr(self, image_bgr: np.ndarray, dt: float = 0.1) -> tuple[PoseMetrics, FallResult, np.ndarray | None]:
    if _ensure_legacy_pose():
      return self._analyze_legacy(image_bgr, dt)

    model_path = self._model_path
    if not model_path.is_file():
      try:
        ensure_pose_model(model_path)
      except Exception as exc:
        logger.warning("自动下载姿态模型失败: %s", exc)
        return (
          PoseMetrics(1.1, 0.0, False, None),
          FallResult(0.0, False, "缺少姿态模型：在终端执行 bash scripts/download_mediapipe_models.sh"),
          image_bgr.copy(),
        )

    if not _ensure_tasks_landmarker(model_path):
      return (
        PoseMetrics(1.1, 0.0, False, None),
        FallResult(0.0, False, "MediaPipe 姿态模块初始化失败"),
        image_bgr.copy(),
      )

    return self._analyze_tasks(image_bgr, dt)

  def decode_upload(self, raw: bytes) -> np.ndarray | None:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img
