from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from care_companion.action.emergency_notifier import EmergencyNotifier
from care_companion.core.events import RobotAction, RobotCommand

logger = logging.getLogger(__name__)


class RobotAdapter(ABC):
  @abstractmethod
  def execute(self, action: RobotAction) -> None: ...

  def shutdown(self) -> None:
    pass


class SimulationAdapter(RobotAdapter):
  """桌面仿真 / 日志输出。"""

  def __init__(self, on_action=None, notifier: EmergencyNotifier | None = None):
    self._on_action = on_action
    self.notifier = notifier or EmergencyNotifier()
    self.history: list[dict] = []

  def execute(self, action: RobotAction) -> None:
    record = {"command": action.command.value, **action.payload}
    self.history.append(record)
    if action.command == RobotCommand.CALL_EMERGENCY:
      rec = self.notifier.trigger(
        action.payload.get("reasons", []),
        {"source": "simulation", **action.payload},
      )
      record["emergency_record"] = rec.__dict__
    logger.info("[SIM] %s", record)
    if self._on_action:
      self._on_action(record)


class ROS2Adapter(RobotAdapter):
  """发布到 /care/robot_cmd，供人形机器人端订阅。"""

  def __init__(self, cfg: dict):
    self._topic = cfg.get("cmd_topic", "/care/robot_cmd")
    self._node = None
    self._pub = None
    try:
      import rclpy
      from rclpy.node import Node
      from std_msgs.msg import String

      if not rclpy.ok():
        rclpy.init()
      self._node = Node("care_companion_bridge")
      self._pub = self._node.create_publisher(String, self._topic, 10)
      self._String = String
      logger.info("ROS2 bridge ready on %s", self._topic)
    except ImportError:
      logger.warning("rclpy 未安装，ROS2Adapter 将退化为日志模式")
    except Exception as e:
      logger.warning("ROS2 初始化失败: %s", e)

  def execute(self, action: RobotAction) -> None:
    payload = {"command": action.command.value, **action.payload}
    text = json.dumps(payload, ensure_ascii=False)
    if self._pub is not None:
      msg = self._String()
      msg.data = text
      self._pub.publish(msg)
      if self._node:
        self._node.spin_once(timeout_sec=0.01)
    logger.info("[ROS2] %s -> %s", self._topic, text)

  def shutdown(self) -> None:
    if self._node is not None:
      self._node.destroy_node()
