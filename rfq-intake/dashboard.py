"""One HTML page for the run: open out/dashboard.html in any browser.

In order: the count in each pile; the emails that need a person, highlighted, with the reason for each; the at-risk
requests, with each one's due date and why; the ready queue in order, with due dates and expected finish; what's
waiting on the buyer; where the rest went; and five ready requests picked at random to spot-check. Everything from an
email is escaped before it goes on the page, because email is written by strangers.
"""

from __future__ import annotations

import re
from collections import Counter

from common.page import STYLE, _e, _table

EXTRA_STYLE = """
.risk{border:2px solid var(--red);border-radius:12px;padding:4px 14px 14px;background:var(--red-bg)}
.risk h2{color:var(--red)}
.tag{display:inline-block;font-size:12px;padding:0 6px;border-radius:6px;border:1px solid var(--line);
color:var(--muted)}
.tag.key{border-color:var(--green);color:var(--green)}
"""


def dashboard(run_) -> str:
    from rfq_intake import (
        DEFAULT_WINDOW,
        FAILED,
        INFO,
        NOT_RFQ,
        ORDER_RULE,
        READY,
        REVIEW,
        ROUTE_TEXT,
        long_date,
        short,
    )

    results, plan = run_.results, run_.plan
    count = Counter(r.status for r in results)
    held = [r for r in results if r.status in (REVIEW, FAILED)]
    risk = plan.at_risk if plan else []
    tiles = [
        ("Emails read", len(results), ""),
        ("Ready to quote", count[READY], "ready"),
        ("Needs info", count[INFO], ""),
        ("Needs a person", len(held), "review" if held else ""),
        ("Not a request", count[NOT_RFQ], ""),
        ("At risk", len(risk), "review" if risk else ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Quotes intake</title><style>{STYLE}{EXTRA_STYLE}</style></head><body><main>",
        "<h1>Quotes mailbox</h1>",
        f"<p class='muted'>As of {long_date(run_.as_of)}. Model: {_e(run_.model_name)}. "
        "Nothing was sent, declined or priced.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{n}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if run_.misses:
        out.append(f"<p class='bad'>{run_.misses} emails had no recorded answer (they're in couldn't process).</p>")
    if held:
        rows = [
            [
                f"<b>{_e(r.mail.subject)}</b><br><span class='muted'>{_e(r.mail.sender_name)} &lt;{_e(r.mail.sender)}"
                f"&gt;, {_e(r.mail.received)} &middot; {_e(r.mail.file)}</span>",
                "".join(f"<span class='reason'>{_e(x)}</span>" for x in r.reasons),
            ]
            for r in held
        ]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>Each of these failed a check. Nothing about them "
            "goes anywhere until someone reads the email and decides.</p>"
            + _table(["Email", "Why it stopped"], rows)
            + "</section>"
        )
    if plan is None:
        out.append(
            "<h2>At risk</h2><p class='bad'>No estimator hours on file from the as-of date: nothing was forecast or "
            "flagged. Update estimator-hours.csv.</p>"
        )
    elif not risk:
        out.append(
            "<h2>At risk</h2><p>None: the forecast has every request in the queue quoted by its due date. "
            f"It expects {plan.load:.0f} hours of quoting against {plan.capacity:.0f} estimator hours on file.</p>"
        )
    else:
        rows = [
            [
                _e(it.label),
                f"{_e(short(it.due))}<br><span class='muted'>{'stated' if it.due_stated else 'default'}</span>",
                f"{it.hours:.1f}",
                _e(why),
            ]
            for it, why in risk
        ]
        out.append(
            "<section class='risk'><h2>At risk: ask the buyer for more time</h2><p>From each request's likely "
            "quoting time and the estimators' hours on file, these would be quoted after their due date. They stay "
            "in the queue below, in their place. Ask each buyer for more time, or find the hours. Nothing has been "
            "declined, and nothing is taken out of the forecast.</p>"
            + _table(["Request", "Due", "Hours", "Why"], rows, {2})
            + f"<p class='muted'>The forecast expects {plan.load:.0f} hours of quoting against {plan.capacity:.0f} "
            "estimator hours on file.</p></section>"
        )
    if plan:
        rows = []
        for n, (it, done_on) in enumerate(plan.queue, 1):
            r, req = it.result, it.request
            what = ""
            if r:
                what = "; ".join(
                    f"{_e(ln.part)} rev {_e(ln.revision)}"
                    + (f" &rarr; <b>rev {_e(ln.revised)}</b>" if ln.revised else "")
                    + f" &times; {_e(ln.quantity)} <span class='tag'>{_e(ln.status.split(' (')[0])}</span>"
                    for ln in r.lines
                )
            notes = req.notes if req else []
            late = done_on is None or done_on > it.due
            rows.append(
                [
                    str(n),
                    f"{_e(short(it.due))}<br><span class='muted'>{'stated' if it.due_stated else 'default'}</span>",
                    _e(it.customer) + (" <span class='tag key'>key</span>" if it.key_account else ""),
                    (what or _e(it.ref)) + "".join(f"<br><span class='muted'>{_e(x)}</span>" for x in notes),
                    f"{it.hours:.1f}",
                    f"<span class='{'soon' if late else ''}'>{_e(short(done_on) or 'later')}</span>",
                    _e(it.ref),
                ]
            )
        out.append(
            f"<h2>Ready queue, in order</h2><p><b>{_e(ORDER_RULE)}</b></p>"
            f"<p class='muted'>Due date first (stated, or {DEFAULT_WINDOW} working days "
            "after the email arrived: <i>default</i>), then key accounts, then oldest. Expected finish is the "
            f"forecast from the estimators' hours on file, {_e(short(plan.start))} to {_e(short(plan.end))} "
            f"({plan.capacity:.0f} hours, {plan.reserved:.0f} of them held back for re-quotes: "
            f"{_e(plan.reserve_from)}), at 0.6 hours a request, plus 0.3 for each extra line, times 1.5 if any part "
            "is a weldment or assembly (a repeat's family from its record, a new part's from its description)"
            + (", and 1.3 more on welded work for junior estimators" if plan.junior else "")
            + ". <i>later</i>: after the hours on file run out.</p>"
        )
        out.append(_table(["#", "Due", "Customer", "Parts", "Hours", "Expected", "Email or RFQ"], rows, {0, 4}))
    info = [r for r in results if r.status == INFO]
    if info:
        rows = [
            [f"<b>{_e(r.mail.subject)}</b><br><span class='muted'>{_e(r.who or r.mail.sender_name)}</span>"]
            + ["<br>".join(_e(q) for q in dict.fromkeys(r.questions))]
            for r in info
        ]
        out.append(
            "<h2>Needs info: waiting on the buyer</h2>"
            "<p class='muted'>A draft question for each is in questions/. A person sends it.</p>"
        )
        out.append(_table(["Request", "What to ask"], rows))
    others = [r for r in results if r.status == NOT_RFQ]
    if others:
        routes = Counter(ROUTE_TEXT[r.kind] for r in others)
        out.append("<h2>Not a request, and where each goes</h2>")
        out.append(_table(["Send to", "Emails"], [[_e(k), str(v)] for k, v in routes.most_common()], {1}))
        linked = [r for r in others if r.link]
        if linked:
            out.append(
                _table(
                    ["Email", "Kind", "Belongs to"],
                    [[_e(r.mail.subject), _e(r.kind), _e(r.link.ref)] for r in linked],
                )
            )
    if run_.audit:
        out.append(
            "<h2>Spot-check these</h2><p class='muted'>Five ready requests picked at random. Open each email and check "
            "every value against it. Count how often you change something: that's the number to watch.</p>"
        )
        out.append(
            _table(
                ["Email", "Customer", "Read as"],
                [
                    [
                        _e(r.mail.file),
                        _e(r.who),
                        _e(
                            "; ".join(
                                f"{ln.part} rev {ln.revision} x {ln.quantity}, need {short(ln.requested) or '?'}"
                                for ln in r.lines
                            )
                            + (f"; quotes due {short(r.quote_due)}" if r.quote_due else "")
                        ),
                    ]
                    for r in run_.audit
                ],
            )
        )
    if run_.scored:
        s = run_.scored
        g = s["n"]
        out.append(
            f"<h2>Against the answer key</h2><p><span class='ok'>{g['right']} of {s['total']}</span> handled as the "
            f"answer key says. Sending everything to a person would get {s['baseline']['right']} right and stop "
            f"{s['free']} needlessly.</p>"
        )
        rows = []
        for key, label in [
            ("let through wrong", "Let through, but wrong: nothing stopped it"),
            ("wrong place", "Sent to the wrong place"),
            ("stopped needlessly", "Stopped, but needn't have been: costs a person a minute"),
        ]:
            cls = "bad" if key == "let through wrong" and g[key] else ""
            rows.append(
                [
                    f"<span class='{cls}'>{_e(label)}</span>",
                    str(g[key]),
                    "<br>".join(_e(x) for x in s["groups"][key]),
                ]
            )
        out.append(_table(["Mistake", "Emails", "Which"], rows, {1}))
        if s["checks"]:
            out.append(
                "<p>Release thresholds: "
                + ("<span class='ok'>all pass</span>" if s["passed"] else "<span class='bad'>at least one fails</span>")
                + " (score.md).</p>"
            )
    out.append("</main></body></html>")
    return re.sub(r"\n\s*", "\n", "\n".join(out))
