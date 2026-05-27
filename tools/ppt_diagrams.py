#!/usr/bin/env python3
"""生成答辩 PPT 用理论框图、流程图、数据图。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "diagrams"

# 中文字体：优先用系统 Noto，缺失时仍生成英文标签框图
import matplotlib.font_manager as fm

_cjk_paths = [
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
  "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
for _p in _cjk_paths:
  if Path(_p).exists():
    fm.fontManager.addfont(_p)
    _prop = fm.FontProperties(fname=_p)
    plt.rcParams["font.sans-serif"] = [_prop.get_name(), "DejaVu Sans"]
    break
plt.rcParams["axes.unicode_minus"] = False

C_DARK = "#143275"
C_BLUE = "#2563EB"
C_CYAN = "#0EA5E9"
C_GREEN = "#10B981"
C_ORANGE = "#F59E0B"
C_RED = "#EF4444"
C_GRAY = "#64748B"
C_BG = "#F8FAFC"


def _save(fig, name: str) -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  p = OUT / name
  fig.savefig(p, dpi=160, bbox_inches="tight", facecolor=C_BG, edgecolor="none")
  plt.close(fig)
  return p


def _box(ax, xy, wh, text, color, fontsize=10, text_color="white"):
  x, y = xy
  w, h = wh
  patch = FancyBboxPatch(
    (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
    facecolor=color, edgecolor="white", linewidth=1.5,
  )
  ax.add_patch(patch)
  ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
          fontsize=fontsize, color=text_color, fontweight="bold", wrap=True)


def gen_cover_banner() -> Path:
  fig, ax = plt.subplots(figsize=(12.8, 7.2))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  ax.add_patch(mpatches.Rectangle((0, 0), 10, 6, facecolor=C_DARK))
  ax.text(5, 4.2, "CareCompanion", ha="center", fontsize=36, color="white", fontweight="bold")
  ax.text(5, 3.2, "智能养老陪伴机器人仿真平台", ha="center", fontsize=18, color="#93C5FD")
  ax.text(5, 2.0, "感知 · 决策 · 执行  一体化闭环", ha="center", fontsize=14, color="#E2E8F0")
  ax.text(5, 0.8, "第二十八届中国机器人及人工智能大赛  |  机器人创新赛道", ha="center", fontsize=11, color="#94A3B8")
  return _save(fig, "cover_banner.png")


def gen_team_card() -> Path:
  fig, ax = plt.subplots(figsize=(8, 6))
  ax.axis("off")
  fields = [
    ("团队", "从容应队"), ("学校", "中山大学"), ("省份", "广东"),
    ("队长", "刘小凡"), ("队员", "白冉"), ("指导教师", "彭键清"),
    ("团队编号", "CRAIC2026-TEAM-8FJQKLMI"), ("作品编号", "CRAIC20264ZEFT1DF"),
  ]
  y = 0.92
  for k, v in fields:
    ax.text(0.05, y, k, fontsize=12, color=C_GRAY, transform=ax.transAxes, fontweight="bold")
    ax.text(0.32, y, v, fontsize=12, color=C_DARK, transform=ax.transAxes)
    y -= 0.11
  ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, transform=ax.transAxes,
             boxstyle="round,pad=0.01", facecolor="none", edgecolor=C_BLUE, linewidth=2))
  return _save(fig, "team_card.png")


def gen_aging_chart() -> Path:
  fig, ax = plt.subplots(figsize=(8, 5))
  years = ["2020", "2025", "2030", "2035"]
  ratio = [13.5, 16.5, 20.5, 24.0]
  bars = ax.bar(years, ratio, color=[C_BLUE, C_CYAN, C_ORANGE, C_RED], width=0.55, edgecolor="white")
  ax.set_ylabel("60岁及以上人口占比 (%)", fontsize=11)
  ax.set_title("我国老龄化趋势（示意）", fontsize=14, color=C_DARK, fontweight="bold")
  ax.set_ylim(0, 28)
  ax.grid(axis="y", alpha=0.3)
  for b, v in zip(bars, ratio):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v}%", ha="center", fontsize=10)
  ax.annotate("跌倒空窗期风险上升", xy=(2, 22), fontsize=10, color=C_RED,
              arrowprops=dict(arrowstyle="->", color=C_RED))
  return _save(fig, "aging_chart.png")


def gen_compare_diagram() -> Path:
  fig, ax = plt.subplots(figsize=(10, 5.5))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  ax.text(2.5, 5.5, "传统方案 Ø", ha="center", fontsize=13, color=C_RED, fontweight="bold")
  ax.text(7.5, 5.5, "本作品 ü", ha="center", fontsize=13, color=C_DARK, fontweight="bold")
  left = ["智能音箱\n无视觉闭环", "摄像头\n只告警", "手环\n难检跌倒", "毕设\n难部署"]
  right = ["多模态\n风险融合", "可解释\n决策", "机器人\n动作执行", "开源\n可复现"]
  for i, (l, r) in enumerate(zip(left, right)):
    y = 4.2 - i * 1.05
    _box(ax, (0.3, y), (3.8, 0.85), l, "#FEE2E2", fontsize=9, text_color="#991B1B")
    _box(ax, (5.9, y), (3.8, 0.85), r, "#DBEAFE", fontsize=9, text_color=C_DARK)
  return _save(fig, "compare.png")


def gen_architecture() -> Path:
  fig, ax = plt.subplots(figsize=(10, 6))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 8)
  ax.axis("off")
  layers = [
    ("交互层", "Web控制台 · GUI · 无头剧本", C_CYAN),
    ("认知层", "RiskEngine · DialogueManager · CarePlanner", C_BLUE),
    ("感知层", "Fall · Emotion · Health · MediaPipe Pose", C_GREEN),
    ("执行层", "RobotAdapter → 仿真 / ROS2 人形", C_ORANGE),
  ]
  y = 6.5
  for title, desc, col in layers:
    _box(ax, (1, y), (8, 1.1), f"{title}\n{desc}", col, fontsize=11)
    y -= 1.55
  _box(ax, (3.5, 0.3), (3, 0.9), "CareOrchestrator\n状态机调度核心", C_DARK, fontsize=10)
  for y0 in [6.5, 5.0, 3.45, 1.9]:
    ax.add_patch(FancyArrowPatch((5, y0), (5, y0 - 0.35), arrowstyle="-|>", color=C_GRAY, lw=2))
  return _save(fig, "architecture.png")


def gen_state_machine() -> Path:
  fig, ax = plt.subplots(figsize=(10, 5))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 5)
  ax.axis("off")
  states = [("MONITOR\n监测", 1), ("CONVERSE\n对话", 3.5), ("ALERT\n告警", 6), ("EMERGENCY\n紧急", 8.5)]
  for label, x in states:
    _box(ax, (x, 2), (1.8, 1.2), label, C_BLUE if "EMERGENCY" not in label else C_RED, fontsize=9)
  for x1, x2 in [(2.8, 3.5), (5.3, 6), (7.3, 8.5)]:
    ax.annotate("", xy=(x2, 2.6), xytext=(x1, 2.6),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2))
  ax.text(5, 0.5, "紧急事件硬优先级：可打断对话与常规任务", ha="center", fontsize=11, color=C_RED, fontweight="bold")
  return _save(fig, "state_machine.png")


def gen_risk_formula() -> Path:
  fig, ax = plt.subplots(figsize=(9, 5.5))
  ax.axis("off")
  ax.text(0.5, 0.85, "多模态风险融合模型", ha="center", fontsize=16, color=C_DARK,
          fontweight="bold", transform=ax.transAxes)
  ax.text(0.5, 0.62, r"$S = 0.45 \cdot S_{fall} + 0.25 \cdot S_{emo} + 0.30 \cdot S_{health}$",
          ha="center", fontsize=18, color=C_BLUE, transform=ax.transAxes)
  items = [
    ("S_fall", "骨架宽高比 · 垂直速度 · 静止时长", C_GREEN),
    ("S_emo", "文本情感词典 + 情绪标签", C_CYAN),
    ("S_health", "心率 · 血氧 · 活动量", C_ORANGE),
  ]
  x = 0.08
  for name, desc, col in items:
    ax.add_patch(FancyBboxPatch((x, 0.22), 0.26, 0.28, transform=ax.transAxes,
                 boxstyle="round", facecolor=col, alpha=0.9))
    ax.text(x + 0.13, 0.42, name, transform=ax.transAxes, ha="center", color="white", fontweight="bold")
    ax.text(x + 0.13, 0.30, desc, transform=ax.transAxes, ha="center", fontsize=8, color="white")
    x += 0.32
  ax.text(0.5, 0.06, "输出：风险分数 · 等级 · 可解释原因列表", ha="center", fontsize=10,
          color=C_GRAY, transform=ax.transAxes)
  return _save(fig, "risk_formula.png")


def gen_fall_flow() -> Path:
  fig, ax = plt.subplots(figsize=(9, 6))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 10)
  ax.axis("off")
  steps = [
    (5, 9, "MediaPipe 骨架输入"),
    (5, 7.5, "计算 R=w/h, v_y"),
    (5, 6, "快速跌倒规则\n(score≥0.7)"),
    (2.5, 4, "是"),
    (7.5, 4, "慢速跌倒规则\n躺倒静止≥2s"),
    (5, 2, "跌倒确认 → 紧急链路"),
  ]
  cols = [C_CYAN, C_BLUE, C_BLUE, C_GREEN, C_ORANGE, C_RED]
  for (x, y, t), c in zip(steps, cols):
    _box(ax, (x - 1.6, y - 0.45), (3.2, 0.9), t, c, fontsize=9)
  arrows = [(5, 8.5, 5, 8), (5, 7, 5, 6.5), (5, 5.5, 2.5, 4.5), (5, 5.5, 7.5, 4.5), (2.5, 3.5, 5, 2.5), (7.5, 3.5, 5, 2.5)]
  for x1, y1, x2, y2 in arrows:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.5))
  return _save(fig, "fall_flow.png")


def gen_pipeline() -> Path:
  fig, ax = plt.subplots(figsize=(10, 4))
  ax.set_xlim(0, 12)
  ax.set_ylim(0, 3)
  ax.axis("off")
  nodes = ["感知采集", "特征提取", "风险融合", "状态机", "规划动作", "机器人执行"]
  xs = [0.5, 2.3, 4.1, 5.9, 7.7, 9.5]
  for x, n in zip(xs, nodes):
    _box(ax, (x, 1), (1.5, 1), n, C_BLUE, fontsize=9)
  for x1, x2 in zip(xs[:-1], xs[1:]):
    ax.annotate("", xy=(x2, 1.5), xytext=(x1 + 1.5, 1.5),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2))
  return _save(fig, "pipeline.png")


def gen_emergency_flow() -> Path:
  fig, ax = plt.subplots(figsize=(10, 3.5))
  ax.set_xlim(0, 12)
  ax.set_ylim(0, 2.5)
  ax.axis("off")
  steps = ["alert_sound\n告警音", "speak\n语音安抚", "call_emergency\n家属通知", "raise_hand\n举手示意"]
  xs = [0.4, 3.2, 6.0, 8.8]
  cols = [C_ORANGE, C_BLUE, C_RED, C_GREEN]
  for x, s, c in zip(xs, steps, cols):
    _box(ax, (x, 0.6), (2.2, 1.2), s, c, fontsize=9)
  for i in range(3):
    ax.annotate("", xy=(xs[i + 1], 1.2), xytext=(xs[i] + 2.2, 1.2),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2))
  return _save(fig, "emergency_flow.png")


def gen_metrics_chart() -> Path:
  fig, ax = plt.subplots(figsize=(8, 5))
  labels = ["Precision", "Recall", "F1", "紧急触发率"]
  vals = [100, 100, 100, 100]
  colors = [C_BLUE, C_CYAN, C_GREEN, C_ORANGE]
  bars = ax.barh(labels, vals, color=colors, height=0.5)
  ax.set_xlim(0, 110)
  ax.set_title("跌倒检测与紧急链路评测（合成6场景）", fontsize=13, color=C_DARK, fontweight="bold")
  ax.set_xlabel("指标值 (%)")
  for b, v in zip(bars, vals):
    ax.text(v - 8, b.get_y() + b.get_height() / 2, f"{v}%", va="center", color="white", fontweight="bold")
  ax.axvline(90, color=C_RED, linestyle="--", alpha=0.5, label="优秀线 90%")
  return _save(fig, "metrics_chart.png")


def gen_innovation_radar() -> Path:
  fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection="polar"))
  cats = ["多模态融合", "安全闭环", "视觉感知", "工程化", "应用价值"]
  vals = [0.92, 0.95, 0.88, 0.90, 0.93]
  angles = [n / float(len(cats)) * 2 * 3.14159 for n in range(len(cats))]
  vals += vals[:1]
  angles += angles[:1]
  ax.plot(angles, vals, "o-", linewidth=2, color=C_BLUE)
  ax.fill(angles, vals, alpha=0.25, color=C_CYAN)
  ax.set_xticks(angles[:-1])
  ax.set_xticklabels(cats, fontsize=10)
  ax.set_ylim(0, 1)
  ax.set_title("创新维度自评", fontsize=13, color=C_DARK, fontweight="bold", pad=20)
  return _save(fig, "innovation_radar.png")


def gen_roadmap() -> Path:
  fig, ax = plt.subplots(figsize=(10, 4))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 4)
  ax.axis("off")
  phases = [
    ("已完成", "Web演示\n评测脚本\n开源仓库", C_GREEN),
    ("进行中", "软著申请\n真机对接", C_BLUE),
    ("计划", "公开数据集\n多房间场景", C_ORANGE),
  ]
  x = 0.5
  for title, body, col in phases:
    _box(ax, (x, 0.8), (2.8, 2.5), f"{title}\n{body}", col, fontsize=10)
    x += 3.2
  return _save(fig, "roadmap.png")


def gen_llm_module() -> Path:
  fig, ax = plt.subplots(figsize=(9, 5))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  _box(ax, (0.5, 4), (2.5, 1.2), "老人话语\n情绪标签", C_CYAN, fontsize=9)
  _box(ax, (3.5, 4), (3, 1.2), "DialogueManager\n(Mock/LLM可插拔)", C_DARK, fontsize=9)
  _box(ax, (7, 4), (2.5, 1.2), "安抚回复\n机器人话术", C_GREEN, fontsize=9)
  ax.annotate("", xy=(3.5, 4.6), xytext=(3, 4.6), arrowprops=dict(arrowstyle="-|>", lw=2))
  ax.annotate("", xy=(7, 4.6), xytext=(6.5, 4.6), arrowprops=dict(arrowstyle="-|>", lw=2))
  ax.text(5, 2.5, "默认离线 Mock 保障隐私与稳定\n可切换 OpenAI 兼容 API", ha="center", fontsize=11, color=C_GRAY)
  return _save(fig, "llm_module.png")


def gen_all() -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  funcs = [
    gen_cover_banner, gen_team_card, gen_aging_chart, gen_compare_diagram,
    gen_architecture, gen_state_machine, gen_risk_formula, gen_fall_flow,
    gen_pipeline, gen_emergency_flow, gen_metrics_chart, gen_innovation_radar,
    gen_roadmap, gen_llm_module,
  ]
  for fn in funcs:
    fn()
  return OUT


if __name__ == "__main__":
  d = gen_all()
  print(f"✅ 框图已生成: {d} ({len(list(d.glob('*.png')))} 张)")
