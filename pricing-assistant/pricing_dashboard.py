"""The pricing dashboard: one HTML page for the estimating team. Customers' words are escaped."""

from __future__ import annotations

from common.page import STYLE, _e, _table


def money(x) -> str:
    return "" if x is None else f"${float(x):,.2f}"


def dashboard(quotes, negs, model_name: str, scored: dict | None, autonomous: bool) -> str:
    review_q = [q for q in quotes if q.status == "needs review"]
    stopped = [n for n in negs if n.outcome in ("needs a person", "escalated")]
    won = [n for n in negs if n.outcome == "won"]
    tiles = [
        ("Repairs priced", str(len(quotes)), ""),
        ("Ready to send", str(len(quotes) - len(review_q)), "ready"),
        ("Negotiations won", f"{len(won)} of {len(negs)}" if negs else "–", ""),
        ("Needs a person", str(len(review_q) + len(stopped)), "review" if review_q or stopped else ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Pricing assistant</title><style>{STYLE}</style></head><body><main>",
        "<h1>Pricing assistant</h1>",
        f"<p class='muted'>Model: {_e(model_name)}. Every price was worked out by code from the price book. "
        + ("Negotiations ran against simulated buyers. " if autonomous and negs else "")
        + "Nothing was sent.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if review_q or stopped:
        rows = [
            [
                f"<b>{_e(q.request['Request'])}</b> {_e(q.request['Customer'])}",
                "repair",
                "<br>".join(_e(p) for p in q.problems),
            ]
            for q in review_q
        ]
        rows += [
            [
                f"<b>{_e(n.quote['Quote'])}</b> {_e(n.quote['Customer'])}",
                _e(n.outcome),
                "<br>".join(_e(p) for p in n.problems),
            ]
            for n in stopped
        ]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>A check stopped these, or the assistant "
            "asked for a manager. Nothing about them goes to the customer until someone decides.</p>"
            + _table(["Which", "What", "Why"], rows)
            + "</section>"
        )
    rows = []
    for q in quotes:
        task = q.task["Description"] if q.task else ""
        rows.append(
            [
                f"<b>{_e(q.request['Request'])}</b> {_e(q.request['Customer'])}<br>"
                f"<span class='muted'>{_e(q.request['Agreement'])} · {_e(q.request['Segment'])}</span>",
                _e(task),
                _e(" ".join(q.clauses)),
                money(q.total),
                "<br>".join(_e(f) for f in q.flags) or ("" if not q.problems else "<span class='bad'>see above</span>"),
            ]
        )
    out.append(
        "<h2>Repair quotes</h2><p class='muted'>The AI picked the task and the guidance clauses; code checked "
        "both and did the arithmetic.</p>"
    )
    out.append(_table(["Request", "Task", "Clauses", "Price", "Notes"], rows, {3}))
    if negs:
        rows = []
        for n in negs:
            ladder = " → ".join(money(o) for o in n.offers)
            pct = f"{n.price / float(n.quote['List price']):.1%} of list" if n.price else ""
            rows.append(
                [
                    f"<b>{_e(n.quote['Quote'])}</b> {_e(n.quote['Customer'])}<br><span class='muted'>"
                    f"{_e(n.quote['Unit'])}</span>",
                    money(n.quote["List price"]),
                    _e(ladder),
                    f"<b>{_e(n.outcome)}</b><br>{pct}",
                ]
            )
        out.append(
            "<h2>Negotiations</h2><p class='muted'>Offers in order. Code held every line: never below the floor, "
            "never beyond the estimator's authority, no more than 2% a round, never back up.</p>"
        )
        out.append(_table(["Quote", "List", "Offers", "Outcome"], rows))
    if scored:
        out.append("<h2>Against the answer key</h2>")
        out.append(
            f"<p>Right task on <b>{scored['task_ok']} of {scored['n']}</b> repairs; right clauses on "
            f"<b>{scored['clause_ok']} of {scored['n']}</b>.</p>"
        )
        if scored["misses"]:
            out.append("<ul>" + "".join(f"<li>{_e(m)}</li>" for m in scored["misses"]) + "</ul>")
        if negs:
            out.append(
                f"<p>{scored['won']} negotiations won; what buyers would still have paid, left on the table: "
                f"<b>{money(scored['left'])}</b>.</p>"
            )
    out.append("</main></body></html>")
    return "\n".join(out)
