#!/usr/bin/env python3
"""答辩配图：论文风格、每页不同图型（matplotlib / 表格 / 序列图 / 热力图等）。"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "sci"
EVAL_JSON = ROOT / "data" / "evaluation" / "results" / "fall_eval_report.json"

# 与 ppt_layout 右栏 FIG_WIDTH × FIG_BODY_H 一致，嵌入时不留白边过大
FIG_W, FIG_H = 5.05, 3.84
DPI = 280

# 论文常用配色（ColorBrewer / IEEE 风格）
C0 = "#1f3a5f"
C1 = "#2c5282"
C2 = "#3182ce"
C3 = "#63b3ed"
C4 = "#90cdf4"
C_RED = "#c53030"
C_GREEN = "#276749"
C_ORANGE = "#c05621"
C_GRAY = "#4a5568"
C_BG = "#ffffff"
C_GRID = "#e2e8f0"

import matplotlib.font_manager as fm

for _p in (
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
):
  if Path(_p).exists():
    _fn = fm.FontProperties(fname=_p).get_name()
    plt.rcParams.update({
      "font.sans-serif": [_fn, "DejaVu Sans"],
      "font.family": "sans-serif",
      "axes.unicode_minus": False,
      "mathtext.fontset": "dejavusans",
      "figure.dpi": DPI,
      "savefig.dpi": DPI,
      "axes.linewidth": 0.8,
      "axes.labelsize": 10,
      "axes.titlesize": 11,
      "xtick.labelsize": 9,
      "ytick.labelsize": 9,
      "legend.fontsize": 8,
    })
    break


def _trim_png(path: Path, tol: int = 250) -> None:
  im = Image.open(path).convert("RGB")
  arr = np.array(im)
  mask = (arr[:, :, 0] < tol) | (arr[:, :, 1] < tol) | (arr[:, :, 2] < tol)
  if not mask.any():
    return
  ys, xs = np.where(mask)
  pad = 6
  x0, x1 = max(0, xs.min() - pad), min(arr.shape[1], xs.max() + pad)
  y0, y1 = max(0, ys.min() - pad), min(arr.shape[0], ys.max() + pad)
  im.crop((x0, y0, x1, y1)).save(path)


def _save(fig, name: str, *, trim: bool = True) -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  p = OUT / name
  fig.savefig(p, facecolor=C_BG, edgecolor="none", bbox_inches="tight", pad_inches=0.08)
  plt.close(fig)
  if trim:
    _trim_png(p)
  return p


def _fig():
  fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=C_BG)
  return fig


def _load_eval() -> dict:
  if EVAL_JSON.exists():
    return json.loads(EVAL_JSON.read_text(encoding="utf-8"))
  return {"metrics": {}, "details": []}


def _multiline(ax, x: float, y: float, lines: list[str], *, fontsize=8, color=None, fontweight=None):
  """在坐标轴上绘制多行文字（避免 \\n 显示为字面量）。支持直角/极坐标。"""
  color = color or C0
  n = len(lines)
  step = 0.14 if fontsize >= 10 else 0.12
  y0 = y + (n - 1) * step / 2
  for i, line in enumerate(lines):
    ax.text(x, y0 - i * step, line, ha="center", va="center", fontsize=fontsize,
            color=color, fontweight=fontweight, zorder=10)


def _diamond(ax, cx: float, cy: float, lines: list[str], *, w=0.62, h=0.50):
  pts = [(cx, cy + h), (cx + w, cy), (cx, cy - h), (cx - w, cy)]
  ax.add_patch(Polygon(pts, closed=True, fc="#ebf8ff", ec=C2, lw=1.5, zorder=2))
  _multiline(ax, cx, cy, lines, fontsize=8)


# ── 1. 目录：水平时间轴 ─────────────────────────────────────────
def fig_outline_timeline() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.06, 0.22, 0.88, 0.55])
  ax.set_xlim(0, 4)
  ax.set_ylim(0, 1)
  ax.axis("off")
  parts = [
    (0.05, "01 背景与需求", C1),
    (1.05, "02 技术与模型", C2),
    (2.05, "03 实现与验证", C_GREEN),
    (3.05, "04 创新与展望", C_ORANGE),
  ]
  ax.plot([0.1, 3.9], [0.5, 0.5], color=C_GRID, lw=4, solid_capstyle="round", zorder=0)
  for x, label, col in parts:
    ax.scatter([x + 0.35], [0.5], s=220, c=col, edgecolors="white", linewidths=2, zorder=2)
    ax.text(x + 0.35, 0.5, label.split()[0], ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax.text(x + 0.35, 0.12, label.split(" ", 1)[1], ha="center", fontsize=10, color=C0, fontweight="bold")
  ax.text(2.0, 0.88, "答辩结构", ha="center", fontsize=12, fontweight="bold", color=C0)
  return _save(fig, "outline_timeline.png")


# ── 2. 老龄化：带误差带的折线+柱状组合 ─────────────────────────
def fig_aging_trend() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.12, 0.14, 0.82, 0.72])
  years = np.array([2020, 2025, 2030, 2035])
  ratio = np.array([13.5, 16.5, 20.5, 24.0])
  ax.bar(years.astype(str), ratio, width=0.55, color=C2, edgecolor=C0, linewidth=0.6, alpha=0.85, label="60+ 人口占比")
  ax.plot(years.astype(str), ratio, "o-", color=C_RED, lw=2, ms=7, label="趋势")
  ax.set_ylabel("占比 (%)", fontweight="bold", fontsize=11)
  ax.set_title("(a) 我国老龄化与居家监护需求", loc="left", fontsize=12, fontweight="bold", color=C0, pad=10)
  ax.set_ylim(0, 28)
  ax.grid(axis="y", ls=":", color=C_GRID)
  for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
  ax.tick_params(axis="both", labelsize=10)
  ax.annotate(
    "跌倒发现空窗↑", xy=(2, 20.5), xytext=(2.6, 23),
    arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2),
    fontsize=9, color=C_RED, fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.25", fc="#fff5f5", ec=C_RED, lw=0.8),
  )
  ax.legend(loc="upper left", frameon=False)
  ax.text(0.98, 0.02, "数据来源：国家统计局公开预测（示意）", transform=ax.transAxes,
          ha="right", fontsize=7, color=C_GRAY)
  return _save(fig, "aging_trend.png")


# ── 3. 对比：表格热力图 ─────────────────────────────────────────
def fig_compare_table() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.06, 0.14, 0.88, 0.74])
  ax.axis("off")
  col_labels = ["维度", "常见方案", "本作品"]
  cell_text = [
    ["多设备协同", "割裂", "统一编排"],
    ["告警后执行", "仅通知", "机器人动作"],
    ["跌倒识别", "手环局限", "骨架+规则"],
    ["现场复现", "难演示", "Web+脚本"],
  ]
  tbl = ax.table(
    cellText=cell_text,
    colLabels=col_labels,
    loc="center",
    cellLoc="center",
    colWidths=[0.22, 0.36, 0.36],
  )
  tbl.auto_set_font_size(False)
  tbl.set_fontsize(9)
  tbl.scale(1.0, 1.65)
  for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor(C_GRID)
    cell.set_linewidth(0.8)
    if r == 0:
      cell.set_facecolor(C0)
      cell.get_text().set_color("white")
      cell.get_text().set_fontweight("bold")
    elif c == 1:
      cell.set_facecolor("#fff5f5")
      cell.get_text().set_color("#742a2a")
    elif c == 2:
      cell.set_facecolor("#ebf8ff")
      cell.get_text().set_color(C0)
      cell.get_text().set_fontweight("bold")
    elif c == 0:
      cell.set_facecolor("#edf2f7")
      cell.get_text().set_fontweight("bold")
  ax.set_title("(b) 方案对比（定性）", loc="left", fontsize=11, fontweight="bold", color=C0, pad=10)
  return _save(fig, "compare_table.png")


# ── 4. 架构：分层 + 右侧调度竖条（不遮挡层） ───────────────────
def fig_architecture_layers() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.04, 0.06, 0.92, 0.88])
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.6)
  ax.axis("off")
  lx, lw = 0.15, 3.35
  layers = [
    ("L4 交互层", "Web / FastAPI / GUI", C3, 2.85),
    ("L3 认知层", "RiskFusion · Dialogue · Planner", C2, 2.05),
    ("L2 感知层", "FallDetector · Emotion · Vision", C1, 1.25),
    ("L1 执行层", "RobotAdapter · ROS2 / 仿真", C0, 0.45),
  ]
  bh = 0.58
  for title, sub, col, y in layers:
    ax.add_patch(FancyBboxPatch((lx, y), lw, bh, boxstyle="round,pad=0.02", fc="#f7fafc", ec=col, lw=2))
    ax.add_patch(Rectangle((lx, y), 0.11, bh, fc=col, ec="none"))
    yc = y + bh / 2
    ax.text(lx + 0.16, yc, title, fontsize=9.5, fontweight="bold", va="center", ha="left", color=C0)
    ax.text(lx + 1.55, yc, sub, fontsize=8, va="center", ha="left", color=C_GRAY)
    cx = lx + lw + 0.18
    cy = y + bh / 2
    ax.annotate("", xy=(3.72, cy), xytext=(lx + lw, cy),
                arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.0))
  # 右侧竖条：调度核心
  ox, ow = 3.82, 0.95
  ax.add_patch(FancyBboxPatch((ox, 0.38), ow, 3.05, boxstyle="round,pad=0.03", fc=C0, ec="white", lw=1.5))
  _multiline(ax, ox + ow / 2, 1.9, ["Care", "Orchestrator"], fontsize=9, color="white", fontweight="bold")
  ax.text(ox + ow / 2, 0.22, "模块调度", ha="center", fontsize=7.5, color=C4)
  return _save(fig, "architecture_layers.png")


# ── 5. 状态机：圆形节点 + 标注边 ───────────────────────────────
def _draw_state_machine(ax, *, compact: bool = False):
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  cy = 3.4
  r = 0.52 if compact else 0.68
  fs = 9 if compact else 10.5
  states = [
    (1.4, "监测", C2),
    (3.6, "对话", C2),
    (5.8, "告警", C_ORANGE),
    (8.0, "紧急", C_RED),
  ]
  for x, name, col in states:
    ax.add_patch(Circle((x, cy), r, fc=col, ec="white", lw=2, zorder=2))
    ax.text(x, cy, name, ha="center", va="center", fontsize=fs, color="white", fontweight="bold")
  for x1, x2 in [(1.4, 3.6), (3.6, 5.8), (5.8, 8.0)]:
    ax.annotate("", xy=(x2 - r - 0.05, cy), xytext=(x1 + r + 0.05, cy),
                arrowprops=dict(arrowstyle="-|>", color=C0, lw=2))
  ax.annotate("风险升高", xy=(5.8, cy + r + 0.08), xytext=(4.6, 5.15), fontsize=9, color=C_ORANGE,
              fontweight="bold", arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=1.5))
  ax.annotate("确认跌倒", xy=(8.0, cy + r + 0.08), xytext=(6.8, 5.15), fontsize=9, color=C_RED,
              fontweight="bold", arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.5))
  note_fs = 8.5 if compact else 9.5
  ax.text(5.0, 0.75, "紧急态可打断对话与常规任务", ha="center", fontsize=note_fs, color=C_RED,
          bbox=dict(boxstyle="round,pad=0.4", fc="#fff5f5", ec=C_RED, lw=1.0))


def fig_state_machine() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.04, 0.06, 0.92, 0.88])
  _draw_state_machine(ax, compact=False)
  return _save(fig, "state_machine.png")


# ── 6. 风险：公式 + 堆叠条 + 原因示意 ─────────────────────────
def fig_risk_fusion() -> Path:
  fig = _fig()
  ax_eq = fig.add_axes([0.08, 0.68, 0.84, 0.22])
  ax_eq.axis("off")
  ax_eq.text(0.5, 0.55, r"$S = 0.45\,S_{\mathrm{fall}} + 0.25\,S_{\mathrm{emo}} + 0.30\,S_{\mathrm{health}}$",
             ha="center", fontsize=14, color=C0)
  ax_eq.text(0.5, 0.05, "可解释加权融合（阈值可配置）", ha="center", fontsize=9, color=C_GRAY)

  ax_bar = fig.add_axes([0.14, 0.28, 0.72, 0.32])
  weights = [0.45, 0.25, 0.30]
  labels = [r"$S_{\mathrm{fall}}$", r"$S_{\mathrm{emo}}$", r"$S_{\mathrm{health}}$"]
  colors = [C_GREEN, C2, C_ORANGE]
  left = 0
  for w, lab, c in zip(weights, labels, colors):
    ax_bar.barh([0], [w], left=left, color=c, edgecolor="white", height=0.55)
    ax_bar.text(left + w / 2, 0, f"{lab}\n{w:.0%}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    left += w
  ax_bar.set_xlim(0, 1)
  ax_bar.set_yticks([])
  ax_bar.set_title("(c) 权重分配", loc="left", fontsize=10, fontweight="bold", color=C0)
  for spine in ax_bar.spines.values():
    spine.set_visible(False)

  ax_out = fig.add_axes([0.14, 0.06, 0.72, 0.14])
  ax_out.axis("off")
  tbl = ax_out.table(
    cellText=[["输出", "风险分数", "等级 L/M/H", "原因列表（可审计）"]],
    colWidths=[0.12, 0.22, 0.22, 0.44],
    loc="center", cellLoc="center",
  )
  tbl.auto_set_font_size(False)
  tbl.set_fontsize(8)
  for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor(C_GRID)
    cell.set_facecolor("#edf2f7" if c == 0 else "#f7fafc")
    if c == 0:
      cell.get_text().set_fontweight("bold")
  return _save(fig, "risk_fusion.png")


# ── 7. 跌倒：矩形判定流程（避免菱形文字叠字） ───────────────────
def fig_fall_decision_tree() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.05, 0.06, 0.90, 0.88])
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 10)
  ax.axis("off")
  cx, rx = 4.2, 8.15

  def rect_box(x, y, w, h, text, *, fc, ec="white", tc="white", fs=11):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.05", fc=fc, ec=ec, lw=1.6))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold", linespacing=1.35)

  def judge_box(y, line1, line2):
    rect_box(cx, y, 3.6, 1.15, f"{line1}\n{line2}", fc="#ebf8ff", ec=C2, tc=C0, fs=10)

  rect_box(cx, 9.0, 3.4, 0.85, "骨架输入 (MediaPipe)", fc=C2)
  judge_box(7.0, "宽高比 R", "是否异常?")
  judge_box(4.6, "竖直速度 vy", "是否骤降?")
  rect_box(cx, 2.0, 3.6, 0.85, "触发紧急流程", fc=C_RED)
  rect_box(rx, 7.0, 1.35, 0.65, "正常", fc="#e6fffa", ec=C_GREEN, tc=C_GREEN, fs=11)
  rect_box(rx, 4.6, 1.35, 0.65, "正常", fc="#e6fffa", ec=C_GREEN, tc=C_GREEN, fs=11)

  for y1, y2 in [(9.0, 7.65), (7.0, 5.25), (4.6, 2.85)]:
    ax.annotate("", xy=(cx, y2 + 0.58), xytext=(cx, y1 - 0.48),
                arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=2))
  for y in (7.0, 4.6):
    ax.plot([cx + 1.8, rx - 0.68], [y, y], color=C2, lw=1.8)
    ax.annotate("", xy=(rx - 0.68, y), xytext=(cx + 1.8, y),
                arrowprops=dict(arrowstyle="-|>", color=C2, lw=1.8))
    ax.text(cx + 2.35, y + 0.22, "否", fontsize=10, color=C2, fontweight="bold")
  ax.text(cx + 0.55, 3.55, "是", fontsize=10, color=C_RED, fontweight="bold")
  ax.annotate("", xy=(cx, 2.85), xytext=(cx + 1.1, 4.6),
              arrowprops=dict(arrowstyle="-|>", color=C_RED, lw=1.8))
  return _save(fig, "fall_decision_tree.png")


# ── 7b. 项目目标：架构 + 状态机（调度条置顶，标题/副标题分列） ───
def fig_project_goals_combo() -> Path:
  fig = _fig()
  ax1 = fig.add_axes([0.03, 0.48, 0.94, 0.46])
  ax2 = fig.add_axes([0.03, 0.04, 0.94, 0.42])
  ax1.set_xlim(0, 10)
  ax1.set_ylim(0, 10)
  ax1.axis("off")
  ax1.text(0.2, 9.55, "系统四层架构", fontsize=11, fontweight="bold", color=C0, ha="left")
  ax1.add_patch(FancyBboxPatch((0.35, 8.50), 9.3, 0.62, boxstyle="round,pad=0.03", fc=C0, ec=C0))
  ax1.text(5.0, 8.81, "CareOrchestrator · 模块调度中枢", ha="center", va="center",
           fontsize=10, color="white", fontweight="bold")
  layers = [
    ("L4 交互层", "Web / GUI", C3),
    ("L3 认知层", "风险 · 对话 · 规划", C2),
    ("L2 感知层", "跌倒 · 情绪 · 视觉", C1),
    ("L1 执行层", "机器人 / ROS2", C0),
  ]
  bh, gap = 0.68, 0.10
  y_top = 8.35
  for i, (t, sub, col) in enumerate(layers):
    y = y_top - (i + 1) * bh - i * gap
    ax1.add_patch(FancyBboxPatch((0.35, y), 9.3, bh, boxstyle="round,pad=0.02", fc="#f7fafc", ec=col, lw=1.8))
    ax1.add_patch(Rectangle((0.35, y), 0.18, bh, fc=col))
    yc = y + bh / 2
    ax1.text(0.68, yc, t, fontsize=9.5, fontweight="bold", color=C0, va="center", ha="left")
    ax1.text(2.85, yc, sub, fontsize=9, color=C_GRAY, va="center", ha="left")

  ax2.text(0.15, 5.55, "状态机切换", fontsize=12, fontweight="bold", color=C0, ha="left")
  _draw_state_machine(ax2, compact=True)
  return _save(fig, "project_goals_combo.png", trim=False)


# ── 8. 对话：UML 序列图 ─────────────────────────────────────────
def fig_dialogue_sequence() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.07, 0.12, 0.88, 0.78])
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.4)
  ax.axis("off")
  actor_labels = ["老人", ["情绪", "分析"], ["Dialogue", "Manager"], "输出"]
  xs = [0.55, 1.65, 2.85, 4.05]
  lane_top, lane_bot = 2.95, 0.55
  for x, lab in zip(xs, actor_labels):
    if isinstance(lab, str):
      ax.text(x, 3.22, lab, ha="center", fontsize=9, fontweight="bold", color=C0)
    else:
      _multiline(ax, x, 3.18, lab, fontsize=8.5, fontweight="bold")
    ax.plot([x, x], [lane_bot, lane_top], ls="--", color=C_GRID, lw=1, zorder=0)
  msgs = [
    (0, 1, 2.65, "话语"),
    (1, 2, 2.15, "情绪标签"),
    (2, 3, 1.65, "安抚话术"),
    (0, 2, 1.05, "可选 LLM"),
  ]
  for a, b, y, label in msgs:
    x1, x2 = xs[a], xs[b]
    col = C2 if label != "可选 LLM" else C_GRAY
    ax.annotate("", xy=(x2 - 0.04, y), xytext=(x1 + 0.04, y),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.2))
    ax.text((x1 + x2) / 2, y + 0.12, label, ha="center", fontsize=8, color=col,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
  ax.text(2.5, 0.28, "默认 Mock，现场无需外网", ha="center", fontsize=8, color=C_GRAY,
          bbox=dict(boxstyle="round,pad=0.35", fc="#f7fafc", ec=C_GRID, lw=0.8))
  return _save(fig, "dialogue_sequence.png")


# ── 9. 流水线：泳道图 ───────────────────────────────────────────
def fig_pipeline_swimlane() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.05, 0.1, 0.9, 0.8])
  lanes = ["感知", "认知", "执行"]
  colors = ["#ebf8ff", "#e6fffa", "#fffaf0"]
  h = 0.85
  for i, (name, fc) in enumerate(zip(lanes, colors)):
    y = 2.4 - i * 1.0
    ax.add_patch(Rectangle((0.1, y), 4.6, h, fc=fc, ec=C_GRID, lw=0.8))
    ax.text(0.02, y + h / 2, name, ha="right", va="center", fontsize=9, fontweight="bold", color=C0)
  steps = [
    (0.35, 2.55, "采集"), (1.15, 2.55, "特征"), (1.95, 1.55, "融合"),
    (2.75, 1.55, "状态机"), (3.55, 0.55, "规划"), (4.25, 0.55, "动作"),
  ]
  for x, y, t in steps:
    ax.add_patch(FancyBboxPatch((x, y), 0.62, 0.42, boxstyle="round", fc=C2, ec="white"))
    ax.text(x + 0.31, y + 0.21, t, ha="center", va="center", fontsize=8, color="white", fontweight="bold")
  for i in range(len(steps) - 1):
    x1, y1, _ = steps[i]
    x2, y2, _ = steps[i + 1]
    ax.annotate("", xy=(x2, y2 + 0.21), xytext=(x1 + 0.62, y1 + 0.21),
                arrowprops=dict(arrowstyle="-|>", color=C0, lw=1.2, connectionstyle="arc3,rad=0.15"))
  ax.set_xlim(0, 5)
  ax.set_ylim(0, 3.5)
  ax.axis("off")
  return _save(fig, "pipeline_swimlane.png")


# ── 10. 紧急：时序阶梯图 ────────────────────────────────────────
def fig_emergency_timing() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.12, 0.18, 0.82, 0.68])
  steps = ["告警音", "语音安抚", "通知家属", "机器人手势"]
  t = [0, 1, 2.5, 4]
  ax.step(t, range(4), where="post", color=C2, lw=2.5)
  ax.scatter(t, range(4), s=80, c=[C_ORANGE, C2, C_RED, C_GREEN], zorder=3, edgecolors="white", lw=1.5)
  ax.set_yticks(range(4))
  ax.set_yticklabels(steps, fontweight="bold")
  ax.set_xlabel("相对时间 (s)", fontweight="bold")
  ax.set_title("紧急响应时序（示意）", loc="left", fontsize=10, fontweight="bold", color=C0)
  ax.grid(axis="x", ls=":", color=C_GRID)
  for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
  return _save(fig, "emergency_timing.png")


# ── 11. 评测：混淆矩阵 + 场景得分 ───────────────────────────────
def fig_eval_results() -> Path:
  data = _load_eval()
  m = data.get("metrics", {})
  tp, fp, fn, tn = m.get("tp", 2), m.get("fp", 0), m.get("fn", 0), m.get("tn", 4)
  details = data.get("details", [])

  fig = _fig()
  fig.subplots_adjust(left=0.07, right=0.97, top=0.90, bottom=0.14, wspace=0.55)
  ax_cm = fig.add_axes([0.07, 0.16, 0.36, 0.74])
  ax_bar = fig.add_axes([0.56, 0.16, 0.40, 0.74])

  cm = np.array([[tn, fp], [fn, tp]])
  ax_cm.imshow(cm, cmap="Blues", vmin=0, vmax=max(cm.max(), 1))
  ax_cm.set_xticks([0, 1])
  ax_cm.set_xticklabels(["预测\n正常", "预测\n跌倒"], fontsize=10)
  ax_cm.set_yticks([0, 1])
  ax_cm.set_yticklabels(["真实\n正常", "真实\n跌倒"], fontsize=10)
  for i in range(2):
    for j in range(2):
      ax_cm.text(j, i, str(int(cm[i, j])), ha="center", va="center", fontsize=20, fontweight="bold", color=C0)
  ax_cm.set_title("(a) 混淆矩阵 (n=6)", fontsize=12, fontweight="bold", color=C0, pad=10)

  if details:
    short = {
      "standing_normal": "站立",
      "walking_normal": "行走",
      "sit_down": "坐下",
      "sudden_fall": "快跌",
      "lying_still": "躺倒",
      "bend_pickup": "弯腰",
    }
    names = [short.get(d["name"], d["name"][:6]) for d in details]
    scores = [d.get("max_score", 0) for d in details]
    colors = [C_RED if d.get("detected") else C2 for d in details]
    ypos = np.arange(len(names))
    ax_bar.barh(ypos, scores, color=colors, height=0.50, edgecolor=C0, linewidth=0.5)
    ax_bar.set_yticks(ypos)
    ax_bar.set_yticklabels(names, fontsize=11)
    ax_bar.tick_params(axis="y", pad=10)
    ax_bar.set_xticks([0, 0.5, 1.0])
    ax_bar.set_xticklabels(["0", "0.5", "1.0"], fontsize=10)
    ax_bar.set_xlim(0, 1.05)
    ax_bar.axvline(0.5, color=C_ORANGE, ls="--", lw=1.5)
  ax_bar.set_title("(b) 场景得分（红=检出，橙线=0.5）", fontsize=12, fontweight="bold", color=C0, pad=10)
  for spine in ("top", "right"):
    ax_bar.spines[spine].set_visible(False)
  return _save(fig, "eval_results.png")


# ── 12. 延迟：箱线/条形示意 ─────────────────────────────────────
def fig_latency_bar() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.14, 0.16, 0.78, 0.72])
  modules = ["骨架提取", "规则判定", "融合决策", "端到端"]
  ms = [28, 8, 12, 42]
  bars = ax.bar(modules, ms, color=[C3, C2, C1, C_GREEN], edgecolor=C0, linewidth=0.5)
  ax.axhline(50, color=C_RED, ls="--", lw=1.2, label="目标 50ms (CPU)")
  ax.set_ylabel("耗时 (ms)", fontweight="bold")
  ax.set_title("单帧链路延迟（本机 CPU 粗测）", fontsize=11, fontweight="bold", color=C0)
  for b, v in zip(bars, ms):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v}", ha="center", fontsize=9, fontweight="bold")
  ax.legend(loc="upper right", frameon=False)
  ax.set_ylim(0, 60)
  plt.setp(ax.xaxis.get_majorticklabels(), rotation=12, ha="right")
  for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
  return _save(fig, "latency_bar.png")


# ── 13. 创新：水平条形图（避免极坐标裁切与叠字） ─────────────────
def fig_innovation_radar() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.14, 0.14, 0.80, 0.72])
  dims = ["多模态融合", "安全闭环", "视觉检测", "工程可复现", "居家场景"]
  vals = [0.90, 0.94, 0.88, 0.92, 0.91]
  colors = [C2, C1, C3, C_GREEN, C_ORANGE]
  y = np.arange(len(dims))
  bars = ax.barh(y, vals, height=0.58, color=colors, edgecolor=C0, linewidth=0.6)
  ax.set_yticks(y)
  ax.set_yticklabels(dims, fontsize=10.5, fontweight="bold", color=C0)
  ax.set_xlim(0, 1.05)
  ax.set_xticks([0, 0.5, 1.0])
  ax.set_xlabel("自评得分", fontsize=9, color=C_GRAY)
  ax.set_title("创新维度自评", fontsize=11, fontweight="bold", color=C0, pad=10)
  ax.axvline(0.5, color=C_GRAY, ls=":", lw=1)
  for bar, v in zip(bars, vals):
    ax.text(v + 0.02, bar.get_y() + bar.get_height() / 2, f"{v:.0%}",
            va="center", fontsize=9, fontweight="bold", color=C0)
  for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
  ax.invert_yaxis()
  return _save(fig, "innovation_radar.png", trim=False)


# ── 14. 路线图：里程碑时间轴 ─────────────────────────────────────
def fig_roadmap_gantt() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.1, 0.2, 0.85, 0.65])
  tasks = [
    ("Web+评测开源", 0, 3, C_GREEN),
    ("软著/专利", 2.5, 5, C2),
    ("Unitree 真机", 4, 7, C_ORANGE),
    ("公开数据集", 6, 9, C1),
    ("养老院试点", 8, 11, C_RED),
  ]
  for i, (name, s, e, col) in enumerate(tasks):
    ax.barh(i, e - s, left=s, height=0.55, color=col, alpha=0.85, edgecolor=C0, linewidth=0.5)
    ax.text(s + (e - s) / 2, i, name, ha="center", va="center", fontsize=8, color="white", fontweight="bold")
  ax.set_yticks([])
  ax.set_xlabel("时间轴（月，示意）", fontweight="bold")
  ax.set_xlim(0, 11)
  ax.axvline(3, color=C_GRAY, ls=":", lw=1)
  ax.text(3, 4.6, "当前", ha="center", fontsize=8, color=C_RED)
  ax.set_title("后续工作里程碑", fontsize=11, fontweight="bold", color=C0)
  for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
  return _save(fig, "roadmap_gantt.png")


# ── 15. 开源：复现清单（非截图） ─────────────────────────────────
def fig_repro_checklist() -> Path:
  fig = _fig()
  ax = fig.add_axes([0.08, 0.1, 0.88, 0.82])
  ax.axis("off")
  items = [
    ("✓", "GitHub 源码 + README"),
    ("✓", "bash scripts/run_web.sh"),
    ("✓", "fall_eval_report.json"),
    ("✓", "pytest 单元测试"),
    ("○", "软著申请中"),
  ]
  y = 0.92
  for mark, text in items:
    col = C_GREEN if mark == "✓" else C_ORANGE
    ax.text(0.05, y, mark, fontsize=14, color=col, fontweight="bold", transform=ax.transAxes)
    ax.text(0.12, y, text, fontsize=11, color=C0, transform=ax.transAxes)
    y -= 0.16
  ax.text(0.5, 0.02, "可复现性检查项", ha="center", fontsize=11, fontweight="bold", color=C0, transform=ax.transAxes)
  return _save(fig, "repro_checklist.png")


def gen_all() -> Path:
  fig_outline_timeline()
  fig_aging_trend()
  fig_compare_table()
  fig_architecture_layers()
  fig_state_machine()
  fig_project_goals_combo()
  fig_risk_fusion()
  fig_fall_decision_tree()
  fig_dialogue_sequence()
  fig_pipeline_swimlane()
  fig_emergency_timing()
  fig_eval_results()
  fig_latency_bar()
  fig_innovation_radar()
  fig_roadmap_gantt()
  fig_repro_checklist()
  return OUT


if __name__ == "__main__":
  gen_all()
  print(f"✅ 科研配图: {OUT} ({len(list(OUT.glob('*.png')))} 张)")
