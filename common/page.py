"""Shared look for the playbooks' one-page HTML dashboards: the style, escaping and tables.

Everything that came from outside (an email, a note, a customer's message) goes through `_e` before it's on
the page, because it was written by strangers.
"""

from __future__ import annotations

from html import escape

STYLE = """
:root{--bg:#f7f6f1;--card:#fff;--text:#22261f;--muted:#5d6457;--line:#dedbd0;--green:#3f6b21;--amber:#9a5b00;
--amber-bg:#fff3d6;--red:#a3281c;--red-bg:#fde8e5;--blue:#28507a}
@media (prefers-color-scheme:dark){:root{--bg:#171a15;--card:#21251e;--text:#e8eadf;--muted:#a7ad9c;--line:#363b31;
--green:#9ccc6c;--amber:#ffc35c;--amber-bg:#3a2d10;--red:#ff8b7d;--red-bg:#3d1b17;--blue:#8fb8e8}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:18px;margin:32px 0 10px}
.muted{color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.tile b{display:block;font-size:30px;line-height:1.1}
.tile.review{background:var(--amber-bg);border-color:var(--amber);animation:pulse 1.6s ease-in-out infinite}
.tile.review b{color:var(--amber)}
.tile.ready b{color:var(--green)}
@keyframes pulse{50%{box-shadow:0 0 0 6px color-mix(in srgb,var(--amber) 25%,transparent)}}
@media (prefers-reduced-motion:reduce){.tile.review{animation:none}}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:13px;color:var(--muted)}
td.num{text-align:right;white-space:nowrap}
.soon{color:var(--red);font-weight:600}
.queue{border:2px solid var(--amber);border-radius:12px;padding:4px 14px 14px;background:var(--amber-bg)}
.queue h2{color:var(--amber)}
.reason{display:block;color:var(--text)}
.wrap{overflow-x:auto}
.bar{display:flex;gap:8px;align-items:center}
.bar span{display:inline-block;height:10px;background:var(--amber);border-radius:5px}
.bad{color:var(--red);font-weight:600}
.ok{color:var(--green);font-weight:600}
"""


def _e(x) -> str:
    return escape(str(x if x is not None else ""))


def _table(head: list[str], rows: list[list[str]], num: set[int] = frozenset()) -> str:
    th = "".join(f"<th>{_e(h)}</th>" for h in head)
    body = "".join(
        "<tr>"
        + "".join(f'<td class="num">{c}</td>' if i in num else f"<td>{c}</td>" for i, c in enumerate(r))
        + "</tr>"
        for r in rows
    )
    return f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
