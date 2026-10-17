"""The inherited-records dashboard: what's ready to merge, and what a person has to settle first. Text is escaped."""

from __future__ import annotations

from common.page import STYLE, _e, _table


def money(x) -> str:
    return "" if x is None else f"${x:,.0f}"


def page(r, rec, model_name, scored=None) -> str:
    matched = [p for p in r.locations if p.site]
    active = [u for u in r.units if not u.replaced_on]
    tiles = [
        ("Tickets read", f"{len(r.tickets):,}", ""),
        ("Locations", str(len(r.locations)), ""),
        ("Already yours", str(len(matched)), "ready"),
        ("Active units", str(len(active)), ""),
        ("Open quotes", money(sum(o["quoted"] or 0 for o in r.open_quotes)), ""),
        ("Needs a person", str(len(r.review)), "review" if r.review else ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Inherited records</title><style>{STYLE}</style></head><body><main>",
        "<h1>Inherited records: Rimview Mechanical</h1>",
        f"<p class='muted'>Reading: {_e(model_name)}. The AI copied what each ticket says; code checked every value, "
        "grouped the tickets, matched them to your records and worked out what was promised. Nothing was imported.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if scored:
        out.append(
            "<h2>Against the answer keys</h2><ul>"
            + "".join(f"<li>{_e(x.removeprefix('- '))}</li>" for x in scored["md"].splitlines())
            + "</ul>"
        )
    if r.review:
        rows = [[_e(x["what"]), _e(x["which"]), _e(x["ticket"]), _e(x["why"])] for x in r.review]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>Settle these before anything is imported. "
            "Everything else is ready.</p>" + _table(["What", "Which", "Where", "Why"], rows) + "</section>"
        )
    out.append("<h2>Promised to customers</h2>")
    names = {p.id: p.name for p in r.locations}
    if r.open_quotes:
        out.append(
            "<p>Quoted, not done. Someone at Rimview told these customers a price; follow up or let them know.</p>"
        )
        rows = [
            [
                _e(o["location"]) + " " + _e(names.get(o["location"], "")),
                _e(o["work"]),
                _e(o["serial"]),
                money(o["quoted"]),
                _e(o["date"]),
                _e(o["ticket"]),
            ]
            for o in sorted(r.open_quotes, key=lambda o: -(o["quoted"] or 0))
        ]
        out.append(_table(["Location", "Work", "Unit serial", "Quoted", "When", "Ticket"], rows, num={3}))
    if r.agreements:
        out.append("<p>Service agreements to honor, with when each renews.</p>")
        rows = [
            [
                _e(a["location"]) + " " + _e(names.get(a["location"], "")),
                _e(a["visits a year"]),
                money(a["annual price"]),
                _e(a["renews"]),
                _e(a["ticket"]),
            ]
            for a in sorted(r.agreements, key=lambda a: str(a["renews"]))
        ]
        out.append(_table(["Location", "Visits a year", "Annual price", "Renews", "From ticket"], rows, num={2}))
    out.append("<h2>Locations</h2>")
    rows = []
    for p in r.locations:
        cust = rec.customers.get(p.customer or "", {}).get("Name", "")
        rows.append(
            [
                _e(p.id),
                _e(p.name),
                _e(p.addresses.most_common(1)[0][0] if p.addresses else "no address given"),
                str(len(p.tickets)),
                _e(f"site {p.site}" if p.site else "new site"),
                _e(cust or ("check" if p.problems else "new customer")),
                _e(p.how),
            ]
        )
    out.append(
        _table(
            ["", "Name, as Rimview wrote it", "Address", "Tickets", "Your site", "Your customer", "How"], rows, num={3}
        )
    )
    out.append("<h2>Equipment</h2>")
    rows = []
    for u in sorted(r.units, key=lambda u: (u.location, u.family, u.number or 0)):
        rows.append(
            [
                _e(u.location),
                _e(f"{u.family} {u.number or ''}"),
                _e(u.makes.most_common(1)[0][0] if u.makes else ""),
                _e(u.models.most_common(1)[0][0] if u.models else ""),
                _e(u.serial or ""),
                _e(u.year or ""),
                _e(u.refrigerant or ""),
                _e(u.summit or "new"),
                "<span class='muted'>replaced</span>" if u.replaced_on else "active",
            ]
        )
    out.append(_table(["", "Unit", "Make", "Model", "Serial", "Year", "Refrigerant", "Yours", "Status"], rows))
    out.append("</main></body></html>")
    return "".join(out)
