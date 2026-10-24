"""Queue replay: a model of Wendlow's quoting queue, to measure what reading every request on arrival is worth.

    python rfq-intake/replay_queue.py                      # the sample window: writes out/replay/
    python rfq-intake/replay_queue.py --data DIR --out DIR # another window (a folder with rfqs.csv, capacity.csv)

Wendlow's estimators read quotes@ twice a week, on Mondays and Thursdays, and key each new request into the ERP
(about ten minutes each, out of the hours they'd otherwise price with). About 4 in 10 requests arrive missing something
needed to price them: a revision, a quantity or the drawing. Nobody checks for that until an estimator opens the
request to price it, so the question goes to the buyer days after the request arrived, and the request waits again for
the answer. Meanwhile the buyer decides.

The model replays every request the estimators had to price in a window (new-part requests and annual re-quotes,
with the queue as it stood on its first morning), day by day, three ways. In all three, new requests are priced
first, in the order they were logged (key accounts at the front), and the annual re-quotes when no new request is
waiting, as Wendlow already does. Every question costs a quarter hour of an estimator's time to check and send.

today     what Wendlow did. Requests are read and keyed on Mondays and Thursdays (a day an estimator is in); one
          missing something is found when it reaches the front, the question goes out that day, and the request goes
          back to the front when the buyer answers.
daily     the same work done by a person every morning, without AI: each request is read and keyed the day it arrives
          (the same keying minutes), and the question for one missing something goes out then.
intake    AI intake: every request read the day it arrives and the question drafted that day; the lines come out as an
          import file for the ERP, so nobody keys them. A person still handles the requests the tool sends to one
          (keyed by hand) and checks each import row (CHECK_MINUTES).

The model of the work, the same in all three: each request's quoting time is `expected_quote_hours` (the simulation's
deterministic part) x one calibration factor x 1.3 for weld-family work a junior prices (with the senior in, he
prices about 3 in 4 of it) x a draw of the simulation's own noise, over 20 seeds. Each day has the estimators' hours
from capacity.csv (before keying), plus two helpers at three hours each on a day the backlog is over two weeks;
occasional customers' new requests are declined past three weeks. The buyer takes the same `answer_days` to
answer whenever the question is asked.

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
import zlib
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

import desk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rfq_intake import JUNIOR_WELD, working_days_after  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "sample-data" / "queue-replay"

POLICIES = ("today", "daily", "intake")
DESK = "desk"  # the quote desk: a fourth way, run alongside the three (ALL)
ALL = POLICIES + (DESK,)
NAMES = {
    "today": "Today: read and keyed twice a week, questions asked when a request is opened",
    "daily": "A person reads and keys every request the morning it arrives, and asks then",
    "intake": "AI intake: read on arrival, questions drafted the same day, an import file instead of keying",
    "desk": (
        "The quote desk: AI intake, plus re-quotes priced from the history brief and low-odds requests behind the rest"
    ),
}
INTAKE_WEEKDAYS = (0, 3)  # Mondays and Thursdays, as Wendlow reads quotes@ (the simulation's INTAKE_WEEKDAYS)
HELPERS, HELPER_HOURS = 2, 3.0  # the sales manager and an engineer, past two weeks of backlog
HELP_WEEKS, TRIAGE_WEEKS = 2, 3
STANDARD_DAY = 10.5  # backlog weeks are counted against the two-estimator standard, whatever the staffing
UNSTARTED = 1.5  # hours a request not yet started counts for in the backlog (the simulation's rule)
SENIOR_WELD_SHARE = 0.75
QUESTION_HOURS = 0.25  # an estimator's time to spot the gap and write the question, today
EXTEND = 120  # at most this many extra working days after capacity.csv ends, at its last day's hours
SEEDS = 20

# Labeled estimates, not results.
KEYING_MINUTES = 10  # an estimator's minutes to read a request and key it into the ERP (the simulation's own)
CHECK_MINUTES = 1  # with AI intake, a person's minutes to look over each request's import rows
TO_A_PERSON = 0.12  # with AI intake, the share of new requests sent to a person (35 of 299 in the recorded months)
REVENUE_PER_WIN = (
    35_800  # first-year revenue per won new-part quote, every order of its parts in the year after the win:
)
# Wendlow's records, quotes won 2022-23 (pathmode-corpus simulations/fabricator/scripts/rfq_value_stats.py)
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
    screened: bool = False  # read and keyed, but never priced (screened out or declined)
    win_rate: float | None = None  # the customer's record of new-part quotes won, as of the request's arrival

    @property
    def requote(self) -> bool:
        return self.kind == "requote"

    @property
    def priced(self) -> bool:
        """A new request someone prices: not a re-quote, not screened out."""
        return not self.requote and not self.screened


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
                    screened=row["outcome"] == "screened out",
                    win_rate=float(row["customer_win_rate"]) if row.get("customer_win_rate") else None,
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


def work_hours(r: Request, scale: float, junior: bool = True) -> float:
    return r.expected_hours * scale * (JUNIOR_WELD if r.weld and junior else 1.0) * r.draw


def days(capacity: list[Day]):
    yield from capacity
    last = capacity[-1]
    d = last.date
    for _ in range(EXTEND):
        d = working_days_after(d, 1)
        yield replace(last, date=d)


def replay(
    requests: list[Request],
    capacity: list[Day],
    policy: str,
    scale: float = 1.0,
    keying_minutes: float = KEYING_MINUTES,
    shop_rate: float | None = None,
    reorder_low: bool | None = None,
) -> Outcome:
    """Day by day: the day's arrivals reach the inbox; on a reading day they're keyed and join the queue; answers
    that came back rejoin it; then the day's hours go first to the keying and the questions, and the rest to the
    queue, front first. No way of working sees a decision date: a Request doesn't have one."""
    if policy not in ALL:
        raise ValueError(f"policy {policy!r} isn't one of {', '.join(ALL)}")
    early = policy in ("daily", "intake", "desk")  # the question goes out when the request is read
    tool = policy in ("intake", "desk")  # the tool reads and keys
    rate = (
        shop_rate
        if shop_rate is not None
        else statistics.mean([r.win_rate for r in requests if r.win_rate is not None] or [0.4])
    )

    def low(r: Request) -> bool:
        """The desk's bid odds: a customer far below the shop's record waits behind the rest."""
        on = desk.REORDER if reorder_low is None else reorder_low
        return on and policy == "desk" and r.win_rate is not None and r.win_rate < desk.LOW_SHARE * rate

    # With AI intake, most requests are read and keyed by the tool every morning, and a person spends a minute
    # checking each; the share it sends to a person is read and keyed by hand the next morning someone is in.
    # Either way, a person sends the drafted question, so it goes out on a day someone is in.
    need = {
        r.id: work_hours(r, scale) * (desk.FAST_TRACK if policy == "desk" and r.requote else 1.0)
        for r in requests
        if not r.screened
    }
    spent = dict.fromkeys(need, 0.0)
    out = Outcome({r.id: None for r in requests if r.priced})
    queue: list[Request] = []  # logged new requests, in order (key accounts at the front)
    later: list[Request] = []  # the desk: low-odds new requests, behind the rest
    requotes: list[Request] = []  # the re-quotes, after every new request
    inbox: list[Request] = []  # arrived, not yet read and keyed
    waiting: dict[str, tuple[date, Request]] = {}  # today: asked when opened, back in on the answer
    ready: dict[str, date] = {}  # daily, intake: asked when read, workable from the answer
    pending = sorted(requests, key=lambda r: (not r.at_start, r.received, r.id))
    debt = [0.0]  # keying and questions owed, paid first thing from the next hours

    def backlog_weeks() -> float:
        items = queue + later + requotes + [r for _, r in waiting.values()]
        return sum(need[r.id] if spent[r.id] > 0 else UNSTARTED for r in items) / STANDARD_DAY / 5

    def by_hand(r: Request) -> bool:
        """With AI intake, the requests the tool sends to a person: a fixed share, chosen by id."""
        return tool and (zlib.crc32(r.id.encode()) % 10_000) / 10_000 < TO_A_PERSON

    def reading_day(day: Day, r: Request) -> bool:
        if tool and not by_hand(r):
            return True  # the tool reads every morning, whoever is in
        return day.hours > 0 and (policy in ("daily", "intake", "desk") or day.date.weekday() in INTAKE_WEEKDAYS)

    unasked: list[Request] = []  # intake: read on a day nobody was in; the question waits for someone

    for day in days(capacity):
        while pending and (pending[0].at_start or pending[0].received <= day.date):
            r = pending.pop(0)
            if r.at_start and not r.screened:
                (requotes if r.requote else queue).append(r)  # already logged before the window
            elif r.requote:
                requotes.append(r)  # raised inside the ERP: nothing to read
            elif not r.at_start:
                inbox.append(r)
        if day.hours > 0:
            for r in unasked:
                out.asked[r.id] = day.date
                ready[r.id] = working_days_after(day.date, r.answer_days)
                debt[0] += QUESTION_HOURS
            unasked.clear()
        for r in [r for r in inbox if reading_day(day, r)]:
            inbox.remove(r)
            machine = tool and not by_hand(r)
            debt[0] += (CHECK_MINUTES if machine else keying_minutes) / 60
            if r.screened:
                continue
            if r.tier == "occasional" and backlog_weeks() > TRIAGE_WEEKS:
                out.declined.append(r.id)
                continue
            if r.missing and early:
                if day.hours > 0:
                    out.asked[r.id] = day.date
                    ready[r.id] = working_days_after(day.date, r.answer_days)
                    debt[0] += QUESTION_HOURS  # a person reads the drafted question and sends it
                else:
                    unasked.append(r)
                    ready[r.id] = date.max  # not workable until the question has gone and been answered
            if low(r):
                later.append(r)
            elif r.tier == "key":
                queue.insert(0, r)  # as the simulation does: a key account's request goes to the front
            else:
                queue.append(r)
        for rid, (back, r) in list(waiting.items()):
            if back <= day.date:
                del waiting[rid]
                queue.insert(0, r)  # the estimator picks it straight back up
        cap = day.hours
        paid = min(cap, debt[0])
        cap -= paid
        debt[0] -= paid
        if backlog_weeks() > HELP_WEEKS:
            cap += HELPERS * HELPER_HOURS
            out.helper_days += 1
        cap = _work(queue, cap, day, need, spent, out, waiting, ready, early, scale)
        cap = _work(later, cap, day, need, spent, out, waiting, ready, early, scale)
        _work(requotes, cap, day, need, spent, out, waiting, ready, early, scale)
        if not queue and not later and not requotes and not pending and not waiting and not inbox and not unasked:
            break
    return out


def _work(queue, cap, day, need, spent, out, waiting, ready, early, scale) -> float:
    """Spend up to `cap` hours on the queue, front first. Today, a request missing something is found when it's
    opened: the question goes out, and it waits for the answer outside the queue. Read on arrival, a request still
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
            need[r.id] = work_hours(r, scale, junior=junior)
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


def expected_wins(sent: dict[str, date | None], truth: dict[str, Truth], reqs: dict[str, Request]) -> float:
    """The quotes that reached the buyer in time, each weighted by its customer's record (what the shop could know):
    so putting a likely winner ahead of an unlikely one counts for what it's worth."""
    return sum(
        reqs[rid].win_rate or 0.0 for rid, d in sent.items() if d and truth[rid].decision and d <= truth[rid].decision
    )


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


def calibrate(requests, capacity, truth, seeds=SEEDS, lo=0.3, hi=4.0, keying_minutes=KEYING_MINUTES):
    """The factor that makes `today` get as many quotes out on time as Wendlow really did."""
    target = on_time({r.id: truth[r.id].sent for r in requests if r.priced}, truth)
    runs = [drawn(requests, s) for s in range(seeds)]

    def mean_today(scale: float) -> float:
        return statistics.mean(on_time(replay(rs, capacity, "today", scale, keying_minutes).sent, truth) for rs in runs)

    for _ in range(30):
        mid = (lo + hi) / 2
        if mean_today(mid) > target:
            lo = mid
        else:
            hi = mid
    scale = (lo + hi) / 2
    return scale, mean_today(scale)


def run(folder: Path = DATA, keying_minutes: float = KEYING_MINUTES, seeds: int = SEEDS) -> dict:
    requests, truth, capacity = load(folder)
    rows = all_rows(folder)
    scale, today_mean = calibrate(requests, capacity, truth, seeds, keying_minutes=keying_minutes)
    actual = on_time({r.id: truth[r.id].sent for r in requests if r.priced}, truth)
    runs = [drawn(requests, s) for s in range(seeds)]
    rate = win_rate(rows)
    res = {}
    by_id = {r.id: r for r in requests}
    for p in ALL:
        outs = [replay(rs, capacity, p, scale, keying_minutes) for rs in runs]
        counts = [on_time(o.sent, truth) for o in outs]
        ews = [expected_wins(o.sent, truth, by_id) for o in outs]
        waits = [
            statistics.mean([(o.asked[r.id] - r.received).days for r in requests if r.id in o.asked] or [0])
            for o in outs
        ]
        res[p] = {
            "name": NAMES[p],
            "on_time": round(statistics.mean(counts), 1),
            "on_time_range": [min(counts), max(counts)],
            "days_until_the_question": round(statistics.mean(waits), 1),
            "expected_wins": round(statistics.mean(ews), 1),
        }
    base = res["today"]["on_time"]
    for p in ALL:
        extra = res[p]["on_time"] - base
        res[p]["extra_on_time"] = round(extra, 1)
        res[p]["extra_wins"] = round(extra * rate, 1)
        res[p]["margin_value"] = round(extra * rate * REVENUE_PER_WIN * MARGIN)
        ew = res[p]["expected_wins"] - res["today"]["expected_wins"]
        res[p]["extra_expected_wins"] = round(ew, 1)
        res[p]["expected_margin_value"] = round(ew * REVENUE_PER_WIN * MARGIN)
    requote_hours = sum(work_hours(r, scale) for r in requests if r.requote)
    span_years = max((capacity[-1].date - capacity[0].date).days, 1) / 365
    start = capacity[0].date
    new = [r for r in requests if r.priced and not r.at_start and r.received >= start]
    return {
        "window": [min(r.received for r in new).isoformat(), max(r.received for r in new).isoformat()],
        "new_requests": len(new),
        "missing_something": sum(bool(r.missing) for r in new),
        "lost_late_in_the_records": sum(truth[r.id].outcome == "lost late" for r in new),
        "on_time_in_the_records": actual,
        "calibration": {"factor": round(scale, 3), "today_model_on_time": round(today_mean, 1)},
        "win_rate": round(rate, 3),
        "parameters": {
            "keying_minutes": keying_minutes,
            "check_minutes": CHECK_MINUTES,
            "to_a_person": TO_A_PERSON,
            "revenue_per_win": REVENUE_PER_WIN,
            "margin": MARGIN,
            "seeds": seeds,
        },
        "policies": res,
        "desk_requote_hours_saved_a_year": round(requote_hours * (1 - desk.FAST_TRACK) / span_years),
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
        "| Way of working | Days until the question | On time | Extra on time | Extra wins | Margin "
        "| Expected wins, by record | Margin, by record |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for k in ALL:
        x = p[k]
        lines.append(
            f"| {x['name']} | {x['days_until_the_question']} | {x['on_time']} | {x['extra_on_time']:+} | "
            f"{x['extra_wins']:+} | ${x['margin_value']:,} | {x['extra_expected_wins']:+} | "
            f"${x['expected_margin_value']:,} |"
        )
    lines += [
        "",
        f"The desk also prices re-quotes from the history brief, in a quarter of the time: about "
        f"{res['desk_requote_hours_saved_a_year']:,} estimator hours a year.",
        "",
        "A model, not a measurement: see the notes at the top of `replay_queue.py`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--out", type=Path, default=Path("out") / "replay")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--keying-minutes", type=float, default=KEYING_MINUTES)
    args = ap.parse_args()
    res = run(args.data, args.keying_minutes, args.seeds)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "replay.json").write_text(json.dumps(res, indent=1) + "\n")
    (args.out / "replay.md").write_text(report(res))
    print(report(res))


if __name__ == "__main__":
    main()
