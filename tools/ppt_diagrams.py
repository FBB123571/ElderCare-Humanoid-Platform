#!/usr/bin/env python3
"""高质量理论框图：固定画幅、大字号、留白充足。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "diagrams"

import matplotlib.font_manager as fm

for _p in (
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
):
  if Path(_p).exists():
    fm.fontManager.addfont(_p)
    plt.rcParams["font.sans-serif"] = [fm.FontProperties(fname=_p).get_name(), "DejaVu Sans"]
    break
plt.rcParams["axes.unicode_minus"] = False

C_DARK = "#143275"
C_BLUE = "#2563EB"
C_CYAN = "#0EA5E9"
C_GREEN = "#10B981"
C_ORANGE = "#F59E0B"
C_RED = "#EF4444"
C_GRAY = "#64748B"
C_BG = "#FFFFFF"
C_CARD = "#F1F5F9"
C_LIGHT = "#EFF6FF"

# 统一画幅：与 PPT 右栏比例接近 5:3.2
FIG_W, FIG_H = 10.0, 6.4
DPI = 240


def _save(fig, name: str) -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  p = OUT / name
  fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor=C_BG, edgecolor="none", pad_inches=0.28)
  plt.close(fig)
  return p


def _fig():
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_facecolor(C_BG)
  fig.patch.set_facecolor(C_BG)
  # 外框卡片
  ax.add_patch(
    FancyBboxPatch(
      (0.04, 0.04), 0.92, 0.92, transform=ax.transAxes,
      boxstyle="round,pad=0.012", facecolor=C_CARD, edgecolor="#CBD5E1", linewidth=2,
    )
  )
  return fig, ax


def _box(ax, xy, wh, text, color, fontsize=12, text_color="white", shadow=True):
  x, y = xy
  w, h = wh
  if shadow:
    ax.add_patch(
      FancyBboxPatch(
        (x + 0.06, y - 0.06), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
        facecolor="#94A3B8", edgecolor="none", alpha=0.35,
      )
    )
  patch = FancyBboxPatch(
    (x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
    facecolor=color, edgecolor="white", linewidth=2.2,
  )
  ax.add_patch(patch)
  ax.text(
    x + w / 2, y + h / 2, text, ha="center", va="center",
    fontsize=fontsize, color=text_color, fontweight="bold", linespacing=1.35,
  )


def _arrow(ax, x1, y1, x2, y2, color=C_GRAY):
  ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
              arrowprops=dict(arrowstyle="-|>", color=color, lw=2.8, mutation_scale=18))


def gen_cover_banner() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.axis("off")
  ax.add_patch(mpatches.Rectangle((0, 0), 10, 6.4, facecolor=C_DARK))
  for cx, cy, r, a in [(1.5, 5.0, 0.7, 0.12), (8.2, 1.2, 0.9, 0.15), (9.0, 5.2, 0.4, 0.1)]:
    ax.add_patch(mpatches.Circle((cx, cy), r, facecolor="white", alpha=a))
  return _save(fig, "cover_banner.png")


def gen_team_card() -> Path:
  fig, ax = _fig()
  ax.axis("off")
  ax.text(0.5, 0.92, "参赛信息", transform=ax.transAxes, ha="center", fontsize=18,
          color=C_DARK, fontweight="bold")
  fields = [
    ("团队", "从容应队"), ("学校", "中山大学"),
    ("队长", "刘小凡"), ("队员", "白冉"), ("指导教师", "彭键清"),
    ("团队编号", "CRAIC2026-TEAM-8FJQKLMI"),
    ("作品编号", "CRAIC20264ZEFT1DF"),
  ]
  y = 0.78
  for k, v in fields:
    ax.add_patch(mpatches.Rectangle((0.08, y - 0.025), 0.2, 0.065, transform=ax.transAxes,
                                    facecolor=C_LIGHT, edgecolor="none"))
    ax.text(0.18, y, k, fontsize=13, color=C_GRAY, transform=ax.transAxes, ha="center", fontweight="bold")
    ax.text(0.34, y, v, fontsize=13, color=C_DARK, transform=ax.transAxes, fontweight="bold")
    y -= 0.095
  return _save(fig, "team_card.png")


def gen_aging_chart() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  fig.patch.set_facecolor(C_BG)
  ax.set_facecolor(C_CARD)
  years = ["2020", "2025", "2030", "2035"]
  ratio = [13.5, 16.5, 20.5, 24.0]
  bars = ax.bar(years, ratio, color=[C_BLUE, C_CYAN, C_ORANGE, C_RED], width=0.5, edgecolor="white", linewidth=2)
  ax.set_ylabel("60岁及以上占比 (%)", fontsize=14, fontweight="bold", labelpad=10)
  ax.set_title("我国老龄化趋势（示意）", fontsize=16, color=C_DARK, fontweight="bold", pad=16)
  ax.set_ylim(0, 28)
  ax.tick_params(labelsize=12)
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)
  ax.grid(axis="y", alpha=0.3, linestyle="--")
  for b, v in zip(bars, ratio):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.7, f"{v}%", ha="center", fontsize=13, fontweight="bold")
  fig.tight_layout(pad=1.8)
  return _save(fig, "aging_chart.png")


def gen_compare_diagram() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  ax.text(2.5, 5.9, "传统方案 · 局限", ha="center", fontsize=16, color=C_RED, fontweight="bold")
  ax.text(7.5, 5.9, "本作品 · 优势", ha="center", fontsize=16, color=C_DARK, fontweight="bold")
  left = ["智能音箱\n功能割裂", "摄像头\n只告警", "手环\n难检跌倒", "毕设\n难复现"]
  right = ["多模态\n风险融合", "可解释\n决策", "机器人\n执行", "开源\n可演示"]
  for i, (l, r) in enumerate(zip(left, right)):
    y = 4.5 - i * 1.15
    _box(ax, (0.35, y), (3.8, 1.0), l, "#FEE2E2", fontsize=12, text_color="#991B1B")
    _box(ax, (5.85, y), (3.8, 1.0), r, "#DBEAFE", fontsize=12, text_color=C_DARK)
    _arrow(ax, 4.2, y + 0.5, 5.8, y + 0.5, C_ORANGE)
  return _save(fig, "compare.png")


def gen_architecture() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  layers = [
    ("交互层", "Web · GUI · 演示剧本", C_CYAN),
    ("认知层", "RiskEngine · Dialogue · Planner", C_BLUE),
    ("感知层", "Fall · Emotion · MediaPipe", C_GREEN),
    ("执行层", "RobotAdapter · 仿真/ROS2", C_ORANGE),
  ]
  y = 5.0
  for title, desc, col in layers:
    _box(ax, (1.0, y), (8.0, 1.05), f"{title}\n{desc}", col, fontsize=13)
    y -= 1.22
  _box(ax, (3.0, 0.35), (4.0, 0.95), "CareOrchestrator\n状态机核心", C_DARK, fontsize=12)
  for y0 in [5.0, 3.78, 2.56, 1.34]:
    _arrow(ax, 5, y0, 5, y0 - 0.12)
  return _save(fig, "architecture.png")


def gen_state_machine() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  states = [("MONITOR\n监测", 0.5), ("CONVERSE\n对话", 2.7), ("ALERT\n告警", 4.9), ("EMERGENCY\n紧急", 7.1)]
  for label, x in states:
    col = C_RED if "EMERGENCY" in label else C_BLUE
    _box(ax, (x, 2.8), (2.0, 1.35), label, col, fontsize=12)
  for x1, x2 in [(2.5, 2.7), (4.7, 4.9), (6.9, 7.1)]:
    _arrow(ax, x1, 3.45, x2, 3.45, C_DARK)
  _box(ax, (1.2, 0.55), (7.6, 0.85), "紧急事件硬优先级 · 可打断对话", "#FEE2E2", fontsize=12, text_color=C_RED, shadow=False)
  return _save(fig, "state_machine.png")


def gen_risk_formula() -> Path:
  fig, ax = _fig()
  ax.axis("off")
  ax.text(0.5, 0.9, "多模态风险融合", transform=ax.transAxes, ha="center", fontsize=18, fontweight="bold", color=C_DARK)
  ax.text(0.5, 0.72, r"$S = 0.45 S_{fall} + 0.25 S_{emo} + 0.30 S_{health}$",
          transform=ax.transAxes, ha="center", fontsize=20, color=C_BLUE)
  items = [("S_fall", "骨架特征", C_GREEN), ("S_emo", "情感词典", C_CYAN), ("S_health", "健康指标", C_ORANGE)]
  x = 0.8
  for name, desc, col in items:
    _box(ax, (x, 1.2), (2.5, 1.5), f"{name}\n{desc}", col, fontsize=13)
    x += 3.0
  ax.text(0.5, 0.08, "输出：分数 · 等级 · 原因列表", transform=ax.transAxes, ha="center",
          fontsize=13, fontweight="bold", color=C_DARK)
  return _save(fig, "risk_formula.png")


def gen_fall_flow() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  nodes = [
    (5, 5.5, "骨架输入", C_CYAN),
    (5, 4.2, "几何特征 R,v", C_BLUE),
    (5, 2.8, "快速跌倒规则", C_BLUE),
    (2.2, 1.3, "慢速躺倒", C_ORANGE),
    (5, 0.35, "紧急链路", C_RED),
  ]
  for x, y, t, c in nodes:
    _box(ax, (x - 1.5, y), (3.0, 0.85), t, c, fontsize=12)
  _arrow(ax, 5, 5.5, 5, 4.65)
  _arrow(ax, 5, 4.2, 5, 3.65)
  _arrow(ax, 5, 2.8, 5, 1.25)
  _arrow(ax, 4.2, 2.4, 2.8, 1.7)
  _arrow(ax, 2.2, 1.3, 4.0, 0.75)
  return _save(fig, "fall_flow.png")


def gen_pipeline() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  nodes = ["感知", "特征", "融合", "状态机", "规划", "执行"]
  ys = [4.8, 3.5, 2.2, 0.9]
  # 横向主流程
  xs = [0.6, 2.1, 3.6, 5.1, 6.6, 8.1]
  for x, n in zip(xs, nodes):
    _box(ax, (x, 2.4), (1.35, 1.1), n, C_BLUE, fontsize=12)
  for x1, x2 in zip(xs[:-1], xs[1:]):
    _arrow(ax, x1 + 1.35, 2.95, x2, 2.95, C_DARK)
  ax.text(5, 5.2, "数据处理与决策流水线", ha="center", fontsize=16, fontweight="bold", color=C_DARK)
  return _save(fig, "pipeline.png")


def gen_emergency_flow() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  steps = [("告警音", C_ORANGE), ("语音安抚", C_BLUE), ("家属通知", C_RED), ("举手示意", C_GREEN)]
  xs = [0.5, 2.7, 4.9, 7.1]
  for (label, col), x in zip(steps, xs):
    _box(ax, (x, 2.5), (2.0, 1.2), label, col, fontsize=13)
  for i in range(3):
    _arrow(ax, xs[i] + 2.0, 3.1, xs[i + 1], 3.1, C_DARK)
  ax.text(5, 5.0, "跌倒确认后紧急响应链路", ha="center", fontsize=16, fontweight="bold", color=C_DARK)
  return _save(fig, "emergency_flow.png")


def gen_metrics_chart() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  fig.patch.set_facecolor(C_BG)
  labels = ["Precision", "Recall", "F1", "紧急触发率"]
  vals = [100, 100, 100, 100]
  colors = [C_BLUE, C_CYAN, C_GREEN, C_ORANGE]
  bars = ax.barh(labels, vals, color=colors, height=0.55, edgecolor="white", linewidth=2)
  ax.set_xlim(0, 115)
  ax.set_title("评测结果（合成6场景）", fontsize=16, fontweight="bold", pad=18)
  ax.tick_params(labelsize=13)
  ax.axvline(90, color=C_RED, linestyle="--", lw=2)
  for b, v in zip(bars, vals):
    ax.text(v - 12, b.get_y() + b.get_height() / 2, f"{v}%", va="center", color="white", fontsize=13, fontweight="bold")
  fig.tight_layout(pad=2.0)
  return _save(fig, "metrics_chart.png")


def gen_innovation_radar() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), subplot_kw=dict(projection="polar"))
  fig.patch.set_facecolor(C_BG)
  cats = ["多模态融合", "安全闭环", "视觉感知", "工程化", "应用价值"]
  vals = [0.92, 0.95, 0.88, 0.90, 0.93]
  angles = [n / len(cats) * 2 * 3.14159 for n in range(len(cats))]
  vp = vals + vals[:1]
  ap = angles + angles[:1]
  ax.plot(ap, vp, "o-", lw=3, color=C_BLUE, markersize=10)
  ax.fill(ap, vp, alpha=0.25, color=C_CYAN)
  ax.set_xticks(angles)
  ax.set_xticklabels(cats, fontsize=13, fontweight="bold")
  ax.set_ylim(0, 1)
  ax.set_title("创新维度", fontsize=16, fontweight="bold", pad=28)
  return _save(fig, "innovation_radar.png")


def gen_roadmap() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  phases = [
    ("已完成", "Web演示\n评测脚本", C_GREEN),
    ("进行中", "软著\n真机对接", C_BLUE),
    ("计划", "数据集\n多场景", C_ORANGE),
  ]
  x = 0.55
  for title, body, col in phases:
    _box(ax, (x, 1.5), (2.7, 3.2), f"{title}\n{body}", col, fontsize=13)
    if x < 7:
      _arrow(ax, x + 2.7, 3.1, x + 3.0, 3.1)
    x += 3.05
  return _save(fig, "roadmap.png")


def gen_llm_module() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6.4)
  ax.axis("off")
  _box(ax, (0.5, 3.8), (2.5, 1.35), "老人话语\n情绪标签", C_CYAN, fontsize=12)
  _box(ax, (3.5, 3.8), (3.2, 1.35), "DialogueManager\nMock/LLM", C_DARK, fontsize=12)
  _box(ax, (7.0, 3.8), (2.5, 1.35), "安抚话术\n动作联动", C_GREEN, fontsize=12)
  _arrow(ax, 3.0, 4.45, 3.5, 4.45)
  _arrow(ax, 6.7, 4.45, 7.0, 4.45)
  _box(ax, (2.0, 1.2), (6.0, 1.1), "默认离线 Mock · 可切换 API", C_LIGHT, fontsize=12, text_color=C_DARK, shadow=False)
  return _save(fig, "llm_module.png")


def gen_all() -> Path:
  for fn in [
    gen_cover_banner, gen_team_card, gen_aging_chart, gen_compare_diagram,
    gen_architecture, gen_state_machine, gen_risk_formula, gen_fall_flow,
    gen_pipeline, gen_emergency_flow, gen_metrics_chart, gen_innovation_radar,
    gen_roadmap, gen_llm_module,
  ]:
    fn()
  return OUT


if __name__ == "__main__":
  gen_all()
  print(f"✅ 框图: {OUT} ({len(list(OUT.glob('*.png')))} 张)")
