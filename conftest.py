"""Lets tests import each playbook's module, and the shared `common` package, by name."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
for folder in sorted(ROOT.iterdir()):
    if folder.is_dir() and (folder / "tests").is_dir():
        sys.path.insert(0, str(folder))
