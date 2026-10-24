"""The quote desk's history: for each repeat part, a brief from the records (the last quote, how the last jobs ran)
and whether it's fast-track; for each customer, bid odds from its record. Code only, no AI.

Reads two optional exports from the ERP, alongside the others in records/:
    quote-history.csv  customer_id, part_number, quote_id, kind (new or requote), sent_on, quantity, unit_price,
                       est_hours, status (won, lost, expired, no award, open), status_date
    job-history.csv    customer_id, part_number, job_id, completed_on, quantity, est_hours, actual_hours

Nothing from after the day a request arrives is used.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# The rules (the estimating lead owns these; plan.md, open question 4).
YEARS = 3  # history counted: the three years before the request
FAST_TRACK = 0.25  # a fast-track part is quoted in a quarter of the time: check the brief, update the price. `Assume`
PULL = 5  # a customer's record is pulled toward the shop's by this many quotes
LOW_SHARE = 0.6  # bid odds below 60% of the shop's are low ...
LOW_MIN = 8  # ... once the customer has at least this many closed new-part quotes
CLOSED = ("won", "lost", "expired", "no award")


def _squash(s: str) -> str:
    return "".join(ch for ch in str(s).upper() if ch.isalnum())


def _d(s: str) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def _f(s: str) -> float | None:
    try:
        return float(s) if s not in ("", None) else None
    except ValueError:
        return None


@dataclass
class Quote:
    sent: date
    kind: str
    quantity: int | None
    price: float | None
    status: str
    status_date: date | None


@dataclass
class Job:
    completed: date
    est: float | None
    actual: float | None


@dataclass
class History:
    quotes: dict[tuple[str, str], list[Quote]] = field(default_factory=lambda: defaultdict(list))
    jobs: dict[tuple[str, str], list[Job]] = field(default_factory=lambda: defaultdict(list))
    new_by_customer: dict[str, list[Quote]] = field(default_factory=lambda: defaultdict(list))

    @classmethod
    def load(cls, folder: Path) -> History:
        h = cls()
        q, j = folder / "quote-history.csv", folder / "job-history.csv"
        if q.exists():
            with q.open(newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    sent = _d(r["sent_on"])
                    if not sent:
                        continue
                    qt = Quote(
                        sent,
                        r["kind"],
                        int(_f(r["quantity"]) or 0) or None,
                        _f(r["unit_price"]),
                        r["status"],
                        _d(r["status_date"]),
                    )
                    h.quotes[(str(r["customer_id"]), _squash(r["part_number"]))].append(qt)
                    if r["kind"] == "new":
                        h.new_by_customer[str(r["customer_id"])].append(qt)
        if j.exists():
            with j.open(newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    done = _d(r["completed_on"])
                    if done:
                        h.jobs[(str(r["customer_id"]), _squash(r["part_number"]))].append(
                            Job(done, _f(r["est_hours"]), _f(r["actual_hours"]))
                        )
        return h

    def closed_new(self, customer: str | None, as_of: date) -> list[Quote]:
        lo = as_of - timedelta(days=365 * YEARS)
        rows = (
            self.new_by_customer.get(customer, [])
            if customer is not None
            else [q for qs in self.new_by_customer.values() for q in qs]
        )
        return [q for q in rows if q.status in CLOSED and q.status_date and q.status_date < as_of and q.sent >= lo]

    def shop_rate(self, as_of: date) -> float:
        rows = self.closed_new(None, as_of)
        return sum(q.status == "won" for q in rows) / len(rows) if rows else 0.4


@dataclass
class Brief:
    as_of: date
    quotes: int = 0
    won: int = 0
    last_quoted: date | None = None
    last_quantity: int | None = None
    last_price: float | None = None
    last_status: str = ""
    jobs: int = 0
    actual_over_estimate: float | None = None

    def text(self) -> str:
        if not self.quotes:
            return "no quotes on file"
        bits = [
            f"last quoted {self.last_quoted}: {self.last_quantity} at ${self.last_price:,.2f} ({self.last_status})"
            if self.last_price is not None
            else f"last quoted {self.last_quoted} ({self.last_status})",
            f"{self.won} of {self.quotes} quotes won",
        ]
        if self.jobs:
            bits.append(
                f"{self.jobs} jobs, actual hours {self.actual_over_estimate:.0%} of estimate"
                if self.actual_over_estimate is not None
                else f"{self.jobs} jobs"
            )
        return "; ".join(bits)


def brief(h: History, customer: str, part: str, as_of: date) -> Brief:
    """What the records say about this customer's part, as of the day the request arrived."""
    key = (str(customer), _squash(part))
    b = Brief(as_of)
    qs = sorted((q for q in h.quotes.get(key, []) if q.sent < as_of), key=lambda q: q.sent)
    if qs:
        last = qs[-1]
        b.quotes, b.won = len(qs), sum(q.status == "won" and q.status_date and q.status_date < as_of for q in qs)
        b.last_quoted, b.last_quantity, b.last_price = last.sent, last.quantity, last.price
        b.last_status = last.status if last.status_date and last.status_date < as_of else "open"
    js = [j for j in h.jobs.get(key, []) if j.completed < as_of]
    b.jobs = len(js)
    est = sum(j.est for j in js if j.est and j.actual)
    act = sum(j.actual for j in js if j.est and j.actual)
    b.actual_over_estimate = act / est if est else None
    return b


def fast_track(b: Brief, status: str) -> bool:
    """A repeat part at the same revision, quoted in the last three years, with a job behind it: the estimator checks
    the brief and updates the price."""
    return (
        status == "repeat"
        and b.last_quoted is not None
        and (b.as_of - b.last_quoted).days <= 365 * YEARS
        and b.jobs >= 1
    )


@dataclass
class Odds:
    rate: float
    closed: int
    won: int
    low: bool

    def text(self) -> str:
        return f"{self.won} of {self.closed} new-part quotes won in three years; odds {self.rate:.0%}" + (
            " (low)" if self.low else ""
        )


def odds(h: History, customer: str | None, as_of: date) -> Odds:
    """The share of this customer's new-part quotes won in the three years before, pulled toward the shop's rate."""
    shop = h.shop_rate(as_of)
    rows = h.closed_new(str(customer), as_of) if customer is not None else []
    won = sum(q.status == "won" for q in rows)
    rate = round((won + PULL * shop) / (len(rows) + PULL), 3)
    return Odds(rate, len(rows), won, len(rows) >= LOW_MIN and rate < LOW_SHARE * shop)


def desk_hours(hours: float, fast: bool) -> float:
    return hours * FAST_TRACK if fast else hours
