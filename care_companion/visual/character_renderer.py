"""双数字人全身立绘 + 中文对白（精致卡通风格，PIL 渲染）。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720

_FONT_CANDIDATES = [
  Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
  Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
  Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  paths = _FONT_CANDIDATES if not bold else [_FONT_CANDIDATES[1], *_FONT_CANDIDATES]
  for p in paths:
    if p.is_file():
      try:
        return ImageFont.truetype(str(p), size)
      except OSError:
        continue
  return ImageFont.load_default()


def _wrap_cn(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
  if not text:
    return []
  lines: list[str] = []
  line = ""
  probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
  for ch in text:
    trial = line + ch
    if probe.textbbox((0, 0), trial, font=font)[2] > max_width and line:
      lines.append(line)
      line = ch
    else:
      line = trial
  if line:
    lines.append(line)
  return lines


def _lerp(a: int, b: int, t: float) -> int:
  return int(a + (b - a) * t)


def _vgradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
  w, h = size
  img = Image.new("RGB", (w, h))
  px = img.load()
  for y in range(h):
    t = y / max(h - 1, 1)
    c = tuple(_lerp(top[i], bottom[i], t) for i in range(3))
    for x in range(w):
      px[x, y] = c
  return img


def _draw_shadow(draw: ImageDraw.ImageDraw, cx: int, ground: int) -> None:
  draw.ellipse([cx - 48, ground - 10, cx + 48, ground + 8], fill=(15, 23, 42))


def _draw_face(draw: ImageDraw.ImageDraw, cx: int, cy: int, mood: str, skin: tuple[int, int, int]) -> None:
  draw.ellipse([cx - 28, cy, cx + 28, cy + 54], fill=skin, outline=(214, 180, 140), width=1)
  # 腮红
  draw.ellipse([cx - 22, cy + 30, cx - 10, cy + 38], fill=(255, 200, 190))
  draw.ellipse([cx + 10, cy + 30, cx + 22, cy + 38], fill=(255, 200, 190))
  eye_y = cy + 24
  draw.ellipse([cx - 14, eye_y, cx - 6, eye_y + 8], fill=(40, 50, 70))
  draw.ellipse([cx + 6, eye_y, cx + 14, eye_y + 8], fill=(40, 50, 70))
  draw.ellipse([cx - 12, eye_y + 1, cx - 8, eye_y + 4], fill=(255, 255, 255))
  draw.ellipse([cx + 8, eye_y + 1, cx + 12, eye_y + 4], fill=(255, 255, 255))
  my = cy + 40
  if mood == "happy":
    draw.arc([cx - 12, my - 4, cx + 12, my + 10], 10, 170, fill=(60, 50, 50), width=2)
  elif mood in ("sad", "anxious", "emergency"):
    draw.arc([cx - 10, my + 2, cx + 10, my + 12], 190, 350, fill=(60, 50, 50), width=2)
    if mood == "anxious":
      draw.line([(cx - 18, cy + 18), (cx - 10, cy + 22)], fill=(80, 60, 60), width=1)
      draw.line([(cx + 18, cy + 18), (cx + 10, cy + 22)], fill=(80, 60, 60), width=1)
  else:
    draw.line([(cx - 8, my + 4), (cx + 8, my + 4)], fill=(60, 50, 50), width=2)


def _draw_elder(draw: ImageDraw.ImageDraw, cx: int, ground: int, mood: str, speaking: bool) -> None:
  base_y = ground - 8
  top = base_y - 200
  skin = (255, 218, 185)
  pants = (55, 65, 81)
  cardigan = (96, 110, 128)
  if mood == "sad":
    cardigan = (82, 96, 118)
  elif mood == "anxious":
    cardigan = (140, 90, 90)
    pants = (75, 55, 55)
  elif mood == "emergency":
    cardigan = (160, 75, 75)

  _draw_shadow(draw, cx, base_y)
  # 腿 / 鞋
  draw.rounded_rectangle([cx - 26, base_y - 52, cx - 8, base_y - 4], radius=6, fill=pants)
  draw.rounded_rectangle([cx + 8, base_y - 52, cx + 26, base_y - 4], radius=6, fill=pants)
  draw.ellipse([cx - 30, base_y - 12, cx - 4, base_y + 2], fill=(45, 55, 70))
  draw.ellipse([cx + 4, base_y - 12, cx + 30, base_y + 2], fill=(45, 55, 70))
  # 开衫
  draw.rounded_rectangle([cx - 40, top + 68, cx + 40, base_y - 48], radius=18, fill=cardigan)
  draw.polygon([(cx - 8, top + 68), (cx + 8, top + 68), (cx, top + 88)], fill=(240, 235, 228))
  # 袖
  draw.rounded_rectangle([cx - 58, top + 78, cx - 34, top + 130], radius=10, fill=cardigan)
  draw.rounded_rectangle([cx + 34, top + 78, cx + 58, top + 125], radius=10, fill=cardigan)
  draw.ellipse([cx - 58, top + 122, cx - 44, top + 136], fill=skin)
  draw.ellipse([cx + 44, top + 118, cx + 58, top + 132], fill=skin)
  head_y = top + 18
  draw.pieslice([cx - 32, head_y - 10, cx + 32, head_y + 22], 200, 340, fill=(210, 212, 220))
  _draw_face(draw, cx, head_y, mood, skin)


def _draw_companion(draw: ImageDraw.ImageDraw, cx: int, ground: int, mood: str, speaking: bool) -> None:
  base_y = ground - 8
  top = base_y - 210
  skin = (255, 228, 200)
  scrubs = (6, 182, 212)
  scrubs_dark = (8, 145, 178)
  if mood == "happy":
    scrubs, scrubs_dark = (34, 197, 94), (22, 163, 74)
  elif mood == "emergency":
    scrubs, scrubs_dark = (239, 68, 68), (185, 28, 28)
  elif mood == "alert":
    scrubs, scrubs_dark = (251, 146, 60), (234, 88, 12)

  _draw_shadow(draw, cx, base_y)
  draw.rounded_rectangle([cx - 24, base_y - 54, cx - 6, base_y - 6], radius=6, fill=scrubs_dark)
  draw.rounded_rectangle([cx + 6, base_y - 54, cx + 24, base_y - 6], radius=6, fill=scrubs_dark)
  draw.rounded_rectangle([cx - 42, top + 72, cx + 42, base_y - 50], radius=20, fill=scrubs)
  draw.rounded_rectangle([cx - 14, top + 72, cx + 14, base_y - 90], radius=6, fill=(240, 253, 255))
  draw.rounded_rectangle([cx - 60, top + 82, cx - 36, top + 128], radius=12, fill=scrubs)
  draw.rounded_rectangle([cx + 36, top + 82, cx + 60, top + 122], radius=12, fill=scrubs)
  draw.ellipse([cx - 62, top + 120, cx - 46, top + 134], fill=skin)
  draw.ellipse([cx + 46, top + 116, cx + 62, top + 130], fill=skin)
  # 护士帽
  head_y = top + 12
  draw.polygon([(cx - 26, head_y + 8), (cx + 26, head_y + 8), (cx + 20, head_y - 8), (cx - 20, head_y - 8)], fill=(240, 249, 255))
  draw.rectangle([cx - 28, head_y + 6, cx + 28, head_y + 14], fill=(240, 249, 255))
  draw.ellipse([cx - 8, head_y - 2, cx + 8, head_y + 10], fill=(248, 113, 113))
  draw.line([(cx, head_y + 2), (cx, head_y + 8)], fill=(255, 255, 255), width=2)
  draw.line([(cx - 4, head_y + 5), (cx + 4, head_y + 5)], fill=(255, 255, 255), width=2)
  _draw_face(draw, cx, head_y + 10, "happy" if mood == "neutral" else mood, skin)
  # 听诊器弧线
  draw.arc([cx - 18, top + 88, cx + 18, top + 118], 0, 180, fill=(148, 163, 184), width=2)


def _draw_bubble_with_tail(
  base: Image.Image,
  xy: tuple[int, int],
  text: str,
  *,
  font: ImageFont.FreeTypeFont,
  fill: tuple[int, int, int],
  accent: tuple[int, int, int],
  tail_cx: int,
  max_w: int = 420,
) -> None:
  lines = _wrap_cn(text, font, max_w - 32)
  if not lines:
    return
  pad = 16
  lh = 32
  probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
  bw = min(max_w, max(probe.textbbox((0, 0), ln, font=font)[2] for ln in lines) + pad * 2)
  bh = len(lines) * lh + pad * 2
  x, y = xy
  layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
  d = ImageDraw.Draw(layer)
  d.rounded_rectangle([x, y, x + bw, y + bh], radius=16, fill=(*fill, 250), outline=(*accent, 255), width=2)
  ty = y + pad
  for ln in lines:
    d.text((x + pad, ty), ln, font=font, fill=(30, 41, 59))
    ty += lh
  tx = max(x + 24, min(tail_cx, x + bw - 24))
  d.polygon([(tx - 12, y + bh), (tx + 12, y + bh), (tx, y + bh + 18)], fill=(*fill, 250))
  d.line([(tx - 12, y + bh), (tx + 12, y + bh)], fill=(*accent, 255), width=2)
  base.alpha_composite(layer)


def render_dual_character_frame(
  title: str,
  dialogue: list[tuple[str, str, str]],
  *,
  elder_mood: str = "neutral",
  companion_mood: str = "neutral",
  active_speaker: str | None = None,
  size: tuple[int, int] = (W, H),
) -> np.ndarray:
  w, h = size
  img = _vgradient((w, h), (30, 41, 59), (15, 23, 42)).convert("RGBA")
  draw = ImageDraw.Draw(img)

  # 地面
  draw.rectangle([0, h - 72, w, h], fill=(22, 32, 52))
  draw.line([(0, h - 72), (w, h - 72)], fill=(51, 65, 85), width=2)

  header = Image.new("RGBA", (w, 56), (0, 0, 0, 0))
  hd = ImageDraw.Draw(header)
  hd.rectangle([0, 0, w, 56], fill=(30, 45, 70, 230))
  img.alpha_composite(header, (0, 0))
  draw = ImageDraw.Draw(img)
  draw.text((24, 14), title, font=_load_font(24, bold=True), fill=(186, 230, 253))

  ground = h - 76
  elder_x, comp_x = int(w * 0.24), int(w * 0.76)

  # 说话光晕
  if active_speaker:
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    tcx = elder_x if active_speaker == "elder" else comp_x
    g.ellipse([tcx - 85, ground - 215, tcx + 85, ground + 5], fill=(56, 189, 248, 40))
    img = Image.alpha_composite(img, glow)

  draw = ImageDraw.Draw(img)
  _draw_elder(draw, elder_x, ground, elder_mood, active_speaker == "elder")
  _draw_companion(draw, comp_x, ground, companion_mood, active_speaker == "companion")

  name_f = _load_font(20)
  draw.text((elder_x - 22, ground + 4), "老人", font=name_f, fill=(253, 230, 138))
  draw.text((comp_x - 22, ground + 4), "小护", font=name_f, fill=(165, 243, 252))

  last_elder = last_comp = last_stage = ""
  for kind, _, text in dialogue:
    if not text:
      continue
    if kind == "elder":
      last_elder = text
    elif kind == "companion":
      last_comp = text
    elif kind == "stage":
      last_stage = text

  stage_f = _load_font(19)
  if last_stage and not (last_elder or last_comp):
    for i, ln in enumerate(_wrap_cn(last_stage, stage_f, w - 120)):
      draw.text((w // 2 - 280, 68 + i * 28), ln, font=stage_f, fill=(148, 163, 184))

  bubble_f = _load_font(23)
  if last_elder:
    _draw_bubble_with_tail(
      img, (int(w * 0.05), 64), last_elder,
      font=bubble_f, fill=(255, 251, 235), accent=(245, 158, 11), tail_cx=elder_x,
    )
  if last_comp:
    _draw_bubble_with_tail(
      img, (int(w * 0.48), 64), last_comp,
      font=bubble_f, fill=(236, 254, 255), accent=(6, 182, 212), tail_cx=comp_x,
    )

  rgb = np.array(img.convert("RGB"))
  return rgb[:, :, ::-1].copy()
