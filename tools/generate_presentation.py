#!/usr/bin/env python3
"""生成国赛风格答辩 PPT：docs/答辩_CareCompanion.pptx"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "答辩_CareCompanion.pptx"
ASSETS = ROOT / "docs" / "assets"
DIAG = ASSETS / "diagrams"

SLIDE_W_IN = 10.0
SLIDE_H_IN = 5.625
HEADER_H_IN = 0.48
FOOTER_H_IN = 0.28
MARGIN_X_IN = 0.38

TITLE_TOP = 0.58
TEXT_LEFT = 0.38
TEXT_W = 4.55
IMG_LEFT = 5.05
IMG_W = 4.55
IMG_TOP = 0.95
IMG_MAX_H = 4.15

WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(28, 32, 44)
DARK = RGBColor(20, 50, 120)
RED = RGBColor(192, 48, 48)
GRAY = RGBColor(90, 98, 115)
LIGHT_BLUE = RGBColor(238, 245, 252)
ACCENT = RGBColor(245, 158, 11)
SOFT_BLUE = RGBColor(219, 234, 254)
FONT_CN = "微软雅黑"

COMP_LINE1 = "第二十八届中国机器人及人工智能大赛"
COMP_LINE2 = "创新赛 · 机器人创新赛道"

TEAM_NAME = "从容应队"
SCHOOL = "中山大学"
PROJECT_TITLE = "基于大语言模型的智能养老陪伴机器人仿真平台"
TEAM_ID = "CRAIC2026-TEAM-8FJQKLMI"
PROJECT_ID = "CRAIC20264ZEFT1DF"
CAPTAIN = "刘小凡"
MEMBER = "白冉"
ADVISOR = "彭键清"
GITHUB_URL = "https://github.com/FBB123571/ElderCare-Humanoid-Platform"


def _slide(prs: Presentation):
  return prs.slides.add_slide(prs.slide_layouts[6])


def _slide_size_inches(prs: Presentation) -> tuple[float, float]:
  return prs.slide_width / 914400, prs.slide_height / 914400


def _set_run_font(run, size: int, *, bold=False, color=BLACK, name=FONT_CN):
  run.font.name = name
  run.font.size = Pt(size)
  run.font.bold = bold
  if color:
    run.font.color.rgb = color
  try:
    rpr = run._r.rPr
    if rpr is not None:
      from lxml import etree
      rfonts = rpr.find(qn("w:rFonts"))
      if rfonts is None:
        rfonts = etree.SubElement(rpr, qn("w:rFonts"))
      rfonts.set(qn("w:eastAsia"), name)
      rfonts.set(qn("w:ascii"), name)
      rfonts.set(qn("w:hAnsi"), name)
  except Exception:
    pass


def _set_para_font(p, size: int, *, bold=False, color=BLACK):
  if not p.runs:
    p.text = p.text or ""
  for run in p.runs:
    _set_run_font(run, size, bold=bold, color=color)
  if not p.runs and p.text:
    _set_run_font(p.add_run(), size, bold=bold, color=color)


def _bg_white(slide):
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = WHITE


def _header_bar(slide, slide_w: float = SLIDE_W_IN):
  bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(slide_w), Inches(HEADER_H_IN))
  bar.fill.solid()
  bar.fill.fore_color.rgb = DARK
  bar.line.fill.background()
  box = slide.shapes.add_textbox(Inches(0.12), Inches(0.06), Inches(9.76), Inches(0.4))
  tf = box.text_frame
  tf.clear()
  p1 = tf.paragraphs[0]
  p1.text = f"{COMP_LINE1}  |  {COMP_LINE2}"
  _set_para_font(p1, 9, bold=True, color=WHITE)


def _footer_bar(slide, slide_w: float, hint: str = ""):
  y = SLIDE_H_IN - FOOTER_H_IN
  bar = slide.shapes.add_shape(1, Inches(0), Inches(y), Inches(slide_w), Inches(FOOTER_H_IN))
  bar.fill.solid()
  bar.fill.fore_color.rgb = SOFT_BLUE
  bar.line.fill.background()
  txt = f"{TEAM_NAME} · {SCHOOL} · {CAPTAIN}/{MEMBER} · 指导教师 {ADVISOR}"
  if hint:
    txt = f"{hint}    |    {txt}"
  box = slide.shapes.add_textbox(Inches(0.15), Inches(y + 0.04), Inches(slide_w - 0.3), Inches(0.22))
  p = box.text_frame.paragraphs[0]
  p.text = txt
  p.alignment = PP_ALIGN.CENTER
  _set_para_font(p, 8, color=GRAY)


def _accent_under_title(slide, left: float, top: float, width: float = 1.1):
  line = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(0.06))
  line.fill.solid()
  line.fill.fore_color.rgb = ACCENT
  line.line.fill.background()


def _title(slide, text: str, top=0.72, size=22, color=BLACK, center=False, height=0.65, width=8.9, left=0.42):
  box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
  tf = box.text_frame
  tf.word_wrap = True
  p = tf.paragraphs[0]
  p.text = text
  _set_para_font(p, size, bold=True, color=color)
  p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
  if not center:
    _accent_under_title(slide, left, top + height - 0.02, min(1.4, width * 0.18))


def _bullets(slide, items: list[str], top=1.05, size=13, width=TEXT_W, left=TEXT_LEFT, highlights: list[int] | None = None):
  highlights = highlights or []
  panel = slide.shapes.add_shape(
    1, Inches(left - 0.06), Inches(top - 0.08),
    Inches(width + 0.12), Inches(min(4.35, 0.42 * len(items) + 0.35)),
  )
  panel.fill.solid()
  panel.fill.fore_color.rgb = LIGHT_BLUE
  panel.line.color.rgb = RGBColor(200, 215, 235)
  panel.line.width = Pt(0.75)
  panel_h = min(4.35, 0.42 * len(items) + 0.35)
  accent = slide.shapes.add_shape(1, Inches(left - 0.06), Inches(top - 0.08), Inches(0.07), Inches(panel_h + 0.16))
  accent.fill.solid()
  accent.fill.fore_color.rgb = DARK
  accent.line.fill.background()

  box = slide.shapes.add_textbox(Inches(left + 0.08), Inches(top), Inches(width - 0.12), Inches(4.0))
  tf = box.text_frame
  tf.word_wrap = True
  for i, line in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line
    _set_para_font(p, size, bold=(i in highlights), color=DARK if i in highlights else BLACK)
    p.space_after = Pt(5)
    p.line_spacing = 1.25


def _image_frame(slide, left: float, top: float, w: float, h: float, caption: str = ""):
  pad = 0.05
  frame = slide.shapes.add_shape(
    1, Inches(left - pad), Inches(top - pad),
    Inches(w + 2 * pad), Inches(h + 2 * pad + (0.28 if caption else 0)),
  )
  frame.fill.solid()
  frame.fill.fore_color.rgb = WHITE
  frame.line.color.rgb = RGBColor(160, 180, 210)
  frame.line.width = Pt(1.0)
  shadow = slide.shapes.add_shape(
    1, Inches(left - pad + 0.04), Inches(top - pad + 0.04),
    Inches(w + 2 * pad), Inches(h + 2 * pad),
  )
  shadow.fill.solid()
  shadow.fill.fore_color.rgb = RGBColor(220, 228, 240)
  shadow.line.fill.background()
  # 将 shadow 移到底层（先加的先在底，这里顺序已 ok）
  if caption:
    cap = slide.shapes.add_textbox(Inches(left), Inches(top + h + 0.06), Inches(w), Inches(0.24))
    cp = cap.text_frame.paragraphs[0]
    cp.text = caption
    cp.alignment = PP_ALIGN.CENTER
    _set_para_font(cp, 8, color=GRAY)


def _place_image(slide, path: Path, left: float, top: float, max_w: float, max_h: float) -> tuple[float, float] | None:
  if not path.exists():
    return None
  w, h = _fit_image_inches(path, max_w, max_h)
  slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(w), height=Inches(h))
  return w, h


def _fit_image_inches(path: Path, max_w: float, max_h: float) -> tuple[float, float]:
  with Image.open(path) as im:
    px_w, px_h = im.size
  aspect = px_h / px_w
  w, h = max_w, max_w * aspect
  if h > max_h:
    h = max_h
    w = max_h / aspect
  return w, h


def _content_slide(prs, title: str, footer_hint: str = ""):
  slide = _slide(prs)
  sw, _ = _slide_size_inches(prs)
  _bg_white(slide)
  _header_bar(slide, sw)
  _footer_bar(slide, sw, footer_hint)
  _title(slide, title, top=TITLE_TOP, size=21)
  return slide


def _slide_lr(
  prs,
  title: str,
  bullets: list[str],
  image: str | Path,
  *,
  diagram: bool = True,
  bullet_size: int = 12,
  caption: str = "",
  highlight_last: bool = False,
  footer_hint: str = "",
  key_takeaway: str = "",
):
  slide = _content_slide(prs, title, footer_hint)
  hi = [len(bullets) - 1] if highlight_last and bullets else []
  _bullets(slide, bullets, top=1.02, size=bullet_size, width=TEXT_W, highlights=hi)

  sub = DIAG / image if diagram else ASSETS / image
  if not sub.exists() and diagram:
    sub = ASSETS / image
  if sub.exists():
    w, h = _fit_image_inches(sub, IMG_W, IMG_MAX_H)
    _image_frame(slide, IMG_LEFT, IMG_TOP, w, h, caption or ("理论框图" if diagram else "系统实拍"))
    _place_image(slide, sub, IMG_LEFT, IMG_TOP, IMG_W, IMG_MAX_H)
  else:
    _image_frame(slide, IMG_LEFT, IMG_TOP, IMG_W, 2.5, f"[缺失: {image}]")

  if key_takeaway:
    ribbon = slide.shapes.add_shape(1, Inches(TEXT_LEFT), Inches(4.55), Inches(TEXT_W), Inches(0.38))
    ribbon.fill.solid()
    ribbon.fill.fore_color.rgb = DARK
    ribbon.line.fill.background()
    box = slide.shapes.add_textbox(Inches(TEXT_LEFT + 0.1), Inches(4.58), Inches(TEXT_W - 0.2), Inches(0.32))
    p = box.text_frame.paragraphs[0]
    p.text = key_takeaway
    _set_para_font(p, 10, bold=True, color=WHITE)
    p.alignment = PP_ALIGN.CENTER
  return slide


def _hero_cover(prs, sw: float, sh: float):
  """封面：左产品截图 + 右标题，避免与底图文字重复。"""
  slide = _slide(prs)
  _header_bar(slide, sw)

  # 左侧浅底 + 产品图
  left_bg = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H_IN), Inches(5.15), Inches(sh - HEADER_H_IN))
  left_bg.fill.solid()
  left_bg.fill.fore_color.rgb = LIGHT_BLUE
  left_bg.line.fill.background()

  hero = ASSETS / "ppt_mediapipe_pose.png"
  if not hero.exists():
    hero = ASSETS / "ppt_full_dashboard.png"
  if hero.exists():
    w, h = _fit_image_inches(hero, 4.75, sh - HEADER_H_IN - 0.35)
    lx = 0.2 + (4.75 - w) / 2
    ly = HEADER_H_IN + 0.15 + (sh - HEADER_H_IN - 0.35 - h) / 2
    _image_frame(slide, lx, ly, w, h, "MediaPipe 全身骨架 · Web 可现场演示")
    _place_image(slide, hero, lx, ly, 4.75, sh - HEADER_H_IN - 0.35)

  # 右侧深蓝信息区
  right_bg = slide.shapes.add_shape(1, Inches(5.15), Inches(HEADER_H_IN), Inches(4.85), Inches(sh - HEADER_H_IN))
  right_bg.fill.solid()
  right_bg.fill.fore_color.rgb = DARK
  right_bg.line.fill.background()
  deco = slide.shapes.add_shape(1, Inches(5.15), Inches(HEADER_H_IN), Inches(0.12), Inches(sh - HEADER_H_IN))
  deco.fill.solid()
  deco.fill.fore_color.rgb = ACCENT
  deco.line.fill.background()

  rx, ry = 5.35, HEADER_H_IN + 0.55
  for text, size, color, bold in [
    ("CareCompanion", 34, WHITE, True),
    ("智能养老陪伴机器人仿真平台", 16, RGBColor(147, 197, 253), True),
    ("感知 · 决策 · 执行  一体化闭环", 13, RGBColor(226, 232, 240), False),
  ]:
    box = slide.shapes.add_textbox(Inches(rx), Inches(ry), Inches(4.5), Inches(0.55))
    p = box.text_frame.paragraphs[0]
    p.text = text
    _set_para_font(p, size, bold=bold, color=color)
    ry += 0.52 if size > 20 else 0.42

  card = slide.shapes.add_shape(1, Inches(rx), Inches(ry + 0.15), Inches(4.35), Inches(1.35))
  card.fill.solid()
  card.fill.fore_color.rgb = RGBColor(30, 64, 130)
  card.line.color.rgb = RGBColor(100, 140, 200)
  card.line.width = Pt(0.75)

  info_lines = [
    f"团队：{TEAM_NAME}（{SCHOOL}）",
    f"队员：{CAPTAIN}（队长）· {MEMBER}",
    f"指导教师：{ADVISOR}",
    f"作品编号：{PROJECT_ID}",
  ]
  box = slide.shapes.add_textbox(Inches(rx + 0.15), Inches(ry + 0.28), Inches(4.1), Inches(1.2))
  tf = box.text_frame
  tf.word_wrap = True
  for i, line in enumerate(info_lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line
    _set_para_font(p, 10, color=RGBColor(220, 230, 255))
    p.space_after = Pt(3)

  tag = slide.shapes.add_textbox(Inches(rx), Inches(sh - 0.55), Inches(4.4), Inches(0.35))
  tp = tag.text_frame.paragraphs[0]
  tp.text = PROJECT_TITLE
  _set_para_font(tp, 9, color=RGBColor(148, 163, 184))
  return slide


def _part_divider(prs, part: str, subtitle: str, preview: list[str], thumb: str = "architecture.png"):
  slide = _slide(prs)
  sw, sh = _slide_size_inches(prs)
  _header_bar(slide, sw)
  _footer_bar(slide, sw)

  main = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H_IN), Inches(6.2), Inches(sh - HEADER_H_IN - FOOTER_H_IN))
  main.fill.solid()
  main.fill.fore_color.rgb = DARK
  main.line.fill.background()

  num = part.replace("第", "").replace("部分", "")[:3]
  circle = slide.shapes.add_shape(9, Inches(0.55), Inches(1.35), Inches(0.95), Inches(0.95))
  circle.fill.solid()
  circle.fill.fore_color.rgb = ACCENT
  circle.line.fill.background()
  nb = slide.shapes.add_textbox(Inches(0.55), Inches(1.42), Inches(0.95), Inches(0.5))
  np = nb.text_frame.paragraphs[0]
  np.text = num
  np.alignment = PP_ALIGN.CENTER
  _set_para_font(np, 28, bold=True, color=WHITE)

  _title(slide, part, top=2.35, size=30, color=WHITE, left=0.45, width=5.5)
  sub = slide.shapes.add_textbox(Inches(0.48), Inches(2.95), Inches(5.4), Inches(0.45))
  sp = sub.text_frame.paragraphs[0]
  sp.text = subtitle
  _set_para_font(sp, 15, color=RGBColor(191, 219, 254))

  prev_box = slide.shapes.add_textbox(Inches(0.55), Inches(3.55), Inches(5.1), Inches(1.5))
  tf = prev_box.text_frame
  tf.word_wrap = True
  for i, line in enumerate(preview):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = f"▸ {line}"
    _set_para_font(p, 12, color=RGBColor(226, 232, 240))
    p.space_after = Pt(4)

  # 右侧缩略图
  p = DIAG / thumb
  if p.exists():
    right_bg = slide.shapes.add_shape(1, Inches(6.2), Inches(HEADER_H_IN), Inches(3.8), Inches(sh - HEADER_H_IN - FOOTER_H_IN))
    right_bg.fill.solid()
    right_bg.fill.fore_color.rgb = LIGHT_BLUE
    right_bg.line.fill.background()
    _image_frame(slide, 6.35, 1.05, 3.5, 3.8, "本章核心示意")
    _place_image(slide, p, 6.35, 1.05, 3.5, 3.8)
  return slide


def _screenshot_slide(prs, title: str, image_file: str, caption: str = ""):
  slide = _slide(prs)
  sw, sh = _slide_size_inches(prs)
  _bg_white(slide)
  _header_bar(slide, sw)
  _footer_bar(slide, sw, "系统实拍")

  title_top = HEADER_H_IN + 0.05
  title_h = 0.4
  caption_h = 0.32 if caption else 0.0
  img_area_top = title_top + title_h + 0.05
  img_area_bottom = sh - FOOTER_H_IN - caption_h - 0.1
  img_max_h = max(0.5, img_area_bottom - img_area_top)
  content_w = sw - 2 * MARGIN_X_IN

  path = ASSETS / image_file
  _title(slide, title, top=title_top, size=18, height=title_h, width=content_w, left=MARGIN_X_IN, center=True)

  if path.exists():
    img_w, img_h = _fit_image_inches(path, content_w - 0.2, img_max_h)
    left = MARGIN_X_IN + (content_w - img_w) / 2
    top = img_area_top + (img_max_h - img_h) / 2
    _image_frame(slide, left, top, img_w, img_h, caption)
    slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(img_w))
  else:
    _paragraph_placeholder(slide, f"[请将截图放入 docs/assets/{image_file}]", img_area_top)

  if caption and path.exists():
    pass  # caption in frame
  return slide


def _paragraph_placeholder(slide, text: str, top: float):
  box = slide.shapes.add_textbox(Inches(0.55), Inches(top + 0.2), Inches(8.9), Inches(0.5))
  p = box.text_frame.paragraphs[0]
  p.text = text
  _set_para_font(p, 13, color=GRAY)


def _thanks_slide(prs, sw: float, sh: float):
  slide = _slide(prs)
  _header_bar(slide, sw)

  left_bg = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H_IN), Inches(5.0), Inches(sh - HEADER_H_IN))
  left_bg.fill.solid()
  left_bg.fill.fore_color.rgb = DARK
  left_bg.line.fill.background()

  thumb = ASSETS / "ppt_full_dashboard.png"
  if thumb.exists():
    w, h = _fit_image_inches(thumb, 4.6, sh - HEADER_H_IN - 0.4)
    _place_image(slide, thumb, 0.2 + (4.6 - w) / 2, HEADER_H_IN + 0.2, 4.6, sh - HEADER_H_IN - 0.4)

  right = slide.shapes.add_shape(1, Inches(5.0), Inches(HEADER_H_IN), Inches(5.0), Inches(sh - HEADER_H_IN))
  right.fill.solid()
  right.fill.fore_color.rgb = LIGHT_BLUE
  right.line.fill.background()

  box = slide.shapes.add_textbox(Inches(5.25), Inches(1.6), Inches(4.5), Inches(0.7))
  p = box.text_frame.paragraphs[0]
  p.text = "敬请批评指正"
  _set_para_font(p, 32, bold=True, color=DARK)
  p.alignment = PP_ALIGN.CENTER

  sub = slide.shapes.add_textbox(Inches(5.25), Inches(2.45), Inches(4.5), Inches(1.2))
  tf = sub.text_frame
  for i, line in enumerate([
    f"{TEAM_NAME} · {SCHOOL}",
    f"{CAPTAIN} · {MEMBER}",
    f"指导教师 {ADVISOR}",
    GITHUB_URL,
  ]):
    para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    para.text = line
    _set_para_font(para, 12, color=GRAY if i == 3 else BLACK, bold=(i == 0))
    para.alignment = PP_ALIGN.CENTER
    para.space_after = Pt(4)

  qr = ASSETS / "ppt_demo_qr.png"
  if qr.exists():
    _place_image(slide, qr, 6.55, 3.85, 1.35, 1.35)


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

  _hero_cover(prs, sw, sh)

  _slide_lr(
    prs, "目录",
    [
      "第一部分  项目背景与需求分析",
      "第二部分  关键技术与理论模型",
      "第三部分  系统实现与实验验证",
      "第四部分  创新点与展望",
      "附录  演示界面与开源仓库",
    ],
    "pipeline.png",
    caption="全篇结构一览",
    key_takeaway="理论模型 + 工程实现 + 现场可演示",
  )

  _slide_lr(
    prs, "参赛信息",
    [
      f"作品：{PROJECT_TITLE}",
      f"赛项：{COMP_LINE2}",
      f"团队编号：{TEAM_ID}",
      f"作品编号：{PROJECT_ID}",
      f"队员：{CAPTAIN}（队长）、{MEMBER}",
      f"指导教师：{ADVISOR}",
    ],
    "team_card.png",
    caption="报名系统信息",
  )

  _part_divider(
    prs, "第一部分", "项目背景 · 需求分析 · 方案定位",
    ["老龄化与跌倒空窗期", "现有方案对比", "CareCompanion 目标定位"],
    "aging_chart.png",
  )

  _slide_lr(
    prs, "社会背景：老龄化与跌倒风险",
    [
      "独居老人增多，跌倒后「发现空窗」是核心痛点",
      "情感陪伴需求上升，监测设备难以形成照护闭环",
      "政策导向：智慧养老与居家安全并重",
      "本项目聚焦可落地的仿真验证与人形接口",
    ],
    "aging_chart.png",
    key_takeaway="痛点明确：发现慢 + 闭环弱",
    highlight_last=True,
  )

  _slide_lr(
    prs, "现有方案对比",
    [
      "传统音箱/摄像头/手环：功能割裂",
      "本作品：感知—决策—执行统一编排",
      "强调可解释风险与紧急硬优先级",
      "配套 Web 演示与量化评测脚本",
    ],
    "compare.png",
    key_takeaway="从模块堆叠到一体化闭环",
  )

  _slide_lr(
    prs, "项目概述与目标",
    [
      "CareCompanion：养老人形陪伴软件平台",
      "CareOrchestrator 统一调度各模块",
      "目标1：跌倒检测与紧急呼叫自动化",
      "目标2：情感对话与机器人动作联动",
      "目标3：ROS2 部署接口 + 开源可复现",
    ],
    "architecture.png",
    key_takeaway="三大目标均可现场验证",
  )

  _part_divider(
    prs, "第二部分", "理论模型 · 算法设计 · 系统架构",
    ["四层架构与状态机", "多模态风险融合", "跌倒检测与应急链路"],
    "state_machine.png",
  )

  _slide_lr(
    prs, "系统总体架构",
    [
      "四层架构：感知 / 认知 / 执行 / 交互",
      "核心：CareOrchestrator + 状态机",
      "模块可替换：仿真、Web、ROS2 共用一套逻辑",
      "配置集中于 config/default.yaml",
    ],
    "architecture.png",
    caption="四层架构框图",
    key_takeaway="理论清晰、模块可替换",
  )

  _slide_lr(
    prs, "状态机与调度策略",
    [
      "MONITOR → CONVERSE → ALERT → EMERGENCY",
      "紧急态可打断对话与常规任务",
      "每个 tick 输出风险、回复、动作序列",
      "便于日志审计与答辩讲解",
    ],
    "state_machine.png",
    caption="状态转移示意",
  )

  _slide_lr(
    prs, "多模态风险融合（理论）",
    [
      "加权融合跌倒、情绪、健康三路分数",
      "输出等级与原因列表，非黑盒端到端",
      "阈值可配置，支持场景调参",
      "契合医疗与养老合规沟通需求",
    ],
    "risk_formula.png",
    caption="可解释融合公式",
  )

  _slide_lr(
    prs, "跌倒检测算法设计",
    [
      "输入：MediaPipe 骨架几何特征",
      "快速跌倒 + 慢速躺倒（养老常见）双规则",
      "合成 6 场景评测 F1=100%",
      "可接摄像头或上传照片分析",
    ],
    "fall_flow.png",
    caption="双规则检测流程",
  )

  _slide_lr(
    prs, "对话与情感模块",
    [
      "文本情感词典 + 情绪标签融合",
      "DialogueManager 生成安抚话术",
      "默认 Mock，可切换 LLM API",
      "与 RiskEngine、CarePlanner 协同",
    ],
    "llm_module.png",
  )

  _slide_lr(
    prs, "数据处理与决策流水线",
    [
      "感知帧 → 特征 → 融合 → 状态机",
      "CarePlanner 生成 RobotAction",
      "RobotAdapter 下发仿真或 ROS2",
      "全链路可在 Web 界面观察",
    ],
    "pipeline.png",
  )

  _slide_lr(
    prs, "紧急响应链路（理论）",
    [
      "确认跌倒后按序触发四类动作",
      "告警音 → 语音 → 家属通知 → 手势",
      "EmergencyNotifier 记录推送渠道",
      "端到端触发率评测 100%",
    ],
    "emergency_flow.png",
    key_takeaway="紧急链路端到端可验证",
  )

  _part_divider(
    prs, "第三部分", "系统实现 · 实验验证 · 现场演示",
    ["Web 控制台", "骨架视觉分析", "量化评测结果"],
    "metrics_chart.png",
  )

  _slide_lr(
    prs, "Web 控制台实现",
    [
      "FastAPI 后端 + 浏览器前端",
      "实时风险仪表盘、对话与指令流",
      "支持上传照片 / 摄像头骨架分析",
      "一键演示剧本：日常→倾诉→跌倒",
    ],
    "ppt_full_dashboard.png",
    diagram=False,
    caption="系统实拍 · 仪表盘",
  )

  _screenshot_slide(prs, "系统界面：MediaPipe 骨架分析（上传照片）", "ppt_mediapipe_pose.png",
                    "上传全身照导出骨架叠加图 · 支持答辩现场上传演示")
  _screenshot_slide(prs, "系统界面：老人倾诉场景（演示剧本）", "ppt_full_dashboard.png",
                    "演示场景「老人倾诉」· 风险 0.23 · 机器人主动安抚")
  _screenshot_slide(prs, "系统界面：风险决策仪表盘", "ppt_risk_panel.png",
                    "多模态融合：风险分数、因素、机器人回应及四项监测指标")
  _screenshot_slide(prs, "系统界面：紧急状态监测", "ppt_header_perception.png",
                    "状态机进入「紧急」· 感知输入与 MediaPipe 视觉模块")
  _screenshot_slide(prs, "系统界面：跌倒紧急对话日志", "ppt_chat_emergency.png",
                    "跌倒紧急流程触发 · 多次紧急安抚语音")
  _screenshot_slide(prs, "系统界面：机器人指令流", "ppt_robot_commands.png",
                    "告警音→语音→紧急呼叫→举手手势，全链路可追溯")

  _slide_lr(
    prs, "实验评测结果",
    [
      "跌倒检测 P/R/F1：100%（6类合成场景）",
      "紧急呼叫端到端触发率：100%",
      "单帧决策延迟 < 50ms（CPU）",
      "pytest + 无头压测全部通过",
      "报告：fall_eval_report.json",
    ],
    "metrics_chart.png",
    key_takeaway="指标可复现、脚本可一键运行",
  )

  _slide_lr(
    prs, "开源与可复现性",
    [
      f"仓库：{GITHUB_URL}",
      f"团队：{TEAM_NAME}（{SCHOOL}）",
      "演示：bash scripts/run_web.sh",
      "录像：docs/assets/demo_carecompanion.mp4",
      "软著：申请中",
    ],
    "ppt_demo_qr.png",
    diagram=False,
    caption="扫码访问 GitHub",
  )

  _part_divider(
    prs, "第四部分", "创新点 · 应用价值 · 后续计划",
    ["五维创新自评", "真机对接路线", "软著与专利布局"],
    "innovation_radar.png",
  )

  _slide_lr(
    prs, "创新维度总结",
    [
      "多模态可解释融合，优于模块堆叠",
      "紧急硬优先级状态机 + 动作闭环",
      "MediaPipe 视觉接入，非纯滑块",
      "工程化：评测脚本 + 开源仓库",
      "面向居家养老的应用场景明确",
    ],
    "innovation_radar.png",
    caption="创新维度雷达图",
  )

  _slide_lr(
    prs, "后续工作计划",
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
    prs, "参考文献与资料",
    [
      "[1] Google MediaPipe Pose",
      "[2] Unitree / ROS2 文档",
      "[3] 「十四五」养老服务规划",
      "[4] docs/TECHNICAL_REPORT.md",
      "[5] GitHub 开源仓库",
    ],
    "pipeline.png",
  )

  slide = _content_slide(prs, "扫码查看代码与演示视频")
  _bullets(slide, [
    "GitHub 完整源码与文档",
    "在线 Web 演示（现场可复现）",
    "演示录像已附仓库",
    "欢迎评委扫码查阅",
  ], top=1.0, size=12, width=TEXT_W)
  qr_path = ASSETS / "ppt_demo_qr.png"
  if qr_path.exists():
    _image_frame(slide, IMG_LEFT, IMG_TOP, 2.0, 2.0, "GitHub 仓库")
    _place_image(slide, qr_path, IMG_LEFT, IMG_TOP, 2.0, 2.0)
  demo_thumb = ASSETS / "ppt_mediapipe_pose.png"
  if demo_thumb.exists():
    _image_frame(slide, IMG_LEFT + 2.25, IMG_TOP, 2.25, 2.0, "演示界面")
    _place_image(slide, demo_thumb, IMG_LEFT + 2.25, IMG_TOP, 2.25, 2.0)

  _thanks_slide(prs, sw, sh)

  OUT.parent.mkdir(parents=True, exist_ok=True)
  prs.save(str(OUT))
  print(f"✅ 已生成国赛风格 PPT: {OUT}")
  print(f"   共 {len(prs.slides)} 页")


if __name__ == "__main__":
  main()
