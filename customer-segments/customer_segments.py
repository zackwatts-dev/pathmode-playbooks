"""Customer segments: group customers by how they actually behave, find who's likely to leave, and say why.

    python customer-segments/customer_segments.py --sample --dry-run
    python customer-segments/customer_segments.py --sample --replay customer-segments/sample-data/recorded-run.json

Machine learning does the finding; the AI does the explaining.
- Features are built from two years of activity up to a cutoff date, and nothing after it: spend and its
  trend, jobs, repeat visits, slow jobs, how late they pay, how often they approve quotes, agreements.
- k-means groups customers into segments. The number of segments is chosen by how well they separate
  (the silhouette score), not by hand.
- A logistic regression scores each customer's chance of leaving, trained on part of the customers and
  tested on the rest. Scores for the list come from cross-validation, so no customer is scored by a model
  that saw them.
- The AI names each segment and suggests how to treat it, and explains each at-risk customer, using only
  the numbers it's given. Code checks every number.

Writes out/dashboard.html (segments and tested predictions), out/dashboard-billing.html (plus the late-payment
list, for billing only), out/segments.csv, out/at-risk.csv, out/customers.csv, out/review-queue.csv,
out/summary.md and, with the sample, out/score.md. Nothing is sent or changed.
"""

from __future__ import annotations

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


# --- features (only data on or before the cutoff) ----------------------------------------------------------


@dataclass
class Customer:
    id: str
    name: str
    segment: str
    branch: str
    x: dict = field(default_factory=dict)
    cluster: int = -1
    risk: float = 0.0
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
    year_ago, half = (
        date(cutoff.year - 1, cutoff.month, cutoff.day),
        date(cutoff.year, 7, 1) if cutoff.month == 12 else cutoff,
    )
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
            (recent if when >= half else before)[r["Customer ID"]] += amt
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


def evaluate(custs: list[Customer], labels: dict[str, int], baseline: str, top_n: int = 25) -> dict:
    """Train on 70% of customers, test on the other 30%, and compare with a one-line rule on the same 30%."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    names = [n for n, _ in FEATURES]
    known = [c for c in custs if c.id in labels]
    x, y = matrix(known, names), [labels[c.id] for c in known]
    xtr, xte, ytr, yte, _, cte = train_test_split(x, y, known, test_size=0.3, stratify=y, random_state=SEED)
    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=3000)).fit(xtr, ytr)
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
        "pipeline": model,
    }


def predictions(custs: list[Customer], folder: Path) -> dict:
    """Two questions, each tested against a simple rule: who'll pay late next year, and who'll leave."""
    late = {r["Customer ID"]: int(r["Paid late (over 20 days)"]) for r in read_csv(folder / "answer-key-late-2025.csv")}
    left = {r["Customer ID"]: int(r["Left in 2025"]) for r in read_csv(folder / "answer-key-churn.csv")}
    return {
        "late": {"question": "Who will pay more than 20 days late next year?", **evaluate(custs, late, "pays_late")},
        "churn": {"question": "Who will leave next year?", **evaluate(custs, left, "days_since_job")},
    }


def score_late(custs: list[Customer], verdict: dict) -> None:
    """Score everyone for paying late next year, with whichever method won, and say which features drive it."""
    names = [n for n, _ in FEATURES]
    pipe = verdict["pipeline"]
    scaler, lr = pipe.named_steps["standardscaler"], pipe.named_steps["logisticregression"]
    z = scaler.transform(matrix(custs, names))
    probs = pipe.predict_proba(matrix(custs, names))[:, 1]
    use_rule = verdict["verdict"].startswith("use the rule")
    for c, p, row in zip(custs, probs, z, strict=True):
        c.risk = round(min(1.0, c.x["pays_late"] / 60), 3) if use_rule else round(float(p), 3)
        contrib = sorted(((names[i], float(lr.coef_[0][i] * row[i])) for i in range(len(names))), key=lambda t: -t[1])
        c.reasons = [(n, round(v, 2)) for n, v in contrib[:3] if v > 0]


# --- the AI explains; code checks ----------------------------------------------------------------------------

NAME_SEGMENT = """You help a commercial HVAC contractor understand one segment of its customers, found by clustering.
From the segment's average numbers (and the same for all customers), answer with JSON only:
{"name": "a short, plain name for the segment (2 to 4 words)",
 "who": "one sentence: who these customers are and how they behave",
 "treat": ["two or three specific things the business should do for this segment"]}
Use only numbers that appear in the data. Don't invent causes."""

EXPLAIN_RISK = """You help the billing team at a commercial HVAC contractor. This customer is likely to pay more than 20
days late next year. From the customer's numbers and the top reasons, answer with JSON only:
{"why": "one or two plain sentences on what in the numbers points to late payment",
 "action": "one specific, respectful next step: for example terms, a deposit, reminders, or a call"}
Use only numbers that appear in the data. It's a signal, not a verdict: say "may", not "will"."""


def check(text: str, allowed: list[float]) -> list[str]:
    bad = unsupported_numbers(text, allowed, tolerance=0.02)
    return [f"uses numbers not in the data ({', '.join(bad)})"] if bad else []


def name_segments(profs: list[dict], model) -> None:
    overall = {
        n: round(mean(p[n] * p["customers"] for p in profs) * len(profs) / sum(p["customers"] for p in profs), 2)
        for n, _ in FEATURES
    }
    for p in profs:
        data = {"segment": p, "all customers": overall, "features": dict(FEATURES)}
        try:
            a = parse_json(
                model.complete(NAME_SEGMENT, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=700)
            )
            if not isinstance(a, dict) or not a.get("name"):
                raise BadAnswer("no name")
        except Exception as e:  # noqa: BLE001
            p["problems"] = [f"couldn't name it: {e}"[:150]]
            p["ai"] = None
            continue
        allowed = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", NAME_SEGMENT + json.dumps(data))]
        allowed += [v * 100 for v in allowed if 0 <= v <= 1]  # shares written as percentages
        text = " ".join([a.get("who", "")] + list(a.get("treat", [])))
        p["ai"], p["problems"] = a, check(text, allowed)


def explain(c: Customer, model) -> None:
    data = {
        "customer": c.id,
        "segment": c.segment,
        "numbers": {lbl: c.x[n] for n, lbl in FEATURES},
        "model's top reasons": [dict(FEATURES)[n] for n, _ in c.reasons],
        "chance of leaving": f"{c.risk:.0%}",
    }
    try:
        a = parse_json(model.complete(EXPLAIN_RISK, f"<<<DATA\n{json.dumps(data, indent=1)}\nDATA>>>", max_tokens=500))
        if not isinstance(a, dict) or not a.get("why"):
            raise BadAnswer("no explanation")
    except Exception as e:  # noqa: BLE001
        c.problems = [f"couldn't explain it: {e}"[:150]]
        return
    # A number is allowed if it was anywhere in what the AI was shown (including "20 days" in the question).
    shown = EXPLAIN_RISK + json.dumps(data)
    allowed = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", shown)] + [float(v) for v in c.x.values()]
    allowed += [v * 100 for v in c.x.values() if 0 <= v <= 1]
    c.explanation = a
    c.problems = check(a.get("why", "") + " " + a.get("action", ""), allowed)
    if re.search(r"\bwill (pay late|be late|not pay|default)\b", a.get("why", ""), re.I):
        c.problems.append('says the customer "will" pay late: it\'s a signal, not a verdict')


# --- scoring and the run ----------------------------------------------------------------------------------------


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
    md = []
    for p in preds.values():
        md.append(
            f"- **{p['question']}** Tested on {p['test']} customers the model never saw ({p['positives']} did). "
            f"Model: {p['model_auc']:.2f}; the rule ({p['baseline']}): {p['rule_auc']:.2f} (0.5 is a coin flip). "
            f"In the top {p['top']}: model {p['model_hits']}, rule {p['rule_hits']}, random about {p['base_hits']}. "
            f"**Verdict: {p['verdict']}.**"
        )
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
    preds = predictions(custs, folder) if answer_key else {}
    if preds:
        score_late(custs, preds["late"])
    else:  # without an answer key there's nothing to train on: fall back to last year's lateness, the rule
        for c in custs:
            c.risk = round(min(1.0, c.x["pays_late"] / 60), 3)
    top = sorted(custs, key=lambda c: -c.risk)[:top_n]
    name_segments(profs, model)
    for c in top:
        explain(c, model)
    scored = score(custs, top, folder, preds) if preds else None
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
            [{"customer": c.id, "name": c.name, "segment": names[c.cluster], "risk": c.risk, **c.x} for c in custs],
            ["customer", "name", "segment", "risk", *[n for n, _ in FEATURES]],
        ),
        write_csv(
            out / "at-risk.csv",
            [
                {
                    "customer": c.id,
                    "name": c.name,
                    "risk": c.risk,
                    "reasons": "; ".join(dict(FEATURES)[n] for n, _ in c.reasons),
                    "why": (c.explanation or {}).get("why", ""),
                    "action": (c.explanation or {}).get("action", ""),
                    "problems": " | ".join(c.problems),
                }
                for c in top
            ],
            ["customer", "name", "risk", "reasons", "why", "action", "problems"],
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
        "at risk listed": len(top),
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
            "action": "Call them and ask how the service has been.",
        }
    )


def main() -> None:
    p = parser("Segment customers and list who may leave, with reasons. Never sends.", SAMPLE)
    p.add_argument("--data", type=Path, help="folder of exports (see README)")
    p.add_argument("--cutoff", type=date.fromisoformat, help="the last day of data to use")
    p.add_argument("--top", type=int, default=25, help="how many at-risk customers to list")
    p.add_argument("--replay", type=Path)
    args = p.parse_args()
    folder = SAMPLE if args.sample else args.data
    if not folder:
        p.error("choose --sample or --data")
    cutoff = args.cutoff or (SAMPLE_CUTOFF if args.sample else date.today())
    model = Replay(args.replay) if args.replay else model_for(args, offline)
    custs, profs, top, written = run(
        folder, model, args.out, cutoff, args.top, answer_key=(folder / "answer-key-churn.csv").exists()
    )
    done(
        model,
        written,
        f"{len(custs)} customers in {len(profs)} segments; {len(top)} on the at-risk list. Open dashboard.html.",
    )


if __name__ == "__main__":
    main()
