"""答辩 PPT 统一版式网格（英寸）。"""
from __future__ import annotations

SLIDE_W = 10.0
SLIDE_H = 5.625
HEADER_H = 0.46
FOOTER_H = 0.26

MARGIN = 0.30
GUTTER = 0.20

TITLE_TOP = HEADER_H + 0.05
TITLE_H = 0.50

CONTENT_TOP = TITLE_TOP + TITLE_H + 0.08
CONTENT_BOTTOM = SLIDE_H - FOOTER_H - 0.06
CONTENT_H = CONTENT_BOTTOM - CONTENT_TOP

# 左文右图：约 41% / 59%
COL_L = MARGIN
COL_L_W = 3.95
COL_R = COL_L + COL_L_W + GUTTER
COL_R_W = SLIDE_W - COL_R - MARGIN

RIBBON_H = 0.34
RIBBON_GAP = 0.10

IMG_PAD = 0.06
CAPTION_H = 0.20


def body_height(*, with_ribbon: bool = False) -> float:
  if with_ribbon:
    return CONTENT_H - RIBBON_H - RIBBON_GAP
  return CONTENT_H


def ribbon_top(*, with_ribbon: bool = True) -> float:
  return CONTENT_TOP + body_height(with_ribbon=with_ribbon) + RIBBON_GAP
