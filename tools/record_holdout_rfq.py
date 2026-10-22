"""Record a real model on RFQ intake's held-back months (holdout-2024-06/, holdout-2024-07/), the way tools/record.py
records the sample. The thresholds in release-thresholds.json were set before these months were first run.

    python tools/record_holdout_rfq.py 2024-06 [--keep]     # through the claude command line (Claude Sonnet 5.5)
"""

from __future__ import annotations

import calendar
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "rfq-intake")]

import record  # noqa: E402
import rfq_intake as ri  # noqa: E402


def month_run(folder: Path, model, out: Path):
    """A held-back month, scored against its own answer key, as of its last day (as the sample is)."""
    records = ri.Records.load(folder / "records")
    mails = ri.read_mailbox(folder / "mailbox")
    first = min(m.received_at for m in mails if m.received_at).date()
    as_of = first.replace(day=calendar.monthrange(first.year, first.month)[1])  # the month's last day, like May 31
    return ri.run(
        mails, records, model, out, as_of, plan_from=ri.sample_plan_from(records), answer_key=folder / "answer-key.csv"
    )


def main() -> None:
    month = sys.argv[1]
    folder = ROOT / "rfq-intake" / f"holdout-{month}"
    inner = record.ClaudeCLI()
    path = folder / "recorded-run.json"
    keep = json.loads(path.read_text())["answers"] if "--keep" in sys.argv and path.exists() else {}
    model = record.Recording(inner, ri.replay_key, keep)
    with tempfile.TemporaryDirectory() as out:
        month_run(folder, model, Path(out))
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
