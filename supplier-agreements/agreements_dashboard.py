"""The one-page dashboard for the supplier-agreements check: money due, the claims and their letters, the
deadlines, and what's waiting for a person. Everything from a document or a supplier is escaped."""

from __future__ import annotations

from collections import defaultdict

from common.page import STYLE, _e, _table

MORE = """
.letter{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;
font-size:14px}
details{margin:8px 0}
summary{cursor:pointer;font-weight:600}
.quote{color:var(--muted);font-style:italic}
"""


def _cut(text: str, n: int = 220) -> str:
    """A long passage shortened at a word, marked as shortened."""
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


def _m(x: float) -> str:
    return f"${x:,.0f}"


def dashboard(r) -> str:
    from supplier_agreements import CLAIM, RETURN

    claims = sorted(r.claims, key=lambda o: -o.gap)
    due = sum(o.gap for o in claims if o.action == CLAIM)
    back = sum(o.gap for o in claims if o.action == RETURN)
    by_kind: dict[str, float] = defaultdict(float)
    for o in claims:
        by_kind[o.kind] += o.gap
    tiles = (
        f'<div class="tiles"><div class="tile ready"><b>{_m(due)}</b>due from suppliers</div>'
        f'<div class="tile ready"><b>{_m(back)}</b>of stock that can go back</div>'
        f'<div class="tile"><b>{len(claims)}</b>claims to review</div>'
        f'<div class="tile"><b>{len(r.terms)}</b>terms read and checked</div>'
        f'<div class="tile{" review" if r.people else ""}"><b>{len(r.people)}</b>for a person</div></div>'
    )
    claim_rows = [
        [
            _e(o.supplier),
            _e(o.kind),
            _m(o.gap),
            _e(o.how),
            f'{_e(o.term.doc)}<br><span class="quote">"{_e(_cut(o.term.quote))}"</span>',
        ]
        for o in claims
    ]
    kinds = _table(["Kind", "Due"], [[_e(k), _m(v)] for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1])], {1})
    deadlines = [
        [_e(o.supplier), _e(o.kind), _e(o.records.get("claim_by") or "none in the terms"), _m(o.gap)]
        for o in claims
        if o.records.get("claim_by")
    ]
    people = [
        [_e(p.supplier), _e(p.what), _e(p.reason), f'<span class="quote">{_e(_cut(p.passage))}</span>']
        for p in r.people
    ]
    by = {"model": "opening and closing by the AI, every figure by code", "code": "written by code"}
    letters = "".join(
        f"<details><summary>{_e(lt.supplier)} <span class='muted'>({by.get(lt.by, lt.by)})</span></summary>"
        f"<div class='letter'>{_e(lt.text)}</div></details>"
        for lt in r.letters
    )
    score = ""
    if r.scored:
        n = r.scored["n"]
        score = (
            f"<h2>Against the answer key</h2><p>{n['right']} right, {n['to a person']} to a person, "
            f"{n['missed']} missed, <span class='{'bad' if n['wrong claim'] else 'ok'}'>{n['wrong claim']} wrong "
            f"claims</span>. {_m(r.scored['found_total'])} found of {_m(r.scored['key_total'])}.</p>"
        )
    missed = (
        f"<p class='bad'>{r.misses} calls had no recorded answer; those suppliers went to a person.</p>"
        if r.misses
        else ""
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Supplier agreements, 2025</title>
<style>{STYLE}{MORE}</style></head><body><main>
<h1>Supplier agreements, 2025 program year</h1>
<p class="muted">Model: {_e(r.model_name)}. Every term below was found, word for word, in the supplier's own documents,
and every amount is worked out from our records. Nothing has been sent.</p>{missed}{tiles}
<h2>Claims, largest first</h2>{
        _table(["Supplier", "Term", "Due", "How it's worked out", "Where it's written"], claim_rows, {2})
    }
<h2>By kind</h2>{kinds}
<h2>Deadlines</h2>{_table(["Supplier", "Term", "Deadline", "At stake"], deadlines, {3})}
<div class="queue"><h2>For a person</h2>{_table(["Supplier", "What", "Why", "The words"], people)}</div>
<h2>Draft letters</h2>{letters}{score}
</main></body></html>"""
