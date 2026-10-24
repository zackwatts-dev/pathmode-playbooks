"""Record a real model on one of estimate check's held-back years, the way tools/record.py records the sample. The
thresholds in release-thresholds.json were set, and the code frozen, before each year's bids were generated.

    python tools/record_holdout_estimates.py [holdout-2025] [--keep] [--parallel N] [--to recorded-run.json]

Through the claude command line (Claude Sonnet 5.5). --keep reuses answers already recorded in that folder for
exactly the same inputs; --to names the file written, so a development run on a year already scored doesn't
overwrite the recording behind its published score.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "estimate-check")]

import estimate_check as A  # noqa: E402
import record  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("year", nargs="?", default="holdout-2025", help="the held-back folder in estimate-check/")
    p.add_argument("--keep", action="store_true", help="reuse answers recorded in that folder for the same inputs")
    p.add_argument("--parallel", type=int, default=0, metavar="N", help="ask N calls at a time")
    p.add_argument("--to", default="recorded-run.json", help="the file to write in that folder")
    args = p.parse_args()
    folder = ROOT / "estimate-check" / args.year
    inner = record.ClaudeCLI()
    keep = {}
    if args.keep:
        for f in sorted(folder.glob("recorded-run*.json")):
            keep |= json.loads(f.read_text())["answers"]
    model = record.Recording(inner, A.replay_key, keep)
    if args.parallel:
        record.prefetch(A, model, args.parallel, run=lambda m, out: A.run(folder, m, key=folder / "answer-key"))
    A.run(folder, model, key=folder / "answer-key")
    data = {
        "model": inner.name,
        "recorded": date.today().isoformat(),
        "calls": model.calls,
        "reused_from_earlier_recording": model.reused,
        "failed_calls": len(model.failed),
        "answers": dict(sorted(model.answers.items())),
    }
    (folder / args.to).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"Recorded {len(model.answers)} answers ({model.calls} new calls) to {folder.name}/{args.to}.")


if __name__ == "__main__":
    main()
