"""The estimate-check dashboard: one static page for the estimating team and the general manager.

Everything on it is escaped, including the AI's notes. It runs no scripts and loads nothing from anywhere else.
"""

from __future__ import annotations

from collections import defaultdict

from estimate_check import (
    CHECK,
    HIGH,
    NOT_CHECKED,
    PERSON,
    PILES,
    RIGHT,
    Run,
    money,
    pct_text,
    token_labels,
    total_gap,
)

from common.page import STYLE, _e, _table

CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'"


def _breakdown(run_: Run, field: str, label: str) -> str:
    groups: dict[str, list] = defaultdict(list)
    for r in run_.results:
        groups[r.row.get(field, "") or "(blank)"].append(r)
    rows = []
    for name, rs in sorted(groups.items(), key=lambda kv: -total_gap(kv[1])):
        rows.append(
            [_e(name), str(len(rs))] + [str(sum(r.pile == p for r in rs)) for p in PILES] + [_e(money(total_gap(rs)))]
        )
    return _table(
        [label, "Lines", *[p.capitalize() for p in PILES], "Under-recovered"], rows, set(range(1, len(PILES) + 3))
    )


def _centres(r) -> str:
    out = []
    for c in sorted(r.centres, key=lambda c: c.gap, reverse=True):
        if c.ratio is None:
            out.append(
                f"{_e(c.work_centre)}: {_e(f'{c.est_hours:.1f}')} h, "
                f"<span class='muted'>no history ({len(c.found.ops)} first runs): estimate kept</span>"
            )
        else:
            ops = c.found.ops
            out.append(
                f"<b>{_e(c.work_centre)}</b>: {_e(f'{c.est_hours:.1f}')} h estimated, "
                f"{_e(f'{c.history_hours:.1f}')} h at history ({_e(pct_text(c.ratio))}; {len(ops)} first runs, "
                f"{_e(ops[0].completed_on.strftime('%b %Y'))} to {_e(ops[-1].completed_on.strftime('%b %Y'))}, "
                f"{_e(c.found.tier)})"
            )
    return "<br>".join(out)


def dashboard(run_: Run) -> str:
    results = run_.results
    tiles = [
        (CHECK, run_.count(CHECK), "review" if run_.count(CHECK) else ""),
        (HIGH, run_.count(HIGH), ""),
        (RIGHT, run_.count(RIGHT), "ready"),
        (PERSON, run_.count(PERSON), "review" if run_.count(PERSON) else ""),
        (NOT_CHECKED, run_.count(NOT_CHECKED), ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta http-equiv='Content-Security-Policy' content=\"{CSP}\">"
        "<meta name='viewport' content='width=device-width,initial-scale=1'><title>Estimate check</title>"
        f"<style>{STYLE}</style></head><body><main>",
        "<h1>Estimate check</h1>",
        f"<p class='muted'>Model (for the notes only): {_e(run_.model_name)}. {len(results)} quote lines. Code "
        "compared every line with first runs of similar work and sorted it; the AI only wrote the notes, and code "
        "checked every number in them. Nothing was sent and no quote was changed.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{n}</b>{_e(label.capitalize())}</div>" for label, n, c in tiles)
        + f"<div class='tile'><b>{_e(money(total_gap(results)))}</b>History's estimate of labour the flagged lines "
        "would under-recover</div>" + "</div>",
    ]
    scope = (
        "Checked: every family (--scope all)."
        if run_.families is None
        else f"Checked: {', '.join(run_.families)} (scope.json). {run_.count(NOT_CHECKED)} lines in other families "
        "weren't checked: the estimator prices them as today."
    )
    out.append(f"<p>{_e(scope)}</p>")
    if run_.misses:
        out.append(f"<p class='bad'>{run_.misses} quotes had no recorded answer: code wrote their notes.</p>")

    checks = sorted((r for r in results if r.pile == CHECK), key=lambda r: r.gap, reverse=True)
    notes = {n.quote_id: n for n in run_.notes}
    shown: set[str] = set()
    rows = []
    for r in checks:
        n = notes.get(r.quote_id)
        if n and r.quote_id not in shown:
            shown.add(r.quote_id)
            by = f"the model ({run_.model_name}), checked by code" if n.by == "model" else "code"
            names = "; ".join(f"{_e(t)} is {_e(lbl)}" for t, lbl in token_labels(n))
            note = (
                f"{_e(n.text)}<span class='muted reason'>{names}</span><span class='muted reason'>Written by {_e(by)}"
                + (f": {_e(n.why)}" if n.why else "")
                + "</span>"
            )
        else:
            note = f"<span class='muted'>See quote {_e(r.quote_id)}'s note above.</span>"
        thin = f"<br><span class='muted'>{_e(r.reason)}</span>" if r.reason else ""
        rows.append(
            [
                f"<b>{_e(r.quote_id)}</b> line {_e(r.line_id)}<br>{_e(r.row.get('customer', ''))}<br>"
                f"<span class='muted'>{_e(r.row.get('estimator', ''))}</span>",
                f"{_e(r.row.get('part_number', ''))} {_e(r.row.get('description', ''))}<br>"
                f"<span class='muted'>{_e(r.row.get('family', ''))}, {_e(r.row.get('material', ''))}, "
                f"qty {_e(r.row.get('quantity', ''))}</span>",
                f"<b>{_e(money(r.gap))}</b><br>{_e(money(r.est_cost))} → {_e(money(r.history_cost))}<br>"
                f"{_e(pct_text(r.ratio))}",
                _centres(r) + thin,
                note,
            ]
        )
    out.append(
        "<section class='queue'><h2>Check these first</h2><p>History says each line's labour runs at least 10% over "
        "the estimate. Largest dollar gap first. The estimator decides.</p>"
        + (_table(["Quote", "Part", "Gap", "Work centres", "Note"], rows, {2}) if rows else "<p>None today.</p>")
        + "</section>"
    )

    people = [r for r in results if r.pile == PERSON]
    if people:
        rows = [
            [
                f"<b>{_e(r.quote_id)}</b> line {_e(r.line_id)}",
                f"{_e(r.row.get('part_number', ''))} {_e(r.row.get('description', ''))}",
                _e(r.row.get("estimator", "")),
                _e(r.reason),
            ]
            for r in people
        ]
        out.append(
            "<h2>Not enough history: a person checks these</h2>" + _table(["Quote", "Part", "Estimator", "Why"], rows)
        )

    thin = [r for r in results if r.pile in (RIGHT, HIGH) and r.thin]
    if thin:
        rows = [
            [
                f"<b>{_e(r.quote_id)}</b> line {_e(r.line_id)}",
                f"{_e(r.row.get('part_number', ''))} {_e(r.row.get('description', ''))}",
                _e(r.row.get("estimator", "")),
                _e(r.pile),
                _e(r.reason),
            ]
            for r in thin
        ]
        out.append(
            "<h2>Sorted, but with a thin work centre</h2><p class='muted'>These lines have a work centre with too few "
            "first runs to judge; its estimated hours were taken as they are. Worth a glance at that centre.</p>"
            + _table(["Quote", "Part", "Estimator", "Pile", "Why"], rows)
        )

    high = sorted((r for r in results if r.pile == HIGH), key=lambda r: r.gap)
    if high:
        rows = [
            [
                f"<b>{_e(r.quote_id)}</b> line {_e(r.line_id)}",
                f"{_e(r.row.get('part_number', ''))} {_e(r.row.get('description', ''))}",
                _e(r.row.get("estimator", "")),
                _e(money(-r.gap)),
                _e(pct_text(r.ratio)),
            ]
            for r in high
        ]
        out.append(
            "<h2>May be priced high</h2><p class='muted'>For information: history says the labour runs at least "
            "15% under the estimate, so we may be losing work we could win. It doesn't hold the quote.</p>"
            + _table(["Quote", "Part", "Estimator", "Labour over history", "Labour vs estimate"], rows, {3})
        )

    out.append("<h2>By estimator</h2>" + _breakdown(run_, "estimator", "Estimator"))
    out.append("<h2>By part family</h2>" + _breakdown(run_, "family", "Family"))

    if run_.rejected:
        rows = [[_e(x.file), str(x.row), _e(x.reason)] for x in run_.rejected[:200]]
        more = len(run_.rejected) - len(rows)
        out.append(
            f"<h2>Input rows that couldn't be used ({len(run_.rejected)})</h2>"
            "<p class='muted'>A bad quote or hours row sends its line to a person; a bad history or rate row isn't "
            "used. All of them are in rejected.csv.</p>"
            + _table(["File", "Row", "Why"], rows, {1})
            + (f"<p class='muted'>And {more} more in rejected.csv.</p>" if more > 0 else "")
        )

    s = run_.scored
    if s:
        n, d = s["n"], s["dollars"]
        out.append("<h2>Against the answer key</h2>")
        out.append(
            f"<p>{s['light']} lines in scope were really light (the work took 10% or more labour than estimated).</p>"
            + _table(
                ["", "Lines", "Labour"],
                [
                    ["Light lines caught (check this)", str(n["right"]), _e(money(d["right"])) + " under-recovered"],
                    [
                        "<span class='bad'>Light lines missed</span> (looks right or may be priced high)",
                        str(n["missed"]),
                        _e(money(d["missed"])) + " under-recovered",
                    ],
                    ["False flags (check this on a fine line)", str(n["false flag"]), _e(money(d["false flag"]))],
                    ["To a person (not enough history)", str(n["to a person"]), _e(money(d["to a person"])) + " light"],
                    ["Fine and not flagged", str(n["clear"]), ""],
                    [
                        "Out of scope (not checked; not in the thresholds)",
                        str(n["out of scope"]),
                        f"{s['out_of_scope_light']} of them light",
                    ],
                ],
                {1, 2},
            )
        )
        b = s["baseline"]
        out.append(
            f"<p>Truly under-recovered on the flagged lines, from the answer key: <b>{_e(money(s['true_on_flagged']))}"
            f"</b>, against history's estimate of {_e(money(total_gap(results)))}.</p>"
            + _table(
                ["", "The check", "Flag every line in scope"],
                [
                    ["Light lines caught", str(n["right"]), str(b["caught"])],
                    ["Light lines missed", str(n["missed"]), str(b["missed"])],
                    ["Flags that were fine", f"{s['false_flag_rate']:.0%}", f"{b['false_flag_rate']:.0%}"],
                ],
                {1, 2},
            )
        )
        if s["checks"]:
            items = "".join(
                f"<li><span class='{'ok' if ok else 'bad'}'>{'pass' if ok else 'fail'}</span>: "
                f"{_e(s['labels'][k])} {v:.0%} (at most {limit:.0%})</li>"
                for k, (v, limit, ok) in s["checks"].items()
            )
            out.append(f"<p>Release thresholds:</p><ul>{items}</ul>")
    out.append("</main></body></html>")
    return "\n".join(out)
