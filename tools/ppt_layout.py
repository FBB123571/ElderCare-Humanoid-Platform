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
CAPTION_H = 0.22

# 右栏配图区（严格不越过 COL_L 分界线）
FIG_PAD_X = 0.10
FIG_PAD_Y = 0.06
FIG_LEFT = COL_R + FIG_PAD_X
FIG_WIDTH = COL_R_W - 2 * FIG_PAD_X
FIG_TOP = CONTENT_TOP + FIG_PAD_Y
FIG_CAP_H = 0.24
# 图体 + 图注均在 CONTENT 内（图注固定底部，不与图重叠）
FIG_TOTAL_H = CONTENT_H - 2 * FIG_PAD_Y
FIG_BODY_H = FIG_TOTAL_H - FIG_CAP_H - 0.06


def body_height(*, with_ribbon: bool = False) -> float:
  if with_ribbon:
    return CONTENT_H - RIBBON_H - RIBBON_GAP
  return CONTENT_H


def ribbon_top(*, with_ribbon: bool = True) -> float:
  return CONTENT_TOP + body_height(with_ribbon=with_ribbon) + RIBBON_GAP
