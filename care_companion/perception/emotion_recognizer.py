from __future__ import annotations

from dataclasses import dataclass


POSITIVE = {"开心", "高兴", "好", "谢谢", "舒服", "不错"}
NEGATIVE = {"难受", "疼", "害怕", "孤独", "烦", "累", "伤心", "抑郁"}


@dataclass
class EmotionResult:
  label: str
  score: float
  source: str


class EmotionRecognizer:
  """多模态情绪：文本情感 + 可选视觉标签（仿真注入）。"""

  def fuse(self, visual: str | None, text: str | None) -> EmotionResult:
    v_label, v_score = self._from_visual(visual)
    t_label, t_score = self._from_text(text)

    if t_score >= v_score:
      return EmotionResult(t_label, t_score, "text")
    return EmotionResult(v_label, v_score, "visual")

  def _from_visual(self, visual: str | None) -> tuple[str, float]:
    if not visual:
      return "neutral", 0.3
    mapping = {
      "happy": ("happy", 0.85),
      "sad": ("sad", 0.85),
      "anxious": ("anxious", 0.8),
      "neutral": ("neutral", 0.5),
    }
    return mapping.get(visual, ("neutral", 0.5))

  def _from_text(self, text: str | None) -> tuple[str, float]:
    if not text:
      return "neutral", 0.25
    for w in NEGATIVE:
      if w in text:
        return "sad", 0.9
    for w in POSITIVE:
      if w in text:
        return "happy", 0.85
    return "neutral", 0.4
