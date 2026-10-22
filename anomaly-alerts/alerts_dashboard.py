"""The briefs: one for each general manager (their store), one for the director of operations (the group), one for
the controller (vendors and cash). Money first; what the log explained, listed separately; what went to a person,
with why. Everything that came from the exports or the AI is escaped."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from common.page import STYLE, _e, _table
from common.util import write_text

MORE = """
.flag{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.flag h3{margin:0 0 4px;font-size:16px}
.flag .why{color:var(--amber)}
.quote{color:var(--muted);font-style:italic}
details{margin:6px 0}
summary{cursor:pointer}
"""


def _m(x: float) -> str:
    return f"${x:,.0f}"


def _who(f, data) -> str:
    if f.about == "employee":
        e = data.emp.get(f.subject, {})
        return f"{e.get('name', f'employee {f.subject}')} ({e.get('job', '')})"
    if f.about == "vendor":
        return data.vendor_names.get(f.subject, f"vendor {f.subject}")
    return data.store_names.get(f.store, f"store {f.store}")


def _card(x, data, show_store: bool) -> str:
    f = x.flag
    seen = next((r for r in f.reads if r.day == x.day), f.reads[0] if f.reads else None)  # the read it explains
    evidence, dollars = (seen.evidence, seen.dollars_week) if seen else (f.evidence, f.dollars_week)
    where = f"{_e(data.store_names.get(f.store, ''))} · " if show_store and f.store else ""
    head = f"<h3>{_e(f.kind.capitalize())}: {_e(_who(f, data))}</h3>"
    meta = f'<div class="muted">{where}since {_e(f.first.isoformat())} · about {_e(_m(dollars))} a week</div>'
    if not x.read:
        body = f'<p class="muted">{_e("; ".join(x.problems))}</p>'
    elif x.problems:
        body = f'<p class="why">For a person: {_e("; ".join(x.problems))}</p>'
    else:
        body = f"<p>{_e(x.explanation)}</p><p><b>Next:</b> {_e(x.next_step)}</p>"
    rows = [
        [
            _e(r.get("record", "")),
            _e(r.get("date", "")),
            _e(_m(r["amount"])) if isinstance(r.get("amount"), (int, float)) else "",
        ]
        for r in evidence
    ]
    table = _table(["Record", "Date", "Amount"], rows, {2})
    ev = f"<details><summary>The records ({len(evidence)})</summary>{table}</details>"
    return f'<div class="flag">{head}{meta}{body}{ev}</div>'


def _page(title: str, intro: str, readings, data, show_store: bool, missing, injected) -> str:
    live = sorted([x for x in readings if not x.explained], key=lambda x: -x.flag.dollars_week)
    explained = [x for x in readings if x.explained]
    person = sum(1 for x in live if x.read and x.problems)
    warn = f'<p class="bad">Missing exports: {_e(", ".join(missing))}</p>' if missing else ""
    tiles = (
        f'<div class="tiles"><div class="tile review"><b>{len(live)}</b>to look at</div>'
        f'<div class="tile"><b>{person}</b>for a person</div>'
        f'<div class="tile ready"><b>{len(explained)}</b>explained by the log</div></div>'
    )
    cards = "".join(_card(x, data, show_store) for x in live) or "<p>Nothing unusual.</p>"
    exp = "".join(
        f"<li>{_e(x.flag.kind)} at {_e(data.store_names.get(x.flag.store, ''))} ({_e(x.flag.first.isoformat())}): "
        f'<span class="quote">"{_e(x.quote)}"</span></li>'
        for x in explained
    )
    inj = ""
    if injected:
        inj = (
            "<h2>Log entries addressed to an AI</h2><ul>"
            + "".join(
                f"<li>{_e(data.store_names.get(int(r['store_id']), ''))}, {_e(r['business_date'])}: "
                f"{_e(r['text'])}</li>"
                for r in injected
            )
            + "</ul>"
        )
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{_e(title)}</title><style>{STYLE}{MORE}</style><main><h1>{_e(title)}</h1>"
        f"<p class=muted>{_e(intro)}</p>{warn}{tiles}<h2>To look at, money first</h2>{cards}"
        f"<h2>Explained by the log</h2><ul>{exp or '<li>None.</li>'}</ul>{inj}</main>"
    )


def briefs(r, data, out: Path) -> list[Path]:
    from anomaly_alerts import latest

    r_readings = list(latest(r).values())
    written = []
    span = f"{r.start.isoformat()} to {r.end.isoformat()}"
    by_store = defaultdict(list)
    for x in r_readings:
        if x.flag.owner in ("gm", "director") and x.flag.store:
            by_store[x.flag.store].append(x)
    for sid, xs in sorted(by_store.items()):
        name = data.store_names.get(sid, f"store {sid}")
        written.append(
            write_text(
                out / "briefs" / f"gm-{sid:02d}.html",
                _page(
                    f"{name}: morning brief",
                    f"Flags raised {span}. Each is a pattern worth a look, not a conclusion.",
                    [x for x in xs if x.flag.owner == "gm"],
                    data,
                    False,
                    r.missing,
                    [],
                ),
            )
        )
    written.append(
        write_text(
            out / "briefs" / "director.html",
            _page(
                "Ironbark: the group",
                f"Every store's flags, {span}, by dollars a week.",
                [x for x in r_readings if x.flag.owner in ("gm", "director")],
                data,
                True,
                r.missing,
                r.injected,
            ),
        )
    )
    ctl = [x for x in r_readings if x.flag.owner == "controller"]
    written.append(
        write_text(
            out / "briefs" / "controller.html",
            _page(
                "Vendors and cash",
                f"Invoice overcharges, short deliveries and deposits, {span}.",
                ctl,
                data,
                True,
                r.missing,
                [],
            ),
        )
    )
    written.append(
        write_text(
            out / "dashboard.html",
            _page(
                "Ironbark: anomaly briefs",
                f"Every flag raised {span}, by dollars a week.",
                r_readings,
                data,
                True,
                r.missing,
                r.injected,
            ),
        )
    )
    return written
