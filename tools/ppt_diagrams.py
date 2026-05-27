#!/usr/bin/env python3
"""生成答辩 PPT 用理论框图、流程图、数据图（纯图形，标题由 pptx 写入）。"""
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

_cjk_paths = [
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
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
C_LIGHT = "#EFF6FF"


def _save(fig, name: str) -> Path:
  OUT.mkdir(parents=True, exist_ok=True)
  p = OUT / name
  fig.savefig(p, dpi=180, bbox_inches="tight", facecolor=C_BG, edgecolor="none", pad_inches=0.15)
  plt.close(fig)
  return p


def _box(ax, xy, wh, text, color, fontsize=10, text_color="white"):
  x, y = xy
  w, h = wh
  patch = FancyBboxPatch(
    (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.1",
    facecolor=color, edgecolor="white", linewidth=1.8,
  )
  ax.add_patch(patch)
  ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
          fontsize=fontsize, color=text_color, fontweight="bold", wrap=True)


def gen_cover_banner() -> Path:
  """装饰底图：无文字，避免与 pptx 标题叠加重复。"""
  fig, ax = plt.subplots(figsize=(12.8, 7.2))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  # 渐变底
  for i in range(80):
    t = i / 79
    c = plt.cm.Blues(0.35 + 0.45 * t)
    ax.add_patch(mpatches.Rectangle((0, 6 * t / 80 * 79), 10, 6 / 80 + 0.02, facecolor=c, edgecolor="none"))
  ax.add_patch(mpatches.Rectangle((0, 0), 10, 6, facecolor=C_DARK, alpha=0.72))
  # 装饰圆与连线
  for cx, cy, r, a in [(1.2, 4.8, 0.55, 0.15), (8.5, 1.5, 0.7, 0.2), (9.0, 5.0, 0.35, 0.1)]:
    ax.add_patch(mpatches.Circle((cx, cy), r, facecolor="white", alpha=a, edgecolor="none"))
  ax.plot([0.5, 3.5, 6.0], [1.0, 2.2, 1.4], color="white", alpha=0.12, lw=2)
  ax.plot([7.0, 9.2], [4.5, 3.0], color="#93C5FD", alpha=0.25, lw=3)
  return _save(fig, "cover_banner.png")


def gen_team_card() -> Path:
  fig, ax = plt.subplots(figsize=(8, 6))
  ax.axis("off")
  ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, transform=ax.transAxes,
             boxstyle="round,pad=0.02", facecolor="white", edgecolor=C_BLUE, linewidth=2.5))
  ax.add_patch(mpatches.Rectangle((0.02, 0.88), 0.96, 0.1, transform=ax.transAxes,
                                  facecolor=C_DARK, edgecolor="none"))
  ax.text(0.5, 0.93, "参赛信息", transform=ax.transAxes, ha="center", fontsize=14,
          color="white", fontweight="bold")
  fields = [
    ("团队", "从容应队"), ("学校", "中山大学"), ("省份", "广东"),
    ("队长", "刘小凡"), ("队员", "白冉"), ("指导教师", "彭键清"),
    ("团队编号", "CRAIC2026-TEAM-8FJQKLMI"), ("作品编号", "CRAIC20264ZEFT1DF"),
  ]
  y = 0.78
  for k, v in fields:
    ax.add_patch(mpatches.Rectangle((0.06, y - 0.02), 0.22, 0.07, transform=ax.transAxes,
                                    facecolor=C_LIGHT, edgecolor="none"))
    ax.text(0.17, y + 0.015, k, fontsize=11, color=C_GRAY, transform=ax.transAxes, ha="center", fontweight="bold")
    ax.text(0.34, y + 0.015, v, fontsize=11, color=C_DARK, transform=ax.transAxes, fontweight="bold")
    y -= 0.095
  return _save(fig, "team_card.png")


def gen_aging_chart() -> Path:
  fig, ax = plt.subplots(figsize=(8, 5.2))
  years = ["2020", "2025", "2030", "2035"]
  ratio = [13.5, 16.5, 20.5, 24.0]
  bars = ax.bar(years, ratio, color=[C_BLUE, C_CYAN, C_ORANGE, C_RED], width=0.55, edgecolor="white", linewidth=1.5)
  ax.set_ylabel("60岁及以上人口占比 (%)", fontsize=11, fontweight="bold")
  ax.set_title("我国老龄化趋势（国家统计局示意）", fontsize=14, color=C_DARK, fontweight="bold", pad=12)
  ax.set_ylim(0, 28)
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)
  ax.grid(axis="y", alpha=0.35, linestyle="--")
  for b, v in zip(bars, ratio):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v}%", ha="center", fontsize=11, fontweight="bold", color=C_DARK)
  ax.annotate("跌倒发现空窗期风险上升", xy=(2.2, 21), fontsize=10, color=C_RED, fontweight="bold",
              bbox=dict(boxstyle="round", facecolor="#FEE2E2", edgecolor=C_RED, alpha=0.9),
              arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.5))
  fig.tight_layout()
  return _save(fig, "aging_chart.png")


def gen_compare_diagram() -> Path:
  fig, ax = plt.subplots(figsize=(10, 5.8))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  ax.text(2.5, 5.55, "传统方案 · 局限", ha="center", fontsize=14, color=C_RED, fontweight="bold")
  ax.text(7.5, 5.55, "本作品 · 优势", ha="center", fontsize=14, color=C_DARK, fontweight="bold")
  left = ["智能音箱\n功能割裂", "摄像头\n只告警不断环", "手环\n难检慢速跌倒", "毕设原型\n难部署复现"]
  right = ["多模态\n风险融合", "可解释\n决策输出", "机器人\n动作执行", "开源\nWeb可演示"]
  for i, (l, r) in enumerate(zip(left, right)):
    y = 4.15 - i * 1.05
    _box(ax, (0.25, y), (3.9, 0.9), l, "#FEE2E2", fontsize=10, text_color="#991B1B")
    _box(ax, (5.85, y), (3.9, 0.9), r, "#DBEAFE", fontsize=10, text_color=C_DARK)
    ax.annotate("", xy=(5.75, y + 0.45), xytext=(4.2, y + 0.45),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=2))
  return _save(fig, "compare.png")


def gen_architecture() -> Path:
  fig, ax = plt.subplots(figsize=(10, 6.2))
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
    _box(ax, (0.8, y), (8.4, 1.15), f"{title}\n{desc}", col, fontsize=11)
    y -= 1.55
  _box(ax, (3.2, 0.25), (3.6, 1.0), "CareOrchestrator\n状态机调度核心", C_DARK, fontsize=10)
  for y0 in [6.5, 4.95, 3.4, 1.85]:
    ax.add_patch(FancyArrowPatch((5, y0), (5, y0 - 0.32), arrowstyle="-|>", color=C_GRAY, lw=2.5))
  return _save(fig, "architecture.png")


def gen_state_machine() -> Path:
  fig, ax = plt.subplots(figsize=(10, 5.2))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 5)
  ax.axis("off")
  states = [("MONITOR\n监测", 0.8), ("CONVERSE\n对话", 3.2), ("ALERT\n告警", 5.6), ("EMERGENCY\n紧急", 8.0)]
  for label, x in states:
    col = C_RED if "EMERGENCY" in label else C_BLUE
    _box(ax, (x, 2.1), (1.9, 1.25), label, col, fontsize=9)
  for x1, x2 in [(2.7, 3.2), (5.1, 5.6), (7.5, 8.0)]:
    ax.annotate("", xy=(x2, 2.7), xytext=(x1 + 1.9, 2.7),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2.5))
  ax.add_patch(FancyBboxPatch((1.5, 0.35), 7, 0.75, boxstyle="round", facecolor="#FEE2E2", edgecolor=C_RED, linewidth=1.5))
  ax.text(5, 0.72, "紧急事件硬优先级：可打断对话与常规任务", ha="center", fontsize=11, color=C_RED, fontweight="bold")
  return _save(fig, "state_machine.png")


def gen_risk_formula() -> Path:
  fig, ax = plt.subplots(figsize=(9, 5.8))
  ax.axis("off")
  ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.94, transform=ax.transAxes,
             boxstyle="round", facecolor="white", edgecolor=C_BLUE, linewidth=2))
  ax.text(0.5, 0.88, "多模态风险融合模型", ha="center", fontsize=16, color=C_DARK,
          fontweight="bold", transform=ax.transAxes)
  ax.text(0.5, 0.68, r"$S = 0.45 \cdot S_{fall} + 0.25 \cdot S_{emo} + 0.30 \cdot S_{health}$",
          ha="center", fontsize=17, color=C_BLUE, transform=ax.transAxes)
  items = [
    ("S_fall", "骨架宽高比\n垂直速度", C_GREEN),
    ("S_emo", "情感词典\n情绪标签", C_CYAN),
    ("S_health", "心率血氧\n活动量", C_ORANGE),
  ]
  x = 0.1
  for name, desc, col in items:
    ax.add_patch(FancyBboxPatch((x, 0.28), 0.24, 0.32, transform=ax.transAxes,
                 boxstyle="round,pad=0.02", facecolor=col, edgecolor="white", linewidth=1.5))
    ax.text(x + 0.12, 0.52, name, transform=ax.transAxes, ha="center", color="white", fontweight="bold", fontsize=12)
    ax.text(x + 0.12, 0.36, desc, transform=ax.transAxes, ha="center", fontsize=9, color="white")
    x += 0.30
  ax.text(0.5, 0.1, "输出：风险分数 · 等级 · 可解释原因列表", ha="center", fontsize=11,
          color=C_DARK, fontweight="bold", transform=ax.transAxes)
  return _save(fig, "risk_formula.png")


def gen_fall_flow() -> Path:
  fig, ax = plt.subplots(figsize=(9, 6.2))
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
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=2))
  return _save(fig, "fall_flow.png")


def gen_pipeline() -> Path:
  fig, ax = plt.subplots(figsize=(10, 4.2))
  ax.set_xlim(0, 12)
  ax.set_ylim(0, 3)
  ax.axis("off")
  nodes = ["感知采集", "特征提取", "风险融合", "状态机", "规划动作", "机器人执行"]
  xs = [0.4, 2.2, 4.0, 5.8, 7.6, 9.4]
  for x, n in zip(xs, nodes):
    _box(ax, (x, 0.9), (1.55, 1.1), n, C_BLUE, fontsize=9)
  for x1, x2 in zip(xs[:-1], xs[1:]):
    ax.annotate("", xy=(x2, 1.45), xytext=(x1 + 1.55, 1.45),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2.5))
  return _save(fig, "pipeline.png")


def gen_emergency_flow() -> Path:
  fig, ax = plt.subplots(figsize=(10, 3.8))
  ax.set_xlim(0, 12)
  ax.set_ylim(0, 2.8)
  ax.axis("off")
  steps = ["alert_sound\n告警音", "speak\n语音安抚", "call_emergency\n家属通知", "raise_hand\n举手示意"]
  xs = [0.3, 3.1, 5.9, 8.7]
  cols = [C_ORANGE, C_BLUE, C_RED, C_GREEN]
  for x, s, c in zip(xs, steps, cols):
    _box(ax, (x, 0.55), (2.3, 1.3), s, c, fontsize=9)
  for i in range(3):
    ax.annotate("", xy=(xs[i + 1], 1.2), xytext=(xs[i] + 2.3, 1.2),
                arrowprops=dict(arrowstyle="-|>", color=C_DARK, lw=2.5))
  return _save(fig, "emergency_flow.png")


def gen_metrics_chart() -> Path:
  fig, ax = plt.subplots(figsize=(8, 5.2))
  labels = ["Precision", "Recall", "F1", "紧急触发率"]
  vals = [100, 100, 100, 100]
  colors = [C_BLUE, C_CYAN, C_GREEN, C_ORANGE]
  bars = ax.barh(labels, vals, color=colors, height=0.52, edgecolor="white", linewidth=1.2)
  ax.set_xlim(0, 110)
  ax.set_title("跌倒检测与紧急链路评测（合成6场景）", fontsize=13, color=C_DARK, fontweight="bold", pad=14)
  ax.set_xlabel("指标值 (%)", fontweight="bold")
  ax.axvline(90, color=C_RED, linestyle="--", alpha=0.6, linewidth=2)
  ax.text(91, 3.35, "优秀线 90%", fontsize=9, color=C_RED)
  for b, v in zip(bars, vals):
    ax.text(v - 10, b.get_y() + b.get_height() / 2, f"{v}%", va="center", color="white", fontweight="bold", fontsize=11)
  fig.tight_layout()
  return _save(fig, "metrics_chart.png")


def gen_innovation_radar() -> Path:
  fig, ax = plt.subplots(figsize=(6.2, 6.2), subplot_kw=dict(projection="polar"))
  cats = ["多模态融合", "安全闭环", "视觉感知", "工程化", "应用价值"]
  vals = [0.92, 0.95, 0.88, 0.90, 0.93]
  angles = [n / float(len(cats)) * 2 * 3.14159 for n in range(len(cats))]
  vals_plot = vals + vals[:1]
  angles_plot = angles + angles[:1]
  ax.plot(angles_plot, vals_plot, "o-", linewidth=2.5, color=C_BLUE, markersize=8)
  ax.fill(angles_plot, vals_plot, alpha=0.28, color=C_CYAN)
  ax.set_xticks(angles)
  ax.set_xticklabels(cats, fontsize=11, fontweight="bold")
  ax.set_ylim(0, 1)
  ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
  ax.set_title("创新维度自评", fontsize=14, color=C_DARK, fontweight="bold", pad=22)
  return _save(fig, "innovation_radar.png")


def gen_roadmap() -> Path:
  fig, ax = plt.subplots(figsize=(10, 4.2))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 4)
  ax.axis("off")
  phases = [
    ("已完成", "Web演示\n评测脚本\n开源仓库", C_GREEN),
    ("进行中", "软著申请\n真机对接", C_BLUE),
    ("计划", "公开数据集\n多房间场景", C_ORANGE),
  ]
  x = 0.4
  for title, body, col in phases:
    _box(ax, (x, 0.7), (2.9, 2.6), f"{title}\n{body}", col, fontsize=11)
    if x < 7:
      ax.annotate("", xy=(x + 3.0, 2.0), xytext=(x + 2.9, 2.0),
                  arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=2))
    x += 3.15
  return _save(fig, "roadmap.png")


def gen_llm_module() -> Path:
  fig, ax = plt.subplots(figsize=(9, 5.2))
  ax.set_xlim(0, 10)
  ax.set_ylim(0, 6)
  ax.axis("off")
  _box(ax, (0.4, 3.8), (2.6, 1.3), "老人话语\n情绪标签", C_CYAN, fontsize=10)
  _box(ax, (3.5, 3.8), (3.1, 1.3), "DialogueManager\n(Mock/LLM可插拔)", C_DARK, fontsize=10)
  _box(ax, (7.0, 3.8), (2.6, 1.3), "安抚回复\n机器人话术", C_GREEN, fontsize=10)
  ax.annotate("", xy=(3.5, 4.45), xytext=(3.0, 4.45), arrowprops=dict(arrowstyle="-|>", lw=2.5, color=C_DARK))
  ax.annotate("", xy=(7.0, 4.45), xytext=(6.6, 4.45), arrowprops=dict(arrowstyle="-|>", lw=2.5, color=C_DARK))
  ax.add_patch(FancyBboxPatch((1.5, 1.8), 7, 1.2, boxstyle="round", facecolor=C_LIGHT, edgecolor=C_BLUE, linewidth=1.5))
  ax.text(5, 2.4, "默认离线 Mock 保障隐私与稳定\n可切换 OpenAI 兼容 API", ha="center", fontsize=11, color=C_DARK, fontweight="bold")
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
