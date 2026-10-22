"""Queue replay: a model of Wendlow's quoting queue, to measure what reading every request on arrival is worth.

    python rfq-intake/replay_queue.py                      # the sample window: writes out/replay/
    python rfq-intake/replay_queue.py --data DIR --out DIR # another window (a folder with rfqs.csv, capacity.csv)

About 3 in 10 of Wendlow's new requests arrive missing something it needs to price them: a revision, a quantity or
the drawing. Today nobody reads a request until an estimator opens it to price it, so that's when the gap is found
and the question goes to the buyer, and the request waits for the answer. In a busy week that's days after it
arrived, and the buyer decides before the quote is ready.

The model replays every request the estimators had to price in a window (new-part requests and annual re-quotes,
with the queue as it stood on its first morning), day by day, three ways. In all three, new requests are priced
first, in the order they came, and the annual re-quotes when no new request is waiting, as Wendlow already does.

today     what Wendlow did. A request missing something is found when it reaches the front; the question goes out
          that day (a quarter hour of the estimator's time), and the request goes back to the front when the buyer
          answers.
ask       every request read the day it arrives, and the question for any that's missing something sent that day,
          so the answer comes back while the request waits its turn.
intake    AI intake: ask, and nobody retypes the lines either (a labeled estimate of the minutes saved).

The model of the work, the same in all three: each request's quoting time is `expected_quote_hours` (the simulation's
deterministic part) x one calibration factor x 1.3 for weld-family work a junior prices (with the senior in, he
prices about 3 in 4 of it) x a draw of the simulation's own noise, over 20 seeds. Each day has the estimators' hours
from capacity.csv, plus two helpers at three hours each on a day the backlog is over two weeks; occasional customers'
new requests are declined past three weeks. The buyer takes the same `answer_days` to answer whenever the question
is asked.

The calibration factor is fitted on `today` alone, so the model of the status quo gets as many quotes out on time as
really did (within 2%); every other way of working runs with the same factor.

A quote is on time if it's sent on or before the buyer's decision date (`decision_date`, from the simulation's truth;
nobody at Wendlow could see it). Only scoring reads it. The value is the extra on-time quotes x the win rate of
on-time new-part quotes in the window's records x first-year revenue per win x margin.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rfq_intake import JUNIOR_WELD, working_days_after  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "sample-data" / "queue-replay"

POLICIES = ("today", "ask", "intake")
NAMES = {
    "today": "Today: questions asked when a request is opened",
    "ask": "Every request read on arrival, questions asked the same day",
    "intake": "AI intake: read on arrival, questions the same day, no retyping",
}
HELPERS, HELPER_HOURS = 2, 3.0  # the sales manager and an engineer, past two weeks of backlog
HELP_WEEKS, TRIAGE_WEEKS = 2, 3
STANDARD_DAY = 10.5  # backlog weeks are counted against the two-estimator standard, whatever the staffing
UNSTARTED = 1.5  # hours a request not yet started counts for in the backlog (the simulation's rule)
SENIOR_WELD_SHARE = 0.75
QUESTION_HOURS = 0.25  # an estimator's time to spot the gap and write the question, today
EXTEND = 120  # at most this many extra working days after capacity.csv ends, at its last day's hours
SEEDS = 20

# Value parameters: labeled, not results.
TYPING_MINUTES = 10  # estimator minutes saved per new request by not retyping its lines: an estimate
REVENUE_PER_WIN = 34_000  # first-year revenue per won new-part quote: Wendlow's records, won new-part quotes 2022-23
MARGIN = 0.27  # the middle of the published 22-31% range for job shops (Wendlow's own books run higher)


@dataclass(frozen=True)
class Request:
    """What the shop could know about a request when it arrived. No decision date, no outcome."""

    id: str
    kind: str  # "new" or "requote"
    tier: str
    received: date
    lines: int
    weld: bool
    expected_hours: float
    missing: str = ""  # what it arrived without: revision, quantity or drawing
    answer_days: int = 0  # working days the buyer takes to answer the question
    at_start: bool = False
    draw: float = 1.0
    pick: float = 1.0

    @property
    def requote(self) -> bool:
        return self.kind == "requote"


@dataclass(frozen=True)
class Day:
    date: date
    hours: float
    senior: bool = False
    junior: bool = True


@dataclass(frozen=True)
class Truth:
    decision: date | None
    outcome: str
    sent: date | None


@dataclass
class Outcome:
    sent: dict[str, date | None]
    declined: list[str] = field(default_factory=list)
    asked: dict[str, date] = field(default_factory=dict)  # the day each question went to the buyer
    helper_days: int = 0
    requote_sent: dict[str, date] = field(default_factory=dict)


def load(folder: Path) -> tuple[list[Request], dict[str, Truth], list[Day]]:
    requests, truth = [], {}
    with (folder / "rfqs.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["outcome"] == "screened out":
                continue
            requests.append(
                Request(
                    row["rfq_id"],
                    row["kind"],
                    row["tier"],
                    date.fromisoformat(row["received_on"]),
                    int(row["lines"]),
                    row["weld_family"] == "1",
                    float(row["expected_quote_hours"]),
                    row.get("missing") or "",
                    int(row.get("answer_days") or 0),
                    row["in_queue_on_start"] == "1",
                )
            )
            truth[row["rfq_id"]] = Truth(
                date.fromisoformat(row["decision_date"]) if row["decision_date"] else None,
                row["outcome"],
                date.fromisoformat(row["quote_sent_on"]) if row["quote_sent_on"] else None,
            )
    capacity = []
    with (folder / "capacity.csv").open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            who = [w for w in r["who"].split(";") if w.strip()]
            capacity.append(
                Day(
                    date.fromisoformat(r["date"]),
                    float(r["estimator_hours"]),
                    any("(senior)" in w for w in who),
                    any("(junior)" in w for w in who),
                )
            )
    return sorted(requests, key=lambda r: (r.received, r.id)), truth, capacity


def all_rows(folder: Path, name: str = "rfqs.csv") -> list[dict]:
    with (folder / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def drawn(requests: list[Request], seed: int) -> list[Request]:
    """Each request's noise and complexity, drawn the way the simulation draws them, and who prices it. Seeded, so
    every way of working gets the same draws."""
    out = []
    for r in requests:
        g = random.Random(f"{seed}:{r.id}")
        f = g.lognormvariate(0, 0.5) * math.sqrt(max(g.lognormvariate(0, 0.35) for _ in range(r.lines)))
        out.append(replace(r, draw=f, pick=g.random()))
    return out


def work_hours(r: Request, scale: float, saving: float = 0.0, junior: bool = True) -> float:
    hours = r.expected_hours * scale * (JUNIOR_WELD if r.weld and junior else 1.0) * r.draw
    return max(hours - (0.0 if r.requote else saving), 0.0)


def days(capacity: list[Day]):
    yield from capacity
    last = capacity[-1]
    d = last.date
    for _ in range(EXTEND):
        d = working_days_after(d, 1)
        yield replace(last, date=d)


def replay(
    requests: list[Request], capacity: list[Day], policy: str, scale: float = 1.0, typing_minutes: float = 0.0
) -> Outcome:
    """Day by day: the day's arrivals join the queue, answers that came back rejoin it, then the day's hours are
    spent on it, front first. No way of working sees a decision date: a Request doesn't have one."""
    if policy not in POLICIES:
        raise ValueError(f"policy {policy!r} isn't one of {', '.join(POLICIES)}")
    early = policy in ("ask", "intake")  # questions asked the day a request arrives
    new_first = True  # Wendlow prices new requests first, re-quotes when none is waiting
    saving = typing_minutes / 60 if policy == "intake" else 0.0
    need = {r.id: work_hours(r, scale, saving) for r in requests}
    spent = dict.fromkeys(need, 0.0)
    out = Outcome({r.id: None for r in requests if not r.requote})
    queue: list[Request] = []  # new requests (and, unless new_first, re-quotes), in order
    requotes: list[Request] = []  # with new_first: the re-quotes, after every new request
    waiting: dict[str, tuple[date, Request]] = {}  # asked when opened (today, order): back in on the answer
    ready: dict[str, date] = {}  # asked on arrival (intake, both): workable from the answer
    pending = sorted(requests, key=lambda r: (not r.at_start, r.received, r.id))

    def backlog_weeks() -> float:
        items = queue + requotes + [r for _, r in waiting.values()]
        return sum(need[r.id] if spent[r.id] > 0 else UNSTARTED for r in items) / STANDARD_DAY / 5

    for day in days(capacity):
        while pending and (pending[0].at_start or pending[0].received <= day.date):
            r = pending.pop(0)
            if r.requote:
                (requotes if new_first else queue).append(r)
                continue
            if r.tier == "occasional" and backlog_weeks() > TRIAGE_WEEKS:
                out.declined.append(r.id)
                continue
            if r.missing and early:
                out.asked[r.id] = r.received
                ready[r.id] = working_days_after(r.received, r.answer_days)
            queue.append(r)
        for rid, (back, r) in list(waiting.items()):
            if back <= day.date:
                del waiting[rid]
                queue.insert(0, r)  # the estimator picks it straight back up
        cap = day.hours
        if backlog_weeks() > HELP_WEEKS:
            cap += HELPERS * HELPER_HOURS
            out.helper_days += 1
        cap = _work(queue, cap, day, need, spent, out, waiting, ready, early, scale, saving)
        _work(requotes, cap, day, need, spent, out, waiting, ready, early, scale, saving)
        if not queue and not requotes and not pending and not waiting:
            break
    return out


def _work(queue, cap, day, need, spent, out, waiting, ready, early, scale, saving) -> float:
    """Spend up to `cap` hours on the queue, front first. Today, a request missing something is found when it's
    opened: the question goes out, and it waits for the answer outside the queue. With intake, a request still
    waiting on its answer is passed over until the answer comes."""
    i = 0
    while cap > 1e-9 and i < len(queue):
        r = queue[i]
        if r.missing and not r.requote:
            if early and ready.get(r.id, day.date) > day.date:
                i += 1
                continue
            if not early and r.id not in out.asked:
                out.asked[r.id] = day.date
                cap -= min(cap, QUESTION_HOURS)
                waiting[r.id] = (working_days_after(day.date, r.answer_days), r)
                queue.pop(i)
                continue
        if spent[r.id] == 0 and r.weld:
            junior = day.junior and not (day.senior and r.pick < SENIOR_WELD_SHARE)
            need[r.id] = work_hours(r, scale, 0.0 if r.requote else saving, junior)
        take = min(cap, need[r.id] - spent[r.id])
        spent[r.id] += take
        cap -= take
        if need[r.id] - spent[r.id] <= 1e-9:
            if r.requote:
                out.requote_sent[r.id] = day.date
            else:
                out.sent[r.id] = day.date
            queue.pop(i)
        else:
            break  # half done: the day ends on it, as the simulation's estimators do
    return cap


def on_time(sent: dict[str, date | None], truth: dict[str, Truth]) -> int:
    return sum(1 for rid, d in sent.items() if d and truth[rid].decision and d <= truth[rid].decision)


def win_rate(rows: list[dict]) -> float:
    """won / (won + lost on price), over the actual new-part quotes sent on or before the decision."""
    on = [
        r
        for r in rows
        if r["kind"] == "new" and r["quote_sent_on"] and r["decision_date"] and r["quote_sent_on"] <= r["decision_date"]
    ]
    won = sum(r["outcome"] == "won" for r in on)
    lost = sum(r["outcome"] == "lost" for r in on)
    return won / (won + lost) if won + lost else 0.0


def calibrate(requests, capacity, truth, seeds=SEEDS, lo=0.3, hi=4.0) -> tuple[float, float]:
    """The factor that makes `today` get as many quotes out on time as Wendlow really did."""
    target = on_time({r.id: truth[r.id].sent for r in requests if not r.requote}, truth)
    runs = [drawn(requests, s) for s in range(seeds)]

    def mean_today(scale: float) -> float:
        return statistics.mean(on_time(replay(rs, capacity, "today", scale).sent, truth) for rs in runs)

    for _ in range(30):
        mid = (lo + hi) / 2
        if mean_today(mid) > target:
            lo = mid
        else:
            hi = mid
    scale = (lo + hi) / 2
    return scale, mean_today(scale)


def run(folder: Path = DATA, typing_minutes: float = TYPING_MINUTES, seeds: int = SEEDS) -> dict:
    requests, truth, capacity = load(folder)
    rows = all_rows(folder)
    scale, today_mean = calibrate(requests, capacity, truth, seeds)
    actual = on_time({r.id: truth[r.id].sent for r in requests if not r.requote}, truth)
    runs = [drawn(requests, s) for s in range(seeds)]
    rate = win_rate(rows)
    res = {}
    for p in POLICIES:
        outs = [replay(rs, capacity, p, scale, typing_minutes) for rs in runs]
        counts = [on_time(o.sent, truth) for o in outs]
        waits = [
            statistics.mean([(o.asked[r.id] - r.received).days for r in requests if r.id in o.asked] or [0])
            for o in outs
        ]
        res[p] = {
            "name": NAMES[p],
            "on_time": round(statistics.mean(counts), 1),
            "on_time_range": [min(counts), max(counts)],
            "days_until_the_question": round(statistics.mean(waits), 1),
        }
    base = res["today"]["on_time"]
    for p in POLICIES:
        extra = res[p]["on_time"] - base
        res[p]["extra_on_time"] = round(extra, 1)
        res[p]["extra_wins"] = round(extra * rate, 1)
        res[p]["margin_value"] = round(extra * rate * REVENUE_PER_WIN * MARGIN)
    new = [r for r in requests if not r.requote and not r.at_start]
    return {
        "window": [min(r.received for r in new).isoformat(), max(r.received for r in new).isoformat()],
        "new_requests": len(new),
        "missing_something": sum(bool(r.missing) for r in new),
        "lost_late_in_the_records": sum(truth[r.id].outcome == "lost late" for r in new),
        "on_time_in_the_records": actual,
        "calibration": {"factor": round(scale, 3), "today_model_on_time": round(today_mean, 1)},
        "win_rate": round(rate, 3),
        "parameters": {
            "typing_minutes": typing_minutes,
            "revenue_per_win": REVENUE_PER_WIN,
            "margin": MARGIN,
            "seeds": seeds,
        },
        "policies": res,
    }


def report(res: dict) -> str:
    p = res["policies"]
    lines = [
        "# Queue replay: what reading every request on arrival is worth",
        "",
        f"Window: {res['window'][0]} to {res['window'][1]}. {res['new_requests']} new requests, "
        f"{res['missing_something']} of them missing a revision, a quantity or the drawing; "
        f"{res['lost_late_in_the_records']} lost because the quote came after the buyer decided.",
        "",
        f"The model of today, calibrated: {res['calibration']['today_model_on_time']} quotes on time, against "
        f"{res['on_time_in_the_records']} in the records. Win rate of on-time quotes: {res['win_rate']:.0%}.",
        "",
        "| Way of working | Days until the question | On time | Extra on time | Extra wins | Margin |",
        "|---|---|---|---|---|---|",
    ]
    for k in POLICIES:
        x = p[k]
        lines.append(
            f"| {x['name']} | {x['days_until_the_question']} | {x['on_time']} | {x['extra_on_time']:+} | "
            f"{x['extra_wins']:+} | ${x['margin_value']:,} |"
        )
    lines += ["", "A model, not a measurement: see the notes at the top of `replay_queue.py`."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--out", type=Path, default=Path("out") / "replay")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--typing-minutes", type=float, default=TYPING_MINUTES)
    args = ap.parse_args()
    res = run(args.data, args.typing_minutes, args.seeds)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "replay.json").write_text(json.dumps(res, indent=1) + "\n")
    (args.out / "replay.md").write_text(report(res))
    print(report(res))


if __name__ == "__main__":
    main()
