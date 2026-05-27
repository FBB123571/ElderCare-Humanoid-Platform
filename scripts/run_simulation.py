#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulation.desktop_gui import main

if __name__ == "__main__":
  main(smoke_test="--smoke-test" in sys.argv)
