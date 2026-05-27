#!/usr/bin/env python3
"""生成国赛风格答辩 PPT：docs/答辩_CareCompanion.pptx"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "答辩_CareCompanion.pptx"
ASSETS = ROOT / "docs" / "assets"
DIAG = ASSETS / "diagrams"

# 图文页布局
TITLE_TOP = 0.60
TEXT_LEFT = 0.42
TEXT_W = 4.25
IMG_LEFT = 4.82
IMG_W = 4.73
IMG_TOP = 1.02
IMG_MAX_H = 4.40

# 国赛常见：白底 + 深蓝标题条
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(30, 30, 30)
DARK = RGBColor(20, 50, 120)
RED = RGBColor(192, 0, 0)
GRAY = RGBColor(80, 80, 80)
LIGHT_BLUE = RGBColor(235, 242, 250)

COMP_LINE1 = "第二十八届中国机器人及人工智能大赛"
COMP_LINE2 = "创新赛 · 机器人创新赛道"

# 报名系统信息（CRAIC）
TEAM_NAME = "从容应队"
SCHOOL = "中山大学"
PROVINCE = "广东"
PROJECT_TITLE = "基于大语言模型的智能养老陪伴机器人仿真平台"
TEAM_ID = "CRAIC2026-TEAM-8FJQKLMI"
PROJECT_ID = "CRAIC20264ZEFT1DF"
CAPTAIN = "刘小凡"
MEMBER = "白冉"
ADVISOR = "彭键清"
ADVISOR_DEPT = "智能科学与技术"
GITHUB_URL = "https://github.com/FBB123571/ElderCare-Humanoid-Platform"

# 与 main() 中 prs 尺寸一致：16:9 → 10" × 5.625"
SLIDE_W_IN = 10.0
SLIDE_H_IN = 5.625
HEADER_H_IN = 0.52
MARGIN_X_IN = 0.45


def _slide(prs: Presentation):
  return prs.slides.add_slide(prs.slide_layouts[6])


def _bg_white(slide):
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = WHITE


def _slide_size_inches(prs: Presentation) -> tuple[float, float]:
  return prs.slide_width / 914400, prs.slide_height / 914400


def _header_bar(slide, slide_w: float = SLIDE_W_IN):
  bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(slide_w), Inches(HEADER_H_IN))
  bar.fill.solid()
  bar.fill.fore_color.rgb = DARK
  bar.line.fill.background()
  box = slide.shapes.add_textbox(Inches(0.15), Inches(0.08), Inches(9.7), Inches(0.45))
  tf = box.text_frame
  tf.clear()
  p1 = tf.paragraphs[0]
  p1.text = COMP_LINE1
  p1.font.size = Pt(10)
  p1.font.bold = True
  p1.font.color.rgb = WHITE
  p2 = tf.add_paragraph()
  p2.text = COMP_LINE2
  p2.font.size = Pt(10)
  p2.font.color.rgb = RGBColor(200, 220, 255)


def _title(
  slide,
  text: str,
  top=0.75,
  size=26,
  color=BLACK,
  center=False,
  height=0.8,
  width=8.9,
  left=0.55,
):
  box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
  tf = box.text_frame
  tf.word_wrap = True
  p = tf.paragraphs[0]
  p.text = text
  p.font.size = Pt(size)
  p.font.bold = True
  p.font.color.rgb = color
  p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT


def _paragraph(slide, text: str, top=1.5, size=16, width=8.9, bold=False):
  box = slide.shapes.add_textbox(Inches(0.55), Inches(top), Inches(width), Inches(3.8))
  tf = box.text_frame
  tf.word_wrap = True
  p = tf.paragraphs[0]
  p.text = text
  p.font.size = Pt(size)
  p.font.color.rgb = BLACK
  p.font.bold = bold
  p.line_spacing = 1.35


def _bullets(slide, items: list[str], top=1.45, size=15, width=8.9):
  box = slide.shapes.add_textbox(Inches(0.55), Inches(top), Inches(width), Inches(4.2))
  tf = box.text_frame
  tf.word_wrap = True
  for i, line in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line
    p.font.size = Pt(size)
    p.font.color.rgb = BLACK
    p.space_after = Pt(6)
    p.level = 0


def _content_slide(prs, title: str):
  slide = _slide(prs)
  sw, _ = _slide_size_inches(prs)
  _bg_white(slide)
  _header_bar(slide, sw)
  _title(slide, title, top=TITLE_TOP, size=22)
  return slide


def _place_image(slide, path: Path, left: float, top: float, max_w: float, max_h: float) -> None:
  if not path.exists():
    return
  w, h = _fit_image_inches(path, max_w, max_h)
  slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(w), height=Inches(h))


def _slide_lr(
  prs,
  title: str,
  bullets: list[str],
  image: str | Path,
  *,
  diagram: bool = True,
  bullet_size: int = 12,
):
  """左文右图（每页必备配图）。"""
  slide = _content_slide(prs, title)
  _bullets(slide, bullets, top=1.05, size=bullet_size, width=TEXT_W)
  sub = ASSETS / image if not diagram else DIAG / image
  if not sub.exists() and diagram:
    sub = ASSETS / image
  pad = 0.04
  frame = slide.shapes.add_shape(
    1, Inches(IMG_LEFT - pad), Inches(IMG_TOP - pad),
    Inches(IMG_W + 2 * pad), Inches(IMG_MAX_H + 2 * pad),
  )
  frame.fill.solid()
  frame.fill.fore_color.rgb = LIGHT_BLUE
  frame.line.color.rgb = RGBColor(180, 195, 220)
  _place_image(slide, sub, IMG_LEFT, IMG_TOP, IMG_W, IMG_MAX_H)
  return slide


def _part_divider_img(prs, part: str, subtitle: str, bg_image: str = "cover_banner.png"):
  slide = _slide(prs)
  sw, sh = _slide_size_inches(prs)
  _bg_white(slide)
  _header_bar(slide, sw)
  p = DIAG / bg_image
  if p.exists():
    slide.shapes.add_picture(str(p), Inches(0), Inches(HEADER_H_IN), width=Inches(sw), height=Inches(sh - HEADER_H_IN))
  overlay = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H_IN), Inches(sw), Inches(sh - HEADER_H_IN))
  overlay.fill.solid()
  overlay.fill.fore_color.rgb = RGBColor(20, 50, 120)
  overlay.fill.transparency = 0.25
  overlay.line.fill.background()
  _title(slide, part, top=sh / 2 - 0.7, size=32, center=True, color=WHITE)
  _title(slide, subtitle, top=sh / 2 - 0.05, size=20, center=True, color=RGBColor(220, 230, 255))


def _fit_image_inches(path: Path, max_w: float, max_h: float) -> tuple[float, float]:
  """按最大宽高（英寸）等比缩放，返回 (width_in, height_in)。"""
  with Image.open(path) as im:
    px_w, px_h = im.size
  aspect = px_h / px_w
  w, h = max_w, max_w * aspect
  if h > max_h:
    h = max_h
    w = max_h / aspect
  return w, h


def _screenshot_slide(prs, title: str, image_file: str, caption: str = ""):
  """截图页：16:9 画布内标题 + 居中配图 + 底注，按实际幻灯片高度计算留白。"""
  slide = _slide(prs)
  sw, sh = _slide_size_inches(prs)
  content_w = sw - 2 * MARGIN_X_IN
  _bg_white(slide)
  _header_bar(slide, sw)

  title_top = HEADER_H_IN + 0.06
  title_h = 0.42
  caption_h = 0.38 if caption else 0.0
  caption_gap = 0.08
  img_area_top = title_top + title_h + 0.06
  img_area_bottom = sh - caption_h - caption_gap - 0.12
  img_max_h = max(0.5, img_area_bottom - img_area_top)
  img_max_w = content_w

  path = ASSETS / image_file
  if not path.exists():
    _title(
      slide,
      title,
      top=title_top,
      size=20,
      height=title_h,
      width=content_w,
      left=MARGIN_X_IN,
      center=True,
    )
    _paragraph(slide, f"[请将截图放入 docs/assets/{image_file}]", top=img_area_top + 0.2, size=14)
    return slide

  img_w, img_h = _fit_image_inches(path, img_max_w, img_max_h)
  left = MARGIN_X_IN + (content_w - img_w) / 2
  top = img_area_top + (img_max_h - img_h) / 2

  # 浅底衬框，避免截图“贴边悬空”
  pad = 0.06
  frame = slide.shapes.add_shape(
    1,
    Inches(left - pad),
    Inches(top - pad),
    Inches(img_w + 2 * pad),
    Inches(img_h + 2 * pad),
  )
  frame.fill.solid()
  frame.fill.fore_color.rgb = LIGHT_BLUE
  frame.line.color.rgb = RGBColor(180, 195, 220)
  frame.line.width = Pt(0.75)

  slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(img_w))

  if caption:
    cap_top = img_area_bottom + caption_gap * 0.35
    box = slide.shapes.add_textbox(Inches(MARGIN_X_IN), Inches(cap_top), Inches(content_w), Inches(caption_h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = caption
    p.font.size = Pt(9)
    p.font.color.rgb = GRAY
    p.alignment = PP_ALIGN.CENTER

  _title(
    slide,
    title,
    top=title_top,
    size=19,
    height=title_h,
    width=content_w,
    left=MARGIN_X_IN,
    center=True,
  )
  return slide


def _compare_block(slide, left_title, left_items, right_title, right_items):
  # 左：现有方案不足 Ø
  lx, rx = 0.45, 5.05
  for x, title, items, color in [
    (lx, left_title, left_items, RED),
    (rx, right_title, right_items, DARK),
  ]:
    t = slide.shapes.add_textbox(Inches(x), Inches(1.35), Inches(4.4), Inches(0.5))
    t.text_frame.text = title
    t.text_frame.paragraphs[0].font.size = Pt(14)
    t.text_frame.paragraphs[0].font.bold = True
    t.text_frame.paragraphs[0].font.color.rgb = color
    b = slide.shapes.add_textbox(Inches(x), Inches(1.85), Inches(4.4), Inches(3.5))
    tf = b.text_frame
    tf.word_wrap = True
    for i, line in enumerate(items):
      p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
      p.text = line
      p.font.size = Pt(13)
      p.font.color.rgb = BLACK


def _metrics_table(slide, rows: list[tuple[str, str]], top=1.5):
  headers = ("指标", "结果")
  n = len(rows) + 1
  table = slide.shapes.add_table(n, 2, Inches(1.2), Inches(top), Inches(7.6), Inches(0.35 * n)).table
  table.columns[0].width = Inches(4.2)
  table.columns[1].width = Inches(3.4)
  for c, h in enumerate(headers):
    cell = table.cell(0, c)
    cell.text = h
    cell.fill.solid()
    cell.fill.fore_color.rgb = DARK
    for p in cell.text_frame.paragraphs:
      p.font.size = Pt(12)
      p.font.bold = True
      p.font.color.rgb = WHITE
  for r, (k, v) in enumerate(rows, start=1):
    table.cell(r, 0).text = k
    table.cell(r, 1).text = v
    for c in range(2):
      for p in table.cell(r, c).text_frame.paragraphs:
        p.font.size = Pt(12)
        p.font.color.rgb = BLACK


def _innovation_table(slide, rows: list[tuple[str, str]]):
  table = slide.shapes.add_table(
    len(rows) + 1, 2, Inches(0.4), Inches(1.35), Inches(9.2), Inches(3.8)
  ).table
  table.columns[0].width = Inches(2.0)
  table.columns[1].width = Inches(7.2)
  table.cell(0, 0).text = "创新维度"
  table.cell(0, 1).text = "描述"
  for c in range(2):
    cell = table.cell(0, c)
    cell.fill.solid()
    cell.fill.fore_color.rgb = DARK
    for p in cell.text_frame.paragraphs:
      p.font.size = Pt(11)
      p.font.bold = True
      p.font.color.rgb = WHITE
  for r, (dim, desc) in enumerate(rows, start=1):
    table.cell(r, 0).text = dim
    table.cell(r, 1).text = desc
    for c in range(2):
      for p in table.cell(r, c).text_frame.paragraphs:
        p.font.size = Pt(10)
        p.font.color.rgb = BLACK


def _ensure_qr_code() -> None:
  qr = ASSETS / "ppt_demo_qr.png"
  if qr.exists():
    return
  try:
    import qrcode

    img = qrcode.make(GITHUB_URL, box_size=8, border=2)
    ASSETS.mkdir(parents=True, exist_ok=True)
    img.save(qr)
  except ImportError:
    pass


def main():
  import sys

  sys.path.insert(0, str(ROOT))
  from tools.ppt_diagrams import gen_all

  _ensure_qr_code()
  gen_all()

  prs = Presentation()
  prs.slide_width = Inches(SLIDE_W_IN)
  prs.slide_height = Inches(SLIDE_H_IN)
  sw, sh = _slide_size_inches(prs)

  # ===== 封面（配图）=====
  slide = _slide(prs)
  _header_bar(slide, sw)
  banner = DIAG / "cover_banner.png"
  if banner.exists():
    slide.shapes.add_picture(str(banner), Inches(0), Inches(HEADER_H_IN), width=Inches(sw), height=Inches(sh - HEADER_H_IN))
  _title(slide, TEAM_NAME, top=sh - 1.15, size=20, center=True, color=WHITE)
  box = slide.shapes.add_textbox(Inches(0.5), Inches(sh - 0.75), Inches(9), Inches(0.4))
  box.text_frame.text = f"{SCHOOL} · {CAPTAIN} / {MEMBER} · 指导教师 {ADVISOR}"
  box.text_frame.paragraphs[0].font.size = Pt(11)
  box.text_frame.paragraphs[0].font.color.rgb = RGBColor(220, 230, 255)
  box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

  _slide_lr(
    prs,
    "目录",
    [
      "第一部分  项目背景与需求分析",
      "第二部分  关键技术与理论模型",
      "第三部分  系统实现与实验验证",
      "第四部分  创新点与展望",
      "附录  演示界面与开源仓库",
    ],
    "architecture.png",
  )

  _slide_lr(
    prs,
    "参赛信息",
    [
      f"作品：{PROJECT_TITLE}",
      f"赛项：{COMP_LINE2}",
      f"团队编号：{TEAM_ID}",
      f"作品编号：{PROJECT_ID}",
      f"队员：{CAPTAIN}（队长）、{MEMBER}",
      f"指导教师：{ADVISOR}",
    ],
    "team_card.png",
  )

  _part_divider_img(prs, "第一部分", "项目背景 · 需求分析 · 方案定位")

  _slide_lr(
    prs,
    "社会背景：老龄化与跌倒风险",
    [
      "独居老人增多，跌倒后「发现空窗」是核心痛点",
      "情感陪伴需求上升，监测设备难以形成照护闭环",
      "政策导向：智慧养老与居家安全并重",
      "本项目聚焦可落地的仿真验证与人形接口",
    ],
    "aging_chart.png",
  )

  _slide_lr(
    prs,
    "现有方案对比",
    [
      "传统音箱/摄像头/手环：功能割裂",
      "本作品：感知—决策—执行统一编排",
      "强调可解释风险与紧急硬优先级",
      "配套 Web 演示与量化评测脚本",
    ],
    "compare.png",
  )

  _slide_lr(
    prs,
    "项目概述与目标",
    [
      "CareCompanion：养老人形陪伴软件平台",
      "CareOrchestrator 统一调度各模块",
      "目标1：跌倒检测与紧急呼叫自动化",
      "目标2：情感对话与机器人动作联动",
      "目标3：ROS2 部署接口 + 开源可复现",
    ],
    "architecture.png",
  )

  _part_divider_img(prs, "第二部分", "理论模型 · 算法设计 · 系统架构")

  _slide_lr(
    prs,
    "系统总体架构",
    [
      "四层架构：感知 / 认知 / 执行 / 交互",
      "核心：CareOrchestrator + 状态机",
      "模块可替换：仿真、Web、ROS2 共用一套逻辑",
      "配置集中于 config/default.yaml",
    ],
    "architecture.png",
  )

  _slide_lr(
    prs,
    "状态机与调度策略",
    [
      "MONITOR → CONVERSE → ALERT → EMERGENCY",
      "紧急态可打断对话与常规任务",
      "每个 tick 输出风险、回复、动作序列",
      "便于日志审计与答辩讲解",
    ],
    "state_machine.png",
  )

  _slide_lr(
    prs,
    "多模态风险融合（理论）",
    [
      "加权融合跌倒、情绪、健康三路分数",
      "输出等级与原因列表，非黑盒端到端",
      "阈值可配置，支持场景调参",
      "契合医疗与养老合规沟通需求",
    ],
    "risk_formula.png",
  )

  _slide_lr(
    prs,
    "跌倒检测算法设计",
    [
      "输入：MediaPipe 骨架几何特征",
      "快速跌倒 + 慢速躺倒（养老常见）双规则",
      "合成 6 场景评测 F1=100%",
      "可接摄像头或上传照片分析",
    ],
    "fall_flow.png",
  )

  _slide_lr(
    prs,
    "对话与情感模块",
    [
      "文本情感词典 + 情绪标签融合",
      "DialogueManager 生成安抚话术",
      "默认 Mock，可切换 LLM API",
      "与 RiskEngine、CarePlanner 协同",
    ],
    "llm_module.png",
  )

  _slide_lr(
    prs,
    "数据处理与决策流水线",
    [
      "感知帧 → 特征 → 融合 → 状态机",
      "CarePlanner 生成 RobotAction",
      "RobotAdapter 下发仿真或 ROS2",
      "全链路可在 Web 界面观察",
    ],
    "pipeline.png",
  )

  _slide_lr(
    prs,
    "紧急响应链路（理论）",
    [
      "确认跌倒后按序触发四类动作",
      "告警音 → 语音 → 家属通知 → 手势",
      "EmergencyNotifier 记录推送渠道",
      "端到端触发率评测 100%",
    ],
    "emergency_flow.png",
  )

  _part_divider_img(prs, "第三部分", "系统实现 · 实验验证 · 现场演示")

  _slide_lr(
    prs,
    "Web 控制台实现",
    [
      "FastAPI 后端 + 浏览器前端",
      "实时风险仪表盘、对话与指令流",
      "支持上传照片 / 摄像头骨架分析",
      "一键演示剧本：日常→倾诉→跌倒",
    ],
    "ppt_full_dashboard.png",
    diagram=False,
  )

  _screenshot_slide(
    prs,
    "系统界面：MediaPipe 骨架分析（上传照片）",
    "ppt_mediapipe_pose.png",
    "上传全身照后导出骨架叠加图 · 宽高比 0.48 · 支持答辩现场上传演示",
  )
  _screenshot_slide(
    prs,
    "系统界面：老人倾诉场景（演示剧本）",
    "ppt_full_dashboard.png",
    "演示场景「老人倾诉」· 风险 0.23 · 机器人主动安抚回复",
  )
  _screenshot_slide(
    prs,
    "系统界面：风险决策仪表盘",
    "ppt_risk_panel.png",
    "多模态融合输出：风险分数、因素、机器人回应及四项监测指标",
  )
  _screenshot_slide(
    prs,
    "系统界面：紧急状态监测",
    "ppt_header_perception.png",
    "状态机进入「紧急」· 感知输入与 MediaPipe 视觉模块",
  )
  _screenshot_slide(
    prs,
    "系统界面：跌倒紧急对话日志",
    "ppt_chat_emergency.png",
    "演示完成：跌倒紧急流程已成功触发 · 多次紧急安抚语音",
  )
  _screenshot_slide(
    prs,
    "系统界面：机器人指令流",
    "ppt_robot_commands.png",
    "告警音 → 语音 → 紧急呼叫（跌倒事件）→ 举手手势，全链路可追溯",
  )

  _slide_lr(
    prs,
    "实验评测结果",
    [
      "跌倒检测 P/R/F1：100%（6类合成场景）",
      "紧急呼叫端到端触发率：100%",
      "单帧决策延迟 < 50ms（CPU）",
      "pytest + 无头压测全部通过",
      "报告：fall_eval_report.json",
    ],
    "metrics_chart.png",
  )

  _slide_lr(
    prs,
    "开源与可复现性",
    [
      f"仓库：{GITHUB_URL}",
      f"团队：{TEAM_NAME}（{SCHOOL}）",
      "演示：bash scripts/run_web.sh",
      "录像：docs/assets/demo_carecompanion.mp4",
      "软著：申请中",
    ],
    "ppt_demo_qr.png",
    diagram=False,
  )

  _part_divider_img(prs, "第四部分", "创新点 · 应用价值 · 后续计划")

  _slide_lr(
    prs,
    "创新维度总结",
    [
      "多模态可解释融合，优于模块堆叠",
      "紧急硬优先级状态机 + 动作闭环",
      "MediaPipe 视觉接入，非纯滑块",
      "工程化：评测脚本 + 开源仓库",
      "面向居家养老的应用场景明确",
    ],
    "innovation_radar.png",
  )

  _slide_lr(
    prs,
    "后续工作计划",
    [
      "对接 Unitree 等人形真机",
      "引入 UR Fall 等公开数据集",
      "多房间遮挡与光照优化",
      "养老院调研与产品化评估",
      "软著与专利布局",
    ],
    "roadmap.png",
  )

  _slide_lr(
    prs,
    "参考文献与资料",
    [
      "[1] Google MediaPipe Pose",
      "[2] Unitree / ROS2 文档",
      "[3] 「十四五」养老服务规划",
      "[4] docs/TECHNICAL_REPORT.md",
      "[5] GitHub 开源仓库",
    ],
    "pipeline.png",
  )

  # 扫码页：左说明右二维码+演示截图缩略
  slide = _content_slide(prs, "扫码查看代码与演示视频")
  _bullets(
    slide,
    [
      "GitHub 完整源码与文档",
      "在线 Web 演示（现场可复现）",
      "演示录像已附仓库",
      "欢迎评委扫码查阅",
    ],
    top=1.05,
    size=12,
    width=TEXT_W,
  )
  qr_path = ASSETS / "ppt_demo_qr.png"
  if qr_path.exists():
    _place_image(slide, qr_path, IMG_LEFT, IMG_TOP, 2.2, 2.2)
  demo_thumb = ASSETS / "ppt_mediapipe_pose.png"
  if demo_thumb.exists():
    _place_image(slide, demo_thumb, IMG_LEFT + 2.4, IMG_TOP + 0.1, 2.3, 2.0)

  # 致谢（配图）
  slide = _slide(prs)
  _header_bar(slide, sw)
  if banner.exists():
    slide.shapes.add_picture(str(banner), Inches(0), Inches(HEADER_H_IN), width=Inches(sw), height=Inches(sh - HEADER_H_IN))
  box = slide.shapes.add_textbox(Inches(0.55), Inches(sh / 2 - 0.55), Inches(8.9), Inches(1.0))
  box.text_frame.text = "敬请批评指正"
  p = box.text_frame.paragraphs[0]
  p.font.size = Pt(34)
  p.font.bold = True
  p.font.color.rgb = WHITE
  p.alignment = PP_ALIGN.CENTER
  sub = slide.shapes.add_textbox(Inches(0.55), Inches(sh / 2 + 0.2), Inches(8.9), Inches(0.8))
  sub.text_frame.text = f"{TEAM_NAME} · {SCHOOL}\n{CAPTAIN} · {MEMBER} · 指导教师 {ADVISOR}"
  for para in sub.text_frame.paragraphs:
    para.font.size = Pt(14)
    para.font.color.rgb = RGBColor(220, 230, 255)
    para.alignment = PP_ALIGN.CENTER

  OUT.parent.mkdir(parents=True, exist_ok=True)
  prs.save(str(OUT))
  print(f"✅ 已生成国赛风格 PPT: {OUT}")
  print(f"   共 {len(prs.slides)} 页")


if __name__ == "__main__":
  main()
