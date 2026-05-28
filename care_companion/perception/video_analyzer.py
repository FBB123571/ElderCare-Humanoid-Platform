"""对视频逐帧做姿态/跌倒与情绪启发式分析。"""
from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np

from care_companion.perception.emotion_recognizer import EmotionRecognizer
from care_companion.perception.pose_pipeline import PosePipeline


def _encode_jpeg_bgr(img: np.ndarray, quality: int = 82) -> str:
  _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
  return base64.b64encode(buf).decode("ascii")


def _emotion_from_metrics(aspect: float, dy: float, motion: float) -> dict[str, float]:
  """轻量启发式：由姿态与运动推断情绪分布（非人脸识别）。"""
  scores = {"neutral": 0.25, "happy": 0.1, "sad": 0.15, "anxious": 0.15}
  if motion > 0.35:
    scores["anxious"] += 0.35
    scores["neutral"] -= 0.1
  if aspect < 0.55:
    scores["sad"] += 0.25
    scores["anxious"] += 0.2
  if dy < -0.25:
    scores["anxious"] += 0.3
  if motion < 0.08 and aspect > 0.85:
    scores["sad"] += 0.2
    scores["neutral"] += 0.15
  if motion < 0.05 and 0.7 < aspect < 1.2:
    scores["happy"] += 0.15
  total = sum(max(0.0, v) for v in scores.values()) or 1.0
  return {k: max(0.0, v) / total for k, v in scores.items()}


class VideoAnalyzer:
  def __init__(self, cfg: dict):
    self.pose = PosePipeline(cfg.get("fall", {}))
    self.fall_cfg = cfg.get("fall", {})
    self.emotion = EmotionRecognizer(cfg.get("emotion", {}))

  def analyze_file(
    self,
    path: Path,
    *,
    max_frames: int = 150,
    frame_stride: int = 2,
    sample_fps: float = 8.0,
  ) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
      return {"ok": False, "error": "无法打开视频文件"}

    native_fps = cap.get(cv2.CAP_PROP_FPS) or sample_fps
    if native_fps <= 0:
      native_fps = sample_fps
    dt = (frame_stride / native_fps) if native_fps > 0 else 0.1

    self.pose.reset()
    timeline: list[dict] = []
    emotion_timeline: list[dict] = []
    centers: list[float] = []

    idx = 0
    read_i = 0
    best_fall = {"score": 0.0, "detected": False, "frame_i": -1, "preview_b64": None}
    dominant_emotion = "neutral"
    max_emotion_scores = {"neutral": 1.0}

    while idx < max_frames:
      ok, frame = cap.read()
      if not ok:
        break
      if read_i % frame_stride != 0:
        read_i += 1
        continue
      read_i += 1

      metrics, fall_r, annotated = self.pose.analyze_bgr(frame, dt=dt)
      motion = 0.0
      if centers:
        motion = abs(centers[-1] - metrics.dy) if metrics.visible else 0.0
      if metrics.visible:
        centers.append(metrics.dy)

      emo_scores = _emotion_from_metrics(metrics.aspect_ratio, metrics.dy, motion)
      dom = max(emo_scores, key=emo_scores.get)
      for k, v in emo_scores.items():
        max_emotion_scores[k] = max_emotion_scores.get(k, 0.0) + v

      t_s = round(idx * dt, 2)
      timeline.append({
        "t_s": t_s,
        "frame_index": idx,
        "aspect_ratio": round(metrics.aspect_ratio, 3),
        "dy": round(metrics.dy, 3),
        "visible": metrics.visible,
        "fall_detected": fall_r.detected,
        "fall_score": round(fall_r.score, 3),
      })
      emotion_timeline.append({"t_s": t_s, "emotion": dom, "scores": {k: round(v, 3) for k, v in emo_scores.items()}})

      if fall_r.score >= best_fall["score"]:
        best_fall = {
          "score": fall_r.score,
          "detected": fall_r.detected,
          "frame_i": idx,
          "preview_b64": _encode_jpeg_bgr(annotated) if annotated is not None else None,
          "reason": fall_r.reason,
        }

      idx += 1

    cap.release()
    frame_count = idx
    duration_s = round(frame_count * dt, 2) if frame_count else 0.0

    if frame_count == 0:
      return {"ok": False, "error": "视频无有效帧"}

    total_emo = sum(max_emotion_scores.values()) or 1.0
    avg_emo = {k: v / total_emo for k, v in max_emotion_scores.items()}
    dominant_emotion = max(avg_emo, key=avg_emo.get)

    first_fall_t = next((x["t_s"] for x in timeline if x["fall_detected"]), None)
    any_fall = best_fall["detected"] or first_fall_t is not None

    return {
      "ok": True,
      "frames_analyzed": frame_count,
      "duration_s": duration_s,
      "dt": round(dt, 3),
      "fall": {
        "detected": any_fall,
        "max_score": round(best_fall["score"], 3),
        "first_alert_t_s": first_fall_t,
        "best_frame_index": best_fall["frame_i"],
        "preview_jpeg_b64": best_fall["preview_b64"],
        "reason": best_fall.get("reason"),
        "timeline": timeline[-40:],
      },
      "emotion": {
        "dominant": dominant_emotion,
        "scores": {k: round(v, 3) for k, v in avg_emo.items()},
        "timeline": emotion_timeline[-40:],
        "fused_label": self.emotion.fuse(dominant_emotion, None).label,
      },
    }
