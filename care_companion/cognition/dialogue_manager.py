from __future__ import annotations

import os
from abc import ABC, abstractmethod


class DialogueProvider(ABC):
  @abstractmethod
  def reply(self, user_text: str, context: dict) -> str: ...


class MockDialogueProvider(DialogueProvider):
  """离线可运行，答辩/仿真默认。"""

  def reply(self, user_text: str, context: dict) -> str:
    risk = context.get("risk_level", "normal")
    emotion = context.get("emotion", "neutral")
    if risk == "emergency":
      return "检测到紧急情况，我已通知家属并播放告警，请保持冷静，援助正在赶来。"
    if "跌倒" in " ".join(context.get("reasons", [])):
      return "请不要动，我正在确认您的状态，必要时将联系紧急联系人。"
    if emotion in ("sad", "anxious"):
      return "我一直陪着您。要不要听听音乐，或者我帮您联系家人聊聊？"
    if user_text and any(w in user_text for w in ("药", "吃药")):
      return "好的，我已记录用药提醒。请按医嘱服药，如有不适请告诉我。"
    if user_text and any(w in user_text for w in ("你好", "嗨", "在吗")):
      return "您好，我是陪伴机器人 CareCompanion，今天感觉怎么样？"
    return "我在听，您可以告诉我身体感受或需要什么帮助。"


class OpenAICompatibleProvider(DialogueProvider):
  def __init__(self, system_prompt: str):
    self.system_prompt = system_prompt

  def reply(self, user_text: str, context: dict) -> str:
    try:
      from openai import OpenAI
    except ImportError as e:
      raise RuntimeError("pip install openai 后使用 openai_compatible 模式") from e

    client = OpenAI(
      api_key=os.environ.get("OPENAI_API_KEY", ""),
      base_url=os.environ.get("OPENAI_BASE_URL"),
    )
    messages = [
      {"role": "system", "content": self.system_prompt},
      {
        "role": "user",
        "content": f"[context]{context}\n老人说：{user_text}",
      },
    ]
    resp = client.chat.completions.create(
      model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
      messages=messages,
      max_tokens=200,
    )
    return resp.choices[0].message.content.strip()


class DialogueManager:
  def __init__(self, cfg: dict):
    provider = cfg.get("provider", "mock")
    prompt = cfg.get("system_prompt", "")
    if provider == "openai_compatible":
      self._provider: DialogueProvider = OpenAICompatibleProvider(prompt)
    else:
      self._provider = MockDialogueProvider()

  def respond(self, user_text: str | None, context: dict) -> str:
    return self._provider.reply(user_text or "", context)
