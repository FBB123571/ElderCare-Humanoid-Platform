# ROS2 机器人端订阅示例（伪代码）

```python
# 在人形机器人机载电脑上运行
import json
from std_msgs.msg import String

def on_cmd(msg):
    data = json.loads(msg.data)
    if data["command"] == "speak":
        tts_play(data["text"])
    elif data["command"] == "gesture":
        sdk_execute_gesture(data["name"])
    elif data["command"] == "call_emergency":
        notify_family(data["reasons"])
```

话题：`/care/robot_cmd`（`std_msgs/String` JSON）
