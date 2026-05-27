from __future__ import annotations

from care_companion.core.events import RobotAction, RobotCommand


class CarePlanner:
  """主动照护：根据风险与状态生成机器人动作序列。"""

  def plan(
    self,
    risk_level: str,
    reasons: list[str],
    reply_text: str | None,
  ) -> list[RobotAction]:
    actions: list[RobotAction] = []

    if risk_level == "emergency":
      actions.extend([
        RobotAction(RobotCommand.ALERT_SOUND, {"level": "high"}),
        RobotAction(RobotCommand.SPEAK, {"text": reply_text or "紧急告警，已联系家属。"}),
        RobotAction(RobotCommand.CALL_EMERGENCY, {"reasons": reasons}),
        RobotAction(RobotCommand.GESTURE, {"name": "raise_hand"}),
      ])
      return actions

    if risk_level == "alert":
      actions.append(RobotAction(RobotCommand.SPEAK, {"text": reply_text or "请注意身体状态。"}))
      actions.append(RobotAction(RobotCommand.GESTURE, {"name": "nod"}))
      if "长时间无活动" in reasons:
        actions.append(RobotAction(RobotCommand.APPROACH, {"distance_m": 1.2}))
      return actions

    if reply_text:
      actions.append(RobotAction(RobotCommand.SPEAK, {"text": reply_text}))
      actions.append(RobotAction(RobotCommand.GESTURE, {"name": "wave"}))
      return actions

    return actions
