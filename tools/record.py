"""Record a real model's answers on a playbook's sample data, for `--replay`.

    PLAYBOOK_PROVIDER=anthropic ANTHROPIC_API_KEY=... python tools/record.py estimate-check
    python tools/record.py estimate-check --cli      # through the `claude` command line instead (Claude Sonnet 5.5)

It imports the playbook's main script, runs it on the sample with a model that passes every call through to the
real one (common/llm.py, from the environment) and keeps each answer under the playbook's `replay_key()`. Then it
writes `<slug>/sample-data/recorded-run.json`: {"model": ..., "recorded": ..., "answers": {key: answer}}.

The playbook needs `replay_key(system, user)`, and either `sample_run(model, out)` or a `main()` that gets its
model from `model_for` (the recorder stands in for it and runs `main()` with `--sample`). It costs real API calls.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from common import llm  # noqa: E402


class Recording:
    """Passes each call to the real model and keeps the answer by the playbook's replay key."""

    def __init__(self, inner, key, keep: dict[str, str] | None = None):
        self.inner, self.key, self.name = inner, key, inner.name
        self.keep = keep or {}  # answers already recorded for exactly these inputs (--keep): reused, not re-asked
        self.answers: dict[str, str] = {}
        self.failed: list[str] = []
        self.calls = 0  # real calls made in this recording
        self.reused = 0  # answers kept from an earlier recording of exactly the same inputs

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        k = self.key(system, user)
        if k in self.answers:  # asked again (a playbook that runs the sample two ways): the same answer, no new call
            return self.answers[k]
        if k in self.keep:  # recorded before, for the very same inputs (the key fingerprints them)
            self.answers[k] = self.keep[k]
            self.reused += 1
            return self.answers[k]
        self.calls += 1
        try:
            answer = self.inner.complete(system, user, max_tokens)
        except Exception:
            self.failed.append(k)
            raise
        self.answers[k] = answer
        return answer


class ClaudeCLI:
    """Claude Sonnet 5.5 through the `claude` command line, with no tools, run from an empty folder so it reads
    nothing but the prompt."""

    name = "claude-sonnet-5-5 (via the claude CLI)"

    def __init__(self):
        self.empty = tempfile.mkdtemp(prefix="record-")

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        cmd = ["claude", "-p", "--model", "claude-sonnet-5-5", "--system-prompt", system, "--tools", ""]
        done = subprocess.run(cmd, input=user, capture_output=True, text=True, cwd=self.empty, timeout=300)
        if done.returncode != 0 or not done.stdout.strip():
            raise llm.ModelError(f"claude CLI failed: {done.stderr.strip()[:200]}")
        return done.stdout.strip()


class _Collect:
    """A stand-in that answers nothing: it notes each call the sample run would make, and fails it."""

    name = "collect"

    def __init__(self, key, known):
        self.key, self.known, self.asks = key, known, {}

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        k = self.key(system, user)
        if k in self.known:
            return self.known[k]
        self.asks[k] = (system, user, max_tokens)
        raise llm.ModelError("collecting")


def prefetch(module, model: Recording, n: int, run=None) -> None:
    """Ask every call the sample run makes (or `run(model, out)`, if given), n at a time, into the recording, as real
    calls. The run afterwards finds them answered, and asks anything that only comes up after an answer (a retry)
    itself."""
    from concurrent.futures import ThreadPoolExecutor

    def ask(item):
        k, (system, user, max_tokens) = item
        try:
            return k, model.inner.complete(system, user, max_tokens)
        except Exception:  # noqa: BLE001 - left for the run afterwards to ask again
            return k, None

    # Calls that depend on an earlier answer (a checker that reads the reader's answer) show up on the next pass.
    for _ in range(4):
        collect = _Collect(model.key, {**model.keep, **model.answers})
        with tempfile.TemporaryDirectory() as out:
            (run or module.sample_run)(collect, Path(out))
        if not collect.asks:
            break
        with ThreadPoolExecutor(n) as pool:
            for k, answer in pool.map(ask, collect.asks.items()):
                if answer is not None:
                    model.answers[k] = answer
                    model.calls += 1


def load(slug: str):
    folder = ROOT / slug
    script = folder / f"{slug.replace('-', '_')}.py"
    if not script.exists():
        raise SystemExit(f"No {script.relative_to(ROOT)}")
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(script.stem, script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[script.stem] = module
    spec.loader.exec_module(module)
    return folder, module


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("slug", help="the playbook's folder, e.g. estimate-check")
    p.add_argument("extra", nargs="*", help="extra arguments for the playbook's main(), after --")
    p.add_argument("--cli", action="store_true", help="call Claude Sonnet 5.5 through the claude command line")
    p.add_argument(
        "--keep", action="store_true", help="reuse recorded answers whose inputs haven't changed; ask only the rest"
    )
    p.add_argument(
        "--parallel",
        type=int,
        default=0,
        metavar="N",
        help="ask N calls at a time (for a playbook whose sample run keeps going when a call fails, as RFQ intake's)",
    )
    args = p.parse_args()
    folder, module = load(args.slug)
    if not hasattr(module, "replay_key"):
        raise SystemExit(f"{args.slug} has no replay_key(): it can't be replayed, so there's nothing to record.")
    try:
        inner = ClaudeCLI() if args.cli else llm.from_env()
    except llm.ModelError as e:
        raise SystemExit(str(e)) from e
    path = folder / "sample-data" / "recorded-run.json"
    keep = json.loads(path.read_text())["answers"] if args.keep and path.exists() else {}
    model = Recording(inner, module.replay_key, keep)
    if args.parallel and hasattr(module, "sample_run"):
        prefetch(module, model, args.parallel)
    with tempfile.TemporaryDirectory() as out:
        if hasattr(module, "sample_run"):
            module.sample_run(model, Path(out))
        else:
            module.model_for = lambda *_: model
            sys.argv = [module.__file__, "--sample", "--out", out, *args.extra]
            module.main()
    data = {
        "model": inner.name,
        "recorded": date.today().isoformat(),
        # How this recording was made, so a cherry-picked one can't pass for a first try.
        "calls": model.calls,
        "reused_from_earlier_recording": model.reused,
        "failed_calls": len(model.failed),
        "answers": dict(sorted(model.answers.items())),
    }
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Recorded {len(model.answers)} answers from {inner.name} to {path.relative_to(ROOT)}.")
    if model.failed:
        print(f"{len(model.failed)} calls failed and weren't recorded: {', '.join(model.failed)}. Run it again.")


if __name__ == "__main__":
    main()
