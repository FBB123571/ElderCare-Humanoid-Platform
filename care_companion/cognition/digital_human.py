"""数字人陪护：对话人设与情景剧脚本。"""
from __future__ import annotations

from dataclasses import dataclass

from care_companion.core.events import PerceptionFrame


@dataclass
class ActingLine:
  speaker: str  # elder | stage
  text: str | None = None
  frame: PerceptionFrame | None = None
  pause_s: float = 0.0


COMPANION_NAME = "小护"
COMPANION_GREETING = "您好，我是陪伴机器人小护，一直在您身边。"

# 自然交互情景剧：倾诉 → 安抚 → 突发跌倒 → 紧急响应
ACTING_SCRIPT: list[ActingLine] = [
  ActingLine("stage", "【场景】客厅午后，老人独坐沙发", pause_s=0.8),
  ActingLine("elder", "小护啊，这几天老是睡不踏实，心里空落落的。"),
  ActingLine("elder", "孩子们都忙，我也不想总打扰他们…"),
  ActingLine(
    "elder",
    None,
    frame=PerceptionFrame(
      user_text="就是有点孤单",
      emotion="sad",
      heart_rate=78,
      activity_level=0.15,
    ),
  ),
  ActingLine("stage", "【转折】老人起身时不稳", pause_s=1.0),
  ActingLine(
    "elder",
    "哎哟——！",
    frame=PerceptionFrame(
      skeleton_aspect_ratio=0.32,
      skeleton_dy=-0.85,
      activity_level=0.04,
      emotion="anxious",
      heart_rate=102,
      fall_detected=True,
      fall_score=0.96,
    ),
  ),
  ActingLine(
    "elder",
    None,
    frame=PerceptionFrame(
      skeleton_aspect_ratio=0.28,
      skeleton_dy=0.0,
      activity_level=0.02,
      emotion="anxious",
      heart_rate=108,
      fall_detected=True,
      fall_score=0.98,
      user_text="",
    ),
  ),
  ActingLine("stage", "【系统】风险融合 → 紧急指令下发", pause_s=0.6),
]


def companion_avatar_state(risk_level: str, emotion: str) -> str:
  if risk_level == "emergency":
    return "emergency"
  if risk_level == "alert":
    return "alert"
  if emotion in ("sad", "anxious", "happy", "neutral"):
    return emotion
  return "neutral"


MOOD_LABEL_ZH = {
  "neutral": "平静",
  "happy": "开心",
  "sad": "低落",
  "anxious": "焦虑",
}

# 老人台词池：按检测到的情绪轮换，配合视频心情轨迹「演戏」
ELDER_MOOD_UTTERANCES: dict[str, list[str]] = {
  "neutral": [
    "小护，我就坐一会儿，也没什么大事。",
    "嗯…今天就这样吧。",
  ],
  "happy": [
    "今天阳光挺好，心里也暖和多了。",
    "小护，跟你说话挺踏实的。",
  ],
  "sad": [
    "小护啊，这几天心里空落落的…",
    "睡也睡不踏实，孩子们都忙。",
    "就是有点孤单，不想总打扰他们。",
  ],
  "anxious": [
    "心里扑通扑通的，有点不踏实。",
    "总觉得要出什么事似的…",
  ],
}


def compress_emotion_timeline(timeline: list[dict], max_segments: int = 5) -> list[dict]:
  """按情绪变化切分关键片段，供情景剧对白。"""
  if not timeline:
    return [{"t_s": 0.0, "emotion": "neutral", "scores": {}}]

  segments: list[dict] = []
  prev: str | None = None
  for item in timeline:
    emo = item.get("emotion", "neutral")
    if emo != prev:
      segments.append(item)
      prev = emo
    if len(segments) >= max_segments:
      break

  if len(segments) < 2:
    step = max(1, len(timeline) // max_segments)
    segments = [timeline[i] for i in range(0, len(timeline), step)][:max_segments]

  return segments or [timeline[0]]


def build_mood_script_from_analysis(analysis: dict) -> list[ActingLine]:
  """由视频心情分析结果生成老人↔小护互动脚本。"""
  emo = analysis.get("emotion") or {}
  fall = analysis.get("fall") or {}
  dominant = emo.get("dominant", "neutral")
  timeline = emo.get("timeline") or []
  duration_s = analysis.get("duration_s", 0)

  lines: list[ActingLine] = [
    ActingLine(
      "stage",
      f"【场景】视频心情分析 · 时长约 {duration_s}s · 主情绪「{MOOD_LABEL_ZH.get(dominant, dominant)}」",
      pause_s=0.7,
    ),
    ActingLine("stage", "【旁白】小护观看画面中的姿态与活动，与老人自然交谈", pause_s=0.5),
  ]

  segments = compress_emotion_timeline(timeline, max_segments=5)
  utter_idx: dict[str, int] = {}

  for seg in segments:
    em = seg.get("emotion", "neutral")
    t_s = seg.get("t_s", 0.0)
    pool = ELDER_MOOD_UTTERANCES.get(em, ELDER_MOOD_UTTERANCES["neutral"])
    idx = utter_idx.get(em, 0)
    text = pool[idx % len(pool)]
    utter_idx[em] = idx + 1

    aspect = 1.05
    dy = 0.0
    activity = 0.22
    hr = 76
    if em == "sad":
      aspect, activity, hr = 0.82, 0.14, 78
    elif em == "anxious":
      aspect, dy, activity, hr = 0.78, -0.15, 0.18, 88
    elif em == "happy":
      aspect, activity = 1.1, 0.35

    lines.append(
      ActingLine(
        "stage",
        f"【画面 t≈{t_s}s】情绪 → {MOOD_LABEL_ZH.get(em, em)}",
        pause_s=0.35,
      )
    )
    lines.append(
      ActingLine(
        "elder",
        text,
        frame=PerceptionFrame(
          user_text=text,
          emotion=em,
          heart_rate=hr,
          activity_level=activity,
          skeleton_aspect_ratio=aspect,
          skeleton_dy=dy,
        ),
      )
    )

  if fall.get("detected"):
    t_fall = fall.get("first_alert_t_s")
    lines.append(
      ActingLine(
        "stage",
        f"【转折】视频 t≈{t_fall}s 检测到跌倒 · 置信 {fall.get('max_score', 0):.2f}",
        pause_s=0.8,
      )
    )
    lines.append(
      ActingLine(
        "elder",
        "哎哟——！",
        frame=PerceptionFrame(
          skeleton_aspect_ratio=0.32,
          skeleton_dy=-0.85,
          activity_level=0.04,
          emotion="anxious",
          heart_rate=102,
          fall_detected=True,
          fall_score=float(fall.get("max_score") or 0.9),
          user_text="",
        ),
      )
    )
    lines.append(ActingLine("stage", "【系统】风险融合 → 小护紧急安抚与指令下发", pause_s=0.5))

  lines.append(ActingLine("stage", "【幕落】视频心情陪护交流结束", pause_s=0.3))
  return lines
