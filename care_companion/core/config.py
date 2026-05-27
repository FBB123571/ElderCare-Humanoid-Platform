from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = _ROOT / "config" / "default.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
  cfg_path = Path(path) if path else _DEFAULT
  with open(cfg_path, encoding="utf-8") as f:
    return yaml.safe_load(f)
