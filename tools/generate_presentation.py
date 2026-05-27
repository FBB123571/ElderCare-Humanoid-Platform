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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.ppt_layout import (
  CAPTION_H,
  COL_L,
  COL_L_W,
  COL_R,
  COL_R_W,
  CONTENT_BOTTOM,
  CONTENT_H,
  CONTENT_TOP,
  FOOTER_H,
  HEADER_H,
  IMG_PAD,
  MARGIN,
  RIBBON_H,
  SLIDE_H,
  SLIDE_W,
  TITLE_H,
  TITLE_TOP,
  body_height,
  ribbon_top,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "答辩_CareCompanion.pptx"
ASSETS = ROOT / "docs" / "assets"
DIAG = ASSETS / "diagrams"

WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(28, 32, 44)
DARK = RGBColor(20, 50, 120)
GRAY = RGBColor(90, 98, 115)
LIGHT_BLUE = RGBColor(241, 247, 255)
ACCENT = RGBColor(245, 158, 11)
SOFT_BLUE = RGBColor(219, 234, 254)
BORDER = RGBColor(186, 200, 220)
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
    p.text = p.text or " "
  for run in p.runs:
    _set_run_font(run, size, bold=bold, color=color)
  if not p.runs:
    _set_run_font(p.add_run(), size, bold=bold, color=color)


def _bg_white(slide):
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = WHITE


def _header_bar(slide):
  bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(SLIDE_W), Inches(HEADER_H))
  bar.fill.solid()
  bar.fill.fore_color.rgb = DARK
  bar.line.fill.background()
  box = slide.shapes.add_textbox(Inches(MARGIN), Inches(0.06), Inches(SLIDE_W - 2 * MARGIN), Inches(0.38))
  p = box.text_frame.paragraphs[0]
  p.text = f"{COMP_LINE1}  |  {COMP_LINE2}"
  _set_para_font(p, 9, bold=True, color=WHITE)


def _footer_bar(slide, hint: str = ""):
  y = SLIDE_H - FOOTER_H
  bar = slide.shapes.add_shape(1, Inches(0), Inches(y), Inches(SLIDE_W), Inches(FOOTER_H))
  bar.fill.solid()
  bar.fill.fore_color.rgb = SOFT_BLUE
  bar.line.fill.background()
  txt = f"{TEAM_NAME} · {SCHOOL} · {CAPTAIN}/{MEMBER} · 指导教师 {ADVISOR}"
  if hint:
    txt = f"{hint}  |  {txt}"
  box = slide.shapes.add_textbox(Inches(MARGIN), Inches(y + 0.05), Inches(SLIDE_W - 2 * MARGIN), Inches(0.2))
  p = box.text_frame.paragraphs[0]
  p.text = txt
  p.alignment = PP_ALIGN.CENTER
  _set_para_font(p, 8, color=GRAY)


def _title(slide, text: str, *, center=False):
  left = MARGIN if not center else MARGIN
  width = SLIDE_W - 2 * MARGIN
  box = slide.shapes.add_textbox(Inches(left), Inches(TITLE_TOP), Inches(width), Inches(TITLE_H))
  p = box.text_frame.paragraphs[0]
  p.text = text
  _set_para_font(p, 20, bold=True, color=DARK)
  p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
  if not center:
    line = slide.shapes.add_shape(1, Inches(left), Inches(TITLE_TOP + TITLE_H - 0.04), Inches(1.25), Inches(0.055))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()


def _ribbon(slide, text: str):
  y = ribbon_top()
  bar = slide.shapes.add_shape(1, Inches(COL_L), Inches(y), Inches(COL_L_W), Inches(RIBBON_H))
  bar.fill.solid()
  bar.fill.fore_color.rgb = DARK
  bar.line.fill.background()
  box = slide.shapes.add_textbox(Inches(COL_L + 0.12), Inches(y + 0.07), Inches(COL_L_W - 0.24), Inches(RIBBON_H - 0.1))
  p = box.text_frame.paragraphs[0]
  p.text = text
  p.alignment = PP_ALIGN.CENTER
  _set_para_font(p, 11, bold=True, color=WHITE)


def _style_cell(cell, text: str, *, bg=DARK, fg=WHITE, bold=True, size=11):
  cell.text = ""
  p = cell.text_frame.paragraphs[0]
  p.text = text
  p.alignment = PP_ALIGN.CENTER
  _set_para_font(p, size, bold=bold, color=fg)
  cell.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
  cell.fill.solid()
  cell.fill.fore_color.rgb = bg
  cell.margin_left = Pt(4)
  cell.margin_right = Pt(4)
  cell.margin_top = Pt(2)
  cell.margin_bottom = Pt(2)


def _bullets_panel(
  slide,
  items: list[str],
  *,
  highlights: list[int] | None = None,
  size: int = 12,
  takeaway: str = "",
):
  """左栏要点：每条独立文本框 + 顶对齐，避免垂直居中造成行距错乱。"""
  highlights = highlights or []
  top = CONTENT_TOP
  height = CONTENT_H
  foot_h = 0.36 if takeaway else 0.0
  pad_top, pad_side = 0.14, 0.20

  panel = slide.shapes.add_shape(1, Inches(COL_L), Inches(top), Inches(COL_L_W), Inches(height))
  panel.fill.solid()
  panel.fill.fore_color.rgb = LIGHT_BLUE
  panel.line.color.rgb = BORDER
  panel.line.width = Pt(0.8)

  stripe = slide.shapes.add_shape(1, Inches(COL_L), Inches(top), Inches(0.08), Inches(height))
  stripe.fill.solid()
  stripe.fill.fore_color.rgb = DARK
  stripe.line.fill.background()

  text_top = top + pad_top
  text_h = height - pad_top - 0.12 - foot_h
  n = max(1, len(items))
  slot_h = text_h / n

  for i, line in enumerate(items):
    y = text_top + i * slot_h
    box = slide.shapes.add_textbox(
      Inches(COL_L + pad_side), Inches(y),
      Inches(COL_L_W - pad_side * 2), Inches(slot_h - 0.02),
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Pt(2)
    tf.margin_top = Pt(0)
    p = tf.paragraphs[0]
    p.text = line if line.startswith("●") else f"● {line}"
    _set_para_font(p, size, bold=(i in highlights), color=DARK if i in highlights else BLACK)
    p.line_spacing = 1.15
    p.space_after = Pt(0)

  if takeaway:
    fy = top + height - foot_h
    foot = slide.shapes.add_shape(
      1, Inches(COL_L + 0.10), Inches(fy), Inches(COL_L_W - 0.20), Inches(foot_h - 0.02),
    )
    foot.fill.solid()
    foot.fill.fore_color.rgb = DARK
    foot.line.fill.background()
    fb = slide.shapes.add_textbox(
      Inches(COL_L + 0.14), Inches(fy + 0.07), Inches(COL_L_W - 0.28), Inches(foot_h - 0.14),
    )
    tf = fb.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    fp = tf.paragraphs[0]
    fp.text = takeaway
    fp.alignment = PP_ALIGN.CENTER
    _set_para_font(fp, 11, bold=True, color=WHITE)


def _fit_image(path: Path, max_w: float, max_h: float) -> tuple[float, float]:
  with Image.open(path) as im:
    px_w, px_h = im.size
  aspect = px_h / px_w
  w, h = max_w, max_w * aspect
  if h > max_h:
    h, w = max_h, max_h / aspect
  return w, h


def _place_figure(
  slide,
  path: Path,
  *,
  left: float,
  top: float,
  max_w: float,
  max_h: float,
  caption: str = "",
  fill_ratio: float = 1.0,
  edge_to_edge: bool = False,
  cover: bool = False,
) -> None:
  """在指定区域内放置配图；cover=True 时放大填满区域（适合数据图）。"""
  if not path.exists():
    return
  cap_h = 0 if edge_to_edge else (CAPTION_H if caption else 0)
  box_w = max_w * fill_ratio
  box_h = (max_h - cap_h) * fill_ratio
  w0, h0 = _fit_image(path, box_w, box_h)
  if cover:
    scale = max(box_w / w0, box_h / h0)
    w, h = w0 * scale, h0 * scale
  else:
    w, h = w0, h0
  x = left + (max_w - w) / 2
  y = top + (max_h - cap_h - h) / 2

  pad = 0.03 if edge_to_edge else 0.05
  if not edge_to_edge:
    frame = slide.shapes.add_shape(
      1, Inches(x - pad), Inches(y - pad),
      Inches(w + 2 * pad), Inches(h + 2 * pad + (CAPTION_H if caption else 0)),
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = WHITE
    frame.line.color.rgb = BORDER
    frame.line.width = Pt(0.8)

  slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
  if caption and not edge_to_edge:
    cap = slide.shapes.add_textbox(Inches(left), Inches(y + h + 0.06), Inches(max_w), Inches(CAPTION_H))
    cp = cap.text_frame.paragraphs[0]
    cp.text = caption
    cp.alignment = PP_ALIGN.CENTER
    _set_para_font(cp, 9, color=GRAY)


def _content_slide(prs, title: str, footer_hint: str = ""):
  slide = _slide(prs)
  _bg_white(slide)
  _header_bar(slide)
  _footer_bar(slide, footer_hint)
  _title(slide, title)
  return slide


def _caption_for(kind: str, custom: str) -> str:
  if custom:
    return custom
  return {"diagram": "理论框图", "chart": "数据示意", "photo": "系统实拍"}.get(kind, "")


def _info_cards_column(slide, left: float, width: float, rows: list[tuple[str, str]]):
  """右栏参赛信息表：单元格垂直居中、行高均分。"""
  top = CONTENT_TOP
  height = CONTENT_H
  n = len(rows)
  tbl = slide.shapes.add_table(n, 2, Inches(left), Inches(top), Inches(width), Inches(height)).table
  label_w = Inches(0.92)
  tbl.columns[0].width = label_w
  tbl.columns[1].width = Inches(width) - label_w

  for r, (label, value) in enumerate(rows):
    _style_cell(tbl.cell(r, 0), label, bg=DARK, fg=WHITE, bold=True, size=10)
    c1 = tbl.cell(r, 1)
    c1.text = ""
    p = c1.text_frame.paragraphs[0]
    p.text = value
    p.alignment = PP_ALIGN.LEFT
    fs = 10 if len(value) <= 28 else 8
    _set_para_font(p, fs, bold=False, color=DARK)
    c1.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    c1.text_frame.word_wrap = True
    c1.fill.solid()
    c1.fill.fore_color.rgb = LIGHT_BLUE
    c1.margin_left = Pt(6)
    c1.margin_right = Pt(4)


def _slide_team_info(prs):
  slide = _content_slide(prs, "参赛信息")
  _bullets_panel(slide, [
    "赛项：创新赛 · 机器人创新赛道",
    "作品：智能养老陪伴机器人仿真平台",
    "（基于大语言模型）",
    "特色：理论清晰 · 系统可演示 · 指标可复现",
  ], size=12)
  _info_cards_column(
    slide, COL_R, COL_R_W,
    [
      ("团队", TEAM_NAME),
      ("学校", SCHOOL),
      ("队长", CAPTAIN),
      ("队员", MEMBER),
      ("指导教师", ADVISOR),
      ("团队编号", TEAM_ID),
      ("作品编号", PROJECT_ID),
    ],
  )
  return slide


def _slide_lr(
  prs,
  title: str,
  bullets: list[str],
  image: str | Path,
  *,
  diagram: bool = True,
  figure_kind: str = "",
  bullet_size: int = 13,
  caption: str = "",
  highlight_last: bool = False,
  footer_hint: str = "",
  key_takeaway: str = "",
):
  slide = _content_slide(prs, title, footer_hint)
  hi = [len(bullets) - 1] if highlight_last and bullets else []
  _bullets_panel(slide, bullets, highlights=hi, size=bullet_size, takeaway=key_takeaway)

  sub = DIAG / image if diagram else ASSETS / image
  if not sub.exists() and diagram:
    sub = ASSETS / image

  kind = figure_kind or ("diagram" if diagram else "photo")
  img_top = CONTENT_TOP + IMG_PAD
  img_h = CONTENT_H - 2 * IMG_PAD
  cap = _caption_for(kind, caption)
  _place_figure(
    slide, sub, left=COL_R, top=img_top, max_w=COL_R_W, max_h=img_h,
    caption=cap, fill_ratio=1.0, cover=(kind == "chart"),
  )
  return slide


def _slide_open_source(prs):
  """开源页：左信息卡片 + 右二维码与演示缩略图（避免 QR 过大）。"""
  slide = _content_slide(prs, "开源与可复现性")

  cards = [
    ("GitHub 仓库", GITHUB_URL),
    ("团队", f"{TEAM_NAME}（{SCHOOL}）"),
    ("本地演示", "bash scripts/run_web.sh"),
    ("演示录像", "docs/assets/demo_carecompanion.mp4"),
    ("软著", "申请中"),
  ]
  card_h = (CONTENT_H - 0.1) / len(cards)
  for i, (label, value) in enumerate(cards):
    y = CONTENT_TOP + 0.05 + i * card_h
    card = slide.shapes.add_shape(1, Inches(COL_L), Inches(y), Inches(COL_L_W), Inches(card_h - 0.08))
    card.fill.solid()
    card.fill.fore_color.rgb = LIGHT_BLUE if i % 2 == 0 else WHITE
    card.line.color.rgb = BORDER
    lb = slide.shapes.add_textbox(Inches(COL_L + 0.15), Inches(y + 0.06), Inches(1.0), Inches(card_h - 0.12))
    lp = lb.text_frame.paragraphs[0]
    lp.text = label
    _set_para_font(lp, 10, bold=True, color=GRAY)
    vb = slide.shapes.add_textbox(Inches(COL_L + 1.1), Inches(y + 0.06), Inches(COL_L_W - 1.25), Inches(card_h - 0.12))
    vp = vb.text_frame.paragraphs[0]
    vp.text = value
    vp.word_wrap = True
    _set_para_font(vp, 10 if len(value) < 40 else 9, color=DARK)

  qr = ASSETS / "ppt_demo_qr.png"
  thumb = ASSETS / "ppt_full_dashboard.png"
  right_top = CONTENT_TOP + 0.08
  right_h = CONTENT_H - 0.16
  if qr.exists():
    _place_figure(slide, qr, left=COL_R + 0.15, top=right_top, max_w=2.0, max_h=2.0, caption="扫码访问", fill_ratio=1.0)
  if thumb.exists():
    _place_figure(
      slide, thumb, left=COL_R + 2.35, top=right_top,
      max_w=COL_R_W - 2.5, max_h=right_h, caption="Web 控制台实拍", fill_ratio=0.96,
    )


def _hero_cover(prs):
  slide = _slide(prs)
  _header_bar(slide)
  sh = SLIDE_H

  left_w = 5.0
  left_bg = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H), Inches(left_w), Inches(sh - HEADER_H))
  left_bg.fill.solid()
  left_bg.fill.fore_color.rgb = LIGHT_BLUE
  left_bg.line.fill.background()

  hero = ASSETS / "ppt_mediapipe_pose.png"
  if not hero.exists():
    hero = ASSETS / "ppt_full_dashboard.png"
  if hero.exists():
    area_h = sh - HEADER_H - 0.25
    _place_figure(slide, hero, left=0.15, top=HEADER_H + 0.12, max_w=left_w - 0.3, max_h=area_h,
                  caption="MediaPipe 骨架 · 可现场演示", fill_ratio=0.98)

  rx = left_w
  right_bg = slide.shapes.add_shape(1, Inches(rx), Inches(HEADER_H), Inches(SLIDE_W - rx), Inches(sh - HEADER_H))
  right_bg.fill.solid()
  right_bg.fill.fore_color.rgb = DARK
  right_bg.line.fill.background()
  deco = slide.shapes.add_shape(1, Inches(rx), Inches(HEADER_H), Inches(0.1), Inches(sh - HEADER_H))
  deco.fill.solid()
  deco.fill.fore_color.rgb = ACCENT
  deco.line.fill.background()

  texts = [
    ("CareCompanion", 32, WHITE, True),
    ("智能养老陪伴机器人仿真平台", 15, RGBColor(147, 197, 253), True),
    ("感知 · 决策 · 执行  一体化闭环", 13, RGBColor(226, 232, 240), False),
  ]
  ty = HEADER_H + 0.45
  for text, sz, col, bold in texts:
    box = slide.shapes.add_textbox(Inches(rx + 0.25), Inches(ty), Inches(4.5), Inches(0.5))
    p = box.text_frame.paragraphs[0]
    p.text = text
    _set_para_font(p, sz, bold=bold, color=col)
    ty += 0.48 if sz > 20 else 0.38

  card_y = ty + 0.2
  card = slide.shapes.add_shape(1, Inches(rx + 0.25), Inches(card_y), Inches(4.35), Inches(1.45))
  card.fill.solid()
  card.fill.fore_color.rgb = RGBColor(30, 64, 130)
  card.line.color.rgb = RGBColor(100, 140, 200)

  infos = [
    f"团队：{TEAM_NAME}（{SCHOOL}）",
    f"队员：{CAPTAIN}（队长）· {MEMBER}",
    f"指导教师：{ADVISOR}",
    f"作品编号：{PROJECT_ID}",
  ]
  box = slide.shapes.add_textbox(Inches(rx + 0.4), Inches(card_y + 0.15), Inches(4.0), Inches(1.2))
  tf = box.text_frame
  for i, line in enumerate(infos):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line
    _set_para_font(p, 10, color=RGBColor(220, 230, 255))
    p.space_after = Pt(5)

  tag = slide.shapes.add_textbox(Inches(rx + 0.25), Inches(sh - 0.5), Inches(4.4), Inches(0.35))
  tp = tag.text_frame.paragraphs[0]
  tp.text = PROJECT_TITLE
  _set_para_font(tp, 9, color=RGBColor(148, 163, 184))


def _part_divider(prs, part: str, subtitle: str, preview: list[str], thumb: str = "architecture.png"):
  slide = _slide(prs)
  _bg_white(slide)
  _header_bar(slide)
  _footer_bar(slide)

  left_w = 4.75
  block_h = CONTENT_BOTTOM - HEADER_H
  main = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H), Inches(left_w), Inches(block_h))
  main.fill.solid()
  main.fill.fore_color.rgb = DARK
  main.line.fill.background()

  num = part.replace("第", "").replace("部分", "")[:1]
  circle = slide.shapes.add_shape(9, Inches(0.42), Inches(HEADER_H + 0.35), Inches(0.72), Inches(0.72))
  circle.fill.solid()
  circle.fill.fore_color.rgb = ACCENT
  circle.line.fill.background()
  nb = slide.shapes.add_textbox(Inches(0.42), Inches(HEADER_H + 0.42), Inches(0.72), Inches(0.45))
  np = nb.text_frame.paragraphs[0]
  np.text = num
  np.alignment = PP_ALIGN.CENTER
  _set_para_font(np, 22, bold=True, color=WHITE)

  ty = HEADER_H + 1.15
  box = slide.shapes.add_textbox(Inches(0.38), Inches(ty), Inches(4.2), Inches(0.5))
  p = box.text_frame.paragraphs[0]
  p.text = part
  _set_para_font(p, 24, bold=True, color=WHITE)

  sub = slide.shapes.add_textbox(Inches(0.4), Inches(ty + 0.52), Inches(4.2), Inches(0.38))
  sp = sub.text_frame.paragraphs[0]
  sp.text = subtitle
  _set_para_font(sp, 12, color=RGBColor(191, 219, 254))

  chip_y = ty + 1.05
  for line in preview:
    chip = slide.shapes.add_shape(1, Inches(0.42), Inches(chip_y), Inches(4.0), Inches(0.42))
    chip.fill.solid()
    chip.fill.fore_color.rgb = RGBColor(30, 64, 130)
    chip.line.color.rgb = RGBColor(100, 140, 200)
    cb = slide.shapes.add_textbox(Inches(0.55), Inches(chip_y + 0.08), Inches(3.75), Inches(0.28))
    cp = cb.text_frame.paragraphs[0]
    cp.text = line
    _set_para_font(cp, 11, color=RGBColor(226, 232, 240))
    chip_y += 0.48

  pth = DIAG / thumb
  right_w = SLIDE_W - left_w
  right_bg = slide.shapes.add_shape(1, Inches(left_w), Inches(HEADER_H), Inches(right_w), Inches(block_h))
  right_bg.fill.solid()
  right_bg.fill.fore_color.rgb = LIGHT_BLUE
  right_bg.line.fill.background()
  if pth.exists():
    _place_figure(
      slide, pth, left=left_w + IMG_PAD, top=CONTENT_TOP + IMG_PAD,
      max_w=right_w - 2 * IMG_PAD, max_h=CONTENT_H - 2 * IMG_PAD,
      caption="", edge_to_edge=True, fill_ratio=1.0,
    )


def _screenshot_slide(prs, title: str, image_file: str, caption: str = ""):
  slide = _content_slide(prs, title, "系统实拍")
  path = ASSETS / image_file
  _place_figure(
    slide, path,
    left=MARGIN, top=CONTENT_TOP + 0.05,
    max_w=SLIDE_W - 2 * MARGIN, max_h=CONTENT_H - 0.05,
    caption=caption, fill_ratio=0.97,
  )


def _thanks_slide(prs):
  slide = _slide(prs)
  _header_bar(slide)
  sh = SLIDE_H

  left_w = 4.85
  left_bg = slide.shapes.add_shape(1, Inches(0), Inches(HEADER_H), Inches(left_w), Inches(sh - HEADER_H))
  left_bg.fill.solid()
  left_bg.fill.fore_color.rgb = DARK
  left_bg.line.fill.background()

  thumb = ASSETS / "ppt_full_dashboard.png"
  if thumb.exists():
    _place_figure(slide, thumb, left=0.12, top=HEADER_H + 0.1, max_w=left_w - 0.24, max_h=sh - HEADER_H - 0.2,
                  caption="系统仪表盘", fill_ratio=0.98)

  rx = left_w
  right_bg = slide.shapes.add_shape(1, Inches(rx), Inches(HEADER_H), Inches(SLIDE_W - rx), Inches(sh - HEADER_H))
  right_bg.fill.solid()
  right_bg.fill.fore_color.rgb = LIGHT_BLUE
  right_bg.line.fill.background()

  box = slide.shapes.add_textbox(Inches(rx + 0.2), Inches(1.35), Inches(SLIDE_W - rx - 0.4), Inches(0.65))
  p = box.text_frame.paragraphs[0]
  p.text = "敬请批评指正"
  p.alignment = PP_ALIGN.CENTER
  _set_para_font(p, 30, bold=True, color=DARK)

  sub = slide.shapes.add_textbox(Inches(rx + 0.2), Inches(2.15), Inches(SLIDE_W - rx - 0.4), Inches(1.1))
  tf = sub.text_frame
  for i, line in enumerate([f"{TEAM_NAME} · {SCHOOL}", f"{CAPTAIN} · {MEMBER}", f"指导教师 {ADVISOR}"]):
    para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    para.text = line
    para.alignment = PP_ALIGN.CENTER
    _set_para_font(para, 13, bold=(i == 0))
    para.space_after = Pt(6)

  qr = ASSETS / "ppt_demo_qr.png"
  if qr.exists():
    _place_figure(slide, qr, left=rx + 1.5, top=3.35, max_w=1.55, max_h=1.55, caption="GitHub", fill_ratio=1.0)


def _slide_qr_dual(prs):
  slide = _content_slide(prs, "扫码查看代码与演示视频")
  _bullets_panel(slide, [
    "GitHub 完整源码与文档",
    "在线 Web 演示（现场可复现）",
    "演示录像已附仓库",
    "欢迎评委扫码查阅",
  ], size=13)
  qr = ASSETS / "ppt_demo_qr.png"
  demo = ASSETS / "ppt_mediapipe_pose.png"
  if qr.exists():
    _place_figure(slide, qr, left=COL_R + 0.1, top=CONTENT_TOP + 0.2, max_w=2.1, max_h=2.1, caption="仓库二维码", fill_ratio=1.0)
  if demo.exists():
    _place_figure(slide, demo, left=COL_R + 2.35, top=CONTENT_TOP + 0.15,
                  max_w=COL_R_W - 2.45, max_h=CONTENT_H - 0.2, caption="演示界面", fill_ratio=1.0)


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
  prs.slide_width = Inches(SLIDE_W)
  prs.slide_height = Inches(SLIDE_H)

  _hero_cover(prs)

  _slide_lr(prs, "目录", [
    "第一部分  项目背景与需求分析",
    "第二部分  关键技术与理论模型",
    "第三部分  系统实现与实验验证",
    "第四部分  创新点与展望",
    "附录  演示界面与开源仓库",
  ], "pipeline.png", caption="全篇结构", key_takeaway="理论 + 工程 + 现场演示")

  _slide_team_info(prs)

  _part_divider(prs, "第一部分", "项目背景 · 需求分析 · 方案定位",
                ["老龄化与跌倒空窗", "方案对比", "项目目标"], "aging_chart.png")

  _slide_lr(prs, "社会背景：老龄化与跌倒风险", [
    "独居老人增多，跌倒「发现空窗」是核心痛点",
    "情感陪伴需求上升，监测难形成照护闭环",
    "政策导向：智慧养老与居家安全并重",
    "本项目：仿真验证 + 人形机器人接口",
  ], "aging_chart.png", figure_kind="chart", caption="国家统计局趋势示意",
    key_takeaway="痛点：发现慢 + 闭环弱", highlight_last=True, bullet_size=12)

  _slide_lr(prs, "现有方案对比", [
    "传统音箱/摄像头/手环：功能割裂",
    "本作品：感知—决策—执行统一编排",
    "强调可解释风险与紧急硬优先级",
    "配套 Web 演示与量化评测脚本",
  ], "compare.png", key_takeaway="从堆叠到一体化闭环")

  _slide_lr(prs, "项目概述与目标", [
    "CareCompanion：养老人形陪伴软件平台",
    "CareOrchestrator 统一调度各模块",
    "目标1：跌倒检测与紧急呼叫自动化",
    "目标2：情感对话与机器人动作联动",
    "目标3：ROS2 部署接口 + 开源可复现",
  ], "architecture.png", key_takeaway="三大目标均可现场验证")

  _part_divider(prs, "第二部分", "理论模型 · 算法设计 · 系统架构",
                ["四层架构", "风险融合", "应急链路"], "state_machine.png")

  _slide_lr(prs, "系统总体架构", [
    "四层架构：感知 / 认知 / 执行 / 交互",
    "核心：CareOrchestrator + 状态机",
    "模块可替换：仿真、Web、ROS2 共用一套逻辑",
    "配置集中于 config/default.yaml",
  ], "architecture.png", caption="四层架构", key_takeaway="理论清晰、可替换")

  _slide_lr(prs, "状态机与调度策略", [
    "MONITOR → CONVERSE → ALERT → EMERGENCY",
    "紧急态可打断对话与常规任务",
    "每个 tick 输出风险、回复、动作序列",
    "便于日志审计与答辩讲解",
  ], "state_machine.png", caption="状态转移")

  _slide_lr(prs, "多模态风险融合（理论）", [
    "加权融合跌倒、情绪、健康三路分数",
    "输出等级与原因列表，非黑盒端到端",
    "阈值可配置，支持场景调参",
    "契合医疗与养老合规沟通需求",
  ], "risk_formula.png", caption="融合公式")

  _slide_lr(prs, "跌倒检测算法设计", [
    "输入：MediaPipe 骨架几何特征",
    "快速跌倒 + 慢速躺倒双规则",
    "合成 6 场景评测 F1=100%",
    "可接摄像头或上传照片分析",
  ], "fall_flow.png", caption="检测流程")

  _slide_lr(prs, "对话与情感模块", [
    "文本情感词典 + 情绪标签融合",
    "DialogueManager 生成安抚话术",
    "默认 Mock，可切换 LLM API",
    "与 RiskEngine、CarePlanner 协同",
  ], "llm_module.png", caption="对话模块")

  _slide_lr(prs, "数据处理与决策流水线", [
    "感知帧 → 特征 → 融合 → 状态机",
    "CarePlanner 生成 RobotAction",
    "RobotAdapter 下发仿真或 ROS2",
    "全链路可在 Web 界面观察",
  ], "pipeline.png", caption="数据流水线")

  _slide_lr(prs, "紧急响应链路（理论）", [
    "确认跌倒后按序触发四类动作",
    "告警音 → 语音 → 家属通知 → 手势",
    "EmergencyNotifier 记录推送渠道",
    "端到端触发率评测 100%",
  ], "emergency_flow.png", key_takeaway="紧急链路可端到端验证")

  _part_divider(prs, "第三部分", "系统实现 · 实验验证 · 现场演示",
                ["Web 控制台", "视觉分析", "量化评测"], "metrics_chart.png")

  _slide_lr(prs, "Web 控制台实现", [
    "FastAPI 后端 + 浏览器前端",
    "实时风险仪表盘、对话与指令流",
    "支持上传照片 / 摄像头骨架分析",
    "一键演示剧本：日常→倾诉→跌倒",
  ], "ppt_full_dashboard.png", diagram=False, caption="仪表盘实拍")

  _screenshot_slide(prs, "系统界面：MediaPipe 骨架分析", "ppt_mediapipe_pose.png",
                    "上传全身照导出骨架图 · 支持现场演示")
  _screenshot_slide(prs, "系统界面：老人倾诉场景", "ppt_full_dashboard.png",
                    "演示「老人倾诉」· 风险 0.23 · 主动安抚")
  _screenshot_slide(prs, "系统界面：风险决策仪表盘", "ppt_risk_panel.png",
                    "多模态融合：分数、因素、回应与监测指标")
  _screenshot_slide(prs, "系统界面：紧急状态监测", "ppt_header_perception.png",
                    "状态机进入紧急 · MediaPipe 视觉模块")
  _screenshot_slide(prs, "系统界面：跌倒紧急对话日志", "ppt_chat_emergency.png",
                    "紧急流程触发 · 多次安抚语音")
  _screenshot_slide(prs, "系统界面：机器人指令流", "ppt_robot_commands.png",
                    "告警音→语音→呼叫→手势，全链路可追溯")

  _slide_lr(prs, "实验评测结果", [
    "跌倒检测 P/R/F1：100%（6类合成场景）",
    "紧急呼叫端到端触发率：100%",
    "单帧决策延迟 < 50ms（CPU）",
    "pytest + 无头压测全部通过",
    "报告：fall_eval_report.json",
  ], "metrics_chart.png", key_takeaway="指标可复现、脚本一键运行")

  _slide_open_source(prs)

  _part_divider(prs, "第四部分", "创新点 · 应用价值 · 后续计划",
                ["创新维度", "真机路线", "软著专利"], "innovation_radar.png")

  _slide_lr(prs, "创新维度总结", [
    "多模态可解释融合，优于模块堆叠",
    "紧急硬优先级状态机 + 动作闭环",
    "MediaPipe 视觉接入，非纯滑块",
    "工程化：评测脚本 + 开源仓库",
    "面向居家养老的应用场景明确",
  ], "innovation_radar.png", caption="创新雷达")

  _slide_lr(prs, "后续工作计划", [
    "对接 Unitree 等人形真机",
    "引入 UR Fall 等公开数据集",
    "多房间遮挡与光照优化",
    "养老院调研与产品化评估",
    "软著与专利布局",
  ], "roadmap.png", caption="路线图")

  _slide_lr(prs, "参考文献与资料", [
    "[1] Google MediaPipe Pose",
    "[2] Unitree / ROS2 文档",
    "[3] 「十四五」养老服务规划",
    "[4] docs/TECHNICAL_REPORT.md",
    "[5] GitHub 开源仓库",
  ], "pipeline.png")

  _slide_qr_dual(prs)
  _thanks_slide(prs)

  OUT.parent.mkdir(parents=True, exist_ok=True)
  prs.save(str(OUT))
  print(f"✅ 已生成: {OUT}  共 {len(prs.slides)} 页")


if __name__ == "__main__":
  main()
