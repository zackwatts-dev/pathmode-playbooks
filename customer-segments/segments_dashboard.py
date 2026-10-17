"""The customer-segments dashboard: one HTML page, with a 2D map of the customers. Names are escaped."""

from __future__ import annotations

from common.page import STYLE, _e, _table

COLORS = ["#3f6b21", "#28507a", "#9a5b00", "#7a2f6b", "#2f7a73", "#8a3a1c", "#5b5b5b"]


def scatter(custs, points, names, at_risk_ids) -> str:
    """Each customer is a dot, placed by the two directions that separate them most (PCA). Ringed: at risk."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h, pad = 760, 380, 18

    def sx(v):
        return pad + (v - x0) / ((x1 - x0) or 1) * (w - 2 * pad)

    def sy(v):
        return h - pad - (v - y0) / ((y1 - y0) or 1) * (h - 2 * pad)

    dots = []
    for c, (a, b) in zip(custs, points, strict=True):
        color = COLORS[c.cluster % len(COLORS)]
        ring = " stroke='#a3281c' stroke-width='2.2' r='6'" if c.id in at_risk_ids else " r='3.2'"
        dots.append(
            f"<circle cx='{sx(a):.1f}' cy='{sy(b):.1f}' fill='{color}' fill-opacity='0.65'{ring}>"
            f"<title>{_e(c.name)}: {_e(names[c.cluster])}</title></circle>"
        )
    legend = "".join(
        "<span style='display:inline-flex;align-items:center;gap:6px;margin-right:14px'>"
        f"<i style='width:10px;height:10px;border-radius:50%;display:inline-block;background:{COLORS[k % 7]}'>"
        f"</i>{_e(n)}</span>"
        for k, n in sorted(names.items())
    )
    return (
        f"<div class='wrap'><svg viewBox='0 0 {w} {h}' style='width:100%;max-width:{w}px;background:var(--card);"
        "border:1px solid var(--line);border-radius:10px' role='img' aria-label='Customers by segment'>"
        f"{''.join(dots)}"
        f"</svg></div><p class='muted'>{legend}"
        + ("<span style='margin-left:6px'>Ringed in red: likely to pay late next year.</span>" if at_risk_ids else "")
        + "</p>"
    )


def dashboard(custs, profs, seg, info, top, names, model_name, scored, viewer: str = "all") -> str:
    """viewer "all": segments and the tested predictions. viewer "billing": adds the late-payment list."""
    if viewer != "billing":
        top = []
    review = [c for c in top if c.problems] + [p for p in profs if p.get("problems")]
    tiles = [
        ("Customers", f"{len(custs):,}", ""),
        ("Segments found", str(seg["k"]), ""),
        ("Predictions tested", str(len(info)), "ready"),
        ("Likely to pay late", str(len(top)) if top else "billing only", ""),
        ("Needs a person", str(len(review)), "review" if review else ""),
    ]
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>Customer segments</title><style>{STYLE}</style></head><body><main>",
        "<h1>Customer segments" + (": billing" if viewer == "billing" else "") + "</h1>",
        f"<p class='muted'>Explanations: {_e(model_name)}. The segments and risk scores come from machine learning; "
        "the names and explanations from the AI, with every number checked. Nothing was sent.</p>",
        "<div class='tiles'>"
        + "".join(f"<div class='tile {c}'><b>{_e(n)}</b>{_e(label)}</div>" for label, n, c in tiles)
        + "</div>",
    ]
    if review:
        rows = [
            [
                _e(getattr(r, "name", None) or names.get(r.get("segment"), "")),
                "<br>".join(_e(p) for p in (r.problems if hasattr(r, "problems") else r["problems"])),
            ]
            for r in review
        ]
        out.append(
            "<section class='queue'><h2>Needs a person first</h2><p>An explanation that didn't pass its checks. "
            "The numbers stand; a person writes the words.</p>" + _table(["Which", "Why"], rows) + "</section>"
        )
    out.append("<h2>The segments</h2>")
    out.append(scatter(custs, seg["points"], names, {c.id for c in top}))
    rows = []
    for p in profs:
        ai = p.get("ai") or {}
        rows.append(
            [
                f"<b>{_e(names[p['segment']])}</b><br><span class='muted'>{p['customers']} customers</span>",
                f"${p['spend']:,.0f}",
                f"{p['pays_late']:.0f} days",
                f"{p['approves']:.0%}",
                f"{p['agreement']:.0%}",
                _e(ai.get("who", "")) + ("<ul>" + "".join(f"<li>{_e(t)}</li>" for t in ai.get("treat", [])) + "</ul>"),
            ]
        )
    out.append(
        _table(
            [
                "Segment",
                "Avg. spend, 12 months",
                "Pays late",
                "Approves quotes",
                "Under agreement",
                "Who they are, and how to treat them",
            ],
            rows,
            {1, 2, 3, 4},
        )
    )
    out.append(
        "<p class='muted'>Number of segments chosen by silhouette score (higher separates better): "
        + ", ".join(f"{k}: {v}" for k, v in seg["silhouette"].items())
        + "</p>"
    )
    if info:
        rows = [
            [
                _e(p["question"]),
                f"{p['model_auc']:.2f}",
                f"{p['rule_auc']:.2f}<br><span class='muted'>{_e(p['baseline'])}</span>",
                f"{p['model_hits']} / {p['rule_hits']} / {p['base_hits']}",
                f"<b>{_e(p['verdict'])}</b>",
            ]
            for p in info.values()
        ]
        out.append(
            "<h2>Predictions, tested before trusting them</h2><p class='muted'>Each one trained on 70% of customers "
            "and tested on the other 30%, against a one-line rule. Score: 0.5 is a coin flip, 1.0 is perfect. "
            "Hits: how many of the top 25 really did it (model / rule / picked at random).</p>"
        )
        out.append(_table(["Question", "Model", "Rule", "Hits in top 25", "Verdict"], rows))
    rows = []
    for c in top if viewer == "billing" else []:
        ex = c.explanation or {}
        rows.append(
            [
                f"<b>{_e(c.name)}</b><br><span class='muted'>{_e(names[c.cluster])}</span>",
                f"{c.x['pays_late']:.0f} days",
                _e(ex.get("why", "")),
                _e(ex.get("action", "")),
            ]
        )
    out.append(
        "<h2>Likely to pay late next year</h2><p class='muted'>Ranked by the method that won the test. "
        "A signal for the billing team, not a verdict.</p>"
    )
    out.append(_table(["Customer", "Late last year", "Why", "Next step"], rows, {1}))
    if scored:
        out.append("<h2>Against the answer key</h2>")
        out.append(
            f"<p>Of the top {scored['top']} on the list, <b>{scored['hit']}</b> actually left in 2025. Picking "
            f"{scored['top']} at random would find about {scored['base'] * scored['top']:.1f}.</p>"
        )
        rows = [
            [
                _e(names.get(k, k)),
                str(h["pays late (hidden)"]),
                str(h["price sensitivity (hidden)"]),
                str(h["approves (hidden)"]),
            ]
            for k, h in sorted(scored["hidden"].items())
        ]
        out.append(
            _table(
                ["Segment", "Pays late (hidden)", "Price sensitivity (hidden)", "Approves (hidden)"], rows, {1, 2, 3}
            )
        )
    out.append("</main></body></html>")
    return "\n".join(out)
