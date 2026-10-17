"""Weekly report: code computes every number; the model only writes the paragraph about them.

    python weekly-report/weekly_report.py --sample --dry-run
    python weekly-report/weekly_report.py --jobs jobs.csv --week-ending 2026-07-12

Reads one row per job (Date, Branch, Type, Revenue, Completed, Callback, Hours: rename your export's
columns, or change COLUMNS below). It works out this week, last week and the four-week average, by branch.
The model gets those numbers and writes a short summary for the owner. Then code checks every number in
the summary against the computed ones. If the model made one up or got one wrong, the summary is marked
and the table, which is always right, comes first.

Writes out/report.md and out/metrics.json. Nothing is sent.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.evidence import unsupported_numbers  # noqa: E402
from common.util import done, model_for, parser, read_csv, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"
SAMPLE_WEEK_ENDING = date(2026, 7, 12)
COLUMNS = {
    "date": "Date",
    "branch": "Branch",
    "type": "Type",
    "revenue": "Revenue",
    "completed": "Completed",
    "callback": "Callback",
    "hours": "Hours",
}

NARRATE = """You write the short weekly summary an owner of a small business reads on Monday morning.
You get this week's numbers, already calculated. Write 3 to 5 plain sentences: what changed, what stands out,
and one thing worth asking about. Use only the numbers given, written exactly as given (you may round a
percentage to a whole number). Don't calculate anything new. Don't explain causes the numbers don't show;
you can say what's worth checking. No headings, no bullet points."""


@dataclass
class Week:
    revenue: float
    jobs: int
    completed: int
    callbacks: int
    hours: float

    @property
    def per_job(self) -> float:
        return round(self.revenue / self.completed, 2) if self.completed else 0.0

    @property
    def callback_rate(self) -> float:
        return round(100 * self.callbacks / self.completed, 1) if self.completed else 0.0


def week_of(rows: list[dict], end: date, branch: str | None = None) -> Week:
    start = end - timedelta(days=6)
    sel = [
        r
        for r in rows
        if start <= date.fromisoformat(r[COLUMNS["date"]]) <= end and (branch is None or r[COLUMNS["branch"]] == branch)
    ]
    done_ = [r for r in sel if r[COLUMNS["completed"]].lower() in ("yes", "y", "true", "1")]
    return Week(
        revenue=round(sum(float(r[COLUMNS["revenue"]] or 0) for r in sel), 2),
        jobs=len(sel),
        completed=len(done_),
        callbacks=sum(1 for r in done_ if r[COLUMNS["callback"]].lower() in ("yes", "y", "true", "1")),
        hours=round(sum(float(r[COLUMNS["hours"]] or 0) for r in sel), 1),
    )


def pct(new: float, old: float) -> float | None:
    return round(100 * (new - old) / old, 1) if old else None


def compute(rows: list[dict], end: date) -> dict:
    this, last = week_of(rows, end), week_of(rows, end - timedelta(days=7))
    prior = [week_of(rows, end - timedelta(days=7 * i)) for i in range(1, 5)]
    avg_rev = round(sum(w.revenue for w in prior) / 4, 2)
    avg_jobs = round(sum(w.completed for w in prior) / 4, 1)
    branches = sorted({r[COLUMNS["branch"]] for r in rows})
    by_branch = {}
    for b in branches:
        t, lw = week_of(rows, end, b), week_of(rows, end - timedelta(days=7), b)
        by_branch[b] = {
            "revenue": t.revenue,
            "revenue_last_week": lw.revenue,
            "revenue_change_pct": pct(t.revenue, lw.revenue),
            "completed": t.completed,
            "callback_rate_pct": t.callback_rate,
        }
    return {
        "week": f"{end - timedelta(days=6):%B %-d} to {end:%B %-d, %Y}",
        "revenue": this.revenue,
        "revenue_last_week": last.revenue,
        "revenue_change_pct": pct(this.revenue, last.revenue),
        "revenue_4wk_avg": avg_rev,
        "revenue_vs_4wk_avg_pct": pct(this.revenue, avg_rev),
        "jobs_completed": this.completed,
        "jobs_completed_last_week": last.completed,
        "jobs_completed_4wk_avg": avg_jobs,
        "jobs_not_completed": this.jobs - this.completed,
        "revenue_per_job": this.per_job,
        "revenue_per_job_last_week": last.per_job,
        "callback_rate_pct": this.callback_rate,
        "callback_rate_last_week_pct": last.callback_rate,
        "hours": this.hours,
        "by_branch": by_branch,
    }


def all_values(metrics: dict) -> list[float]:
    out = []
    for v in metrics.values():
        if isinstance(v, dict):
            out += all_values(v)
        elif isinstance(v, (int, float)) and v is not None:
            out += [float(v), float(round(v)), abs(float(v)), float(abs(round(v)))]
    return out


def money(x: float) -> str:
    return f"${x:,.0f}"


def table(m: dict) -> str:
    def change(v):
        return "n/a" if v is None else f"{v:+.1f}%"

    lines = [
        "| | This week | Last week | Change |",
        "|---|---:|---:|---:|",
        f"| Revenue | {money(m['revenue'])} | {money(m['revenue_last_week'])} | {change(m['revenue_change_pct'])} |",
        f"| Jobs completed | {m['jobs_completed']} | {m['jobs_completed_last_week']} | |",
        f"| Revenue per job | {money(m['revenue_per_job'])} | {money(m['revenue_per_job_last_week'])} | |",
        f"| Callback rate | {m['callback_rate_pct']}% | {m['callback_rate_last_week_pct']}% | |",
        "",
        f"Four-week average revenue: {money(m['revenue_4wk_avg'])} (this week "
        f"{change(m['revenue_vs_4wk_avg_pct'])}). Jobs not completed this week: {m['jobs_not_completed']}.",
        "",
        "| Branch | Revenue | Last week | Change | Jobs completed | Callback rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for b, v in m["by_branch"].items():
        lines.append(
            f"| {b} | {money(v['revenue'])} | {money(v['revenue_last_week'])} | "
            f"{change(v['revenue_change_pct'])} | {v['completed']} | {v['callback_rate_pct']}% |"
        )
    return "\n".join(lines)


def report(m: dict, narrative: str, model_name: str) -> tuple[str, list[str]]:
    bad = unsupported_numbers(narrative, all_values(m), tolerance=0.01, ignore_small=0)
    lines = [f"# Weekly report: {m['week']}", ""]
    if bad:
        lines += [
            f"> **Check the summary:** it has numbers that don't match the data ({', '.join(bad)}). "
            "The tables below are calculated directly from your records.",
            "",
            table(m),
            "",
            "## Summary (unchecked)",
            "",
            narrative,
        ]
    else:
        lines += [narrative, "", table(m)]
    lines += [
        "",
        f"*Numbers calculated from your records. Summary written by {model_name}, and every number in it "
        "checked against the data.*"
        if not bad
        else f"*Summary written by {model_name}.*",
    ]
    return "\n".join(lines) + "\n", bad


def offline(system: str, user: str) -> str:
    m = json.loads(user.split("<<<METRICS", 1)[1].split("METRICS>>>")[0])
    branches = sorted(m["by_branch"].items(), key=lambda kv: kv[1]["revenue_change_pct"] or 0)
    low, worst_cb = branches[0], max(m["by_branch"].items(), key=lambda kv: kv[1]["callback_rate_pct"])
    return (
        f"Revenue was {money(m['revenue'])}, {m['revenue_change_pct']}% against last week's "
        f"{money(m['revenue_last_week'])}, with {m['jobs_completed']} jobs completed. "
        f"{low[0]} changed most, at {low[1]['revenue_change_pct']}%. "
        f"The highest callback rate was {worst_cb[0]} at {worst_cb[1]['callback_rate_pct']}%, worth a look."
    )


def run(rows: list[dict], end: date, model, out: Path) -> tuple[str, list[str], list[Path]]:
    m = compute(rows, end)
    narrative = model.complete(NARRATE, f"<<<METRICS\n{json.dumps(m, indent=1)}\nMETRICS>>>").strip()
    text, bad = report(m, narrative, model.name)
    return text, bad, [write_text(out / "report.md", text), write_text(out / "metrics.json", json.dumps(m, indent=2))]


def main() -> None:
    p = parser("Write the weekly numbers report: code does the math, the model writes the summary.", SAMPLE)
    p.add_argument("--jobs", type=Path, help="one row per job, CSV")
    p.add_argument("--week-ending", type=date.fromisoformat, help="last day of the week (default: last Sunday)")
    args = p.parse_args()
    if args.sample:
        path, end = SAMPLE / "jobs.csv", args.week_ending or SAMPLE_WEEK_ENDING
    elif args.jobs:
        today = date.today()
        path, end = args.jobs, args.week_ending or today - timedelta(days=(today.weekday() + 1) % 7 or 7)
    else:
        p.error("choose --sample or --jobs")
    model = model_for(args, offline)
    _, bad, written = run(read_csv(path), end, model, args.out)
    done(
        model,
        written,
        "Every number in the summary checks out."
        if not bad
        else f"The summary has numbers that don't match ({', '.join(bad)}): it's marked in the report.",
    )


if __name__ == "__main__":
    main()
