"""Gets a simulated business ready for the analyst: a copy of its warehouse with only the source systems' tables,
its warehouse documentation, and the staff names the words check holds back. For scoring, a separate database
with the simulation's truth tables (schema `truth`) beside the same warehouse tables, which no analyst session
ever opens.

    python business-analyst/prepare.py hartwell --corpus ../pathmode-corpus

Writes business-analyst/data/<business>/ (kept out of git: the warehouses are large and come from the corpus).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import duckdb

HERE = Path(__file__).parent

# Where each business's records are in the corpus, which warehouse schemas are source systems (anything an
# earlier analysis built is left out), and where the staff names are.
BUSINESSES = {
    "hartwell": {"folder": "simulations/hartwell", "schemas": ["main"],
                 "names": "select name from erp_sales_reps"},
    "fabricator": {"folder": "simulations/fabricator", "schemas": ["main"],
                   "names": "select name from hr_employees"},
    # Summit: the five systems, the weather and the warehouse's own conformed layer (dw, built by the
    # simulation's warehouse script, not by an analysis). Its primer is cut to the development businesses' level
    # (primers/summit.md: the corpus primer without its "three things that will bite you" and the share of visits
    # with no hours), and its table list is generated the way theirs were. No concepts or saved queries.
    "summit": {"folder": "simulation", "schemas": ["fsm", "portal", "acct", "inbox", "inv", "ext", "dw"],
               "names": "select name from fsm.technicians", "primer": "primers/summit.md", "tables_doc": True},
}


def tables_doc(wh: Path) -> str:
    """Every table with its row count and columns, as the development businesses' table lists are."""
    con = duckdb.connect(str(wh), read_only=True)
    lines = ["# Tables", "", "Every table in the warehouse, with its row count and columns.", ""]
    for schema, table in con.execute("select table_schema, table_name from information_schema.tables "
                                     "order by 1, 2").fetchall():
        n = con.execute(f'select count(*) from "{schema}"."{table}"').fetchone()[0]
        cols = con.execute("select column_name, data_type from information_schema.columns where table_schema = ? "
                           "and table_name = ? order by ordinal_position", [schema, table]).fetchall()
        lines += [f"## {schema}.{table} ({n:,} rows)", "", ", ".join(f"`{c}` {t.lower()}" for c, t in cols), ""]
    con.close()
    return "\n".join(lines)


def prepare(name: str, corpus: Path, out: Path) -> None:
    cfg = BUSINESSES[name]
    src = corpus / cfg["folder"]
    dest = out / name
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "docs").mkdir(parents=True)
    wh = dest / "warehouse.duckdb"
    source = duckdb.connect(str(src / "data" / "warehouse.duckdb"), read_only=True)
    target = duckdb.connect(str(wh))
    target.execute(f"ATTACH '{src / 'data' / 'warehouse.duckdb'}' AS src (READ_ONLY)")
    tables = source.execute(
        "select table_schema, table_name from information_schema.tables where table_schema in ({}) order by 1, 2"
        .format(",".join(f"'{s}'" for s in cfg["schemas"]))).fetchall()
    for schema, table in tables:
        if schema != "main":
            target.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        target.execute(f'CREATE TABLE "{schema}"."{table}" AS SELECT * FROM src."{schema}"."{table}"')
    names = [r[0] for r in target.execute(cfg["names"]).fetchall() if r[0]]
    target.execute("DETACH src")
    target.close()
    source.close()
    if cfg.get("primer"):
        shutil.copy(HERE / cfg["primer"], dest / "docs" / "layer0-context-primer.md")
    else:
        shutil.copy(src / "dw-docs" / "layer0-context-primer.md", dest / "docs" / "layer0-context-primer.md")
    if cfg.get("tables_doc"):
        (dest / "docs" / "layer2-tables.md").write_text(tables_doc(wh))
    else:
        shutil.copy(src / "dw-docs" / "layer2-tables.md", dest / "docs" / "layer2-tables.md")
    (dest / "staff-names.json").write_text(json.dumps(sorted(set(names))))

    truth = dest / "truth.duckdb"
    shutil.copy(wh, truth)
    t = duckdb.connect(str(truth))
    t.execute("CREATE SCHEMA truth.truth")
    t.execute("INSTALL sqlite; LOAD sqlite")
    t.execute(f"ATTACH '{src / 'data' / 'truth' / 'truth.sqlite'}' AS lite (TYPE sqlite, READ_ONLY)")
    for (table,) in t.execute("select table_name from information_schema.tables where table_catalog = 'lite'")\
            .fetchall():
        t.execute(f'CREATE TABLE truth.truth."{table}" AS SELECT * FROM lite."{table}"')
    t.execute("DETACH lite")
    t.close()
    print(f"{name}: {len(tables)} tables, {len(names)} staff names -> {dest}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("business", choices=sorted(BUSINESSES))
    p.add_argument("--corpus", type=Path, default=HERE.parent.parent / "pathmode-corpus")
    p.add_argument("--out", type=Path, default=HERE / "data")
    a = p.parse_args()
    prepare(a.business, a.corpus, a.out)


if __name__ == "__main__":
    main()
