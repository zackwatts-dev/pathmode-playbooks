"""Customer segments: group customers by how they actually behave, list who's likely to pay late, and say why.

    python customer-segments/customer_segments.py --sample --dry-run
    python customer-segments/customer_segments.py --sample --replay customer-segments/sample-data/recorded-run.json

Machine learning does the finding; the AI does the explaining.
- Features are built from two years of activity up to a cutoff date, and nothing after it: spend and its
  trend, jobs, repeat visits, slow jobs, how late they pay, how often they approve quotes, agreements.
- k-means groups customers into segments. The number of segments is chosen by how well they separate
  (the silhouette score), not by hand.
- Two questions are tested, each against a one-line rule on customers the model never saw: "who'll pay more
  than 20 days late next year?" and "who'll leave next year?". The verdict is the model, the rule, or "not
  predictable".
- The late-payment list ranks everyone by their chance of paying more than 20 days late, with whichever method
  won. With an answer key, a model's scores come from cross-validation, so no customer is scored by a model that
  saw their outcome. Without one, the model learns from history: features as they stood a year before the cutoff,
  and what happened in the year after.
- The leaving question is only tested and reported. Nobody is listed or scored for it.
- The AI names each segment and suggests how to treat it, and explains each customer on the late-payment list,
  using only the numbers it's given. Code checks every number.

Writes out/dashboard.html (segments and tested predictions), out/dashboard-billing.html (plus the late-payment
list, for billing only), out/segments.csv, out/late-payment-list.csv, out/customers.csv, out/review-queue.csv,
out/runs.csv and, when there's an answer key (the sample), out/score.md. Nothing is sent or changed.
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

from common.evidence import unsupported_numbers  # noqa: E402
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
    ("pays_late", "Days late they pay, on average"),
    ("approves", "Share of quotes they approve"),
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


@dataclass
class Customer:
    id: str
    name: str
    segment: str
    branch: str
    x: dict = field(default_factory=dict)
    cluster: int = -1
    late_risk: float = 0.0  # chance of paying more than 20 days late next year
    reasons: list[tuple[str, float]] = field(default_factory=list)
    explanation: dict | None = None
    problems: list[str] = field(default_factory=list)


def build_features(folder: Path, cutoff: date) -> dict[str, Customer]:
    """One row of features per customer, from exports, never looking past the cutoff."""

    def upto(rows, col):
        return [r for r in rows if d(r[col]) and d(r[col]) <= cutoff]

    custs = {
        r["Customer ID"]: Customer(r["Customer ID"], r["Name"], r["Segment"], r["Branch"])
        for r in read_csv(folder / "customers.csv")
    }
    since = {r["Customer ID"]: d(r["Since"]) for r in read_csv(folder / "customers.csv")}
    # The last 12 months, and their second half for the trend, counted back from whatever the cutoff is.
    year_ago, half_ago = months_before(cutoff, 12), months_before(cutoff, 6)
    sites = defaultdict(set)
    for r in read_csv(folder / "sites.csv"):
        sites[r["Customer ID"]].add(r["Site ID"])
    covered = defaultdict(set)
    for r in upto(read_csv(folder / "agreements.csv"), "Start"):
        if not r["End"] or d(r["End"]) > cutoff:
            covered[r["Customer ID"]].add(r["Site ID"])
    spend, recent, before = defaultdict(float), defaultdict(float), defaultdict(float)
    due = {}
    for r in upto(read_csv(folder / "invoices.csv"), "Date"):
        when, amt = d(r["Date"]), float(r["Amount"] or 0)
        if when > year_ago:
            spend[r["Customer ID"]] += amt
            (recent if when > half_ago else before)[r["Customer ID"]] += amt
        due[r["Invoice"]] = (r["Customer ID"], d(r["Due"]))
    late = defaultdict(list)
    for r in upto(read_csv(folder / "payments.csv"), "Paid"):
        if r["Invoice"] in due and due[r["Invoice"]][1]:
            cid, when_due = due[r["Invoice"]]
            late[cid].append(max(0, (d(r["Paid"]) - when_due).days))
    jobs = defaultdict(list)
    for r in upto(read_csv(folder / "jobs.csv"), "Created"):
        jobs[r["Customer ID"]].append(r)
    quotes = defaultdict(list)
    for r in upto(read_csv(folder / "quotes.csv"), "Sent"):
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
        slow = sum(1 for j in last_year if j["Completed"] and (d(j["Completed"]) - d(j["Created"])).days > 21)
        decided = [q for q in quotes[cid] if q["Status"] in ("Accepted", "Declined")]
        n_sites = max(1, len(sites[cid]))
        c.x = {
            "spend": round(spend[cid], 2),
            "trend": round(recent[cid] / spend[cid], 2) if spend[cid] else 0.0,
            "jobs_per_site": round(len(last_year) / n_sites, 2),
            "repair_share": round(len(repairs) / len(last_year), 2) if last_year else 0.0,
            "repeat_share": round(repeats / len(repairs), 2) if repairs else 0.0,
            "slow_share": round(slow / len(last_year), 2) if last_year else 0.0,
            "days_since_job": (cutoff - max(d(j["Created"]) for j in js)).days if js else 730,
            "pays_late": round(mean(late[cid]), 1) if late[cid] else 0.0,
            "approves": round(sum(q["Status"] == "Accepted" for q in decided) / len(decided), 2) if decided else 0.5,
            "decides_days": round(mean((d(q["Decided"]) - d(q["Sent"])).days for q in decided), 1) if decided else 0.0,
            "agreement": round(len(covered[cid] & sites[cid]) / n_sites, 2),
            "sites": n_sites,
            "years": round((cutoff - since[cid]).days / 365.25, 1) if since.get(cid) else 0.0,
        }
    return custs


def matrix(custs: list[Customer], names: list[str]) -> list[list[float]]:
    """Features as numbers a model can use: money and counts on a log scale, so a few giants don't dominate."""
    logged = {"spend", "jobs_per_site", "days_since_job", "decides_days", "sites"}
    return [[math.log1p(max(0.0, c.x[n])) if n in logged else float(c.x[n]) for n in names] for c in custs]


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
        for name, _ in FEATURES:
            p[name] = round(mean(c.x[name] for c in members), 2)
        out.append(p)
    return out


NAMES = [n for n, _ in FEATURES]
MIN_EXAMPLES = 10  # fewer customers than this with either outcome, and there's nothing to test a prediction on
NOT_ENOUGH = "not enough examples in the records to test it"


def new_model():
    """The one model every prediction uses: scaled features into a logistic regression."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=3000))


def rule_risk(c: Customer) -> float:
    """The one-line rule as a score: how late they paid this year, out of 60 days."""
    return round(min(1.0, c.x["pays_late"] / 60), 3)


def evaluate(custs: list[Customer], labels: dict[str, int], baseline: str, top_n: int = 25) -> dict:
    """Train on 70% of customers, test on the other 30%, and compare with a one-line rule on the same 30%."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    known = [c for c in custs if c.id in labels]
    x, y = matrix(known, NAMES), [labels[c.id] for c in known]
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
    p_rule = [c.x[baseline] for c in cte]

    def top_hits(scores):
        order = sorted(range(len(yte)), key=lambda i: -scores[i])[:top_n]
        return sum(yte[i] for i in order)

    m_auc, r_auc = float(roc_auc_score(yte, p_model)), float(roc_auc_score(yte, p_rule))
    m_hits, r_hits = top_hits(list(p_model)), top_hits(p_rule)
    if max(m_auc, r_auc) < 0.65:
        verdict = "not predictable from these records"
    elif r_auc >= m_auc - 0.01 and r_hits >= m_hits:
        verdict = "use the rule: it's as good, and anyone can check it"
    else:
        verdict = "use the model"
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
    days_late, active_before, active_after = defaultdict(list), set(), set()

    def active(cid, when):
        if when and before < when <= start:
            active_before.add(cid)
        elif when and start < when <= end:
            active_after.add(cid)

    for r in read_csv(folder / "invoices.csv"):
        cid, due = r["Customer ID"], d(r["Due"])
        active(cid, d(r["Date"]))
        if cid in existed and due and start < due <= end:
            days_late[cid] += [max(0, (p - due).days) for p in paid[r["Invoice"]]] or [max(0, (end - due).days)]
    for r in read_csv(folder / "jobs.csv"):
        active(r["Customer ID"], d(r["Created"]))
    late = {cid: int(mean(v) > 20) for cid, v in days_late.items()}
    left = {cid: int(cid not in active_after) for cid in active_before & existed}
    return late, left


def score_late(custs: list[Customer], test: dict) -> None:
    """Rank everyone by their chance of paying more than 20 days late next year, with the method that won the test,
    and say which features push each customer's chance up."""
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    known, y = test["known"], test["y"]
    use_model = test["verdict"] == "use the model"
    if len(set(y)) < 2:  # no outcomes to learn from: the rule, and its one reason
        for c in custs:
            c.late_risk = rule_risk(c)
            c.reasons = [("pays_late", c.x["pays_late"])] if c.x["pays_late"] > 0 else []
        return
    # The reasons come from a model fit on every labelled example: they describe the pattern it learned. When the
    # model wins, the scores on the list never come from a model that saw that customer's outcome (below).
    model = new_model().fit(matrix(known, NAMES), y)
    chance = dict(zip([c.id for c in custs], model.predict_proba(matrix(custs, NAMES))[:, 1], strict=True))
    if use_model and test["out_of_fold"]:
        # Learned from the answer key, the labelled customers are the ones being scored: each is scored by a model
        # trained on the other four folds. Customers without a label weren't trained on, so the full model is fair.
        folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        oof = cross_val_predict(new_model(), matrix(known, NAMES), y, cv=folds, method="predict_proba")[:, 1]
        chance.update(zip([c.id for c in known], oof, strict=True))
    # Learned from history, the model saw last year's features and outcomes, never this year's: it scores everyone.
    scaler, lr = model.named_steps["standardscaler"], model.named_steps["logisticregression"]
    for c, row in zip(custs, scaler.transform(matrix(custs, NAMES)), strict=True):
        c.late_risk = round(float(chance[c.id]), 3) if use_model else rule_risk(c)
        contrib = sorted(((n, float(lr.coef_[0][i] * row[i])) for i, n in enumerate(NAMES)), key=lambda t: -t[1])
        c.reasons = [(n, round(v, 2)) for n, v in contrib[:3] if v > 0]


# --- the AI explains; code checks ----------------------------------------------------------------------------

NAME_SEGMENT = """You help a commercial HVAC contractor understand one segment of its customers, found by clustering.
From the segment's average numbers (and the same for all customers), answer with JSON only:
{"name": "a short, plain name for the segment (2 to 4 words)",
 "who": "one sentence: who these customers are and how they behave",
 "treat": ["two or three specific things the business should do for this segment"]}
Use only numbers that appear in the data. Don't invent causes."""

EXPLAIN_LATE = """You help the billing team at a commercial HVAC contractor. This customer is likely to pay more than 20
days late next year. From the customer's numbers and the top reasons, answer with JSON only:
{"why": "one or two plain sentences on what in the numbers points to late payment",
 "action": "one specific, respectful next step: for example terms, a deposit, reminders, or a call"}
Use only numbers that appear in the data. It's a signal, not a verdict: say "may", not "will"."""


def check(text: str, allowed: list[float]) -> list[str]:
    bad = unsupported_numbers(text, allowed, tolerance=0.02)
    return [f"uses numbers not in the data ({', '.join(bad)})"] if bad else []


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
    overall = {
        n: round(mean(p[n] * p["customers"] for p in profs) * len(profs) / sum(p["customers"] for p in profs), 2)
        for n, _ in FEATURES
    }
    for p in profs:
        data = {"segment": p, "all customers": overall, "features": dict(FEATURES)}
        try:
            raw = model.complete(NAME_SEGMENT, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=700)
            a = valid_answer(raw, ["name", "who"], ("treat",))
        except Exception as e:  # noqa: BLE001
            p["problems"] = [f"couldn't name it: {e}"[:150]]
            p["ai"] = None
            continue
        allowed = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", NAME_SEGMENT + json.dumps(data))]
        allowed += [v * 100 for v in allowed if 0 <= v <= 1]  # shares written as percentages
        text = " ".join([a["who"], *a["treat"]])
        p["ai"], p["problems"] = a, check(text, allowed)


def explain(c: Customer, model) -> None:
    data = {
        "customer": c.id,
        "segment": c.segment,
        "numbers": {lbl: c.x[n] for n, lbl in FEATURES},
        "model's top reasons": [dict(FEATURES)[n] for n, _ in c.reasons],
        "chance of paying more than 20 days late next year": f"{c.late_risk:.0%}",
    }
    try:
        raw = model.complete(EXPLAIN_LATE, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=500)
        a = valid_answer(raw, ["why", "action"])
    except Exception as e:  # noqa: BLE001
        c.problems = [f"couldn't explain it: {e}"[:150]]
        return
    # A number is allowed if it was anywhere in what the AI was shown (including "20 days" in the question).
    shown = EXPLAIN_LATE + json.dumps(data)
    allowed = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", shown)] + [float(v) for v in c.x.values()]
    allowed += [v * 100 for v in c.x.values() if 0 <= v <= 1]
    c.explanation = a
    c.problems = check(a["why"] + " " + a["action"], allowed)
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


def score(custs: list[Customer], top: list[Customer], folder: Path, preds: dict) -> dict:
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
    md += [
        f"- **The late-payment list:** of the top {len(top)}, **{hit} actually paid more than 20 days late** in 2025. "
        f"Picking {len(top)} at random would find about {base * len(top):.1f}.",
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


def run(folder: Path, model, out: Path, cutoff: date, top_n: int = 25, answer_key: bool = True):
    from segments_dashboard import dashboard

    custs = list(build_features(folder, cutoff).values())
    seg = segment(custs)
    profs = profiles(custs)
    # With an answer key (the sample), learn from it; without one, learn from last year's history.
    preds = predictions(custs, folder) if answer_key else predictions_from_history(folder, cutoff)
    score_late(custs, preds["late"])
    top = sorted(custs, key=lambda c: -c.late_risk)[:top_n]
    name_segments(profs, model)
    for c in top:
        explain(c, model)
    # The list can be scored against the answer key whichever way the predictions learned.
    has_key = all((folder / f).exists() for f in ("answer-key-late-2025.csv", "answer-key-behavior.csv"))
    scored = score(custs, top, folder, preds) if has_key else None
    info = preds
    names = {p["segment"]: (p["ai"] or {}).get("name", f"Segment {p['segment']}") for p in profs}
    written = [
        write_text(out / "dashboard.html", dashboard(custs, profs, seg, info, top, names, model.name, scored)),
        write_text(
            out / "dashboard-billing.html",
            dashboard(custs, profs, seg, info, top, names, model.name, scored, "billing"),
        ),
        write_csv(
            out / "segments.csv",
            [
                {
                    "segment": p["segment"],
                    "name": names[p["segment"]],
                    "customers": p["customers"],
                    **{n: p[n] for n, _ in FEATURES},
                    "who": (p["ai"] or {}).get("who", ""),
                    "treat": " | ".join((p["ai"] or {}).get("treat", [])),
                    "problems": " | ".join(p.get("problems", [])),
                }
                for p in profs
            ],
            ["segment", "name", "customers", *[n for n, _ in FEATURES], "who", "treat", "problems"],
        ),
        write_csv(
            out / "customers.csv",
            [
                {"customer": c.id, "name": c.name, "segment": names[c.cluster], "late_risk": c.late_risk, **c.x}
                for c in custs
            ],
            ["customer", "name", "segment", "late_risk", *[n for n, _ in FEATURES]],
        ),
        write_csv(
            out / "late-payment-list.csv",
            [
                {
                    "customer": c.id,
                    "name": c.name,
                    "late_risk": c.late_risk,
                    "reasons": "; ".join(dict(FEATURES)[n] for n, _ in c.reasons),
                    "why": (c.explanation or {}).get("why", ""),
                    "action": (c.explanation or {}).get("action", ""),
                    "problems": " | ".join(c.problems),
                }
                for c in top
            ],
            ["customer", "name", "late_risk", "reasons", "why", "action", "problems"],
        ),
        write_csv(
            out / "review-queue.csv",
            [{"which": c.name, "why": " | ".join(c.problems)} for c in top if c.problems]
            + [{"which": names[p["segment"]], "why": " | ".join(p["problems"])} for p in profs if p.get("problems")],
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
        "late model auc": (info.get("late") or {}).get("model_auc"),
        "on the late-payment list": len(top),
    }
    log = out / "runs.csv"
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    written.append(log)
    return custs, profs, top, written


class Replay:
    """Recorded answers, keyed by segment or customer, so the run repeats exactly and for free."""

    def __init__(self, path: Path):
        data = json.loads(path.read_text())
        self.answers, self.name = data["answers"], f"{data['model']}, recorded {data['recorded']} (replayed)"

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        key = replay_key(system, user)
        if key not in self.answers:
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
    custs, profs, top, written = run(
        folder, model, args.out, cutoff, args.top, answer_key=not args.from_history and keyed(folder)
    )
    learned = "the answer key" if not args.from_history and keyed(folder) else "last year's history"
    done(
        model,
        written,
        f"{len(custs)} customers in {len(profs)} segments; {len(top)} on the late-payment list "
        f"(predictions learned from {learned}). Open dashboard.html.",
    )


if __name__ == "__main__":
    main()
