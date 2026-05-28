from care_companion.perception.video_analyzer import _emotion_from_metrics


def test_emotion_fall_like():
  scores = _emotion_from_metrics(aspect=0.4, dy=-0.5, motion=0.2)
  assert scores["anxious"] > scores["happy"]


def test_emotion_calm():
  scores = _emotion_from_metrics(aspect=1.0, dy=0.0, motion=0.05)
  assert sum(scores.values()) == 1.0
