"""Record a real model on the supplier-agreements held-back year (holdout-2024/), the way tools/record.py records
the sample. The thresholds in release-thresholds.json were set before this was first run.

    python tools/record_holdout_agreements.py          # through the claude command line (Claude Sonnet 5.5)
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "supplier-agreements")]

import record  # noqa: E402
import supplier_agreements as sa  # noqa: E402

HOLDOUT = ROOT / "supplier-agreements" / "holdout-2024"


def main() -> None:
    inner = record.ClaudeCLI()
    path = HOLDOUT / "recorded-run.json"
    keep = json.loads(path.read_text())["answers"] if "--keep" in sys.argv and path.exists() else {}
    model = record.Recording(inner, sa.replay_key, keep)
    with tempfile.TemporaryDirectory() as out:
        sa.run(HOLDOUT, model, Path(out), HOLDOUT / "answer-key" / "entitlements-key.csv")
    data = {"model": inner.name, "recorded": date.today().isoformat(), "answers": dict(sorted(model.answers.items()))}
    (HOLDOUT / "recorded-run.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"Recorded {len(model.answers)} answers to {HOLDOUT.name}/recorded-run.json.")
    if model.failed:
        print(f"{len(model.failed)} calls failed: {', '.join(model.failed)}. Run it again.")


if __name__ == "__main__":
    main()
