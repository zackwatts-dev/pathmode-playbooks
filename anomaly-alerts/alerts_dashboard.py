"""The anomaly dashboard: one HTML page. Notes and names come from records, so everything is escaped."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from common.page import STYLE, _e, _table


def dashboard(
    flags,
    top,
    data,
    start: date,
    end: date,
    budget: int,
    model_name: str,
    scored: dict | None,
    viewer: str = "Service manager",
) -> str:
    """One owner's view. Technician signals appear only on the service manager's page."""
    if viewer != "Service manager":
        flags = [fl for fl in flags if not fl.subject.startswith("T")]
        top = [fl for fl in top if not fl.subject.startswith("T")]
    from anomaly_alerts import CHECK_FAILED, EXPLAINED

    review = [fl for fl in top if fl.status == CHECK_FAILED]
    money = sum(fl.value or 0 for fl in flags)
    jobs = sum(1 for j in data.jobs.values() if j["Completed"] and start <= date.fromisoformat(j["Completed"]) <= end)
    tiles = [
        ("Jobs checked", f"{jobs:,}", ""),
        ("Flags", f"{len(flags):,}", ""),
        ("At stake, where countable", f"${money:,.0f}", "ready"),
        (f"Investigated ({budget} per owner)", str(len(top)), ""),
        ("Needs a person", str(len(review)), "review" if review else ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Anomaly alerts</title><style>{STYLE}</style></head><body><main>",
        f"<h1>Anomaly alerts: {_e(viewer.lower())}</h1>",
        f"<p class='muted'>Jobs completed {start:%B %-d} to {end:%B %-d, %Y}. Explanations: {_e(model_name)}. "
        "Nothing was sent or changed. Every flag is a signal to check, not a conclusion.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if review:
        rows = [
            [
                f"<b>{_e(fl.check)}</b><br><span class='muted'>{_e(fl.subject)}</span>",
                _e(fl.detail),
                "<br>".join(_e(p) for p in fl.problems),
            ]
            for fl in review
        ]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>The flag stands, but its explanation didn't "
            "pass the checks. Open the records and decide.</p>"
            + _table(["Flag", "What was found", "Why the explanation failed"], rows)
            + "</section>"
        )
    rows = []
    for fl in top:
        if fl.status == EXPLAINED:
            ex = fl.explanation
            cause = f"<br><span class='muted'>Likely cause: {_e(ex.get('likely_cause'))}</span>"
            text = _e(ex.get("what_happened")) + cause
            act = _e(ex.get("action"))
        else:
            text, act = "<span class='muted'>See above.</span>", ""
        value = f"${fl.value:,.2f}" if fl.value else ""
        rows.append(
            [f"<b>{_e(fl.check)}</b><br><span class='muted'>{_e(fl.subject)} · {_e(fl.owner)}</span>", value, text, act]
        )
    out.append(
        f"<h2>Investigated this run: {len(top)}</h2><p class='muted'>Up to {budget} per owner: the most money "
        "first, then other record problems, technician patterns last. Each owner gets theirs as a digest draft in "
        "alerts/.</p>"
    )
    out.append(_table(["Flag", "At stake", "What happened", "Next step"], rows, {1}))
    counts, values, kinds = defaultdict(int), defaultdict(float), {}
    for fl in flags:
        counts[fl.check] += 1
        values[fl.check] += fl.value or 0
        kinds[fl.check] = fl.kind
    found_by = {
        "rule": "a rule (reconciling records)",
        "baseline": "a baseline (vs. branch peers)",
        "model": "the model (Isolation Forest)",
    }
    rows = [
        [_e(k), _e(found_by[kinds[k]]), str(n), f"${values[k]:,.0f}" if values[k] else "—"]
        for k, n in sorted(counts.items(), key=lambda x: -x[1])
    ]
    out.append("<h2>Every flag, by check</h2>")
    out.append(_table(["Check", "Found by", "Flags", "At stake"], rows, {2, 3}))
    techs = [fl for fl in flags if fl.subject.startswith("T")]
    if techs:
        out.append(
            "<h2>Technician signals</h2><p class='muted'>For the service manager only. A habit well above branch "
            "peers is a pattern worth a conversation (training, the jobs they're given, the paperwork), never a "
            "verdict.</p>"
        )
        rows = [
            [
                _e(fl.check),
                _e(data.techs[fl.subject[1:]]["Name"]) + ", " + _e(fl.detail),
                f"{fl.score} MADs" if fl.kind == "baseline" else f"score {fl.score}",
            ]
            for fl in techs
        ]
        out.append(_table(["Signal", "Detail", "How unusual"], rows, {2}))
    if scored:
        rows = [
            [_e(r["problem"]), str(r["real"]), str(r["caught"]), str(r["flags"]), str(r["flags that were real"])]
            for r in scored["rows"]
        ]
        mf, mr = scored["model"]
        b, br = scored["top"]
        out.append("<h2>Against the answer key</h2>")
        out.append(_table(["Problem", "Real", "Caught", "Flags", "Flags that were real"], rows, {1, 2, 3, 4}))
        tf, tr, tk = scored["techs"]
        out.append(
            f"<p>Technicians flagged: <b>{tf}</b>; <b>{tr}</b> have a habit the answer key knows about (of {tk}). "
            f"Of the {b} investigated flags, <b>{br}</b> were real.</p>"
        )
        if mf:
            out.append(f"<p>The model over individual jobs flagged <b>{mf}</b>; <b>{mr}</b> had a real problem.</p>")
    out.append("</main></body></html>")
    return "\n".join(out)
