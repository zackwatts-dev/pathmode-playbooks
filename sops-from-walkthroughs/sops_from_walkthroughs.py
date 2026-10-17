"""SOPs from walkthroughs: turn a recorded "here's how I do it" into a written procedure.

    python sops-from-walkthroughs/sops_from_walkthroughs.py --sample --dry-run
    python sops-from-walkthroughs/sops_from_walkthroughs.py --transcript walkthrough.txt --owner "Ann Lee"

Record the person who does the job talking through it while they do it, get the transcript, and run this.
Each step must quote what the person said; code checks the quotes, so a step the model added on its own is
marked "not in the walkthrough" for the person to confirm or delete. The open questions are often the most
useful part: they're what only one person knows.

Writes out/sop.md. Nothing leaves your computer except the transcript sent to the model.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.evidence import quote_found  # noqa: E402
from common.util import BadAnswer, done, model_for, parse_json, parser, require, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"

EXTRACT = """You turn a transcript of someone explaining how they do a task into a standard operating
procedure (SOP) someone else could follow. Answer with JSON only:
{"title": "verb + object, e.g. Close out a service ticket",
 "purpose": "one sentence: why this matters",
 "when": "when or how often it's done",
 "tools": ["systems, files, places used"],
 "steps": [{"step": "imperative, short", "detail": "what to check or watch for", "quote": "their exact words"}],
 "checks": ["things that must be true before it's done"],
 "exceptions": [{"if": "the situation", "then": "what to do", "quote": "their exact words"}],
 "open_questions": ["what a new person would still need to ask"],
 "single_points_of_failure": ["knowledge only one person seems to have"]}
Use only what the transcript says. Keep the person's own terms for screens and buttons. If something is
unclear, put it in open_questions rather than guessing."""


def build(transcript: str, model) -> dict:
    sop = require(
        parse_json(model.complete(EXTRACT, f"<<<TRANSCRIPT\n{transcript}\nTRANSCRIPT>>>")), ["title", "steps"]
    )
    for item in [*sop.get("steps", []), *sop.get("exceptions", [])]:
        item["grounded"] = quote_found(str(item.get("quote", "")), transcript)
    return sop


def sop_md(sop: dict, owner: str, today: date, model_name: str) -> str:
    ungrounded = [s for s in sop["steps"] if not s["grounded"]]
    lines = [
        f"# {sop['title']}",
        "",
        f"**Owner:** {owner or '(name the person responsible)'}  ",
        f"**Written:** {today:%B %-d, %Y} from a recorded walkthrough  ",
        f"**Review by:** {today + timedelta(days=182):%B %-d, %Y}  ",
        f"**Status:** Draft by {model_name}. "
        "Have the person who does this job read it, then have someone else follow it once.",
        "",
    ]
    if sop.get("purpose"):
        lines += [f"**Why it matters:** {sop['purpose']}", ""]
    if sop.get("when"):
        lines += [f"**When:** {sop['when']}", ""]
    if sop.get("tools"):
        lines += ["**You'll need:** " + ", ".join(sop["tools"]), ""]
    lines += ["## Steps", ""]
    for i, s in enumerate(sop["steps"], 1):
        mark = "" if s["grounded"] else " *(not in the walkthrough: confirm or delete)*"
        lines.append(f"{i}. **{s['step']}**{mark}")
        if s.get("detail"):
            lines.append(f"   {s['detail']}")
    lines.append("")
    if sop.get("exceptions"):
        lines += ["## If something's different", ""]
        for e in sop["exceptions"]:
            mark = "" if e["grounded"] else " *(not in the walkthrough: confirm or delete)*"
            lines.append(f"- **If {e['if']}:** {e['then']}{mark}")
        lines.append("")
    if sop.get("checks"):
        lines += ["## Done when", ""] + [f"- [ ] {c}" for c in sop["checks"]] + [""]
    if sop.get("open_questions") or ungrounded:
        lines += ["## Questions to answer before this is final", ""] + [f"- {q}" for q in sop.get("open_questions", [])]
        lines.append("")
    if sop.get("single_points_of_failure"):
        lines += ["## Only one person knows this", "", "Teach a second person these, first:", ""]
        lines += [f"- {x}" for x in sop["single_points_of_failure"]] + [""]
    return "\n".join(lines)


def offline(system: str, user: str) -> str:
    """Offline stand-in: one step per sentence that starts with an action. A model writes a real SOP."""
    text = user.split("<<<TRANSCRIPT", 1)[-1].split("TRANSCRIPT>>>")[0]
    speech = " ".join(line.split(": ", 1)[-1] for line in text.strip().splitlines())
    sentences = re.split(r"(?<=[.?!])\s+", speech)
    steps, exceptions = [], []
    for s in sentences:
        m = re.match(r"(?:First|Then|Last thing,|Next),? (?:I )?(.+?)[.?!]$", s)
        if m:
            steps.append({"step": m.group(1)[0].upper() + m.group(1)[1:], "detail": "", "quote": s})
        elif re.match(r"If ", s):
            cond, _, then = s[3:].partition(",")
            if then.strip():
                exceptions.append({"if": cond.strip(), "then": then.strip().rstrip("."), "quote": s})
    spof = [s.rstrip(".") for s in sentences if re.search(r"nobody else|only (I|one)", s, re.I)]
    return json.dumps(
        {
            "title": "Procedure from the walkthrough",
            "purpose": "",
            "when": "",
            "tools": [],
            "steps": steps,
            "checks": [],
            "exceptions": exceptions,
            "open_questions": ["Who covers this when the owner is out?"],
            "single_points_of_failure": spof,
        }
    )


def main() -> None:
    p = parser("Turn a walkthrough transcript into a written procedure.", SAMPLE)
    p.add_argument("--transcript", type=Path)
    p.add_argument("--owner", default="")
    args = p.parse_args()
    if args.sample:
        path, owner = SAMPLE / "walkthrough-closing-a-ticket.txt", args.owner or "Ann Lee"
    elif args.transcript:
        path, owner = args.transcript, args.owner
    else:
        p.error("choose --sample or --transcript")
    model = model_for(args, offline)
    try:
        sop = build(path.read_text(encoding="utf-8"), model)
    except BadAnswer as e:
        sys.exit(f"The model's answer couldn't be read ({e}). Try again.")
    written = [write_text(args.out / "sop.md", sop_md(sop, owner, date.today(), model.name))]
    ungrounded = sum(1 for s in sop["steps"] if not s["grounded"])
    done(model, written, f"{len(sop['steps'])} steps, {ungrounded} not found in the walkthrough.")


if __name__ == "__main__":
    main()
