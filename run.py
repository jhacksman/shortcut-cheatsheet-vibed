#!/usr/bin/env python3
"""Run the Shortcut Cheatsheet application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from shortcut_cheatsheet.main import main

if __name__ == "__main__":
    sys.exit(main())
