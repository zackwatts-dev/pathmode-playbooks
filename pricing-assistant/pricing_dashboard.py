# ruff: noqa: E501  (HTML fragments read better on one line)
"""The sales manager's page: today's quote drafts with their suggested discounts, what needs the sales manager, the
questions for customers, the replies and what to do about each, text addressed to an AI, and, with an answer key,
the year's money test. Every word from a customer or the AI is escaped."""

from __future__ import annotations

from pathlib import Path

from common.page import STYLE, _e, _table

MORE = """
.quote{color:var(--muted);font-style:italic}
"""


def _m(x: float) -> str:
    return f"${x:,.0f}"


def _p(x: float) -> str:
    return f"{100 * x:.2f}".rstrip("0").rstrip(".") + "%"


def render_rows(rows: list[list[str]]) -> str:
    """A plain table of text cells, every one escaped."""
    return _table(["", ""], [[_e(c) for c in r] for r in rows])


def dashboard(r) -> str:
    drafts = [d for d in r.drafts if d.suggestion]
    manager = [d for d in drafts if d.suggestion.needs_manager]
    questions = [(d.reading.request_id, q) for d in r.drafts for q in d.reading.questions]
    person = [(d.reading.request_id, x) for d in r.drafts for x in d.reading.to_person] + [
        (a.reply_id, x) for a in r.answers for x in a.to_person
    ]
    tiles = (
        f'<div class="tiles"><div class="tile"><b>{len(r.drafts)}</b>requests read</div>'
        f'<div class="tile ready"><b>{len(drafts)}</b>quotes drafted</div>'
        f'<div class="tile"><b>{len(questions)}</b>questions for customers</div>'
        f'<div class="tile{" review" if manager else ""}"><b>{len(manager)}</b>need the sales manager</div>'
        f'<div class="tile{" review" if person else ""}"><b>{len(person)}</b>for a person</div></div>'
    )
    rows = []
    for d in sorted(drafts, key=lambda d: -sum(p.qty * p.agreed for p in d.priced)):
        s = d.suggestion
        total = sum(p.qty * p.agreed for p in d.priced)
        rows.append(
            [
                _e(d.reading.request_id),
                _e(f"{len(d.priced)} items"),
                _e(_m(total)),
                f"<b>{_e(_p(s.extra))}</b>" + (" (sales manager)" if s.needs_manager else ""),
                _e(f"{round(100 * s.p0)}% to {round(100 * s.p)}%"),
                _e(d.note),
            ]
        )
    table = _table(
        ["Request", "Items", "At the agreed price", "Extra discount", "Chance of winning", "Note"], rows, {2}
    )
    qs = "".join(f"<li>{_e(rid)}: {_e(q)}</li>" for rid, q in questions)
    reps = _table(
        ["Reply", "Kind", "Their price", "What to do", "Why"],
        [
            [
                _e(a.reply_id),
                _e(a.kind),
                _e(_m(a.amount) if a.amount else ""),
                f"<b>{_e(a.decision.action)}</b>",
                _e(a.decision.why),
            ]
            for a in r.answers
            if a.decision
        ],
    )
    addressed = [(d.reading.request_id, x) for d in r.drafts for x in d.reading.addressed_to_ai] + [
        (a.reply_id, x) for a in r.answers for x in a.addressed_to_ai
    ]
    inj = ""
    if addressed:
        inj = (
            "<h2>Text addressed to an AI (it did nothing)</h2><ul>"
            + "".join(f'<li>{_e(i)}: <span class="quote">"{_e(x)}"</span></li>' for i, x in addressed)
            + "</ul>"
        )
    ppl = ""
    if person:
        ppl = (
            '<div class="queue"><h2>For a person</h2><ul>'
            + "".join(f"<li>{_e(i)}: {_e(x)}</li>" for i, x in person)
            + "</ul></div>"
        )
    score = ""
    if r.score:
        m = r.score["money"]
        score = (
            f"<h2>The year's money test</h2><p>Every one of {m['quotes']:,} quotes in {m['year']}, priced at the suggested discount instead of the one given: "
            f"<b>{_e(_m(m['gain']))} more expected margin</b>, {m['gain_points']:.2f} points on {_e(_m(m['won_sales']))} of won quotes. "
            f"Worked out with the simulation's own chances of winning; at a real company, a split trial proves it.</p>"
        )
    return (
        f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>Quote pricing: today's drafts</title><style>{STYLE}{MORE}</style></head><body><main>"
        f"<h1>Quote pricing</h1><p class=muted>{_e(r.model)}</p>{tiles}{ppl}{score}"
        f"<h2>Drafts</h2>{table}<h2>Questions for customers</h2><ul>{qs or '<li>None.</li>'}</ul><h2>Replies</h2>{reps}{inj}</main></body></html>"
    )


def write(r, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dashboard(r), encoding="utf-8")
    return path
