"""Shared helpers: reading the model's JSON, the command line, and writing output files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from common import llm
from common.fake import OfflineModel


class BadAnswer(ValueError):
    """The model's answer wasn't the JSON we asked for. Callers treat this as 'a person needs to look'."""


def parse_json(text: str) -> dict | list:
    """The first JSON object or array in the model's answer, tolerating code fences and stray prose."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    pairs = sorted((("{", "}"), ("[", "]")), key=lambda oc: (cleaned.find(oc[0]) == -1, cleaned.find(oc[0])))
    for opener, closer in pairs:
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise BadAnswer(f"No JSON in the model's answer: {text[:200]!r}")


def require(obj: dict, keys: Iterable[str]) -> dict:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise BadAnswer(f"The model's answer is missing {', '.join(missing)}")
    return obj


def parser(description: str, sample_dir: Path) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--sample", action="store_true", help=f"use the bundled sample data in {sample_dir.name}/")
    p.add_argument("--out", type=Path, default=Path("out"), help="folder for the results (default: out/)")
    p.add_argument("--dry-run", action="store_true", help="no AI: use the offline stand-in, to try it for free")
    return p


def model_for(args: argparse.Namespace, offline: Callable[[str, str], str]) -> llm.Model:
    if args.dry_run:
        return OfflineModel(offline)
    try:
        return llm.from_env()
    except llm.ModelError as e:
        sys.exit(str(e))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def done(model: llm.Model, written: list[Path], note: str) -> None:
    print(f"Model: {model.name}")
    for p in written:
        print(f"  wrote {p}")
    print(note)
