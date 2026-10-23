# ruff: noqa: E501  (HTML fragments and spec fixtures read better on one line)
"""The year's dashboard for the chief estimator: the bids with the most to add, each with its gaps (the words quoted,
the section, the cost to add), what's priced but not required, the labor flags, and what went to a person. Every
word from the documents or the AI is escaped."""

from __future__ import annotations

from collections import defaultdict

from common.page import STYLE, _e, _table

MORE = """
.bid{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.bid h3{margin:0 0 4px;font-size:16px}
.quote{color:var(--muted);font-style:italic}
details{margin:6px 0}
summary{cursor:pointer}
"""


def _m(x: float) -> str:
    return f"${x:,.0f}"


def _where(source: str) -> str:
    return source if source.startswith("Addendum") else f"Section {source}"


def _card(rv) -> str:
    head = f"<h3>{_e(rv.name or 'Project ' + rv.pid)}</h3>"
    meta = (
        f'<div class="muted">{_e(rv.estimator)} · ready {_e(rv.ready_on)} · due {_e(rv.due)} · '
        f"{len(rv.accepted)} requirements read</div>"
    )
    gaps = "".join(
        f"<li><b>{_e(g.kind_title)}</b>, {_e(_where(g.source))}: add about {_e(_m(g.cost))} "
        f'(from {_e(_m(g.low))} to {_e(_m(g.high))}, {_e(g.basis)}). <span class="quote">"{_e(g.quote)}"</span></li>'
        for g in rv.gaps
    )
    nr = "".join(
        f'<li><b>{_e(n.kind_title)}</b> is {_e(n.status)} ({_e(n.source)}: <span class="quote">"{_e(n.quote)}"</span>), '
        f"but the estimate carries {_e(_m(n.amount))} for it: {_e(n.line)}.</li>"
        for n in rv.not_required
    )
    lab = "".join(
        f"<li><b>{_e(f.system.capitalize())} labor:</b> on {f.jobs} of this estimator's completed jobs, actual hours ran "
        f"{(f.ratio / f.company - 1):.0%} over the company's usual. At that rate this estimate's {f.hours:,.0f} hours would be "
        f"{f.hours + f.extra_hours:,.0f}, about {_e(_m(f.dollars))} more.</li>"
        for f in rv.labor
    )
    ref = "".join(f"<li>{_e(x)}</li>" for x in rv.referrals)
    body = ""
    if gaps:
        body += f"<p>Not priced:</p><ul>{gaps}</ul>"
    if nr:
        body += f"<p>Priced but not required:</p><ul>{nr}</ul>"
    if lab:
        body += f"<p>Labor:</p><ul>{lab}</ul>"
    if ref:
        body += f"<details><summary>For a person ({len(rv.referrals)})</summary><ul>{ref}</ul></details>"
    return f'<div class="bid">{head}{meta}{body}</div>'


def dashboard(r) -> str:
    from estimate_check import KINDS

    for rv in r.reviews:
        for g in rv.gaps:
            g.kind_title = KINDS[g.kind][0]
        for n in rv.not_required:
            n.kind_title = KINDS[n.kind][0]
    reviews = r.reviews
    gaps = sum(len(x.gaps) for x in reviews)
    gap_cost = sum(x.gap_cost for x in reviews)
    labor = sum(len(x.labor) for x in reviews)
    nr = sum(len(x.not_required) for x in reviews)
    person = sum(1 for x in reviews if x.referrals)
    tiles = (
        f'<div class="tiles"><div class="tile"><b>{len(reviews)}</b>bids checked</div>'
        f'<div class="tile review"><b>{gaps}</b>requirements not priced, about {_m(gap_cost)}</div>'
        f'<div class="tile"><b>{nr}</b>priced but not required</div>'
        f'<div class="tile"><b>{labor}</b>labor flags</div>'
        f'<div class="tile"><b>{person}</b>bids with something for a person</div></div>'
    )
    top = sorted(
        [x for x in reviews if x.gaps or x.not_required or x.labor],
        key=lambda x: -(x.gap_cost + sum(f.dollars for f in x.labor) + sum(n.amount for n in x.not_required)),
    )
    cards = "".join(_card(x) for x in top[:40]) or "<p>Nothing to add.</p>"
    by_kind: dict[str, list] = {}
    for x in reviews:
        for g in x.gaps:
            k = by_kind.setdefault(g.kind_title, [0, 0.0])
            k[0] += 1
            k[1] += g.cost
    kinds = _table(
        ["Requirement", "Gaps", "Cost to add"],
        [[_e(k), str(v[0]), _e(_m(v[1]))] for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1][1])],
        {1, 2},
    )
    addressed = [(x, a) for x in reviews for a in x.addressed]
    inj = ""
    if addressed:
        items = "".join(
            f'<li>{_e(x.name)}, {_e(a["source"])}: <span class="quote">"{_e(a["quote"])}"</span> '
            f"(found by {_e(a['by'])}; ignored)</li>"
            for x, a in addressed
        )
        inj = f"<h2>Text in the documents addressed to an AI</h2><ul>{items}</ul>"
    probs = f'<p class="bad">{_e("; ".join(r.problems))}</p>' if r.problems else ""
    score = ""
    if r.score:
        s = defaultdict(float, r.score)
        score = (
            f"<h2>Against the answer key</h2><p>Found {s.get('found', 0):.0f} of {s.get('missed', 0):.0f} missed requirements "
            f"({_m(s['found_cost'])} of {_m(s['missed_cost'])}); on the bids won, {_m(s['found_won_cost'])} of "
            f"{_m(s['missed_won_cost'])}. Wrong flags: {(s.get('false_gap', 0) + s.get('wrongly_required', 0) + s.get('phantom', 0)) / max(s['bids'], 1):.2f} a bid. "
            f"What pricing each find into its bid would do is in score.md.</p>"
        )
    return (
        f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>Spec check: the year's bids</title><style>{STYLE}{MORE}</style></head><body><main>"
        f"<h1>Spec check: the year's bids</h1><p class=muted>{_e(r.model)}</p>{probs}{tiles}{score}"
        f"<h2>Bids with the most to add</h2>{cards}<h2>By kind of requirement</h2>{kinds}{inj}</main></body></html>"
    )
