from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
  sys.path.insert(0, str(_ROOT))

import customtkinter as ctk

from care_companion.action.robot_adapter import SimulationAdapter
from care_companion.core.config import load_config
from care_companion.core.events import PerceptionFrame
from care_companion.core.orchestrator import CareOrchestrator
from simulation.scenarios import demo_scenarios


class CareCompanionApp(ctk.CTk):
  def __init__(self):
    super().__init__()
    self.title("CareCompanion · 智能养老人形陪伴机器人仿真")
    self.geometry("1100x720")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    cfg = load_config()
    self._adapter = SimulationAdapter(on_action=self._on_robot_action)
    self._orch = CareOrchestrator(cfg, self._adapter)
    self._running = False

    self._build_ui()
    self._append_log("系统就绪。可点击「运行演示剧本」或手动发送老人话语。")

  def _build_ui(self):
    self.grid_columnconfigure(1, weight=1)
    self.grid_rowconfigure(0, weight=1)

    left = ctk.CTkFrame(self, width=320)
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    ctk.CTkLabel(left, text="感知输入", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=8)

    self.hr = self._slider(left, "心率", 40, 140, 72)
    self.spo2 = self._slider(left, "血氧", 85, 100, 98)
    self.activity = self._slider(left, "活动量", 0, 100, 40)
    self.aspect = self._slider(left, "姿态宽高比×100", 20, 150, 110)
    self.dy = self._slider(left, "垂直速度×100", -100, 50, 0)

    ctk.CTkLabel(left, text="情绪(视觉)").pack(anchor="w", padx=12)
    self.emotion_var = ctk.StringVar(value="neutral")
    ctk.CTkOptionMenu(
      left, values=["neutral", "happy", "sad", "anxious"], variable=self.emotion_var
    ).pack(fill="x", padx=12, pady=4)

    ctk.CTkLabel(left, text="老人话语").pack(anchor="w", padx=12, pady=(8, 0))
    self.user_text = ctk.CTkEntry(left, placeholder_text="输入或留空")
    self.user_text.pack(fill="x", padx=12, pady=4)

    ctk.CTkButton(left, text="单步推理", command=self._single_tick).pack(fill="x", padx=12, pady=8)
    ctk.CTkButton(left, text="运行演示剧本", fg_color="#c0392b", command=self._run_demo).pack(
      fill="x", padx=12, pady=4
    )

    right = ctk.CTkFrame(self)
    right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    right.grid_rowconfigure(1, weight=1)
    right.grid_columnconfigure(0, weight=1)

    self.status = ctk.CTkLabel(
      right, text="状态: MONITOR | 风险: 0.00", font=ctk.CTkFont(size=16)
    )
    self.status.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

    self.log_box = ctk.CTkTextbox(right, font=ctk.CTkFont(family="Consolas", size=13))
    self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    self.robot_box = ctk.CTkTextbox(right, height=140, font=ctk.CTkFont(family="Consolas", size=12))
    self.robot_box.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
    self.robot_box.insert("0.0", "机器人指令将显示在这里…\n")

  def _slider(self, parent, label, lo, hi, default):
    ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12)
    s = ctk.CTkSlider(parent, from_=lo, to=hi, number_of_steps=hi - lo)
    s.set(default)
    s.pack(fill="x", padx=12, pady=(0, 8))
    return s

  def _current_frame(self) -> PerceptionFrame:
    return PerceptionFrame(
      heart_rate=int(self.hr.get()),
      spo2=int(self.spo2.get()),
      activity_level=self.activity.get() / 100.0,
      skeleton_aspect_ratio=self.aspect.get() / 100.0,
      skeleton_dy=self.dy.get() / 100.0,
      emotion=self.emotion_var.get(),
      user_text=self.user_text.get().strip() or None,
    )

  def _single_tick(self):
    summary = self._orch.tick(self._current_frame())
    self._update_status(summary)

  def _run_demo(self):
    if self._running:
      return
    self._running = True
    threading.Thread(target=self._demo_thread, daemon=True).start()

  def _demo_thread(self):
    for step in demo_scenarios():
      self.after(0, lambda s=step: self._append_log(f"—— 场景: {s.name} ——"))
      t0 = time.time()
      while time.time() - t0 < step.duration_s:
        summary = self._orch.tick(step.frame)
        self.after(0, lambda sm=summary: self._update_status(sm))
        time.sleep(0.4)
    self.after(0, lambda: self._append_log("演示剧本结束。"))
    self._running = False

  def _update_status(self, summary: dict):
    risk = summary["risk"]
    self.status.configure(
      text=f"状态: {summary['state'].upper()} | 风险: {risk.score:.2f} ({risk.level})"
    )
    self._append_log(
      f"{summary['state']} | {', '.join(risk.reasons) or '无异常'} | 回复: {summary['reply'][:40]}…"
    )

  def _on_robot_action(self, record: dict):
    self.after(0, lambda: self.robot_box.insert("end", f"{record}\n"))

  def _append_log(self, msg: str):
    self.log_box.insert("end", msg + "\n")
    self.log_box.see("end")


def _run_smoke_test(app: CareCompanionApp) -> None:
  """SSH 无 DISPLAY 时在虚拟屏上自动跑演示并退出。"""
  app._append_log("冒烟测试：自动运行演示剧本…")
  app._run_demo()

  def _finish():
    log = app.log_box.get("1.0", "end")
    if "emergency" not in log.lower():
      app.destroy()
      raise SystemExit("GUI 冒烟测试失败：未触发 emergency 状态")
    app._append_log("✅ GUI 冒烟测试通过（窗口、推理、跌倒流程正常）")
    app.after(400, app.destroy)

  app.after(11000, _finish)


def main(smoke_test: bool = False):
  app = CareCompanionApp()
  if smoke_test:
    app.after(300, lambda: _run_smoke_test(app))
  app.mainloop()


if __name__ == "__main__":
  main(smoke_test="--smoke-test" in sys.argv)
