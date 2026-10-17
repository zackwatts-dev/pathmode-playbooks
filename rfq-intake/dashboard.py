"""One HTML page that shows how the run went: open out/dashboard.html in any browser.

Everything from an email is escaped before it goes on the page, because email is written by strangers.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from common.page import STYLE, _e, _table

CHECKS = [
    ("couldn't process", "Couldn't process (the model's answer was unusable)"),
    ("instructions aimed at an assistant", "Instructions aimed at an assistant"),
    ("attachment we couldn't read", "Attachment it couldn't read"),
    ("isn't in our records", "Equipment not in our records"),
    ("another customer", "Equipment or name belongs to another customer"),
    ("quoted words", "Quoted words not found in the email"),
    ("deadline", "Deadline doesn't check out"),
]


def dashboard(results, as_of: date, model_name: str, scored: dict | None, audit: list) -> str:
    from rfq_intake import FAILED, INFO, NOT_RFQ, READY, REVIEW, long_date

    count = Counter(r.status for r in results)
    held = [r for r in results if r.status in (REVIEW, FAILED)]
    tiles = [
        ("Emails read", len(results), ""),
        ("Ready to quote", count[READY], "ready"),
        ("Waiting on the customer", count[INFO], ""),
        ("Needs a person", len(held), "review" if held else ""),
        ("Not a quote request", count[NOT_RFQ], ""),
    ]
    out = [
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Quotes intake</title><style>{STYLE}</style></head><body><main>",
        "<h1>Quotes mailbox</h1>",
        f"<p class='muted'>As of {long_date(as_of)}. Model: {_e(model_name)}. Nothing was sent, priced or changed.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{n}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if held:
        rows = [
            [
                f"<b>{_e(r.mail.subject)}</b><br><span class='muted'>{_e(r.mail.sender_name)}, {_e(r.mail.received)}"
                f" &middot; {_e(r.mail.file)}</span>",
                "".join(f"<span class='reason'>{_e(x)}</span>" for x in r.reasons),
            ]
            for r in held
        ]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>Each of these failed a check. "
            "Nothing about them goes anywhere until someone reads the email and decides.</p>"
            + _table(["Email", "Why it stopped"], rows)
            + "</section>"
        )
        reasons = Counter()
        for r in held:
            for x in r.reasons:
                reasons[next((label for key, label in CHECKS if key in x), "Other check")] += 1
        top = max(reasons.values())
        out.append("<h2>Which checks stopped them</h2>")
        out.append(
            _table(
                ["Check", "Emails"],
                [
                    [_e(k), f"<div class='bar'><span style='width:{60 * v // top}px'></span>{v}</div>"]
                    for k, v in reasons.most_common()
                ],
            )
        )
    ready = sorted((r for r in results if r.status == READY), key=lambda r: (r.quote_due or date.max, r.mail.file))
    if ready:
        rows = []
        for r in ready:
            left = r.days_to_quote
            cls = " class='soon'" if left is not None and left <= 3 else ""
            what = f"{r.request_type}: " + ", ".join(
                (f"{ln.unit.make} {ln.unit.model} (#{ln.unit.id})" if ln.unit else ln.what or "agreement")
                + (f" at {ln.site.name}" if ln.site and len(r.sites) > 1 else "")
                for ln in r.lines
            )
            site = r.sites[0].name if len(r.sites) == 1 else (f"{len(r.sites)} sites" if r.sites else "")
            rows.append(
                [
                    _e(r.quote_due or "none given"),
                    f"<span{cls}>{'' if left is None else left}</span>",
                    _e(r.who),
                    _e(site),
                    _e(what),
                ]
            )
        out.append(
            "<h2>Ready to quote, soonest due first</h2><p class='muted'>Days to quote: from the email arriving "
            "to the customer's deadline. Three days or fewer is in red.</p>"
        )
        out.append(_table(["Due", "Days to quote", "Customer", "Site", "What"], rows, {1}))
    info = [r for r in results if r.status == INFO]
    if info:
        rows = [
            [f"<b>{_e(r.mail.subject)}</b><br><span class='muted'>{_e(r.who or r.mail.sender_name)}</span>"]
            + ["<br>".join(_e(q) for q in dict.fromkeys(r.questions))]
            for r in info
        ]
        out.append(
            "<h2>Waiting on the customer</h2>"
            "<p class='muted'>A draft question for each is in questions/. A person sends it.</p>"
        )
        out.append(_table(["Request", "What we asked"], rows))
    routes = Counter(r.route for r in results if r.status == NOT_RFQ)
    if routes:
        out.append("<h2>Not quote requests, and where they go</h2>")
        urgent = [r for r in results if any("urgent" in n for n in r.notes)]
        rows = [[_e(k), str(v)] for k, v in routes.most_common()]
        out.append(_table(["Send to", "Emails"], rows, {1}))
        if urgent:
            out.append(
                f"<p class='bad'>{len(urgent)} urgent service request(s) landed here: forward to dispatch now.</p>"
            )
    if audit:
        out.append(
            "<h2>Spot-check these</h2><p class='muted'>Five ready requests picked at random. Open each email and "
            "check the match. Count how often you change something: that's the number to watch.</p>"
        )
        out.append(
            _table(
                ["Email", "Customer", "Matched to"],
                [
                    [
                        _e(r.mail.file),
                        _e(r.who),
                        _e(
                            "; ".join(ln.unit.serial if ln.unit else ln.what for ln in r.lines)
                            or ", ".join(s.name for s in r.sites)
                        ),
                    ]
                    for r in audit
                ],
            )
        )
    if scored:
        g = scored["groups"]
        right = len(g["right"])
        out.append(
            f"<h2>Against the answer key</h2><p><span class='ok'>{right} of {scored['total']}</span> "
            "handled as the answer key says.</p>"
        )
        rows = []
        for key, label in [
            ("let through, wrong", "Let through, but wrong: nothing stopped it"),
            ("stopped, needn't have been", "Stopped, but needn't have been: costs a person a minute"),
            ("wrong pile", "Wrong pile: sent to the wrong place"),
        ]:
            cls = "bad" if key == "let through, wrong" and g[key] else ""
            rows.append(
                [f"<span class='{cls}'>{_e(label)}</span>", str(len(g[key])), "<br>".join(_e(x) for x in g[key])]
            )
        out.append(_table(["Mistake", "Emails", "Which"], rows, {1}))
    out.append("</main></body></html>")
    return re.sub(r"\n\s*", "\n", "\n".join(out))
