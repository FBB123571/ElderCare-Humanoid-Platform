#!/usr/bin/env python3
"""生成答辩 PPT：docs/答辩_CareCompanion.pptx"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "答辩_CareCompanion.pptx"

BG = RGBColor(15, 23, 42)
ACCENT = RGBColor(56, 189, 248)
WHITE = RGBColor(240, 244, 252)
MUTED = RGBColor(148, 163, 184)


def _style_title(shape, size=32, bold=True):
  tf = shape.text_frame
  p = tf.paragraphs[0]
  p.font.size = Pt(size)
  p.font.bold = bold
  p.font.color.rgb = WHITE
  p.alignment = PP_ALIGN.LEFT


def _add_bullets(slide, items: list[str], left=0.8, top=1.8, width=8.5, height=4.5):
  box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
  tf = box.text_frame
  tf.word_wrap = True
  for i, line in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line
    p.level = 0
    p.font.size = Pt(18)
    p.font.color.rgb = WHITE
    p.space_after = Pt(10)


def _slide_title(prs: Presentation, title: str, subtitle: str = ""):
  slide = prs.slides.add_slide(prs.slide_layouts[6])
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = BG
  t = slide.shapes.add_textbox(Inches(0.6), Inches(0.5), Inches(9), Inches(1.2))
  t.text_frame.text = title
  _style_title(t, 30)
  if subtitle:
    s = slide.shapes.add_textbox(Inches(0.6), Inches(1.35), Inches(9), Inches(0.8))
    s.text_frame.text = subtitle
    s.text_frame.paragraphs[0].font.size = Pt(16)
    s.text_frame.paragraphs[0].font.color.rgb = MUTED
  return slide


def main():
  prs = Presentation()
  prs.slide_width = Inches(10)
  prs.slide_height = Inches(7.5)

  # 1 封面
  slide = prs.slides.add_slide(prs.slide_layouts[6])
  slide.background.fill.solid()
  slide.background.fill.fore_color.rgb = BG
  t = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(8.5), Inches(1.5))
  t.text_frame.text = "CareCompanion"
  _style_title(t, 44)
  sub = slide.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(8.5), Inches(1.2))
  sub.text_frame.text = "智能养老人形陪伴机器人系统"
  sub.text_frame.paragraphs[0].font.size = Pt(24)
  sub.text_frame.paragraphs[0].font.color.rgb = ACCENT
  foot = slide.shapes.add_textbox(Inches(0.8), Inches(5.2), Inches(8.5), Inches(1))
  foot.text_frame.text = "中国机器人及人工智能大赛 · 机器人创新赛道\n多模态感知 · 风险决策 · 人形机器人部署"
  foot.text_frame.paragraphs[0].font.size = Pt(14)
  foot.text_frame.paragraphs[0].font.color.rgb = MUTED

  # 2 痛点
  slide = _slide_title(prs, "1. 背景与痛点", "Population Aging & Home Care")
  _add_bullets(slide, [
    "我国老龄化加速，空巢/独居老人安全与情感需求突出",
    "跌倒为老年人意外伤害首要原因之一，发现滞后后果严重",
    "传统智能音箱：缺乏视觉安全闭环，无法实体援助",
    "单一健康手环：缺乏对话陪伴与主动干预",
    "→ 需要「感知 + 决策 + 人形执行」一体化陪伴系统",
  ])

  # 3 创新点
  slide = _slide_title(prs, "2. 创新点", "Innovation")
  _add_bullets(slide, [
    "多模态风险融合引擎：跌倒 + 情绪 + 生理指标 → 可解释评分",
    "硬优先级状态机：紧急事件覆盖对话与常规任务",
    "主动式照护规划：不仅聊天，还执行告警/靠近/呼救",
    "仿真与真机统一接口：SimulationAdapter / ROS2Adapter",
    "边缘优先：视觉本地 MediaPipe，对话可离线 Mock",
  ])

  # 4 架构
  slide = _slide_title(prs, "3. 系统架构", "Architecture")
  _add_bullets(slide, [
    "感知层：FallDetector · EmotionRecognizer · HealthMonitor · PosePipeline",
    "认知层：RiskEngine · DialogueManager · CarePlanner",
    "执行层：RobotAdapter → 仿真 / ROS2 / 人形 SDK",
    "交互层：Web 控制台 + 桌面仿真 + 无头压测",
    "核心：CareOrchestrator 统一 tick 循环",
  ])

  # 5 跌倒算法
  slide = _slide_title(prs, "4. 跌倒检测算法", "Fall Detection")
  _add_bullets(slide, [
    "几何特征：骨架宽高比 + 垂直速度 + 静止持续时间",
    "MediaPipe Pose：浏览器/摄像头实时骨架提取",
    "快速跌倒：下落 + 躺倒（score ≥ 0.7）",
    "慢速跌倒：躺倒静止 ≥2s（养老场景）",
    "合成场景评测：Precision/Recall/F1 = 100%",
  ])

  # 6 风险引擎
  slide = _slide_title(prs, "5. 风险融合与决策", "Risk Engine")
  _add_bullets(slide, [
    "加权融合：跌倒 45% · 情绪 25% · 健康 30%",
    "三级输出：normal / alert / emergency + 原因列表",
    "状态机：MONITOR → CONVERSE → ALERT → EMERGENCY",
    "紧急时：告警音 + 语音 + call_emergency + 手势",
    "紧急通知：家属 App / 短信备份 / 本地告警（可扩展）",
  ])

  # 7 对话
  slide = _slide_title(prs, "6. 情感陪伴与对话", "Dialogue")
  _add_bullets(slide, [
    "文本情感词典 + 视觉情绪标签融合",
    "可插拔 LLM：默认 Mock 离线，支持 OpenAI 兼容 API",
    "场景示例：「有点孤独」→ 温暖安抚 + 挥手",
    "用药/问候等关键词触发专属回复",
    "与风险等级联动，紧急时优先安全话术",
  ])

  # 8 Web演示
  slide = _slide_title(prs, "7. Web 控制台演示", "Demo")
  _add_bullets(slide, [
    "浏览器访问：感知调节 + 实时风险仪表盘",
    "摄像头：MediaPipe 骨架叠加 + 自动填充姿态参数",
    "一键剧本：日常监测 → 倾诉 → 跌倒 → 紧急",
    "对话日志 + 机器人指令流可视化",
    "部署：bash scripts/run_web.sh · 端口 8765",
  ])

  # 9 评测
  slide = _slide_title(prs, "8. 实验与评测", "Evaluation")
  _add_bullets(slide, [
    "跌倒检测：6 类合成场景，F1=100%（见 docs/evaluation/METRICS.md）",
    "端到端：run_headless_demo 100% 触发紧急呼叫",
    "单元测试：pytest 覆盖决策与紧急链路",
    "单 tick 延迟 <50ms（无云端 LLM）",
    "待补充：公开数据集 + 真机视频",
  ])

  # 10 部署
  slide = _slide_title(prs, "9. 人形机器人部署", "Deployment")
  _add_bullets(slide, [
    "边缘 NUC/Jetson 运行 care_companion",
    "ROS2 发布 /care/robot_cmd JSON 指令",
    "机器人端订阅 → Unitree / 智元 SDK 映射",
    "指令：speak · gesture · approach · call_emergency",
    "与 Isaac Lab 仿真可对接扩展",
  ])

  # 11 对比
  slide = _slide_title(prs, "10. 与现有方案对比", "Comparison")
  _add_bullets(slide, [
    "vs 智能音箱：多模态安全 + 实体动作 + 紧急硬优先级",
    "vs 纯监控摄像头：主动对话 + 机器人执行 + 可解释决策",
    "vs 纯仿真毕设：ROS2 真机路径 + 评测脚本 + 开源仓库",
    "应用：社区养老、居家陪护、康复中心预研",
  ])

  # 12 社会价值
  slide = _slide_title(prs, "11. 社会价值与应用前景", "Impact")
  _add_bullets(slide, [
    "契合智慧养老、适老化改造政策方向",
    "降低跌倒「发现空窗期」，提升救援效率",
    "情感陪伴缓解孤独，辅助用药与活动提醒",
    "模块化部署，可按需启用视觉/LLM/真机",
    "已开源：https://github.com/FBB123571/ElderCare-Humanoid-Platform",
  ])

  # 13 总结
  slide = _slide_title(prs, "12. 总结与展望", "Conclusion")
  _add_bullets(slide, [
    "完成：多模态决策核心 + Web 可视化 + MediaPipe 视觉 + 评测体系",
    "创新：可解释风险融合 + 紧急闭环 + 人形接口",
    "展望：真机联调 · 公开数据集 · 多老人交互 · 联邦隐私",
    "感谢各位评委老师！",
  ])

  # 14 Q&A
  slide = _slide_title(prs, "Q & A", "欢迎提问")
  _add_bullets(slide, [
    "演示：Web 控制台 live demo",
    "代码：GitHub 开源可复现",
    "联系方式：（请填写团队信息）",
  ], top=2.5)

  OUT.parent.mkdir(parents=True, exist_ok=True)
  prs.save(str(OUT))
  print(f"✅ 已生成: {OUT}")


if __name__ == "__main__":
  main()
