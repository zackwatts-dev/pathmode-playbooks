"""Queue replay: a counterfactual MODEL of Wendlow's quoting queue. Not a measurement.

    python rfq-intake/replay_queue.py                      # the sample, March to June 2024: writes out/replay/
    python rfq-intake/replay_queue.py --data DIR --out DIR # another window (a folder with rfqs.csv, capacity.csv)

The intake tool doesn't use this. It asks: would a different order have got more quotes to buyers before they
decided? It replays every request the estimators had to price in the window (new-part RFQs and annual re-quotes,
with the queue as it stood on its first morning), day by day, five ways:

(a)     what Wendlow did, as the records show it: one queue, first in, first out, re-quotes included, and occasional
        customers' new RFQs declined while the backlog is over three weeks. (The design says key accounts go first,
        and the simulation's code puts each new key RFQ at the front, but in the records every tier waited the same;
        `key_first` is a variant.)
(d)     first in, first out, with new requests ahead of the re-quotes: the process change alone, no tool.
(b)     the tool's order (stated due date or six working days after arrival, then key accounts, then oldest), new
        requests ahead of the re-quotes. Its at-risk flags are information (ask the buyer for more time): nothing is
        taken out.
(b-old) the same, with the first design's Moore-Hodgson removal: an at-risk request isn't quoted. For the record.
(c)     (b), plus the time extraction saves: no one retypes part numbers, revisions, quantities and dates, a
        labelled estimate of `--typing-minutes` (default 10) per new RFQ.

The model of the work, the same in all five: each request's quoting time is `expected_quote_hours` (the simulation's
deterministic part), times one calibration factor, times 1.3 for weld-family work a junior prices (on days with the
senior estimator in, he prices about 3 in 4 of it), times a draw of the simulation's own noise (lognormal(0, 0.5), and
the square root of the largest of the lines' lognormal(0, 0.35) complexities), over 20 seeds. Each day has the
estimators' hours from capacity.csv (an absent estimator's are 0), plus two helpers at 3 hours each on any day the
backlog is over two weeks (backlog weeks = queued hours / 10.5 / 5, a request not yet started counting 1.5 hours).
After the last day on file, its hours carry on until the queue is empty. Screened-out RFQs never enter the queue.
Re-quotes come as the records have them; the simulation stops raising them while the backlog is over two weeks, so a
shorter queue would have seen a few more.

The calibration factor is fitted on (a) alone, so the model of the status quo gets as many quotes out on time as
really did (within 2%); every other policy runs with the same factor. The model is tuned to what Wendlow did, never
to the tool.

A quote is on time if it's sent on or before the buyer's true decision date (`decision_date`, from the simulation's
truth; nobody at Wendlow could see it). Only scoring reads it: the policies get requests without it. The value is the
extra on-time quotes x the win rate of on-time new-part quotes in the window's actual records (won / (won + lost on
price)) x first-year revenue per win x margin, for the window: labelled parameters below. It isn't annualised: the
windows are estimator vacancies, rare (two in 2021-24), and in normal months almost nothing is lost late. The
re-quotes' wait is reported for each policy, because a longer wait has a cost the model doesn't charge.
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
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rfq_intake import (  # noqa: E402
    DEFAULT_WINDOW,
    JUNIOR_WELD,
    QueueItem,
    forecast,
    forecast_with_removal,
    quote_hours,
    working_days_after,
)

HERE = Path(__file__).resolve().parent
DATA = HERE / "sample-data" / "queue-replay"

POLICIES = ("a", "d", "b", "b-old", "c")
NAMES = {
    "a": "(a) Wendlow's rule: FIFO",
    "d": "(d) FIFO, new requests before re-quotes",
    "b": "(b) The tool's order, new before re-quotes, flags only",
    "b-old": "(b-old) The same, with the old removal",
    "c": "(c) (b), and no retyping",
}
HELPERS, HELPER_HOURS = 2, 3.0  # the sales manager and an engineer, past two weeks of backlog
HELP_WEEKS, TRIAGE_WEEKS = 2, 3
STANDARD_DAY = 10.5  # backlog weeks are counted against the two-estimator standard, whatever the staffing
UNSTARTED = 1.5  # hours a request not yet started counts for in the backlog (the simulation's rule)
SENIOR_WELD_SHARE = 0.75  # with the senior in, he prices about this share of the weld-family work
EXTEND = 120  # at most this many extra working days after capacity.csv ends, at its last day's hours
FORECAST_DAYS = 180  # how far ahead the tool's forecast looks, in calendar days
RESERVE_DAYS = 20  # the tool holds back the last four weeks' re-quote hours (20 working days), in its forecast
REQUOTE_RESERVE = 0.0  # hours a day the tool's forecast holds back for re-quotes: forecast.json's default (0)
SEEDS = 20
CALIBRATION_TOLERANCE = 0.02

# Value parameters: labelled estimates, not results.
# The cost of a re-quote waiting one more working day: the old price stays on the part's repeat orders for that day.
# From Wendlow's records, re-quotes sent 2022-23: the new price averaged 13.9% over the old, on about $13,400 a year of
# repeat revenue per part, so (new - old) x a year's quantity / 250 working days = $5.31 a day (the median is $0.68).
REQUOTE_DAY_COST = 5.31
TYPING_MINUTES = 10  # (c) estimator minutes saved per new RFQ by not retyping its lines: an estimate
REVENUE_PER_WIN = 34_000  # first-year revenue per won new-part quote: Wendlow's records, won new-part quotes 2022-23
MARGIN = 0.27  # the middle of the published 22-31% range for job shops (Wendlow's own books run higher)


@dataclass(frozen=True)
class Request:
    """What the shop could know about a request when it arrived. No decision date, no outcome."""

    id: str
    kind: str  # "new" or "requote"
    customer: str
    tier: str
    received: date
    stated_due: date | None
    lines: int
    weld: bool
    expected_hours: float
    at_start: bool = False  # in the queue on the morning the replay starts
    draw: float = 1.0  # the noise and complexity factor on its quoting time
    pick: float = 1.0  # who prices it, on a day the senior is in: the senior if below SENIOR_WELD_SHARE

    @property
    def requote(self) -> bool:
        return self.kind == "requote"


@dataclass(frozen=True)
class Day:
    date: date
    hours: float
    senior: bool = False  # a senior estimator works that day
    junior: bool = True  # a junior estimator works that day
    junior_hours: float = 0.0


@dataclass(frozen=True)
class Truth:
    """What happened, and what nobody could see: for scoring only."""

    decision: date | None
    outcome: str
    sent: date | None


@dataclass
class Outcome:
    sent: dict[str, date | None]  # new RFQ id -> the day its quote went out (None: never)
    declined: list[str] = field(default_factory=list)  # (a), (d): occasional customers past three weeks of backlog
    flagged: set[str] = field(default_factory=set)  # flagged at risk at least once (b, c: informational)
    removed: list[str] = field(default_factory=list)  # (b-old): taken out as at risk, never quoted
    helper_days: int = 0
    requote_sent: dict[str, date] = field(default_factory=dict)


def load(folder: Path) -> tuple[list[Request], dict[str, Truth], list[Day]]:
    requests, truth = [], {}
    with (folder / "rfqs.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["outcome"] == "screened out":
                continue  # never in the queue
            requests.append(
                Request(
                    row["rfq_id"],
                    row["kind"],
                    row["customer_id"],
                    row["tier"],
                    date.fromisoformat(row["received_on"]),
                    date.fromisoformat(row["stated_due"]) if row["stated_due"] else None,
                    int(row["lines"]),
                    row["weld_family"] == "1",
                    float(row["expected_quote_hours"]),
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
            juniors = sum("(junior)" in w for w in who)
            capacity.append(
                Day(
                    date.fromisoformat(r["date"]),
                    float(r["estimator_hours"]),
                    any("(senior)" in w for w in who),
                    juniors > 0,
                    6.0 * juniors,
                )
            )
    return sorted(requests, key=lambda r: (r.received, r.id)), truth, capacity


def all_rows(folder: Path, name: str = "rfqs.csv") -> list[dict]:
    with (folder / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def drawn(requests: list[Request], seed: int) -> list[Request]:
    """Each request's noise and complexity drawn the way the simulation draws them, and who prices it. Seeded, so it
    repeats exactly; the same seed gives every policy the same draws."""
    out = []
    for r in requests:
        g = random.Random(f"{seed}:{r.id}")
        f = g.lognormvariate(0, 0.5) * math.sqrt(max(g.lognormvariate(0, 0.35) for _ in range(r.lines)))
        out.append(replace(r, draw=f, pick=g.random()))
    return out


def work_hours(r: Request, scale: float, saving: float = 0.0, junior: bool = True) -> float:
    """The model's quoting time: expected hours x the calibration factor x1.3 for weld-family work a junior prices
    x the draw, less the typing a new RFQ no longer needs (policy c)."""
    hours = r.expected_hours * scale * (JUNIOR_WELD if r.weld and junior else 1.0) * r.draw
    return max(hours - (0.0 if r.requote else saving), 0.0)


def days(capacity: list[Day]):
    """Each working day on file, then the last day carried on for up to EXTEND working days."""
    yield from capacity
    last = capacity[-1]
    d = last.date
    for _ in range(EXTEND):
        d = working_days_after(d, 1)
        yield replace(last, date=d)


def tool_due(r: Request) -> tuple[date, bool]:
    return (r.stated_due, True) if r.stated_due else (working_days_after(r.received, DEFAULT_WINDOW), False)


def tool_hours(r: Request, junior: bool, saving: float = 0.0) -> float:
    """The intake tool's forecast for a new RFQ: its formula, with the family it reads from each part's description
    and the junior factor when the day's hours are mostly a junior's; less the typing saved, in (c)."""
    return max(quote_hours(r.lines, r.weld, junior=junior) - saving, 0.0)


def _work(queue: list[Request], cap: float, need, spent, out: Outcome, day: Day, scale: float, saving: float) -> float:
    """Spend up to `cap` hours on the queue, front first. A request's time is set when it's started: who prices it
    decides the junior factor. Returns the hours left over."""
    while cap > 1e-9 and queue:
        r = queue[0]
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
            queue.pop(0)
    return cap


def replay(
    requests: list[Request],
    capacity: list[Day],
    policy: str,
    scale: float = 1.0,
    saving_hours: float = 0.0,
    helpers: bool = True,
    key_first: bool = False,
    requote_reserve: float = REQUOTE_RESERVE,
) -> Outcome:
    """Day by day: the day's arrivals join the queue, then the day's hours are spent on it. No policy sees a decision
    date: a Request doesn't have one."""
    if policy not in POLICIES:
        raise ValueError(f"policy {policy!r} isn't one of {', '.join(POLICIES)}")
    saving = saving_hours if policy == "c" else 0.0
    need = {r.id: work_hours(r, scale, saving) for r in requests}
    spent = dict.fromkeys(need, 0.0)
    out = Outcome({r.id: None for r in requests if not r.requote})
    queue: list[Request] = []  # (a): everything; the others: new requests
    requotes: list[Request] = []  # the others: re-quotes, first in first out, after the new requests
    pending = sorted(requests, key=lambda r: (not r.at_start, r.received, r.id))
    fifo = policy in ("a", "d")

    def backlog_weeks() -> float:
        return sum(need[r.id] if spent[r.id] > 0 else UNSTARTED for r in queue + requotes) / STANDARD_DAY / 5

    for day in days(capacity):
        while pending and (pending[0].at_start or pending[0].received <= day.date):
            r = pending.pop(0)
            if r.requote:
                (queue if policy == "a" else requotes).append(r)
            elif fifo and r.tier == "occasional" and backlog_weeks() > TRIAGE_WEEKS:
                out.declined.append(r.id)
            elif fifo and key_first and r.tier == "key":
                queue.insert(0, r)
            else:
                queue.append(r)
        cap = day.hours
        if helpers and backlog_weeks() > HELP_WEEKS:
            cap += HELPERS * HELPER_HOURS
            out.helper_days += 1
        if not fifo and queue:
            reserve = requote_reserve
            junior = day.junior_hours >= day.hours / 2 if day.hours else True
            queue = _tool_order(
                queue, day.date, max(day.hours - reserve, 0.0), spent, need, saving, out, policy, junior
            )
        left = _work(queue, cap, need, spent, out, day, scale, saving)
        _work(requotes, left, need, spent, out, day, scale, saving)
        if not queue and not requotes and not pending:
            break
    return out


def _tool_order(queue, d, hours, spent, need, saving, out: Outcome, policy: str, junior: bool) -> list[Request]:
    """The tool's view of the new requests today: its order and its forecast from today's hours less the re-quote
    reserve (carried on over the coming working days). Its at-risk flags are recorded; only (b-old) takes them out.
    Work already started is never taken out."""
    items, by_ref = [], {}
    for r in queue:
        due, stated = tool_due(r)
        left = 1 - spent[r.id] / need[r.id] if need[r.id] else 0.0
        items.append(
            QueueItem(
                r.id,
                r.id,
                r.customer,
                r.tier == "key",
                datetime.combine(r.received, datetime.min.time()),
                d,
                due,
                stated,
                tool_hours(r, junior, saving) * left,
                protected=spent[r.id] > 0,
            )
        )
        by_ref[r.id] = r
    plan_with = forecast_with_removal if policy == "b-old" else forecast
    plan = plan_with(items, lambda x: hours if x.weekday() < 5 else 0.0, d, d + timedelta(days=FORECAST_DAYS))
    out.flagged |= {it.ref for it, _ in plan.at_risk}
    if policy == "b-old":
        out.removed += [it.ref for it, _ in plan.at_risk]
    return [by_ref[it.ref] for it, _ in plan.queue]


def win_rate(rows: list[dict]) -> tuple[float, int, int]:
    """won / (won + lost on price), over the actual new-part quotes that went out on or before the decision."""
    on = [r for r in rows if r["kind"] == "new" and r["quote_sent_on"] and r["quote_sent_on"] <= r["decision_date"]]
    won = sum(r["outcome"] == "won" for r in on)
    lost = sum(r["outcome"] == "lost" for r in on)
    return (won / (won + lost) if won + lost else 0.0), won, lost


def on_time(sent: dict[str, date | None], truth: dict[str, Truth]) -> int:
    return sum(s is not None and truth[i].decision is not None and s <= truth[i].decision for i, s in sent.items())


def actual_on_time(truth: dict[str, Truth], requests: list[Request]) -> int:
    return on_time({r.id: truth[r.id].sent for r in requests if not r.requote}, truth)


def calibrate(requests, capacity, truth, seeds=SEEDS, lo=0.3, hi=4.0, key_first=False) -> tuple[float, float]:
    """The single factor on expected quote hours that makes policy (a), averaged over the seeds, get as many quotes
    out on time as the records show. Bisection (more hours, fewer on time), on (a) only."""
    target = actual_on_time(truth, requests)
    draws = [drawn(requests, s) for s in range(1, seeds + 1)]

    def mean_a(scale: float) -> float:
        return statistics.mean(
            on_time(replay(rs, capacity, "a", scale, key_first=key_first).sent, truth) for rs in draws
        )

    for _ in range(16):
        mid = (lo + hi) / 2
        if mean_a(mid) > target:
            lo = mid
        else:
            hi = mid
    scale = round((lo + hi) / 2, 3)
    return scale, mean_a(scale)


def requote_wait(o: Outcome, received: dict[str, date]) -> float:
    waits = [(sent - received[rid]).days for rid, sent in o.requote_sent.items()]
    return statistics.median(waits) if waits else 0.0


def late(o: Outcome, truth: dict[str, Truth]) -> int:
    """New RFQs whose buyer decided without our quote: sent after the decision, or never sent (declined or removed)."""
    return sum(s is None or (truth[i].decision is not None and s > truth[i].decision) for i, s in o.sent.items())


def awarded(truth: dict[str, Truth]) -> set[str]:
    """New RFQs a buyer awarded to someone. A cancelled project ("no award") can't be won, on time or not."""
    return {i for i, t in truth.items() if t.decision is not None and t.outcome != "no award"}


def requote_wait_days(o: Outcome, requests: list[Request], end: date) -> int:
    """Working days the re-quotes waited in all, from arrival to being done (to the last day, if never done)."""
    total = 0
    for r in requests:
        if r.requote:
            done = o.requote_sent.get(r.id, end)
            total += sum(
                1 for k in range((done - r.received).days) if (r.received + timedelta(days=k + 1)).weekday() < 5
            )
    return total


def money(x: float) -> int:
    return round(x / 100) * 100


def run(folder: Path = DATA, typing_minutes: float = TYPING_MINUTES, seeds: int = SEEDS) -> dict:
    requests, truth, capacity = load(folder)
    received = {r.id: r.received for r in requests}
    rate, won, lost = win_rate(all_rows(folder))
    target = actual_on_time(truth, requests)
    scale, fitted = calibrate(requests, capacity, truth, seeds)
    saving = typing_minutes / 60
    draws = [drawn(requests, s) for s in range(1, seeds + 1)]
    outs = {p: [replay(rs, capacity, p, scale, saving) for rs in draws] for p in POLICIES}
    start, end = capacity[0].date, capacity[-1].date
    per_win = rate * REVENUE_PER_WIN * MARGIN
    months = ((end - start).days + 1) / 30.44
    won_able = awarded(truth)
    horizon = end + timedelta(days=200)

    def on_time_aw(o: Outcome) -> int:
        return on_time({i: s_ for i, s_ in o.sent.items() if i in won_able}, truth)

    def late_aw(o: Outcome) -> int:
        return sum(i in won_able for i in o.sent) - on_time_aw(o)

    waits = {p: [requote_wait_days(o, requests, horizon) for o in os_] for p, os_ in outs.items()}
    res = {}
    for p, os_ in outs.items():
        counts = [on_time(o.sent, truth) for o in os_]
        diffs = [on_time_aw(o) - on_time_aw(a) for o, a in zip(os_, outs["a"], strict=True)]
        extra = statistics.mean(diffs)
        made = [late_aw(a) - late_aw(o) for o, a in zip(os_, outs["a"], strict=True)]
        extra_wait = statistics.mean(w - wa for w, wa in zip(waits[p], waits["a"], strict=True))
        margin = extra * per_win
        res[p] = {
            "name": NAMES[p],
            "on_time_mean": round(statistics.mean(counts), 1),
            "on_time_range": [min(counts), max(counts)],
            "extra_awarded_on_time_mean": round(extra, 1),
            "extra_awarded_on_time_range": [min(diffs), max(diffs)],
            "late_awarded_mean": round(statistics.mean(late_aw(o) for o in os_), 1),
            "late_made_on_time_mean": round(statistics.mean(made), 1),
            "late_made_on_time_share": round(
                statistics.mean(m / late_aw(a) if late_aw(a) else 0.0 for m, a in zip(made, outs["a"], strict=True)),
                3,
            ),
            "expected_extra_wins_window": round(extra * rate, 1),
            "margin_window": money(margin),
            "margin_window_range": [money(x * per_win) for x in (min(diffs), max(diffs))],
            "margin_per_month": money(margin / months),
            "requote_extra_wait_days": round(extra_wait),
            "requote_delay_cost_window": money(extra_wait * REQUOTE_DAY_COST),
            "net_margin_window": money(margin - extra_wait * REQUOTE_DAY_COST),
            "net_margin_per_month": money((margin - extra_wait * REQUOTE_DAY_COST) / months),
            "break_even_requote_day_cost": round(margin / extra_wait) if extra_wait > 0 else None,
            "declined_mean": round(statistics.mean(len(o.declined) for o in os_), 1),
            "flagged_mean": round(statistics.mean(len(o.flagged) for o in os_), 1),
            "removed_mean": round(statistics.mean(len(o.removed) for o in os_), 1),
            "removed_on_time_under_a_mean": round(
                statistics.mean(
                    sum(oa.sent[i] is not None and oa.sent[i] <= truth[i].decision for i in o.removed)
                    for oa, o in zip(outs["a"], os_, strict=True)
                ),
                1,
            ),
            "helper_days_mean": round(statistics.mean(o.helper_days for o in os_), 1),
            "requote_median_wait_days": round(statistics.mean(requote_wait(o, received) for o in os_), 1),
        }
    for p in ("b", "b-old", "c"):
        dd = [on_time_aw(x) - on_time_aw(y) for x, y in zip(outs[p], outs["d"], strict=True)]
        res[p]["extra_vs_d_mean"] = round(statistics.mean(dd), 1)
        res[p]["extra_vs_d_range"] = [min(dd), max(dd)]
        res[p]["margin_vs_d_window"] = money(statistics.mean(dd) * per_win)
    kf_scale, kf_fit = calibrate(requests, capacity, truth, seeds, key_first=True)
    kf = [replay(rs, capacity, "a", kf_scale, key_first=True) for rs in draws]
    real_helpers = sum(int(r["helper_quotes"] or 0) > 0 for r in all_rows(folder, "capacity.csv"))
    real_requote_wait = statistics.median(
        (truth[r.id].sent - r.received).days for r in requests if r.requote and truth[r.id].sent
    )
    return {
        "model": "a counterfactual model of the quoting queue, not a measurement",
        "window": [start.isoformat(), end.isoformat()],
        "months": round(months, 2),
        "lost_late_in_records": sum(t.outcome == "lost late" for t in truth.values()),
        "no_award_rfqs": sum(t.outcome == "no award" for t in truth.values()),
        "new_rfqs": sum(not r.requote for r in requests),
        "requotes": sum(r.requote for r in requests),
        "in_queue_on_start": sum(r.at_start for r in requests),
        "seeds": seeds,
        "calibration": {
            "factor": scale,
            "actual_on_time": target,
            "model_a_on_time": round(fitted, 1),
            "gap": round(fitted - target, 1),
            "gap_share": round((fitted - target) / target, 4) if target else 0.0,
            "within_tolerance": abs(fitted - target) <= CALIBRATION_TOLERANCE * target,
            "actual_helper_days": real_helpers,
            "actual_requote_median_wait_days": real_requote_wait,
            "key_first_variant": {
                "factor": kf_scale,
                "on_time": round(kf_fit, 1),
                "helper_days_mean": round(statistics.mean(o.helper_days for o in kf), 1),
                "declined_mean": round(statistics.mean(len(o.declined) for o in kf), 1),
            },
        },
        "parameters": {
            "typing_minutes_per_new_rfq": typing_minutes,
            "revenue_per_win": REVENUE_PER_WIN,
            "margin": MARGIN,
            "requote_day_cost": REQUOTE_DAY_COST,
            "win_rate_on_time": {"rate": round(rate, 4), "won": won, "lost_on_price": lost},
        },
        "policies": res,
    }


def _rng(x, signed: bool = False) -> str:
    return f"{x[0]:+d} to {x[1]:+d}" if signed else f"{x[0]} to {x[1]}"


def report(res: dict) -> str:
    cal, par, pol = res["calibration"], res["parameters"], res["policies"]
    kf, w = cal["key_first_variant"], par["win_rate_on_time"]
    a = pol["a"]
    lines = [
        "# Queue replay: a model, not a measurement",
        "",
        f"Every request Wendlow's estimators had to price from {res['window'][0]} to {res['window'][1]}: "
        f"{res['new_rfqs']} new-part RFQs and {res['requotes']} annual re-quotes ({res['in_queue_on_start']} already in"
        " the queue on the first morning; screened-out RFQs left out), replayed day by day five ways, "
        f"{res['seeds']} times each with the simulation's noise drawn (the same draws for every policy). The model is "
        "described at the top of `replay_queue.py`.",
        "",
        f"**Calibration.** One factor on every request's expected quoting hours, fitted on Wendlow's own rule (a) "
        f"only: **{cal['factor']:g}**. With it, the model of (a) gets {cal['model_a_on_time']:g} quotes out on time on "
        f"average, against {cal['actual_on_time']} in the records ({cal['gap']:+g}, {cal['gap_share']:+.1%}: "
        f"{'within' if cal['within_tolerance'] else '**outside**'} 2%). Every other policy runs with the same factor: "
        f"the model is tuned to the status quo, never to the tool. It brings in helpers on {a['helper_days_mean']:g} "
        f"days on average (the records show helpers' quotes on {cal['actual_helper_days']}), and re-quotes wait a "
        f"median {a['requote_median_wait_days']:g} days (the records: {cal['actual_requote_median_wait_days']:g}).",
        "",
        "**Why first in, first out for (a).** Calibrated the same way with each new key-account RFQ to the front (the "
        f"design's rule, and the simulation's code), the factor would be {kf['factor']:g}, with helpers on "
        f"{kf['helper_days_mean']:g} days and {kf['declined_mean']:g} RFQs declined that were in fact quoted. In the "
        "records no request was ever quoted before one received earlier, key accounts' included.",
        "",
        f'Value counts only RFQs a buyer awarded to someone: the {res["no_award_rfqs"]} "no award" RFQs (cancelled '
        f"projects) are left out of it. In the records, {res['lost_late_in_records']} RFQs were really lost late.",
        "",
        "| Policy | On time (mean; lowest to highest seed) | Late quotes made on time (share of (a)'s) | Margin in "
        "the window (seed range) | Per month of window | Re-quotes' extra wait, working days | Net of re-quote "
        "delay, window | Net, per month |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in POLICIES:
        x = pol[p]
        if p == "a":
            lines.append(
                f"| {x['name']} | {x['on_time_mean']:g} ({_rng(x['on_time_range'])}) | ({x['late_awarded_mean']:g} "
                f"late, awarded RFQs) | | | | | |"
            )
            continue
        lines.append(
            f"| {x['name']} | {x['on_time_mean']:g} ({_rng(x['on_time_range'])}) | {x['late_made_on_time_mean']:g} "
            f"({x['late_made_on_time_share']:.0%}) | ${x['margin_window']:,} (${x['margin_window_range'][0]:,} to "
            f"${x['margin_window_range'][1]:,}) | ${x['margin_per_month']:,} | {x['requote_extra_wait_days']:+,} | "
            f"${x['net_margin_window']:,} | ${x['net_margin_per_month']:,} |"
        )
    b, old = pol["b"], pol["b-old"]
    lines += [
        "",
        "Net of re-quote delay: each working day a re-quote waits longer than under (a), its part's repeat orders go "
        f"out at the old price, about ${par['requote_day_cost']:g} a day from Wendlow's records (re-quotes sent "
        "2022-23: 13.9% higher prices on about $13,400 a year of repeat revenue per part). At $0 a day, the net is the "
        "margin column. The (d) rule's case depends on re-quotes waiting being cheap: its gain is gone at about "
        f"${pol['d']['break_even_requote_day_cost'] or 0:,} per re-quote per working day of extra wait.",
        "",
        f"- **The tool's own part, over the process change (d):** (b) {b['extra_vs_d_mean']:+g} awarded RFQs on time "
        f"({_rng(b['extra_vs_d_range'], True)}), about ${b['margin_vs_d_window']:,} in the window; (c) "
        f"{pol['c']['extra_vs_d_mean']:+g} ({_rng(pol['c']['extra_vs_d_range'], True)}), about "
        f"${pol['c']['margin_vs_d_window']:,}.",
        f"- **(b)'s flags:** {b['flagged_mean']:g} requests on average are flagged at risk at some point (ask the "
        "buyer for more time); none is taken out.",
        f"- **(b-old)'s removal:** {old['removed_mean']:g} requests taken out on average, "
        f"{old['removed_on_time_under_a_mean']:g} of which Wendlow's own order got out on time: the tool judges "
        "them on stated or default due dates, not on when the buyer really decides.",
        f"- **Declined** under (a): {a['declined_mean']:g} on average; under (d): {pol['d']['declined_mean']:g}. "
        f"Re-quotes' median wait: (a) {a['requote_median_wait_days']:g} days, "
        f"(d) {pol['d']['requote_median_wait_days']:g}, "
        f"(b) {b['requote_median_wait_days']:g}, (c) {pol['c']['requote_median_wait_days']:g}.",
        "",
        "Parameters (labelled estimates, not results):",
        "",
        f"- **Typing saved (c):** {par['typing_minutes_per_new_rfq']:g} minutes per new RFQ, an estimate of the time "
        "to retype part numbers, revisions, quantities and dates. `--typing-minutes` changes it.",
        f"- **Win rate:** {w['rate']:.1%}, on-time new-part quotes in this window's records ({w['won']} won of "
        f"{w['won'] + w['lost_on_price']} won or lost on price). A quote made on time is assumed to win at this "
        "average rate.",
        f"- **First-year revenue per win:** ${par['revenue_per_win']:,}, from Wendlow's records for won new-part "
        "quotes in 2022-23.",
        f"- **Margin:** {par['margin']:.0%}, the middle of the published 22-31% range for job shops (Wendlow's own "
        "books run higher).",
        f"- **Re-quote delay:** ${par['requote_day_cost']:g} per re-quote per working day of extra wait (above).",
        f"- **Per window, not per year.** This window is {res['months']:g} months of an estimator vacancy. Wendlow "
        "had two such windows in the decade's last four years (2021 and 2024), and in normal months almost nothing is "
        "lost late, so a window's value isn't a yearly one.",
        "- **The stated due dates are an assumption:** a labelled noise rule in the generator (most at or just before "
        "the decision, some padded early, some after it), not observed buyer behaviour.",
        "",
        "In the simulation about 1 in 20 re-quoted parts is re-sourced, late or not, which the model doesn't charge "
        "for. The decision dates are the simulation's truth: no real shop has them, which is why this is a replay of a "
        "simulation and not a forecast for yours.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Replay Wendlow's quoting queue five ways (a model, not a measurement).")
    p.add_argument("--data", type=Path, default=DATA, help="folder with rfqs.csv and capacity.csv")
    p.add_argument("--out", type=Path, default=Path("out") / "replay", help="folder for replay.md and replay.json")
    p.add_argument("--typing-minutes", type=float, default=TYPING_MINUTES, help="(c): minutes saved per new RFQ")
    p.add_argument("--seeds", type=int, default=SEEDS, help="draws of the simulation's noise")
    args = p.parse_args()
    res = run(args.data, args.typing_minutes, args.seeds)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "replay.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    (args.out / "replay.md").write_text(report(res), encoding="utf-8")
    print(f"  wrote {args.out / 'replay.md'}\n  wrote {args.out / 'replay.json'}")
    cal, pol = res["calibration"], res["policies"]
    print(
        f"A model, not a measurement. {res['window'][0]} to {res['window'][1]}. Calibration factor {cal['factor']:g}: "
        f"(a) {cal['model_a_on_time']:g} on time against {cal['actual_on_time']} actual ({cal['gap_share']:+.1%}). "
        + "; ".join(f"{p} {pol[p]['on_time_mean']:g}" for p in POLICIES)
        + "."
    )


if __name__ == "__main__":
    main()
