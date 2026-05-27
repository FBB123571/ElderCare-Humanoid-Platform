#!/usr/bin/env python3
"""生成国赛风格答辩 PPT：docs/答辩_CareCompanion.pptx"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "答辩_CareCompanion.pptx"
ASSETS = ROOT / "docs" / "assets"

# 国赛常见：白底 + 深蓝标题条
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(30, 30, 30)
DARK = RGBColor(20, 50, 120)
RED = RGBColor(192, 0, 0)
GRAY = RGBColor(80, 80, 80)
LIGHT_BLUE = RGBColor(235, 242, 250)

COMP_LINE1 = "第二十六届中国机器人及人工智能大赛"
COMP_LINE2 = "机器人创新赛道"


def _slide(prs: Presentation):
  return prs.slides.add_slide(prs.slide_layouts[6])


def _bg_white(slide):
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = WHITE


def _header_bar(slide):
  bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.55))
  bar.fill.solid()
  bar.fill.fore_color.rgb = DARK
  bar.line.fill.background()
  box = slide.shapes.add_textbox(Inches(0.15), Inches(0.08), Inches(9.7), Inches(0.45))
  tf = box.text_frame
  tf.clear()
  p1 = tf.paragraphs[0]
  p1.text = COMP_LINE1
  p1.font.size = Pt(11)
  p1.font.bold = True
  p1.font.color.rgb = WHITE
  p2 = tf.add_paragraph()
  p2.text = COMP_LINE2
  p2.font.size = Pt(10)
  p2.font.color.rgb = RGBColor(200, 220, 255)


def _title(slide, text: str, top=0.75, size=26, color=BLACK, center=False):
  box = slide.shapes.add_textbox(Inches(0.55), Inches(top), Inches(8.9), Inches(0.8))
  tf = box.text_frame
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
  _bg_white(slide)
  _header_bar(slide)
  _title(slide, title)
  return slide


def _screenshot_slide(prs, title: str, image_file: str, caption: str = ""):
  """插入答辩截图（置于 docs/assets/）。"""
  slide = _content_slide(prs, title)
  path = ASSETS / image_file
  if not path.exists():
    _paragraph(slide, f"[请将截图放入 docs/assets/{image_file}]", top=2.0, size=14)
    return slide
  slide.shapes.add_picture(str(path), Inches(0.32), Inches(1.12), width=Inches(9.35))
  if caption:
    box = slide.shapes.add_textbox(Inches(0.32), Inches(5.05), Inches(9.35), Inches(0.45))
    p = box.text_frame.paragraphs[0]
    p.text = caption
    p.font.size = Pt(11)
    p.font.color.rgb = GRAY
    p.alignment = PP_ALIGN.CENTER
  return slide


def _part_divider(prs, part: str, subtitle: str):
  slide = _slide(prs)
  _bg_white(slide)
  _header_bar(slide)
  _title(slide, part, top=2.0, size=32, center=True)
  _title(slide, subtitle, top=2.85, size=22, color=DARK, center=True)


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


def main():
  prs = Presentation()
  prs.slide_width = Inches(10)
  prs.slide_height = Inches(5.625)

  # ===== 封面 =====
  slide = _slide(prs)
  _bg_white(slide)
  _header_bar(slide)
  _title(slide, "CareCompanion", top=1.6, size=36, center=True, color=DARK)
  _title(
    slide,
    "智能养老人形陪伴机器人系统",
    top=2.35,
    size=22,
    center=True,
    color=BLACK,
  )
  _paragraph(
    slide,
    "第一部分\n\n「感知—决策—执行」一体化的居家养老安全陪伴平台",
    top=3.0,
    size=18,
    width=8.0,
    bold=True,
  )
  for i, t in enumerate([COMP_LINE1, COMP_LINE2]):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(4.85 + i * 0.28), Inches(8.9), Inches(0.3))
    box.text_frame.text = t
    box.text_frame.paragraphs[0].font.size = Pt(11)
    box.text_frame.paragraphs[0].font.color.rgb = GRAY
    box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

  _part_divider(prs, "第一部分", "项目背景与需求分析")

  slide = _content_slide(prs, "社会背景与痛点")
  _paragraph(
    slide,
    "随着我国老龄化程度加深，空巢与独居老人数量持续增加。跌倒已成为老年人意外伤害的首要原因之一，"
    "而「发现延迟」往往导致救援错过黄金时间。与此同时，老人对情感陪伴的需求日益增长——"
    "他们不仅需要被监测，更需要被理解、被回应。",
    top=1.35,
    size=15,
  )

  slide = _content_slide(prs, "现有方案的不足")
  _compare_block(
    slide,
    "现有产品/方案（Ø）",
    [
      "Ø 智能音箱：无视觉安全闭环，无法实体援助",
      "Ø 监控摄像头：只告警不陪伴，缺乏对话与动作",
      "Ø 健康手环：难发现跌倒过程，无机器人执行",
      "Ø 纯仿真毕设：缺少真机部署路径与量化评测",
    ],
    "CareCompanion（ü）",
    [
      "ü 多模态融合：跌倒+情绪+生理→统一风险引擎",
      "ü 可解释决策：输出风险分数与原因列表",
      "ü 主动照护：告警/语音/手势/紧急呼叫联动",
      "ü 人形接口：ROS2 标准话题，仿真与真机同源",
      "ü 开源可复现：Web 控制台 + 评测脚本 + GitHub",
    ],
  )

  slide = _content_slide(prs, "项目概述")
  _paragraph(
    slide,
    "基于上述需求，我们开发了 CareCompanion 智能养老人形陪伴机器人软件平台。"
    "平台以 CareOrchestrator 为核心，融合 MediaPipe 视觉姿态、文本情感与健康指标，"
    "在 Web 控制台完成演示验证，并通过 ROS2 适配层对接人形机器人。"
    "系统已实现跌倒紧急链路自动化验证，合成场景跌倒检测 F1 达 100%。",
    top=1.35,
    size=15,
  )

  _part_divider(prs, "第二部分", "关键技术与系统架构")

  slide = _content_slide(prs, "系统总体架构")
  _bullets(
    slide,
    [
      "感知层：FallDetector · EmotionRecognizer · HealthMonitor · PosePipeline（MediaPipe）",
      "认知层：RiskEngine（多模态融合）· DialogueManager · CarePlanner",
      "执行层：RobotAdapter → SimulationAdapter / ROS2Adapter",
      "交互层：Web 控制台 · 桌面 GUI · 无头自动化剧本",
      "状态机：MONITOR → CONVERSE → ALERT → EMERGENCY（紧急硬优先级）",
    ],
    size=14,
  )

  slide = _content_slide(prs, "多模态风险融合引擎")
  _bullets(
    slide,
    [
      "融合公式：S = 0.45·S_fall + 0.25·S_emo + 0.30·S_health",
      "输出：风险分数、等级（normal/alert/emergency）、原因列表",
      "阈值：alert ≥ 0.65，emergency ≥ 0.85 或确认跌倒",
      "优势：非黑盒 LLM，便于答辩解释与医疗合规沟通",
    ],
    size=14,
  )
  _paragraph(slide, "config/default.yaml 集中管理权重与阈值，支持场景调参。", top=4.0, size=12)

  slide = _content_slide(prs, "跌倒检测算法")
  _bullets(
    slide,
    [
      "几何特征：骨架宽高比 R=w/h、垂直速度 v_y、静止持续时间",
      "快速跌倒：快速下落 + 躺倒姿态（score ≥ 0.7）",
      "慢速跌倒：躺倒静止 ≥ 2s（养老场景常见，score ≥ 0.55）",
      "MediaPipe Pose：浏览器/摄像头实时骨架 → 自动填充感知参数",
      "评测：6 类合成场景，Precision/Recall/F1 = 100%",
    ],
    size=14,
  )

  slide = _content_slide(prs, "情感陪伴与紧急响应")
  _bullets(
    slide,
    [
      "对话：文本情感词典 + 视觉情绪标签融合；可插拔 LLM（默认离线 Mock）",
      "紧急链路：alert_sound → speak → call_emergency → raise_hand",
      "EmergencyNotifier：家属 App / 短信 / 本地告警（可审计日志）",
    ],
    top=1.35,
    size=13,
  )
  _screenshot_slide(
    prs,
    "（界面）情感倾诉交互",
    "ppt_emotion_input.png",
    "老人输入「最近有点孤独，睡不太好」→ 系统识别情绪低落并生成安抚话术",
  )

  slide = _content_slide(prs, "数据处理与决策流程")
  _bullets(
    slide,
    [
      "1. 采集感知帧：摄像头骨架 / 滑块仿真 / 可穿戴 JSON",
      "2. FallDetector 更新跌倒分数，Emotion/Health 更新标签",
      "3. RiskEngine 评估等级，状态机切换",
      "4. DialogueManager 生成回复，CarePlanner 输出 RobotAction 序列",
      "5. RobotAdapter 下发至仿真日志或 ROS2 /care/robot_cmd",
    ],
    size=14,
  )

  _part_divider(prs, "第三部分", "系统实现 · 评测 · 演示")

  slide = _content_slide(prs, "Web 控制台（CareCompanion）")
  _bullets(
    slide,
    [
      "访问地址：http://localhost:8765（bash scripts/run_web.sh）",
      "技术栈：FastAPI + 浏览器前端，支持答辩现场演示",
      "以下截图为实际运行界面（2026-05-27 答辩预演录制）",
    ],
    top=1.35,
    size=13,
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

  slide = _content_slide(prs, "实验评测结果")
  _metrics_table(
    slide,
    [
      ("跌倒检测 Precision（合成6场景）", "100%"),
      ("跌倒检测 Recall", "100%"),
      ("跌倒检测 F1", "100%"),
      ("端到端紧急呼叫触发率", "100%"),
      ("单帧决策延迟（CPU，无云端LLM）", "< 50 ms"),
      ("单元测试 + 无头压测", "pytest 全部通过"),
    ],
  )
  _paragraph(slide, "详见 data/evaluation/results/fall_eval_report.json", top=4.35, size=11)

  slide = _content_slide(prs, "开源与知识产权")
  _bullets(
    slide,
    [
      "GitHub 开源：https://github.com/FBB123571/ElderCare-Humanoid-Platform",
      "答辩演示：http://localhost:8765（现场端口转发）",
      "软件名称建议：CareCompanion 智能养老人形陪伴机器人系统 V1.0",
      "核心代码：care_companion/ · web/ · scripts/ · tests/",
      "文档：技术报告 · 架构说明 · 部署指南 · 竞赛答辩要点",
      "（请填写）软著登记号 / 团队成员 / 指导教师",
    ],
    size=14,
  )

  _part_divider(prs, "第四部分", "创新维度与未来展望")

  slide = _content_slide(prs, "创新维度总结")
  _innovation_table(
    slide,
    [
      ("多模态融合", "跌倒、情绪、健康统一 RiskEngine，输出可解释原因，优于孤立模块堆叠"),
      ("安全闭环", "紧急事件硬优先级状态机，覆盖对话与常规任务，触发 call_emergency"),
      ("视觉感知", "MediaPipe 姿态接入 Web 与本地摄像头，非纯滑块仿真"),
      ("工程化", "仿真/Web/ROS2 共用 Orchestrator；一键评测与无头验证脚本"),
      ("应用价值", "契合智慧养老政策，降低跌倒发现空窗，支持边缘本地推理保护隐私"),
    ],
  )

  slide = _content_slide(prs, "未来工作")
  _bullets(
    slide,
    [
      "p 对接 Unitree 等人形机器人，完成 speak/gesture/approach 真机视频",
      "p 引入 UR Fall 等公开数据集，开展泛化评测与误报分析",
      "p 多老人房间场景、遮挡与光照鲁棒性优化",
      "p 结合社区/养老院调研，完善产品化与成本评估",
      "p 申请软件著作权 V1.0，探索专利（跌倒融合决策方法）",
    ],
    size=14,
  )

  slide = _content_slide(prs, "参考文献")
  _bullets(
    slide,
    [
      "[1] Google MediaPipe Pose: Real-time pose estimation.",
      "[2] Unitree Robotics SDK / ROS2 documentation.",
      "[3] 国务院：《「十四五」国家老龄事业发展和养老服务体系规划》.",
      "[4] CareCompanion 项目文档：docs/TECHNICAL_REPORT.md",
      "[5] 仓库：github.com/FBB123571/ElderCare-Humanoid-Platform",
    ],
    size=12,
    top=1.35,
  )

  # 致谢
  slide = _slide(prs)
  _bg_white(slide)
  _header_bar(slide)
  box = slide.shapes.add_textbox(Inches(0.55), Inches(2.2), Inches(8.9), Inches(1.2))
  box.text_frame.text = "敬请批评指正"
  p = box.text_frame.paragraphs[0]
  p.font.size = Pt(36)
  p.font.bold = True
  p.font.color.rgb = DARK
  p.alignment = PP_ALIGN.CENTER
  sub = slide.shapes.add_textbox(Inches(0.55), Inches(3.2), Inches(8.9), Inches(0.6))
  sub.text_frame.text = "CareCompanion 团队 · 感谢各位评委老师"
  sub.text_frame.paragraphs[0].font.size = Pt(16)
  sub.text_frame.paragraphs[0].font.color.rgb = GRAY
  sub.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

  OUT.parent.mkdir(parents=True, exist_ok=True)
  prs.save(str(OUT))
  print(f"✅ 已生成国赛风格 PPT: {OUT}")
  print(f"   共 {len(prs.slides)} 页")


if __name__ == "__main__":
  main()
