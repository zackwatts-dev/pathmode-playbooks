"""The analyst's three tools, and nothing else: query (read-only SQL), docs (the warehouse documentation) and
save (the stage's output file). Run as an MCP server over stdin and stdout, one per AI session, so the Claude
CLI can offer these three tools and no others.

Every call is written to the run's ledger by this code, not by the AI, so the checks never rely on what the
AI says it ran.

    python analyst_tools.py --run out/run --session inv-1 --stage investigate --warehouse wh.duckdb --docs docs/
"""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import fcntl
import json
import sys
import threading
from pathlib import Path

import duckdb

SHOWN_ROWS = 200
QUERY_SECONDS = 120
MAX_QUERIES = 150

# What each stage may save. Anything else is refused.
SAVES = {
    "orient": {"map.json"},
    "propose": {"hypotheses.json"},
    "investigate": {"prediction.json", "finding.json", "notes.md"},
    "challenge": {"challenge.json"},
    "revise": {"finding.json"},
    "summary": {"summary.json"},
    "grade": {"grade.json"},
}

# Functions that reach outside the warehouse or run SQL from a string. The engine refuses files and the network
# as well (external access off); this refuses them first, with a reason the AI can read.
BLOCKED_FUNCTIONS = {
    "glob", "query", "query_table", "getenv", "sniff_csv", "parquet_scan", "parquet_metadata", "parquet_schema",
    "parquet_file_metadata", "parquet_kv_metadata", "delta_scan", "iceberg_scan", "iceberg_metadata",
    "sqlite_scan", "sqlite_attach", "postgres_scan", "postgres_attach", "mysql_scan", "csv_scan", "json_scan",
}
BLOCKED_PREFIXES = ("read_",)


def guard(sql: str) -> str | None:
    """None if the statement may run; otherwise why not. Parsed by DuckDB, not matched by pattern."""
    if not sql or not sql.strip():
        return "empty statement"
    try:
        statements = duckdb.connect().extract_statements(sql)
    except duckdb.Error as e:
        return f"doesn't parse: {str(e).splitlines()[0]}"
    if len(statements) != 1:
        return "one statement at a time"
    if statements[0].type != duckdb.StatementType.SELECT:
        return f"only SELECT and WITH are allowed, not {statements[0].type.name}"
    tokens = [(off, kind) for off, kind in duckdb.tokenize(sql) if kind != duckdb.token_type.comment]
    texts = []
    for i, (off, kind) in enumerate(tokens):
        end = tokens[i + 1][0] if i + 1 < len(tokens) else len(sql)
        texts.append((sql[off:end].strip(), kind))
    for i, (text, kind) in enumerate(texts):
        nxt = texts[i + 1][0] if i + 1 < len(texts) else ""
        if kind in (duckdb.token_type.identifier, duckdb.token_type.keyword) and nxt.startswith("("):
            name = text.strip('"').lower()
            if name in BLOCKED_FUNCTIONS or name.startswith(BLOCKED_PREFIXES):
                return f"the function {name}() isn't allowed: the warehouse's tables are all there is"
        if kind == duckdb.token_type.string_const and i > 0:
            prev = texts[i - 1][0].lower()
            if prev in ("from", "join") or (prev == "," and _in_from_list(texts, i)):
                return "reading a file isn't allowed: query the warehouse's tables"
    return None


def _in_from_list(texts: list[tuple[str, object]], i: int) -> bool:
    """Is the comma before token i part of a FROM list (rather than a select list or a function's arguments)?"""
    depth = 0
    for text, _kind in reversed(texts[:i]):
        low = text.lower()
        if low.endswith(")"):
            depth += 1
        elif low.endswith("("):
            if depth == 0:
                return False
            depth -= 1
        elif depth == 0 and low in ("from", "join"):
            return True
        elif depth == 0 and low in ("select", "where", "group", "order", "having"):
            return False
    return False


def connect(warehouse: Path) -> duckdb.DuckDBPyConnection:
    """The warehouse, read-only, with files and the network turned off and the setting locked."""
    con = duckdb.connect(str(warehouse), read_only=True, config={"enable_external_access": False})
    con.execute("SET lock_configuration = true")
    return con


def plain(value):
    """A result value as JSON: numbers stay numbers, everything else becomes text."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    return str(value)


class Ledger:
    """Append-only, one JSON line per call, numbered across the whole run. Locked, so sessions may overlap."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def append(self, entry: dict) -> dict:
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            lines = f.read().splitlines()
            seq = len(lines) + 1
            if entry.get("kind") == "query":
                n = sum(1 for line in lines if json.loads(line).get("kind") == "query") + 1
                entry = {**entry, "id": f"{entry.get('prefix', 'q')}{n}"}
                entry.pop("prefix", None)
            entry = {"seq": seq, **entry, "at": dt.datetime.now().isoformat(timespec="seconds")}
            f.write(json.dumps(entry) + "\n")
            fcntl.flock(f, fcntl.LOCK_UN)
        return entry

    def entries(self) -> list[dict]:
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]


def table(columns: list[str], rows: list[list], total: int) -> str:
    head = f"{total} row{'s' if total != 1 else ''}" + (f", the first {SHOWN_ROWS} shown" if total > SHOWN_ROWS else "")
    lines = [head, " | ".join(columns)]
    for r in rows[:SHOWN_ROWS]:
        lines.append(" | ".join("" if v is None else str(v) for v in r))
    return "\n".join(lines)


class Session:
    """One AI session's tools: its own folder, the shared ledger, the read-only warehouse."""

    def __init__(self, run: Path, session: str, stage: str, warehouse: Path, docs: Path,
                 max_queries: int = MAX_QUERIES, prefix: str = "q"):
        self.run, self.session, self.stage = Path(run), session, stage
        self.folder = self.run / session
        self.folder.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.run / "ledger.jsonl")
        self.warehouse, self.docs_dir = Path(warehouse), Path(docs).resolve()
        self.max_queries, self.prefix = max_queries, prefix
        self.con = None

    def _count(self) -> int:
        return sum(1 for e in self.ledger.entries() if e.get("kind") == "query" and e["session"] == self.session)

    def query(self, sql: str) -> str:
        base = {"kind": "query", "prefix": self.prefix, "session": self.session, "sql": sql}
        if self._count() >= self.max_queries:
            return f"Refused: this session's cap of {self.max_queries} queries is reached. Save what you have."
        why = guard(sql)
        if why:
            e = self.ledger.append({**base, "columns": [], "rows": [], "row_count": 0, "error": f"refused: {why}"})
            return f"{e['id']}: refused: {why}"
        if self.con is None:
            self.con = connect(self.warehouse)
        timer = threading.Timer(QUERY_SECONDS, self.con.interrupt)
        timer.start()
        try:
            cur = self.con.execute(sql)
            columns = [d[0] for d in cur.description or []]
            rows = [[plain(v) for v in r] for r in cur.fetchall()]
        except duckdb.Error as err:
            e = self.ledger.append({**base, "columns": [], "rows": [], "row_count": 0,
                                    "error": str(err).splitlines()[0][:500]})
            return f"{e['id']}: error: {e['error']}"
        finally:
            timer.cancel()
        e = self.ledger.append({**base, "columns": columns, "rows": rows, "row_count": len(rows), "error": None})
        return f"{e['id']}: {table(columns, rows, len(rows))}"

    def docs(self, path: str) -> str:
        target = (self.docs_dir / path).resolve()
        if not target.is_relative_to(self.docs_dir) or not target.is_file():
            listing = sorted(str(p.relative_to(self.docs_dir)) for p in self.docs_dir.rglob("*") if p.is_file())
            return f"Refused: no such document. The documents are: {', '.join(listing)}"
        self.ledger.append({"kind": "docs", "session": self.session, "file": path})
        return target.read_text()

    def save(self, name: str, content: str) -> str:
        allowed = SAVES.get(self.stage, set())
        if name not in allowed:
            return f"Refused: this stage saves only {', '.join(sorted(allowed))}."
        if name.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return f"Not saved: that isn't valid JSON ({e}). Fix it and save again."
        (self.folder / name).write_text(content)
        self.ledger.append({"kind": "save", "session": self.session, "file": name})
        return f"Saved {name}."


TOOLS = [
    {
        "name": "query",
        "description": "Run one read-only SQL statement (SELECT or WITH, DuckDB dialect) against the warehouse. "
        "Returns the query's id, the row count and up to 200 rows. Cite the id for every number you use.",
        "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
    },
    {
        "name": "docs",
        "description": "Read one file of the warehouse documentation, by its path (for example "
        "layer0-context-primer.md). An unknown path lists the files.",
        "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "save",
        "description": "Save this stage's output file into your folder: name is the file name the instructions "
        "give, content is its full text (JSON where the name ends in .json). Saving again replaces it.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "content": {"type": "string"}},
            "required": ["name", "content"],
        },
    },
]


def serve(s: Session) -> None:
    """A minimal MCP server: initialize, tools/list, tools/call, over newline-delimited JSON-RPC."""

    def send(obj: dict) -> None:
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}}, "serverInfo": {"name": "analyst", "version": "1"}}})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name, a = params.get("name"), params.get("arguments") or {}
            if name == "query":
                text = s.query(str(a.get("sql", "")))
            elif name == "docs":
                text = s.docs(str(a.get("path", "")))
            elif name == "save":
                text = s.save(str(a.get("name", "")), str(a.get("content", "")))
            else:
                text = f"No tool named {name}."
            send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}})
        elif mid is not None:
            send({"jsonrpc": "2.0", "id": mid, "result": {}})


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--stage", required=True, choices=sorted(SAVES))
    p.add_argument("--warehouse", type=Path, required=True)
    p.add_argument("--docs", type=Path, required=True)
    p.add_argument("--max-queries", type=int, default=MAX_QUERIES)
    p.add_argument("--prefix", default="q")
    a = p.parse_args()
    serve(Session(a.run, a.session, a.stage, a.warehouse, a.docs, a.max_queries, a.prefix))


if __name__ == "__main__":
    main()
