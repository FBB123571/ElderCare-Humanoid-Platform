"""视频心情 → 数字人情景剧脚本。"""
from care_companion.cognition.digital_human import (
  build_mood_script_from_analysis,
  compress_emotion_timeline,
)


def test_compress_emotion_timeline_changes():
  tl = [
    {"t_s": 0, "emotion": "neutral"},
    {"t_s": 1, "emotion": "neutral"},
    {"t_s": 2, "emotion": "sad"},
    {"t_s": 3, "emotion": "anxious"},
  ]
  seg = compress_emotion_timeline(tl, max_segments=5)
  emotions = [s["emotion"] for s in seg]
  assert emotions[0] == "neutral"
  assert "sad" in emotions
  assert "anxious" in emotions


def test_build_mood_script_includes_fall():
  analysis = {
    "duration_s": 8.0,
    "emotion": {
      "dominant": "anxious",
      "timeline": [
        {"t_s": 0, "emotion": "neutral"},
        {"t_s": 3, "emotion": "anxious"},
      ],
    },
    "fall": {"detected": True, "max_score": 0.8, "first_alert_t_s": 3.0},
  }
  script = build_mood_script_from_analysis(analysis)
  texts = [ln.text for ln in script if ln.text]
  assert any("哎哟" in t for t in texts)
  assert any("跌倒" in t for t in texts)
