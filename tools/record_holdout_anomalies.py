"""Record a real model on anomaly alerts' held-back year (holdout-2025/), the way tools/record.py records the
sample. The thresholds in release-thresholds.json were set, and the code frozen, before this year was generated.

    python tools/record_holdout_anomalies.py [--keep]     # through the claude command line (Claude Sonnet 5.5)
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "anomaly-alerts")]

import anomaly_alerts as A  # noqa: E402
import record  # noqa: E402


def main() -> None:
    folder = ROOT / "anomaly-alerts" / "holdout-2025"
    inner = record.ClaudeCLI()
    path = folder / "recorded-run.json"
    keep = json.loads(path.read_text())["answers"] if "--keep" in sys.argv and path.exists() else {}
    model = record.Recording(inner, A.replay_key, keep)
    A.run(folder, model, key=folder / "answer-key")
    data = {
        "model": inner.name,
        "recorded": date.today().isoformat(),
        "calls": model.calls,
        "reused_from_earlier_recording": model.reused,
        "failed_calls": len(model.failed),
        "answers": dict(sorted(model.answers.items())),
    }
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"Recorded {len(model.answers)} answers to {folder.name}/recorded-run.json.")


if __name__ == "__main__":
    main()
