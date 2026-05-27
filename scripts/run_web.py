#!/usr/bin/env python3
"""启动 CareCompanion Web 控制台。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
  port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
  print(f"\n🌐 CareCompanion Web: http://127.0.0.1:{port}")
  print("   Cursor Remote SSH 请在「端口」面板转发 8765，浏览器打开 http://localhost:8765\n")
  uvicorn.run("web.server:app", host="0.0.0.0", port=port, reload=False)
