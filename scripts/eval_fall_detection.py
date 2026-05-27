#!/usr/bin/env python3
"""跌倒检测合成评测，输出 Precision/Recall/F1 与 JSON 报告。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from care_companion.perception.fall_detector import FallDetector


def load_scenarios(path: Path) -> list[dict]:
  data = yaml.safe_load(path.read_text(encoding="utf-8"))
  return data["scenarios"]


def eval_scenario(detector: FallDetector, scenario: dict, dt: float = 0.5) -> dict:
  label = scenario["label"]
  detected_any = False
  max_score = 0.0
  for frame in scenario["frames"]:
    r = detector.from_metrics(frame["aspect"], frame["dy"], dt)
    max_score = max(max_score, r.score)
    if r.detected:
      detected_any = True
  pred = "fall" if detected_any else "normal"
  return {
    "name": scenario["name"],
    "label": label,
    "pred": pred,
    "detected": detected_any,
    "max_score": max_score,
  }


def metrics(rows: list[dict]) -> dict:
  # fall 为正类
  tp = fp = fn = tn = 0
  for r in rows:
    gt_fall = r["label"] == "fall"
    pr_fall = r["pred"] == "fall"
    if gt_fall and pr_fall:
      tp += 1
    elif not gt_fall and pr_fall:
      fp += 1
    elif gt_fall and not pr_fall:
      fn += 1
    else:
      tn += 1
  prec = tp / (tp + fp) if (tp + fp) else 0.0
  rec = tp / (tp + fn) if (tp + fn) else 0.0
  f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
  acc = (tp + tn) / len(rows) if rows else 0.0
  return {
    "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    "precision": round(prec, 4),
    "recall": round(rec, 4),
    "f1": round(f1, 4),
    "accuracy": round(acc, 4),
    "n_scenarios": len(rows),
  }


def main():
  cfg_path = ROOT / "config" / "default.yaml"
  fall_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")).get("fall", {})
  scenarios = load_scenarios(ROOT / "data" / "evaluation" / "fall_scenarios.yaml")

  rows = []
  for sc in scenarios:
    det = FallDetector(fall_cfg)
    rows.append(eval_scenario(det, sc))

  m = metrics(rows)
  out_dir = ROOT / "data" / "evaluation" / "results"
  out_dir.mkdir(parents=True, exist_ok=True)
  report = {"metrics": m, "details": rows}
  out_path = out_dir / "fall_eval_report.json"
  out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

  print("CareCompanion 跌倒检测评测（合成场景）")
  print(f"  场景数: {m['n_scenarios']}")
  print(f"  Precision: {m['precision']:.2%}")
  print(f"  Recall:    {m['recall']:.2%}")
  print(f"  F1:        {m['f1']:.2%}")
  print(f"  Accuracy:  {m['accuracy']:.2%}")
  print(f"  报告: {out_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
