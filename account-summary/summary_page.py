"""The account-summary dashboard: every request, who asked, and the briefing or the refusal. Text is escaped."""

from __future__ import annotations

from common.page import STYLE, _e, _table

BRIEF = """
.brief{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.brief.review{background:var(--amber-bg);border-color:var(--amber)}
.brief h3{font-size:17px}
.brief ul{margin:6px 0;padding-left:20px}
.brief blockquote{border-left:3px solid var(--line);padding-left:10px}
"""


def money(x) -> str:
    return "" if x is None else (f"−${-x:,.0f}" if x < 0 else f"${x:,.0f}")


def pct(x) -> str:
    return "" if x is None else (f"−{-x:.1f}%" if x < 0 else f"+{x:.1f}%" if x else "0%")


def card(b, data) -> str:
    r = b.request
    who = data.users[r["User"]]
    title = (
        data.customers[r["Subject"]]["Name"]
        if r["Kind"] == "customer" and r["Subject"] in data.customers and not b.refused
        else (f"Customer {r['Subject']}" if r["Kind"] == "customer" else r["Subject"])
    )
    head = (
        f"<h3 style='margin:0'>{_e(title)} <span class='muted' style='font-weight:400'>({_e(r['Kind'])}, "
        f"{_e(r['Request'])})</span></h3><p class='muted' style='margin:2px 0 8px'>Asked by {_e(who['Name'])}, "
        f"{_e(who['Role'].lower())}</p>"
    )
    if b.refused:
        return (
            f"<div class='brief'>{head}<p class='bad'>Refused before anything was gathered: {_e(b.refused)}.</p></div>"
        )
    f = b.facts
    q = f["quotes"]
    nums = [
        (f"Revenue Q{b.quarter.n}", money(f["revenue"])),
        (f"vs {b.quarter.last_year.label}", pct(f["revenue_vs_last_year"]["percent"])),
        ("Jobs", f"{f['jobs']['total']:,}"),
        ("First-time fix", "" if f["first_time_fix"] is None else f"{f['first_time_fix']:.0f}%"),
        ("Quotes won (value)", "" if q["by value"] is None else f"{q['by value']:.0f}%"),
        ("Overdue", money(f["overdue"]["balance"])),
    ]
    if "emails" in f:
        nums.append(("Emails (chasing)", f"{f['emails']['total']} ({f['emails']['chasing']})"))
    strip = "".join(
        f"<span style='margin-right:16px'><span class='muted'>{_e(k)}</span> <b>{_e(v)}</b></span>" for k, v in nums
    )
    a = b.answer or {}
    body = [f"<p style='margin:0 0 6px'>{strip}</p>"]
    if a:
        body.append(f"<p><b>{_e(a.get('headline', ''))}</b></p><ul>")
        body += [
            f"<li>{_e(p.get('text', ''))} <span class='muted'>({_e(', '.join(p.get('metrics', [])))})</span></li>"
            for p in a.get("points", [])
            if isinstance(p, dict)
        ]
        body.append("</ul>")
        if a.get("customers_say"):
            body.append("<p class='muted' style='margin-bottom:2px'>What they've said:</p>")
            body += [
                f"<blockquote style='margin:4px 0 4px 12px'>“{_e(x.get('quote', ''))}” "
                f"<span class='muted'>({_e(x.get('email', ''))})</span></blockquote>"
                for x in a["customers_say"]
            ]
        if a.get("worth_asking"):
            body.append(
                "<p class='muted' style='margin-bottom:2px'>Worth asking:</p><ul>"
                + "".join(f"<li>{_e(x)}</li>" for x in a["worth_asking"])
                + "</ul>"
            )
    if b.problems:
        body.append(
            "<p class='reason'>" + "<br>".join(f"<span class='bad'>Check:</span> {_e(p)}" for p in b.problems) + "</p>"
        )
    cls = "brief review" if b.problems else "brief"
    return f"<div class='{cls}'>{head}{''.join(body)}</div>"


def page(briefings, data, model_name, quarter, scored=None, viewer=None) -> str:
    review = [b for b in briefings if b.problems]
    refused = [b for b in briefings if b.refused]
    tiles = [
        ("Requests", str(len(briefings)), ""),
        ("Ready", str(len(briefings) - len(review) - len(refused)), "ready"),
        ("Refused (out of scope)", str(len(refused)), ""),
        ("Needs a person", str(len(review)), "review" if review else ""),
    ]
    if scored:
        tiles.append(("Match the answer key", f"{scored['ok']} of {scored['n']}", "ready"))
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Account summaries</title><style>{STYLE}{BRIEF}</style></head><body><main>",
        f"<h1>Account summaries: {_e(quarter.label)}</h1>",
        f"<p><b>{_e(viewer['Name'])}</b>, {_e(viewer['Role'].lower())}: "
        + ("everything, including every refusal." if viewer["Scope"] == "all" else "your own requests only.")
        + "</p>"
        if viewer
        else "",
        f"<p class='muted'>Words: {_e(model_name)}. Every number comes from code, from the definitions below; the AI "
        "only writes the sentences, and code checks each number, metric and quote. Nothing was sent.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if review:
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>A briefing whose words didn't pass a "
            "check. The facts stand; a person fixes the sentence before it goes out.</p>"
            + _table(
                ["Request", "Why"], [[_e(b.request["Request"]), "<br>".join(_e(p) for p in b.problems)] for b in review]
            )
            + "</section>"
        )
    out.append("<h2>The briefings</h2><div style='display:grid;gap:12px'>")
    out += [card(b, data) for b in briefings]
    out.append("</div>")
    from account_summary import METRICS

    out.append("<h2>What each number means</h2>")
    out.append(_table(["Metric", "Definition", "Owner"], [[_e(k), _e(v[0]), _e(v[1])] for k, v in METRICS.items()]))
    out.append("</main></body></html>")
    return "".join(out)
