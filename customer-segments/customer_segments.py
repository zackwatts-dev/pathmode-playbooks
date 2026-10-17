"""Customer segments: group customers by how they actually behave, list who's likely to pay late, and say why.

    python customer-segments/customer_segments.py --sample --dry-run
    python customer-segments/customer_segments.py --sample --replay customer-segments/sample-data/recorded-run.json

Machine learning does the finding; the AI does the explaining.
- Features are built from two years of activity up to a cutoff date, and nothing after it, for customers who existed
  at the cutoff: spend and its trend, jobs, repeat visits, slow jobs, days late on invoices due in the last 12 months
  (unpaid ones count by the days since due), whether and how often they approve quotes, agreements. A value a
  customer doesn't have (no decided quotes: no approval rate) stays empty, never a made-up default.
- k-means groups customers into segments. The number of segments is chosen by how well they separate
  (the silhouette score), not by hand.
- Two questions are tested, each against a one-line rule on customers the model never saw: "who'll pay more
  than 20 days late next year?" and "who'll leave next year?". The verdict is the model, the rule, or "not
  predictable".
- The late-payment list ranks everyone with whichever method won, by a score for ranking (not a probability). With
  an answer key, a model's scores come from cross-validation, so no customer is scored by a model that saw their
  outcome. Without one, the model learns from history: features as they stood a year before the cutoff, and what
  happened in the year after. If the verdict is "not predictable" or "not enough examples", nobody is listed.
- The leaving question is only tested and reported. Nobody is listed or scored for it.
- The AI names each segment and suggests how to treat it, and explains each customer on the late-payment list,
  using only the numbers it's given. Code checks every number and what kind it is, and every "higher", "faster" or
  "slow-paying" against the data. Words that fail go to a person and aren't shown as ready.

Writes, for the team: out/dashboard.html, out/segments.csv, out/customers.csv (no late-payment measure),
out/review-queue.csv, out/runs.csv and, with an answer key (the sample), out/score.md. For billing only, in
out/billing/: dashboard-billing.html, customers.csv (with days late), late-payment-list.csv, late-scores.csv and
review-queue.csv. Nothing is sent or
changed.
"""

from __future__ import annotations

import calendar
import csv
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.evidence import NUMBER, to_float, unsupported_numbers  # noqa: E402
from common.util import BadAnswer, done, model_for, parse_json, parser, read_csv, write_csv, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"
SAMPLE_CUTOFF = date(2024, 12, 31)
SEED = 7

FEATURES = [
    ("spend", "Spend in the last 12 months ($)"),
    ("trend", "Share of the year's spend in the last 6 months"),
    ("jobs_per_site", "Jobs per site in the last 12 months"),
    ("repair_share", "Share of jobs that were repairs"),
    ("repeat_share", "Share of repairs followed by another within 30 days"),
    ("slow_share", "Share of jobs open more than 21 days"),
    ("days_since_job", "Days since their last job"),
    ("pays_late", "Days late on invoices due in the last 12 months, on average (unpaid: days since due)"),
    ("has_quotes", "Has decided quotes (1 yes, 0 no)"),
    ("approves", "Share of decided quotes they approved"),
    ("decides_days", "Days to decide on a quote"),
    ("agreement", "Sites under agreement (share)"),
    ("sites", "Sites"),
    ("years", "Years as a customer"),
]
SEGMENT_FEATURES = [
    "spend",
    "jobs_per_site",
    "repair_share",
    "pays_late",
    "has_quotes",
    "approves",
    "decides_days",
    "agreement",
    "sites",
]


def d(s: str) -> date | None:
    return date.fromisoformat(s[:10]) if s else None


def months_before(day: date, months: int) -> date:
    """The same day some months earlier. A day the earlier month doesn't have (Feb 29, Aug 31) becomes its last."""
    y, m = divmod(day.year * 12 + day.month - 1 - months, 12)
    return date(y, m + 1, min(day.day, calendar.monthrange(y, m + 1)[1]))


# --- features (only data on or before the cutoff) ----------------------------------------------------------


# Why a feature can have no value. A customer with no decided quotes has no approval rate: it's left out of every
# average and shown as n/a, never filled in with a made-up number.
NO_VALUE = {
    "trend": "no spend in the last 12 months",
    "repair_share": "no jobs in the last 12 months",
    "repeat_share": "no repairs in the last 12 months",
    "slow_share": "no jobs in the last 12 months",
    "pays_late": "no invoices due in the last 12 months",
    "approves": "no decided quotes",
    "decides_days": "no decided quotes",
}


@dataclass
class Customer:
    id: str
    name: str
    segment: str
    branch: str
    x: dict = field(default_factory=dict)
    cluster: int = -1
    late_score: float = 0.0  # for ranking who may pay more than 20 days late next year; not a probability
    reasons: list[tuple[str, float]] = field(default_factory=list)
    explanation: dict | None = None
    problems: list[str] = field(default_factory=list)


def money(s: str) -> float:
    """An amount as exports write it: "1225.42", "$1,225.42", "(12.50)" for a credit. Anything else raises."""
    t = s.replace("$", "").replace(",", "").replace(" ", "")
    negative = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    return 0.0 if not t else (-1 if negative else 1) * float(t)


def days_late(invoices: dict[str, tuple[str, date]], paid: dict[str, list[date]], start: date, end: date) -> dict:
    """Days late for every invoice due after `start` and by `end`, per customer. An invoice still unpaid at `end`
    counts as late by the days since it was due, so the worst payers aren't the ones left out."""
    late = defaultdict(list)
    for inv, (cid, due) in invoices.items():
        if due and start < due <= end:
            late[cid] += [max(0, (p - due).days) for p in paid.get(inv, [])] or [max(0, (end - due).days)]
    return late


def build_features(folder: Path, cutoff: date, problems: list[dict] | None = None) -> dict[str, Customer]:
    """One row of features per customer who existed at the cutoff, from exports, never looking past the cutoff.

    Exports are taken later than the cutoff, so a row can carry what happened afterwards: a job completed in
    January, a quote decided in January, a site added in March. Only events dated on or before the cutoff count:
    a job completed after it was still open, a quote decided after it was still undecided. A row that can't be read
    (an unreadable amount, a decided quote with no decision date) is left out and listed in `problems`."""
    problems = [] if problems is None else problems

    def upto(rows, col):
        return [r for r in rows if d(r[col]) and d(r[col]) <= cutoff]

    def on_time(s: str) -> date | None:
        when = d(s)
        return when if when and when <= cutoff else None

    rows = read_csv(folder / "customers.csv")
    # A customer who joined after the cutoff wasn't a customer at the cutoff.
    custs = {
        r["Customer ID"]: Customer(r["Customer ID"], r["Name"], r["Segment"], r["Branch"])
        for r in rows
        if not d(r["Since"]) or d(r["Since"]) <= cutoff
    }
    since = {r["Customer ID"]: d(r["Since"]) for r in rows}
    # The last 12 months, and their second half for the trend, counted back from whatever the cutoff is.
    year_ago, half_ago = months_before(cutoff, 12), months_before(cutoff, 6)
    jobs = defaultdict(list)
    for r in upto(read_csv(folder / "jobs.csv"), "Created"):
        jobs[r["Customer ID"]].append(r)
    covered, started = defaultdict(set), set()
    for r in upto(read_csv(folder / "agreements.csv"), "Start"):
        started.add(r["Site ID"])
        if not r["End"] or d(r["End"]) > cutoff:
            covered[r["Customer ID"]].add(r["Site ID"])
    sites = defaultdict(set)
    site_rows = read_csv(folder / "sites.csv")
    dated = next((k for k in ("Added", "Created", "Since", "Start") if site_rows and k in site_rows[0]), None)
    # Sites carry no date in most exports. A site counts once something dated shows it existed: a job or an
    # agreement on or before the cutoff (or its own date, when the export has one).
    active = {j["Site ID"] for js in jobs.values() for j in js} | started
    for r in site_rows:
        own = d(r[dated]) if dated else None
        if (own <= cutoff) if own else r["Site ID"] in active:
            sites[r["Customer ID"]].add(r["Site ID"])
    spend, recent = defaultdict(float), defaultdict(float)
    due = {}
    for r in upto(read_csv(folder / "invoices.csv"), "Date"):
        try:
            when, amt = d(r["Date"]), money(r["Amount"])
        except ValueError:
            problems.append(
                {"which": f"invoice {r['Invoice']}", "why": f"amount {r['Amount']!r} can't be read; left out"}
            )
            continue
        if when > year_ago:
            spend[r["Customer ID"]] += amt
            if when > half_ago:
                recent[r["Customer ID"]] += amt
        due[r["Invoice"]] = (r["Customer ID"], d(r["Due"]))
    paid = defaultdict(list)
    for r in upto(read_csv(folder / "payments.csv"), "Paid"):
        paid[r["Invoice"]].append(d(r["Paid"]))
    # "Paid late in the last 12 months": invoices due in those months, paid or still unpaid at the cutoff.
    late = days_late(due, paid, year_ago, cutoff)
    quotes = defaultdict(list)
    for r in upto(read_csv(folder / "quotes.csv"), "Sent"):
        if r["Status"] in ("Accepted", "Declined") and not d(r["Decided"]):
            problems.append({"which": f"quote {r['Quote']}", "why": f"{r['Status']} with no decision date; left out"})
            continue
        quotes[r["Customer ID"]].append(r)
    for cid, c in custs.items():
        js = jobs[cid]
        last_year = [j for j in js if d(j["Created"]) > year_ago]
        repairs = [j for j in last_year if j["Type"] == "repair"]
        by_unit = defaultdict(list)
        for j in sorted(js, key=lambda j: j["Created"]):
            if j["Type"] == "repair" and j["Equipment ID"]:
                by_unit[j["Equipment ID"]].append(d(j["Created"]))
        repeats = sum(
            1
            for dates in by_unit.values()
            for a, b in zip(dates, dates[1:], strict=False)
            if (b - a).days <= 30 and b > year_ago
        )
        slow = sum(1 for j in last_year if on_time(j["Completed"]) and (d(j["Completed"]) - d(j["Created"])).days > 21)
        # Decided as of the cutoff: a quote decided later was still waiting then.
        decided = [q for q in quotes[cid] if q["Status"] in ("Accepted", "Declined") and on_time(q["Decided"])]
        n_sites = max(1, len(sites[cid]))
        c.x = {
            "spend": round(spend[cid], 2),
            "trend": round(recent[cid] / spend[cid], 2) if spend[cid] else None,
            "jobs_per_site": round(len(last_year) / n_sites, 2),
            "repair_share": round(len(repairs) / len(last_year), 2) if last_year else None,
            "repeat_share": round(repeats / len(repairs), 2) if repairs else None,
            "slow_share": round(slow / len(last_year), 2) if last_year else None,
            "days_since_job": (cutoff - max(d(j["Created"]) for j in js)).days if js else 730,
            "pays_late": round(mean(late[cid]), 1) if late[cid] else None,
            "has_quotes": 1 if decided else 0,
            "approves": round(sum(q["Status"] == "Accepted" for q in decided) / len(decided), 2) if decided else None,
            "decides_days": round(mean((d(q["Decided"]) - d(q["Sent"])).days for q in decided), 1) if decided else None,
            "agreement": round(len(covered[cid] & sites[cid]) / n_sites, 2),
            "sites": n_sites,
            "years": round((cutoff - since[cid]).days / 365.25, 1) if since.get(cid) else 0.0,
        }
    return custs


def fill_values(custs: list[Customer], names: list[str]) -> dict[str, float]:
    """What a model uses where a customer has no value: the average of those who have one. That keeps them neutral
    on that feature; the "has quotes" indicator says who had none, so the model never mistakes it for a fact."""
    out = {}
    for n in names:
        vals = [c.x[n] for c in custs if c.x[n] is not None]
        out[n] = mean(vals) if vals else 0.0
    return out


def matrix(custs: list[Customer], names: list[str], fill: dict | None = None) -> list[list[float]]:
    """Features as numbers a model can use: money and counts on a log scale, so a few giants don't dominate."""
    logged = {"spend", "jobs_per_site", "days_since_job", "decides_days", "sites"}
    fill = fill or fill_values(custs, names)

    def num(c, n):
        v = fill[n] if c.x[n] is None else c.x[n]
        return math.log1p(max(0.0, v)) if n in logged else float(v)

    return [[num(c, n) for n in names] for c in custs]


# --- the machine learning ---------------------------------------------------------------------------------


def segment(custs: list[Customer], ks=range(3, 8)) -> dict:
    """k-means, with the number of segments chosen by silhouette score."""
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    x = StandardScaler().fit_transform(matrix(custs, SEGMENT_FEATURES))
    tried = {}
    for k in ks:
        labels = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(x)
        tried[k] = round(float(silhouette_score(x, labels, random_state=SEED)), 3)
    best = max(tried, key=tried.get)
    labels = KMeans(n_clusters=best, n_init=10, random_state=SEED).fit_predict(x)
    for c, label in zip(custs, labels, strict=True):
        c.cluster = int(label)
    points = PCA(n_components=2, random_state=SEED).fit_transform(x)
    return {"k": best, "silhouette": tried, "points": [(float(a), float(b)) for a, b in points]}


def profiles(custs: list[Customer]) -> list[dict]:
    out = []
    for k in sorted({c.cluster for c in custs}):
        members = [c for c in custs if c.cluster == k]
        p = {
            "segment": k,
            "customers": len(members),
            "kinds": {s: sum(c.segment == s for c in members) for s in sorted({c.segment for c in members})},
        }
        # Averages over the customers who have the value, with how many that is: no made-up defaults.
        p["n"] = {}
        for name, _ in FEATURES:
            vals = [c.x[name] for c in members if c.x[name] is not None]
            p[name] = round(mean(vals), 2) if vals else None
            p["n"][name] = len(vals)
        out.append(p)
    return out


def overall_profile(profs: list[dict]) -> dict:
    """Averages for all customers, from the segments' averages and counts (customers without a value left out)."""
    out = {}
    for name, _ in FEATURES:
        with_value = [(p[name], p["n"][name]) for p in profs if p[name] is not None]
        n = sum(k for _, k in with_value)
        out[name] = round(sum(v * k for v, k in with_value) / n, 2) if n else None
    return out


def shown(p: dict) -> dict:
    """A segment as the AI sees it: averages, and how many customers had no value for each (and why)."""
    data = {k: p[k] for k in ("segment", "customers", "kinds")}
    data.update({name: "n/a" if p[name] is None else p[name] for name, _ in FEATURES})
    missing = {
        name: f"{p['customers'] - p['n'][name]} n/a ({NO_VALUE[name]})"
        for name in NO_VALUE
        if p["n"][name] < p["customers"]
    }
    if missing:
        data["customers left out of an average (no value)"] = missing
    return data


NAMES = [n for n, _ in FEATURES]
MIN_EXAMPLES = 10  # fewer customers than this with either outcome, and there's nothing to test a prediction on
NOT_ENOUGH = "not enough examples in the records to test it"
NOT_PREDICTABLE = "not predictable from these records"
USE_RULE = "use the rule: it's as good, and anyone can check it"
USE_MODEL = "use the model"


def new_model():
    """The one model every prediction uses: scaled features into a logistic regression."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=3000))


def rule_score(c: Customer) -> float:
    """The one-line rule as a score for ranking, not a probability: days late on invoices due in the last 12 months,
    out of 60 (capped at 1). No invoices due, nothing to go on: 0."""
    return round(min(1.0, (c.x["pays_late"] or 0.0) / 60), 3)


def evaluate(custs: list[Customer], labels: dict[str, int], baseline: str, top_n: int = 25) -> dict:
    """Train on 70% of customers, test on the other 30%, and compare with a one-line rule on the same 30%."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    known = [c for c in custs if c.id in labels]
    x, y = matrix(known, NAMES, fill_values(known, NAMES)), [labels[c.id] for c in known]
    examples = {"known": known, "y": y}
    if min(sum(y), len(y) - sum(y)) < MIN_EXAMPLES:
        empty = dict.fromkeys(["model_auc", "rule_auc", "model_hits", "rule_hits", "base_hits"])
        return {
            "test": 0,
            "positives": int(sum(y)),
            **empty,
            "top": top_n,
            "baseline": baseline,
            "verdict": NOT_ENOUGH,
            **examples,
        }
    xtr, xte, ytr, yte, _, cte = train_test_split(x, y, known, test_size=0.3, stratify=y, random_state=SEED)
    model = new_model().fit(xtr, ytr)
    p_model = model.predict_proba(xte)[:, 1]
    p_rule = [c.x[baseline] or 0.0 for c in cte]  # no value, nothing to go on

    def top_hits(scores):
        order = sorted(range(len(yte)), key=lambda i: -scores[i])[:top_n]
        return sum(yte[i] for i in order)

    m_auc, r_auc = float(roc_auc_score(yte, p_model)), float(roc_auc_score(yte, p_rule))
    m_hits, r_hits = top_hits(list(p_model)), top_hits(p_rule)
    if max(m_auc, r_auc) < 0.65:
        verdict = NOT_PREDICTABLE
    elif r_auc >= m_auc - 0.01 and r_hits >= m_hits:
        verdict = USE_RULE
    else:
        verdict = USE_MODEL
    return {
        "test": len(yte),
        "positives": int(sum(yte)),
        "model_auc": round(m_auc, 3),
        "rule_auc": round(r_auc, 3),
        "model_hits": int(m_hits),
        "rule_hits": int(r_hits),
        "base_hits": round(sum(yte) / len(yte) * top_n, 1),
        "top": top_n,
        "baseline": baseline,
        "verdict": verdict,
        **examples,
    }


LATE = "Who will pay more than 20 days late next year?"
LEAVE = "Who will leave next year?"


def predictions(custs: list[Customer], folder: Path) -> dict:
    """Two questions, each tested against a simple rule, learned from the answer key: who'll pay late next year,
    and who'll leave. The customers learned from are the ones being scored, so the list is scored out-of-fold."""
    late = {r["Customer ID"]: int(r["Paid late (over 20 days)"]) for r in read_csv(folder / "answer-key-late-2025.csv")}
    left = {r["Customer ID"]: int(r["Left in 2025"]) for r in read_csv(folder / "answer-key-churn.csv")}
    how = {"learned_from": "the answer key", "out_of_fold": True}
    return {
        "late": {"question": LATE, **how, **evaluate(custs, late, "pays_late")},
        "churn": {"question": LEAVE, **how, **evaluate(custs, left, "days_since_job")},
    }


def predictions_from_history(folder: Path, cutoff: date) -> dict:
    """The same two questions, without an answer key: what a real company has. Features as they stood a year before
    the cutoff, and what happened in the year after, are last year's examples. Testing holds out 30% of them; the
    list then scores this year's features, which no model has seen."""
    back = months_before(cutoff, 12)
    past = list(build_features(folder, back).values())
    late, left = history_labels(folder, back, cutoff)
    how = {"learned_from": f"history (features to {back}, outcomes to {cutoff})", "out_of_fold": False}
    return {
        "late": {"question": LATE, **how, **evaluate(past, late, "pays_late")},
        "churn": {"question": LEAVE, **how, **evaluate(past, left, "days_since_job")},
    }


def history_labels(folder: Path, start: date, end: date) -> tuple[dict[str, int], dict[str, int]]:
    """What happened in the year after `start`, for customers who were customers by then.

    Paid late: invoices due in the year were paid more than 20 days late on average, as in the answer key. An invoice
    still unpaid at the end counts as late by the days since it was due, so the latest of the late payers aren't
    dropped. Left: active in the year before `start` (a job or an invoice), and no job or invoice in the year after.
    The records hold no "left" date, so that's the nearest they come."""
    since = {r["Customer ID"]: d(r["Since"]) for r in read_csv(folder / "customers.csv")}
    existed = {cid for cid, s in since.items() if not s or s <= start}
    before = months_before(start, 12)
    paid = defaultdict(list)
    for r in read_csv(folder / "payments.csv"):
        if d(r["Paid"]) and d(r["Paid"]) <= end:
            paid[r["Invoice"]].append(d(r["Paid"]))
    invoices, active_before, active_after = {}, set(), set()

    def active(cid, when):
        if when and before < when <= start:
            active_before.add(cid)
        elif when and start < when <= end:
            active_after.add(cid)

    for r in read_csv(folder / "invoices.csv"):
        active(r["Customer ID"], d(r["Date"]))
        if r["Customer ID"] in existed:
            invoices[r["Invoice"]] = (r["Customer ID"], d(r["Due"]))
    for r in read_csv(folder / "jobs.csv"):
        active(r["Customer ID"], d(r["Created"]))
    late = {cid: int(mean(v) > 20) for cid, v in days_late(invoices, paid, start, end).items()}
    left = {cid: int(cid not in active_after) for cid in active_before & existed}
    return late, left


def score_late(custs: list[Customer], test: dict) -> None:
    """Rank everyone by how likely they look to pay more than 20 days late next year, with the method that won the
    test, and say which features push each customer up. The score is for ranking: the rule's is days late out of 60,
    and the model's is weighted for the rarer outcome, so neither is a probability."""
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    known, y = test["known"], test["y"]
    use_model = test["verdict"] == USE_MODEL
    if len(set(y)) < 2:  # no outcomes to learn from: the rule, and its one reason
        for c in custs:
            c.late_score = rule_score(c)
            c.reasons = [("pays_late", c.x["pays_late"])] if (c.x["pays_late"] or 0) > 0 else []
        return
    # One set of fill-ins for customers with no value (from the labelled examples), for training and scoring alike.
    fill = fill_values(known, NAMES)
    # The reasons come from a model fit on every labelled example: they describe the pattern it learned. When the
    # model wins, the scores on the list never come from a model that saw that customer's outcome (below).
    model = new_model().fit(matrix(known, NAMES, fill), y)
    scores = dict(zip([c.id for c in custs], model.predict_proba(matrix(custs, NAMES, fill))[:, 1], strict=True))
    if use_model and test["out_of_fold"]:
        # Learned from the answer key, the labelled customers are the ones being scored: each is scored by a model
        # trained on the other four folds. Customers without a label weren't trained on, so the full model is fair.
        folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        oof = cross_val_predict(new_model(), matrix(known, NAMES, fill), y, cv=folds, method="predict_proba")[:, 1]
        scores.update(zip([c.id for c in known], oof, strict=True))
    # Learned from history, the model saw last year's features and outcomes, never this year's: it scores everyone.
    scaler, lr = model.named_steps["standardscaler"], model.named_steps["logisticregression"]
    for c, row in zip(custs, scaler.transform(matrix(custs, NAMES, fill)), strict=True):
        c.late_score = round(float(scores[c.id]), 3) if use_model else rule_score(c)
        contrib = sorted(((n, float(lr.coef_[0][i] * row[i])) for i, n in enumerate(NAMES)), key=lambda t: -t[1])
        c.reasons = [(n, round(v, 2)) for n, v in contrib[:3] if v > 0]


def makes_a_list(verdict: str) -> bool:
    """Only a tested method names anyone: "not predictable" or "not enough examples" means no list."""
    return verdict in (USE_RULE, USE_MODEL)


# --- the AI explains; code checks ----------------------------------------------------------------------------

NAME_SEGMENT = """You help a commercial HVAC contractor understand one segment of its customers, found by clustering.
From the segment's average numbers (and the same for all customers), answer with JSON only:
{"name": "a short, plain name for the segment (2 to 4 words)",
 "who": "one sentence: who these customers are and how they behave",
 "treat": ["two or three specific things the business should do for this segment"]}
Use only numbers that appear in the data. Don't invent causes. "n/a" means no value: an average leaves those out."""

EXPLAIN_LATE = """You help the billing team at a commercial HVAC contractor. This customer is high on the list of who
may pay more than 20 days late next year. From the customer's numbers and the top reasons, answer with JSON only:
{"why": "one or two plain sentences on what in the numbers points to late payment",
 "action": "one specific, respectful next step: for example terms, a deposit, reminders, or a call"}
Use only numbers that appear in the data. "n/a" means no value. It's a signal, not a verdict: say "may", not "will"."""

# The numbers the AI is shown, by what they measure, so "88 days" can't pass because 0.88 was a share somewhere.
MONEY = {"spend"}
SHARES = {"trend", "repair_share", "repeat_share", "slow_share", "has_quotes", "approves", "agreement"}
DAYS = {"pays_late", "decides_days", "days_since_job"}
YEARS = {"years"}
# Per-customer late-payment measures: next to a name, only billing sees them.
LATE_MEASURES = {"pays_late"}
# Numbers in the instructions and feature labels: "20 days late", "open more than 21 days", "within 30 days".
GIVEN = {"days": [20.0, 21.0, 30.0], "months": [12.0, 6.0], "any": [20.0, 21.0, 30.0, 12.0, 6.0]}


def allowed_numbers(rows: list[dict], extra: list[float] = ()) -> dict[str, list[float]]:
    """What each kind of number may be: money only a spend, days only a day count, percents only a share."""
    out = {kind: list(v) for kind, v in GIVEN.items()} | {"money": [], "percent": [], "years": []}
    for row in rows:
        for n, _ in FEATURES:
            v = row.get(n)
            if not isinstance(v, int | float):
                continue
            out["any"].append(float(v))
            if n in MONEY:
                out["money"].append(float(v))
            elif n in SHARES:
                out["percent"].append(v * 100)
                out["any"].append(v * 100)
            elif n in DAYS:
                out["days"].append(float(v))
            elif n in YEARS:
                out["years"].append(float(v))
    out["any"] += [float(v) for v in extra]
    return out


UNIT = re.compile(r"[\s-]*(days?|percent|per cent|years?|months?)\b", re.I)
KIND = {"day": "days", "days": "days", "percent": "percent", "per cent": "percent", "year": "years", "years": "years"}
KIND |= {"month": "months", "months": "months"}


def kind_of(text: str, m: re.Match) -> str | None:
    """What a number in the AI's words claims to be: money, a percent, days, years, a calendar year, or unknown."""
    token = m.group()
    if "$" in token:
        return "money"
    if token.endswith("%"):
        return "percent"
    if re.search(r"\bnet[\s-]*$", text[max(0, m.start() - 6) : m.start()], re.I):
        return "days"  # payment terms: "net 30"
    unit = UNIT.match(text, m.end())
    if unit:
        return KIND[unit.group(1).lower()]
    if re.fullmatch(r"(19|20)\d\d", token):
        return "calendar year"
    return None


def number_problems(text: str, allowed: dict[str, list[float]]) -> list[str]:
    """Every number must be one the AI was shown, and of the right kind: "$5k" must be a spend, "88 days" a day count,
    "40%" a share. A calendar year ("since 1999") is never in the data. Small counts (up to 10) pass, as everywhere."""
    out = []
    bad = list(dict.fromkeys(unsupported_numbers(text, allowed["any"], tolerance=0.02)))
    if bad:
        out.append(f"uses numbers not in the data ({', '.join(bad)})")
    wrong = []
    for m in NUMBER.finditer(text):
        kind, value = kind_of(text, m), to_float(m.group())
        if kind is None or m.group() in bad:
            continue
        if kind == "calendar year":
            wrong.append(f"{m.group()} (a year: the data has none)")
        elif kind in ("days", "years", "months") and value.is_integer() and abs(value) <= 10:
            continue
        elif not any(abs(value - a) <= max(abs(a) * 0.02, 0.051) for a in allowed[kind]):
            wrong.append(f"{m.group()} as {kind}")
    if wrong:
        out.append(f"uses numbers that aren't in the data as what they measure: {'; '.join(dict.fromkeys(wrong))}")
    return out


# Direction words, checked against the data: a segment called the "fastest payers" must pay faster than average.
UP = {"higher", "highest", "more", "most", "larger", "largest", "bigger", "biggest", "greater", "above", "heavier"}
DOWN = {"lower", "lowest", "less", "least", "fewer", "fewest", "smaller", "smallest", "below", "lighter"}
SLOWER = {"slower", "slowest", "later", "latest", "longer", "longest"}
FASTER = {"faster", "fastest", "quicker", "quickest", "sooner", "earlier", "shorter", "shortest"}
TOPICS = [
    (r"pa(?:y|ys|id|ying|yer|yers|yment|yments)", "pays_late"),
    (r"spen(?:d|ds|ding|t|der|ders)", "spend"),
    (r"repairs?", "repair_share"),
    (r"repeats?", "repeat_share"),
    (r"approv\w*|accept\w*", "approves"),
    (r"decid\w*|decisions?", "decides_days"),
    (r"agreements?|coverage|covered", "agreement"),
    (r"sites?|locations?", "sites"),
    (r"tenure", "years"),
    (r"jobs?|visits?", "jobs_per_site"),
]
# Phrases that point a direction without a comparative: "slow-paying", "prompt payers", "big spenders".
ADJECTIVES = [
    (r"\b(slow|late)[\s-]+pa(?:y|ying|yer|yers)\b", "pays_late", 1),
    (r"\b(fast|quick|prompt|early|timely|on-time)[\s-]+pa(?:y|ying|yer|yers)\b", "pays_late", -1),
    (r"\b(high|big|large|top|heavy)[\s-]+(?:spend\w*|value|revenue)\b", "spend", 1),
    (r"\b(low|small|light)[\s-]+(?:spend\w*|value|revenue)\b", "spend", -1),
]
HEDGES = {"likely", "chance", "risk", "able", "willing", "time"}  # "less likely to pay on time" isn't "pays less"


def claimed_directions(text: str) -> list[tuple[str, str, int]]:
    """(the words, the feature, +1 or -1) for each direction the text claims about a feature."""
    out = []
    for pattern, feature, sign in ADJECTIVES:
        out += [(m.group(), feature, sign) for m in re.finditer(pattern, text, re.I)]
    for clause in re.split(r"[.;,:()!?]|\b(?:but|while|whereas|vs|versus|although)\b", text.lower()):
        words = re.findall(r"[a-z]+(?:-[a-z]+)*|\d[\d.,]*", clause)  # "slow-paying" is one word, read by ADJECTIVES
        for i, w in enumerate(words):
            if w not in UP | DOWN | SLOWER | FASTER:
                continue
            if words[i + 1 : i + 2] == ["than"] and re.fullmatch(r"[\d.,]+", "".join(words[i + 2 : i + 3]) or "x"):
                continue  # "more than 20 days late" is a threshold, not a comparison
            near = words[i + 1 : i + 4] + words[max(0, i - 3) : i][::-1]
            if HEDGES & set(words[max(0, i - 3) : i + 4]):
                continue
            feature = next((f for t in near for p, f in TOPICS if re.fullmatch(p, t)), None)
            if feature is None or (w in SLOWER | FASTER and feature not in DAYS):
                continue
            out.append((f"{w} ... {feature}", feature, 1 if w in UP | SLOWER else -1))
    return out


def direction_problems(text: str, mine: dict, overall: dict) -> list[str]:
    """Each direction claimed must match the data: higher or lower than all customers, by more than 5%."""
    out = []
    for words, feature, sign in claimed_directions(text):
        a, b = mine.get(feature), overall.get(feature)
        if not isinstance(a, int | float) or not isinstance(b, int | float) or abs(a - b) <= 0.05 * abs(b):
            continue
        if (a > b) != (sign > 0):
            label = dict(FEATURES)[feature].lower()
            out.append(f'says "{words}", but the data says otherwise ({label}: {a} here, {b} for all customers)')
    return out


RISKY = re.compile(
    r"\b(bankrupt\w*|insolven\w*|fraud\w*|lawsuits?|litigation|sue|suing|legal action|collections? agenc\w*|"
    r"blacklist\w*|stop (?:doing business|working) with|cut (?:them|the customer|this customer) off|"
    r"drop (?:them|this customer|the customer))\b",
    re.I,
)


def risky_words(text: str) -> list[str]:
    """Words about bankruptcy, fraud, the law or ending the relationship: the records can't support them, and
    they're not for code to send on."""
    found = sorted({m.group().lower() for m in RISKY.finditer(text)})
    return [f"mentions {', '.join(found)}: a person decides what to say"] if found else []


def valid_answer(raw: str, texts: list[str], lists: tuple[str, ...] = ()) -> dict:
    """The model's answer, checked in one place before anything uses it: a JSON object whose text fields are
    non-empty text and whose list fields are lists of text (a null list becomes []). Anything else is a bad answer,
    and goes to a person rather than stopping the run."""
    a = parse_json(raw)
    if not isinstance(a, dict):
        raise BadAnswer("the answer isn't a JSON object")
    for k in texts:
        if not isinstance(a.get(k), str) or not a[k].strip():
            raise BadAnswer(f"no {k} (or it isn't text)")
    for k in lists:
        a[k] = [] if a.get(k) is None else a[k]
        if not isinstance(a[k], list) or not all(isinstance(t, str) for t in a[k]):
            raise BadAnswer(f"{k} isn't a list of text")
    return a


def name_segments(profs: list[dict], model) -> None:
    overall = overall_profile(profs)
    for p in profs:
        data = {"segment": shown(p), "all customers": overall, "features": dict(FEATURES)}
        try:
            raw = model.complete(NAME_SEGMENT, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=700)
            a = valid_answer(raw, ["name", "who"], ("treat",))
        except Exception as e:  # noqa: BLE001
            p["problems"] = [f"couldn't name it: {e}"[:150]]
            p["ai"] = None
            continue
        missing = [p["customers"] - k for k in p["n"].values()]
        allowed = allowed_numbers([p, overall], [p["customers"], *p["kinds"].values(), *missing])
        text = " ".join([a["name"], a["who"], *a["treat"]])
        # The name and the description say what the segment is: their directions must match its averages.
        p["ai"] = a
        p["problems"] = (
            number_problems(text, allowed)
            + direction_problems(f"{a['name']}. {a['who']}", p, overall)
            + risky_words(text)
        )


def explain(c: Customer, model, overall: dict | None = None) -> None:
    data = {
        "customer": c.id,
        "segment": c.segment,
        "numbers": {lbl: f"n/a ({NO_VALUE[n]})" if c.x[n] is None else c.x[n] for n, lbl in FEATURES},
        "model's top reasons": [dict(FEATURES)[n] for n, _ in c.reasons],
        "late-payment score (0 to 1, for ranking; not a probability)": c.late_score,
    }
    try:
        raw = model.complete(EXPLAIN_LATE, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=500)
        a = valid_answer(raw, ["why", "action"])
    except Exception as e:  # noqa: BLE001
        c.problems = [f"couldn't explain it: {e}"[:150]]
        return
    c.explanation = a
    text = a["why"] + " " + a["action"]
    c.problems = number_problems(text, allowed_numbers([c.x], [c.late_score])) + risky_words(text)
    if overall:
        c.problems += direction_problems(a["why"], c.x, overall)
    if re.search(r"\bwill (pay late|be late|not pay|default)\b", a["why"], re.I):
        c.problems.append('says the customer "will" pay late: it\'s a signal, not a verdict')


# --- scoring and the run ----------------------------------------------------------------------------------------


def tested(p: dict) -> str:
    """One prediction's test, in a sentence."""
    source = "" if p["learned_from"] == "the answer key" else f"Learned from {p['learned_from']}. "
    if p["verdict"] == NOT_ENOUGH:
        return f"**{p['question']}** {source}{p['positives']} of {len(p['y'])} did. **Verdict: {p['verdict']}.**"
    return (
        f"**{p['question']}** {source}Tested on {p['test']} customers the model never saw ({p['positives']} did). "
        f"Model: {p['model_auc']:.2f}; the rule ({p['baseline']}): {p['rule_auc']:.2f} (0.5 is a coin flip). "
        f"In the top {p['top']}: model {p['model_hits']}, rule {p['rule_hits']}, random about {p['base_hits']}. "
        f"**Verdict: {p['verdict']}.**"
    )


def score(custs: list[Customer], top: list[Customer], folder: Path, preds: dict, misses: int | None = None) -> dict:
    late = {r["Customer ID"]: int(r["Paid late (over 20 days)"]) for r in read_csv(folder / "answer-key-late-2025.csv")}
    behavior = {r["Customer ID"]: r for r in read_csv(folder / "answer-key-behavior.csv")}
    base = sum(late.values()) / len(late)
    hit = sum(late.get(c.id, 0) for c in top)
    by = defaultdict(list)
    for c in custs:
        if c.id in behavior:
            by[c.cluster].append(behavior[c.id])
    hidden = {
        k: {
            "pays late (hidden)": round(mean(float(b["Pays late by (days)"]) for b in v), 1),
            "price sensitivity (hidden)": round(mean(float(b["Price sensitivity"]) for b in v), 2),
            "approves (hidden)": round(mean(float(b["Approves quotes (share)"]) for b in v), 2),
        }
        for k, v in by.items()
    }
    md = [f"- {tested(p)}" for p in preds.values()]
    md.append(
        f"- **The late-payment list:** of the top {len(top)}, **{hit} actually paid more than 20 days late** in 2025. "
        f"Picking {len(top)} at random would find about {base * len(top):.1f}."
        if top
        else f'- **No late-payment list:** the test\'s verdict was "{preds["late"]["verdict"]}", so nobody is named.'
    )
    if misses is not None:
        md.append(f"- **Replay:** {misses} items had no recorded answer (they went to a person).")
    md += [
        "- **Segments against hidden behavior:**",
        "",
        "| Segment | Pays late (hidden) | Price sensitivity (hidden) | Approves (hidden) |",
        "|---|---:|---:|---:|",
    ]
    md += [
        f"| {k} | {h['pays late (hidden)']} | {h['price sensitivity (hidden)']} | {h['approves (hidden)']} |"
        for k, h in sorted(hidden.items())
    ]
    return {"hit": hit, "top": len(top), "base": base, "hidden": hidden, "md": "\n".join(md)}


def shown_name(p: dict) -> str:
    """The segment's name on the dashboards: the AI's, if its answer passed every check; otherwise a number."""
    if p.get("ai") and not p.get("problems"):
        return p["ai"]["name"]
    return f"Segment {p['segment']} (to be named)"


def list_note(late: dict, top: list[Customer]) -> str:
    """What the list is, in words that match how it was made."""
    if not top:
        return f"no late-payment list (the test said: {late['verdict']})"
    if late["verdict"] == USE_RULE:
        return (
            f"{len(top)} on the late-payment list, ranked by the rule (days late in the last 12 months), "
            f"which tested as good as a model learned from {late['learned_from']}"
        )
    return f"{len(top)} on the late-payment list, ranked by a model learned from {late['learned_from']}"


def run(folder: Path, model, out: Path, cutoff: date, top_n: int = 25, answer_key: bool = True):
    """Everything, written to `out` for the team and to `out/billing` for billing only. Returns the customers, the
    segments, the late-payment list, the files written and a one-line summary."""
    from segments_dashboard import dashboard

    unread = []
    custs = list(build_features(folder, cutoff, unread).values())
    seg = segment(custs)
    profs = profiles(custs)
    # With an answer key (the sample), learn from it; without one, learn from last year's history.
    preds = predictions(custs, folder) if answer_key else predictions_from_history(folder, cutoff)
    score_late(custs, preds["late"])
    # Only a method that passed its test puts names on a list.
    ranked = sorted(custs, key=lambda c: -c.late_score)
    top = ranked[:top_n] if makes_a_list(preds["late"]["verdict"]) else []
    name_segments(profs, model)
    overall = overall_profile(profs)
    for c in top:
        explain(c, model, overall)
    misses = getattr(model, "misses", None)
    # The list can be scored against the answer key whichever way the predictions learned.
    has_key = all((folder / f).exists() for f in ("answer-key-late-2025.csv", "answer-key-behavior.csv"))
    scored = score(custs, top, folder, preds, misses) if has_key else None
    # The AI's name is used only if its answer passed every check: a stale or wrong name would mislabel a segment.
    names = {p["segment"]: shown_name(p) for p in profs}
    billing = out / "billing"  # readable by billing only: the named list, and everyone's late-payment score
    feats = [n for n, _ in FEATURES]
    written = [
        write_text(out / "dashboard.html", dashboard(custs, profs, seg, preds, [], names, model.name, scored)),
        write_csv(
            out / "segments.csv",
            [
                {
                    "segment": p["segment"],
                    "name": names[p["segment"]],
                    "ai_name": (p["ai"] or {}).get("name", ""),
                    "customers": p["customers"],
                    **{n: p[n] for n in feats},
                    **{f"{n} (n/a)": p["customers"] - p["n"][n] for n in NO_VALUE},
                    "who": (p["ai"] or {}).get("who", ""),
                    "treat": " | ".join((p["ai"] or {}).get("treat", [])),
                    "problems": " | ".join(p.get("problems", [])),
                }
                for p in profs
            ],
            [
                "segment",
                "name",
                "ai_name",
                "customers",
                *feats,
                *[f"{n} (n/a)" for n in NO_VALUE],
                "who",
                "treat",
                "problems",
            ],
        ),
        # The team's customer file: segments and the features that say nothing about paying late.
        write_csv(
            out / "customers.csv",
            [{"customer": c.id, "name": c.name, "segment": names[c.cluster], **c.x} for c in custs],
            ["customer", "name", "segment", *[n for n in feats if n not in LATE_MEASURES]],
        ),
        write_csv(
            out / "review-queue.csv",
            [
                {
                    "which": f"{names[p['segment']]}, suggested: {(p['ai'] or {}).get('name', '-')}",
                    "why": " | ".join(p["problems"]),
                }
                for p in profs
                if p.get("problems")
            ]
            + unread,
            ["which", "why"],
        ),
        write_text(
            billing / "dashboard-billing.html",
            dashboard(custs, profs, seg, preds, top, names, model.name, scored, "billing"),
        ),
        write_csv(
            billing / "late-payment-list.csv",
            [
                {
                    "customer": c.id,
                    "name": c.name,
                    "late_score": c.late_score,
                    "reasons": "; ".join(dict(FEATURES)[n] for n, _ in c.reasons),
                    "why": (c.explanation or {}).get("why", ""),
                    "action": (c.explanation or {}).get("action", ""),
                    "problems": " | ".join(c.problems),
                }
                for c in top
            ],
            ["customer", "name", "late_score", "reasons", "why", "action", "problems"],
        ),
        # Billing's customer file: every feature, including how late each customer paid.
        write_csv(
            billing / "customers.csv",
            [{"customer": c.id, "name": c.name, "segment": names[c.cluster], **c.x} for c in custs],
            ["customer", "name", "segment", *feats],
        ),
        write_csv(
            billing / "late-scores.csv",
            [
                {"customer": c.id, "name": c.name, "segment": names[c.cluster], "late_score": c.late_score}
                for c in ranked
            ]
            if top
            else [],
            ["customer", "name", "segment", "late_score"],
        ),
        write_csv(
            billing / "review-queue.csv",
            [{"which": c.name, "why": " | ".join(c.problems)} for c in top if c.problems],
            ["which", "why"],
        ),
    ]
    if scored:
        written.append(write_text(out / "score.md", "# Against the answer key\n\n" + scored["md"] + "\n"))
    row = {
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "model": model.name,
        "customers": len(custs),
        "segments": seg["k"],
        "late model auc": (preds.get("late") or {}).get("model_auc"),
        "on the late-payment list": len(top),
        "no recorded answer": "" if misses is None else misses,
    }
    log = out / "runs.csv"
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    written.append(log)
    note = f"{len(custs)} customers in {len(profs)} segments; {list_note(preds['late'], top)}."
    if unread:
        note += f" {len(unread)} export rows couldn't be used (review-queue.csv)."
    if misses is not None:
        note += f" {misses} items had no recorded answer."
    return custs, profs, top, written, note + " Open dashboard.html (billing: billing/dashboard-billing.html)."


class Replay:
    """Recorded answers, keyed by segment or customer, so the run repeats exactly and for free. An item with no
    recorded answer goes to a person, and is counted, so a stale recording can't pass quietly."""

    def __init__(self, path: Path):
        data = json.loads(path.read_text())
        self.answers, self.name = data["answers"], f"{data['model']}, recorded {data['recorded']} (replayed)"
        self.misses = 0

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        key = replay_key(system, user)
        if key not in self.answers:
            self.misses += 1
            raise BadAnswer(f"no recorded answer for {key}")
        return self.answers[key]


def replay_key(system: str, user: str) -> str:
    data = json.loads(user.split("<<<DATA\n", 1)[1].rsplit("\nDATA>>>", 1)[0])
    return (
        f"segment:{data['segment']['segment']}"
        if system.startswith("You help a commercial")
        else f"customer:{data['customer']}"
    )


def offline(system: str, user: str) -> str:
    """A crude stand-in, no AI: names segments by their biggest customer type, and restates the reasons."""
    data = json.loads(user.split("<<<DATA\n", 1)[1].rsplit("\nDATA>>>", 1)[0])
    if system.startswith("You help a commercial"):
        kinds = data["segment"]["kinds"]
        top = max(kinds, key=kinds.get).replace("_", " ")
        return json.dumps(
            {"name": f"Mostly {top}s", "who": f"Mostly {top} customers.", "treat": ["Review this segment."]}
        )
    return json.dumps(
        {
            "why": "The model's top reasons: " + ", ".join(data["model's top reasons"]).lower() + ".",
            "action": "Call their accounts-payable contact before the next invoice goes out.",
        }
    )


def keyed(folder: Path) -> bool:
    """Whether the folder has answer keys to learn from (only the simulated sample does)."""
    return all((folder / f).exists() for f in ("answer-key-late-2025.csv", "answer-key-churn.csv"))


def main() -> None:
    p = parser("Segment customers and list who may pay late, with reasons. Never sends.", SAMPLE)
    p.add_argument("--data", type=Path, help="folder of exports (see README)")
    p.add_argument("--cutoff", type=date.fromisoformat, help="the last day of data to use")
    p.add_argument("--top", type=int, default=25, help="how many customers to put on the late-payment list")
    p.add_argument(
        "--from-history",
        action="store_true",
        help="learn from last year's records, even when an answer key is there (it's then only used to score)",
    )
    p.add_argument("--replay", type=Path)
    args = p.parse_args()
    folder = SAMPLE if args.sample else args.data
    if not folder:
        p.error("choose --sample or --data")
    cutoff = args.cutoff or (SAMPLE_CUTOFF if args.sample else date.today())
    model = Replay(args.replay) if args.replay else model_for(args, offline)
    *_, written, note = run(
        folder, model, args.out, cutoff, args.top, answer_key=not args.from_history and keyed(folder)
    )
    done(model, written, note)


if __name__ == "__main__":
    main()
