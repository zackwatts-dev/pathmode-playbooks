"""The request-routing dashboards. The shared view never shows a private request's words (pay and personal): it
counts them. A private request that's also about safety is still listed under Urgent, without its words, so the
office sees that the safety officer has it."""

from __future__ import annotations

from collections import Counter

from common.page import STYLE, _e, _table


def page(reqs, people, model_name, now, scored=None, private: str | bool = False) -> str:
    """private: False for the shared page, or "payroll" / "safety" for the page only that person sees."""
    from request_routing import QUEUES, shared_text, shared_why

    hidden = [] if private else [r for r in reqs if r.private and r.queue != "safety"]
    shown = reqs if private else [r for r in reqs if not r.private or r.queue == "safety"]
    text = (lambda r: r.row["Text"]) if private else shared_text
    why = (lambda r: r.why + r.overrides + r.problems) if private else (lambda r: shared_why(r) + r.problems)
    late = [r for r in shown if r.due < now]
    urgent = [r for r in shown if r.urgent]
    triage = [r for r in shown if r.queue == "triage"]
    overrides = [r for r in shown if r.overrides]
    tiles = [
        ("Requests", str(len(reqs)), ""),
        ("Urgent", str(len(urgent)), "review" if urgent else ""),
        ("At the office manager", str(len(triage) + sum(r.queue == "triage" for r in hidden)), ""),
        ("Code overrode the AI", str(len(overrides)), ""),
    ]
    if not private:
        tiles.append(("Private: not shown here", str(len(hidden)), ""))
    if scored:
        tiles.append(("Match the answer key", f"{scored['right']} of {scored['n']}", "ready"))
    name = {pid: p["Name"] for pid, p in people.items()}
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Request routing</title><style>{STYLE}</style></head><body><main>",
        "<h1>Requests: " + (f"{private} only" if private else "who has what") + "</h1>",
        f"<p class='muted'>Routing: {_e(model_name)}, with code holding the lines (safety, approval limits, nobody "
        f"approves their own request, pay is private). As of {_e(now.strftime('%a %b %-d, %-I:%M %p'))}. Nothing was "
        "sent or approved.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if scored:
        out.append(
            "<h2>Against the answer key</h2><ul>"
            + "".join(f"<li>{_e(x.removeprefix('- '))}</li>" for x in scored["md"].splitlines())
            + "</ul>"
        )
    if urgent:
        out.append(
            "<section class='queue'><h2>Urgent</h2>"
            + _table(
                ["Request", "From", "Goes to", "Received", "Request"],
                [
                    [
                        _e(r.id),
                        _e(r.sender["Name"]),
                        _e(name.get(r.holder, r.holder)),
                        _e(r.received.strftime("%a %-I:%M %p")),
                        _e(text(r)),
                    ]
                    for r in urgent
                ],
            )
            + "</section>"
        )
    out.append("<h2>By who has it</h2>")
    rows = []
    for holder, n in Counter(r.holder for r in shown).most_common():
        mine = [r for r in shown if r.holder == holder]
        due = min(r.due for r in mine)
        late_n = sum(r.due < now for r in mine)
        rows.append(
            [
                _e(name.get(holder, holder)),
                _e(people.get(holder, {}).get("Role", "")),
                str(n),
                f"<span class='soon'>{late_n} past due</span>" if late_n else "",
                _e(due.strftime("%a %-I:%M %p")),
            ]
        )
    out.append(_table(["Person", "Role", "Requests", "", "Next due"], rows, num={2}))
    if overrides:
        out.append(
            "<h2>Where code overrode the AI</h2><p class='muted'>The lines code holds, whatever the AI "
            "thought.</p>"
            + _table(
                ["Request", "What code did", "Request"],
                [
                    [
                        _e(r.id),
                        "<br>".join(_e(o) for o in (r.overrides if private or not r.private else shared_why(r)[1:])),
                        _e(text(r)),
                    ]
                    for r in overrides
                ],  # fmt: skip
            )
        )
    out.append("<h2>Every request</h2>")
    rows = [
        [
            _e(r.id),
            _e(r.sender["Name"]),
            _e(QUEUES.get(r.queue, r.queue))
            + (f"<br><span class='muted'>also: {_e(QUEUES.get(r.also, r.also))}</span>" if r.also else ""),
            _e(name.get(r.holder, r.holder)),
            ("<span class='soon'>urgent</span><br>" if r.urgent else "") + _e(r.due.strftime("%a %-I:%M %p")),
            _e(text(r)),
            "<br>".join(_e(x) for x in why(r)),
        ]
        for r in sorted(shown, key=lambda r: r.due)
    ]
    out.append(_table(["", "From", "What it is", "Goes to", "Due", "Request", "Why"], rows))
    out.append(f"<p class='muted'>{len(late)} past due as of the time above.</p></main></body></html>")
    return "".join(out)
