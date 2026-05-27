#!/usr/bin/env python3
"""答辩框图：画幅贴合 PPT 右栏比例，少留白、大字号。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import numpy as np

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
C_LIGHT = "#EFF6FF"

# 与 PPT 右栏一致：宽约 5.0in，高约 3.9in → 比例 ~1.28
FIG_W, FIG_H = 5.0, 3.9
DPI = 260


def _trim_png(path: Path, tol: int = 248) -> None:
  im = Image.open(path).convert("RGB")
  arr = np.array(im)
  mask = (arr[:, :, 0] < tol) | (arr[:, :, 1] < tol) | (arr[:, :, 2] < tol)
  if not mask.any():
    return
  ys, xs = np.where(mask)
  pad = 8
  x0, x1 = max(0, xs.min() - pad), min(arr.shape[1], xs.max() + pad)
  y0, y1 = max(0, ys.min() - pad), min(arr.shape[0], ys.max() + pad)
  im.crop((x0, y0, x1, y1)).save(path)


def _save(fig, name: str) -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  p = OUT / name
  fig.savefig(p, dpi=DPI, facecolor=C_BG, edgecolor="none", bbox_inches="tight", pad_inches=0.04)
  plt.close(fig)
  _trim_png(p)
  return p


def _canvas():
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.04)
  ax.set_facecolor(C_BG)
  fig.patch.set_facecolor(C_BG)
  return fig, ax


def _box(ax, xy, wh, text, color, fontsize=11, text_color="white"):
  x, y = xy
  w, h = wh
  ax.add_patch(
    FancyBboxPatch(
      (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.1",
      facecolor=color, edgecolor="white", linewidth=2,
    )
  )
  ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
          fontsize=fontsize, color=text_color, fontweight="bold", linespacing=1.3)


def _arrow(ax, x1, y1, x2, y2, color=C_GRAY):
  ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
              arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5, mutation_scale=16))


def gen_cover_banner() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.axis("off")
  ax.add_patch(mpatches.Rectangle((0, 0), 5, 3.9, facecolor=C_DARK))
  return _save(fig, "cover_banner.png")


def gen_team_card() -> Path:
  """备用小图（章节页等）；参赛页已改用 pptx 原生信息卡。"""
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  ax.add_patch(FancyBboxPatch((0.1, 0.08), 4.8, 3.74, boxstyle="round", facecolor=C_LIGHT, edgecolor=C_BLUE, lw=2.5))
  fields = [
    ("团队", "从容应队"), ("学校", "中山大学"),
    ("队长", "刘小凡"), ("队员", "白冉"), ("指导", "彭键清"),
    ("团队编号", "CRAIC2026-TEAM-8FJQKLMI"),
    ("作品编号", "CRAIC20264ZEFT1DF"),
  ]
  y = 3.35
  for k, v in fields:
    _box(ax, (0.25, y - 0.42), (1.1, 0.38), k, C_DARK, fontsize=10)
    ax.text(1.5, y - 0.22, v, fontsize=11, color=C_DARK, fontweight="bold", va="center")
    y -= 0.48
  return _save(fig, "team_card.png")


def gen_aging_chart() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  fig.patch.set_facecolor(C_BG)
  ax.set_facecolor("#F8FAFC")
  years = ["2020", "2025", "2030", "2035"]
  ratio = [13.5, 16.5, 20.5, 24.0]
  bars = ax.bar(years, ratio, color=[C_BLUE, C_CYAN, C_ORANGE, C_RED], width=0.58, edgecolor="white", lw=2)
  ax.set_ylabel("60岁及以上人口占比 (%)", fontsize=13, fontweight="bold", labelpad=8)
  ax.set_title("我国老龄化趋势", fontsize=15, fontweight="bold", color=C_DARK, pad=12)
  ax.set_ylim(0, 30)
  ax.tick_params(labelsize=12, width=0)
  for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
  ax.grid(axis="y", alpha=0.35, ls="--")
  for b, v in zip(bars, ratio):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.9, f"{v}%", ha="center", fontsize=13, fontweight="bold", color=C_DARK)
  ax.annotate(
    "跌倒发现\n空窗风险↑", xy=(2.15, 21), fontsize=11, color=C_RED, fontweight="bold", ha="center",
    bbox=dict(boxstyle="round,pad=0.4", fc="#FEE2E2", ec=C_RED, lw=1.5),
    arrowprops=dict(arrowstyle="->", color=C_RED, lw=2),
  )
  fig.subplots_adjust(left=0.16, right=0.98, top=0.90, bottom=0.12)
  return _save(fig, "aging_chart.png")


def gen_compare_diagram() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  ax.text(1.25, 3.65, "传统局限", ha="center", fontsize=12, color=C_RED, fontweight="bold")
  ax.text(3.75, 3.65, "本作品优势", ha="center", fontsize=12, color=C_DARK, fontweight="bold")
  left = ["音箱\n割裂", "摄像头\n只告警", "手环\n难检跌", "毕设\n难复现"]
  right = ["多模态\n融合", "可解释\n决策", "机器人\n执行", "开源\n演示"]
  for i, (l, r) in enumerate(zip(left, right)):
    y = 2.85 - i * 0.72
    _box(ax, (0.15, y), (1.85, 0.58), l, "#FEE2E2", fontsize=9, text_color="#991B1B")
    _box(ax, (3.0, y), (1.85, 0.58), r, "#DBEAFE", fontsize=9, text_color=C_DARK)
    _arrow(ax, 2.05, y + 0.29, 2.95, y + 0.29, C_ORANGE)
  return _save(fig, "compare.png")


def gen_architecture() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  layers = [
    ("交互层", "Web · GUI", C_CYAN),
    ("认知层", "Risk · Dialogue", C_BLUE),
    ("感知层", "Fall · MediaPipe", C_GREEN),
    ("执行层", "Robot · ROS2", C_ORANGE),
  ]
  y = 3.15
  for title, desc, col in layers:
    _box(ax, (0.35, y), (4.3, 0.62), f"{title}  {desc}", col, fontsize=10)
    y -= 0.72
  _box(ax, (1.35, 0.18), (2.3, 0.52), "CareOrchestrator", C_DARK, fontsize=10)
  for y0 in [3.15, 2.43, 1.71, 0.99]:
    _arrow(ax, 2.5, y0, 2.5, y0 - 0.08)
  return _save(fig, "architecture.png")


def gen_state_machine() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  states = [("MONITOR", 0.15), ("CONVERSE", 1.35), ("ALERT", 2.55), ("EMERGENCY", 3.75)]
  for label, x in states:
    col = C_RED if "EMERGENCY" in label else C_BLUE
    _box(ax, (x, 1.85), (1.05, 0.95), label, col, fontsize=9)
  for x1, x2 in [(1.2, 1.35), (2.4, 2.55), (3.6, 3.75)]:
    _arrow(ax, x1, 2.32, x2, 2.32, C_DARK)
  _box(ax, (0.35, 0.35), (4.3, 0.55), "紧急态可打断对话", "#FEE2E2", fontsize=10, text_color=C_RED)
  ax.text(2.5, 3.45, "CareOrchestrator 状态机", ha="center", fontsize=12, fontweight="bold", color=C_DARK)
  return _save(fig, "state_machine.png")


def gen_risk_formula() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  ax.text(2.5, 3.55, "多模态风险融合", ha="center", fontsize=14, fontweight="bold", color=C_DARK)
  ax.text(2.5, 2.95, r"$S = 0.45S_{fall} + 0.25S_{emo} + 0.30S_{health}$",
          ha="center", fontsize=16, color=C_BLUE)
  items = [("S_fall\n骨架", C_GREEN), ("S_emo\n情感", C_CYAN), ("S_health\n健康", C_ORANGE)]
  x = 0.35
  for text, col in items:
    _box(ax, (x, 1.35), (1.35, 1.15), text, col, fontsize=11)
    x += 1.55
  ax.text(2.5, 0.55, "输出：分数 · 等级 · 原因列表", ha="center", fontsize=11, fontweight="bold", color=C_DARK)
  return _save(fig, "risk_formula.png")


def gen_fall_flow() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  nodes = [(2.5, 3.35, "骨架输入", C_CYAN), (2.5, 2.55, "几何特征", C_BLUE),
           (2.5, 1.75, "快速规则", C_BLUE), (2.5, 0.55, "紧急链路", C_RED)]
  for x, y, t, c in nodes:
    _box(ax, (x - 1.1, y), (2.2, 0.55), t, c, fontsize=10)
  for y1, y2 in [(3.35, 2.9), (2.55, 2.1), (1.75, 1.15)]:
    _arrow(ax, 2.5, y1, 2.5, y2)
  return _save(fig, "fall_flow.png")


def gen_pipeline() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  nodes = ["感知", "特征", "融合", "状态机", "规划", "执行"]
  xs = [0.12, 0.92, 1.72, 2.52, 3.32, 4.12]
  for x, n in zip(xs, nodes):
    _box(ax, (x, 1.55), (0.72, 0.75), n, C_BLUE, fontsize=9)
  for x1, x2 in zip(xs[:-1], xs[1:]):
    _arrow(ax, x1 + 0.72, 1.92, x2, 1.92, C_DARK)
  ax.text(2.5, 3.35, "决策流水线", ha="center", fontsize=13, fontweight="bold", color=C_DARK)
  return _save(fig, "pipeline.png")


def gen_emergency_flow() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  steps = [("告警音", C_ORANGE), ("语音", C_BLUE), ("通知", C_RED), ("手势", C_GREEN)]
  xs = [0.2, 1.45, 2.7, 3.95]
  for (label, col), x in zip(steps, xs):
    _box(ax, (x, 1.5), (1.05, 0.85), label, col, fontsize=10)
  for i in range(3):
    _arrow(ax, xs[i] + 1.05, 1.92, xs[i + 1], 1.92, C_DARK)
  ax.text(2.5, 3.35, "紧急响应链路", ha="center", fontsize=13, fontweight="bold", color=C_DARK)
  return _save(fig, "emergency_flow.png")


def gen_metrics_chart() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
  fig.patch.set_facecolor(C_BG)
  labels = ["Precision", "Recall", "F1", "紧急触发"]
  vals = [100, 100, 100, 100]
  colors = [C_BLUE, C_CYAN, C_GREEN, C_ORANGE]
  bars = ax.barh(labels, vals, color=colors, height=0.55, edgecolor="white", lw=1.5)
  ax.set_xlim(0, 115)
  ax.set_title("评测结果（6场景）", fontsize=13, fontweight="bold", pad=10)
  ax.tick_params(labelsize=10)
  ax.axvline(90, color=C_RED, ls="--", lw=1.8)
  for b, v in zip(bars, vals):
    ax.text(v - 12, b.get_y() + b.get_height() / 2, f"{v}%", va="center", color="white", fontsize=11, fontweight="bold")
  fig.subplots_adjust(left=0.22, right=0.95, top=0.88, bottom=0.12)
  return _save(fig, "metrics_chart.png")


def gen_innovation_radar() -> Path:
  fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), subplot_kw=dict(projection="polar"))
  fig.patch.set_facecolor(C_BG)
  cats = ["多模态", "安全闭环", "视觉", "工程化", "应用"]
  vals = [0.92, 0.95, 0.88, 0.90, 0.93]
  angles = [n / len(cats) * 2 * 3.14159 for n in range(len(cats))]
  vp, ap = vals + vals[:1], angles + angles[:1]
  ax.plot(ap, vp, "o-", lw=2.5, color=C_BLUE, markersize=7)
  ax.fill(ap, vp, alpha=0.25, color=C_CYAN)
  ax.set_xticks(angles)
  ax.set_xticklabels(cats, fontsize=10, fontweight="bold")
  ax.set_ylim(0, 1)
  ax.set_title("创新维度", fontsize=13, fontweight="bold", pad=16)
  return _save(fig, "innovation_radar.png")


def gen_roadmap() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  phases = [("已完成", "Web·评测", C_GREEN), ("进行中", "软著·真机", C_BLUE), ("计划", "数据集", C_ORANGE)]
  x = 0.25
  for title, body, col in phases:
    _box(ax, (x, 0.9), (1.45, 2.4), f"{title}\n{body}", col, fontsize=11)
    if x < 3.5:
      _arrow(ax, x + 1.45, 2.1, x + 1.6, 2.1)
    x += 1.58
  return _save(fig, "roadmap.png")


def gen_llm_module() -> Path:
  fig, ax = _canvas()
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.9)
  ax.axis("off")
  _box(ax, (0.2, 2.35), (1.35, 0.95), "话语\n情绪", C_CYAN, fontsize=10)
  _box(ax, (1.82, 2.35), (1.55, 0.95), "Dialogue\nMock/LLM", C_DARK, fontsize=9)
  _box(ax, (3.55, 2.35), (1.25, 0.95), "安抚\n话术", C_GREEN, fontsize=10)
  _arrow(ax, 1.55, 2.82, 1.82, 2.82)
  _arrow(ax, 3.37, 2.82, 3.55, 2.82)
  _box(ax, (0.55, 0.55), (3.9, 0.75), "离线Mock · 可切换API", C_LIGHT, fontsize=10, text_color=C_DARK)
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
  print(f"✅ 框图: {OUT}")
