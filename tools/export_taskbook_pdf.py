#!/usr/bin/env python3
"""将 docs/项目任务书.md 导出为 PDF（中文排版）。"""
from __future__ import annotations

import re
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "项目任务书.md"
OUT_PATH = ROOT / "docs" / "项目任务书.pdf"

FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

CSS = f"""
@page {{
  size: A4;
  margin: 22mm 18mm 24mm 18mm;
  @bottom-center {{
    content: counter(page) " / " counter(pages);
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 9pt;
    color: #666;
  }}
}}
@font-face {{
  font-family: "Noto Sans CJK SC";
  src: url("file://{FONT_REGULAR}");
  font-weight: normal;
}}
@font-face {{
  font-family: "Noto Sans CJK SC";
  src: url("file://{FONT_BOLD}");
  font-weight: bold;
}}
body {{
  font-family: "Noto Sans CJK SC", "Noto Serif CJK SC", sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: #1a1a1a;
}}
h1 {{
  font-size: 20pt;
  text-align: center;
  margin: 0 0 6mm;
  color: #0d47a1;
  border-bottom: 2pt solid #0d47a1;
  padding-bottom: 4mm;
}}
h2 {{
  font-size: 13pt;
  margin: 7mm 0 3mm;
  color: #1565c0;
  page-break-after: avoid;
}}
h3 {{
  font-size: 11pt;
  margin: 5mm 0 2mm;
  color: #1976d2;
  page-break-after: avoid;
}}
p {{ margin: 2mm 0; text-align: justify; }}
hr {{ border: none; border-top: 0.5pt solid #ccc; margin: 5mm 0; }}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 3mm 0 5mm;
  font-size: 9.5pt;
  page-break-inside: avoid;
}}
th, td {{
  border: 0.5pt solid #bbb;
  padding: 2.5mm 3mm;
  vertical-align: top;
}}
th {{
  background: #e3f2fd;
  font-weight: bold;
  text-align: left;
}}
tr:nth-child(even) td {{ background: #fafafa; }}
code {{
  font-family: "DejaVu Sans Mono", monospace;
  font-size: 9pt;
  background: #f5f5f5;
  padding: 0.5pt 2pt;
}}
pre {{
  background: #f5f5f5;
  padding: 3mm;
  font-size: 8.5pt;
  overflow-wrap: break-word;
  white-space: pre-wrap;
}}
ul {{ margin: 2mm 0 2mm 5mm; }}
li {{ margin: 1mm 0; }}
em, i {{ font-style: italic; }}
strong, b {{ font-weight: bold; }}
a {{ color: #1565c0; text-decoration: none; }}
.doc-subtitle {{
  text-align: center;
  font-size: 12pt;
  color: #424242;
  margin-bottom: 8mm;
}}
.doc-footer {{
  margin-top: 8mm;
  font-size: 9pt;
  color: #616161;
  font-style: italic;
}}
"""


def _md_to_html(md_text: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    # 首段 h1 后插入副标题样式（第二段 h2 在 md 里是 ## CareCompanion...）
    body = re.sub(
        r"(<h1>项目任务书</h1>\s*)(<h2>)",
        r'\1<div class="doc-subtitle">CareCompanion · 基于大语言模型的智能养老陪伴机器人仿真平台</div>',
        body,
        count=1,
    )
    # 去掉重复的 ## 副标题（已在 subtitle 展示）
    body = re.sub(
        r'<h2>CareCompanion · 基于大语言模型的智能养老陪伴机器人仿真平台</h2>\s*',
        "",
        body,
        count=1,
    )
    return body


def main() -> None:
    if not MD_PATH.is_file():
        raise SystemExit(f"找不到: {MD_PATH}")
    md_text = MD_PATH.read_text(encoding="utf-8")
    body = _md_to_html(md_text)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"/><style>{CSS}</style></head>
<body>{body}</body>
</html>"""
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(OUT_PATH))
    print(f"✅ 已生成: {OUT_PATH}")


if __name__ == "__main__":
    main()
