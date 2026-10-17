"""Meeting follow-ups: decisions, tasks with owners and dates, and a follow-up email, from a transcript.

    python meeting-follow-ups/meeting_follow_ups.py --sample --dry-run
    python meeting-follow-ups/meeting_follow_ups.py --transcript meeting.vtt --date 2026-07-13

Reads a transcript downloaded from Teams, Zoom or Meet (.vtt, .txt with "Name: words", or .docx). Every
decision and task has to quote the transcript; code checks that the quote is really there, that each task
has an owner who was in the meeting, and that each date is real. Anything that fails is flagged, not
dropped: a task nobody owns is exactly what this is for.

Writes out/minutes.md, out/tasks.csv (to import into your task tool) and out/follow-up.txt. Nothing is sent.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.evidence import quote_found  # noqa: E402
from common.util import BadAnswer, done, model_for, parse_json, parser, require, write_csv, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"
SAMPLE_DATE = date(2026, 7, 13)

EXTRACT = """You turn a meeting transcript into minutes. The meeting was on {day}. Answer with JSON only:
{{"decisions": [{{"decision": "what was decided", "quote": "the exact words from the transcript"}}],
 "tasks": [{{"task": "start with a verb", "owner": "a person's name, or empty if nobody took it",
            "due": "YYYY-MM-DD, or empty if no date was said", "quote": "the exact words"}}],
 "open_questions": ["things raised but not decided"],
 "follow_up_email": "a short email to the attendees: decisions, then who does what by when"}}
Rules: only what was said. A task belongs to someone only if they took it or were clearly given it. Turn
"Friday" or "next Monday" into a date counted from the meeting date. Don't invent owners or dates."""


@dataclass
class Transcript:
    speakers: list[str]
    text: str


@dataclass
class Minutes:
    decisions: list[dict] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    email: str = ""
    flags: list[str] = field(default_factory=list)


def read_transcript(path: Path) -> Transcript:
    if path.suffix.lower() == ".docx":
        import docx  # type: ignore

        raw = "\n".join(p.text for p in docx.Document(path).paragraphs)
    else:
        raw = path.read_text(encoding="utf-8", errors="replace")
    lines, speakers = [], []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        m = re.match(r"<v ([^>]+)>(.*?)(</v>)?$", line) or re.match(r"([A-Z][\w.' -]{1,40}):\s+(.*)", line)
        if m:
            speaker, words = m.group(1).strip(), m.group(2).strip()
            if speaker not in speakers:
                speakers.append(speaker)
            lines.append(f"{speaker}: {words}")
        else:
            lines.append(line)
    return Transcript(speakers, "\n".join(lines))


def owner_in(owner: str, speakers: list[str]) -> bool:
    first = owner.split()[0].lower() if owner.split() else ""
    return bool(first) and any(first == s.split()[0].lower() for s in speakers)


def extract(t: Transcript, day: date, model) -> Minutes:
    answer = parse_json(model.complete(EXTRACT.format(day=f"{day:%A, %B %-d, %Y}"), f"<<<TRANSCRIPT\n{t.text}\n>>>"))
    require(answer, ["decisions", "tasks"])
    m = Minutes(
        open_questions=[str(q) for q in answer.get("open_questions") or []],
        email=str(answer.get("follow_up_email", "")),
    )
    for d in answer["decisions"]:
        if not quote_found(str(d.get("quote", "")), t.text):
            m.flags.append(f"Decision not found in the transcript, check it: {d.get('decision')}")
        m.decisions.append(d)
    for task in answer["tasks"]:
        problems = []
        owner, due = str(task.get("owner") or "").strip(), str(task.get("due") or "").strip()
        if not owner:
            problems.append("nobody owns this")
        elif not owner_in(owner, t.speakers):
            problems.append(f"{owner} wasn't a speaker in this meeting")
        if due:
            try:
                d = date.fromisoformat(due)
                if d < day:
                    problems.append(f"due {due} is before the meeting")
                elif d > day + timedelta(days=365):
                    problems.append(f"due {due} is more than a year away")
            except ValueError:
                problems.append(f"{due!r} isn't a date")
                due = ""
        else:
            problems.append("no due date")
        if not quote_found(str(task.get("quote", "")), t.text):
            problems.append("not found in the transcript")
        m.tasks.append(
            {
                "task": str(task.get("task", "")),
                "owner": owner,
                "due": due,
                "quote": str(task.get("quote", "")),
                "check": "; ".join(problems),
            }
        )
    return m


def minutes_md(m: Minutes, day: date, t: Transcript, model_name: str) -> str:
    lines = [
        f"# Meeting, {day:%B %-d, %Y}",
        "",
        f"Attendees (speakers): {', '.join(t.speakers)}",
        "",
        f"Drafted by {model_name} from the transcript. Check it before you send it.",
        "",
    ]
    needs = [x for x in m.tasks if x["check"]]
    if needs or m.flags:
        lines += ["## Check these first", ""]
        lines += [f"- **{x['task']}**: {x['check']}" for x in needs] + [f"- {f}" for f in m.flags] + [""]
    lines += ["## Decisions", ""] + [f"- {d.get('decision')}" for d in m.decisions] + [""]
    lines += ["## Tasks", "", "| Task | Owner | Due |", "|---|---|---|"]
    lines += [f"| {x['task']} | {x['owner'] or '**nobody**'} | {x['due'] or '**no date**'} |" for x in m.tasks]
    if m.open_questions:
        lines += ["", "## Still open", ""] + [f"- {q}" for q in m.open_questions]
    return "\n".join(lines) + "\n"


# Offline stand-in: looks for a few phrasings of commitments, sentence by sentence. A model catches far more.
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _due(sentence: str, day: date) -> str:
    lower = sentence.lower()
    if "today" in lower:
        return day.isoformat()
    found = [(lower.find(w), w) for w in WEEKDAYS if w in lower]
    if not found:
        return ""
    _, when = min(found)
    ahead = (WEEKDAYS.index(when) - day.weekday()) % 7 or 7
    return (day + timedelta(days=ahead + (7 if f"next {when}" in lower else 0))).isoformat()


def offline(system: str, user: str) -> str:
    day = datetime.strptime(re.search(r"on \w+, (\w+ \d+, \d{4})", system).group(1), "%B %d, %Y").date()
    tasks, decisions, questions = [], [], []
    for line in (ln for ln in user.splitlines() if ": " in ln):
        speaker, words = line.split(": ", 1)
        for sentence in re.split(r"(?<=[.?!])\s+", words):
            lower = sentence.lower()
            mine = re.search(r"\bI(?:'ll| can| will) (.+?)[.?!]?$", sentence)
            named = re.search(r"\b([A-Z][a-z]+), (?:can you (.+?)|by (\w+))[.?!]?(?: please)?[.?!]?$", sentence)
            if mine:
                tasks.append({"task": mine.group(1), "owner": speaker, "due": _due(sentence, day), "quote": sentence})
            elif named:
                owner = named.group(1)
                earlier = next((t for t in reversed(tasks) if t["owner"].split()[0] == owner and not t["due"]), None)
                if earlier and named.group(3):
                    earlier["due"], earlier["quote"] = _due(sentence, day), earlier["quote"]
                else:
                    tasks.append(
                        {
                            "task": named.group(2) or sentence,
                            "owner": owner,
                            "due": _due(sentence, day),
                            "quote": sentence,
                        }
                    )
            elif re.search(r"someone should|somebody needs to", lower):
                task = re.split(r"someone should |somebody needs to ", sentence, flags=re.I)[-1]
                tasks.append({"task": task.rstrip("."), "owner": "", "due": "", "quote": sentence})
            elif re.search(r"let's talk about|next week", lower):
                questions.append(sentence.rstrip("."))
            elif re.search(r"^(and )?no \w+ charge|pause the|^then let's|^let's (send|move|go)", lower):
                decisions.append({"decision": sentence.rstrip("."), "quote": sentence})
    return json.dumps(
        {
            "decisions": decisions,
            "tasks": tasks,
            "open_questions": questions,
            "follow_up_email": "Thanks, everyone. Here's what we decided and who's doing what.",
        }
    )


def follow_up(m: Minutes) -> str:
    tasks = "\n".join(
        f"- {x['owner'] or 'Nobody yet'}: {x['task']}" + (f", by {x['due']}" if x["due"] else "") for x in m.tasks
    )
    return f"Subject: Follow-up from today's meeting\n\n{m.email.strip()}\n\nWho's doing what:\n{tasks}\n"


def run(t: Transcript, day: date, model, out: Path) -> tuple[Minutes, list[Path]]:
    m = extract(t, day, model)
    rows = [
        {
            "Title": x["task"],
            "Assigned to": x["owner"],
            "Due date": x["due"],
            "Notes": f'From the meeting on {day}: "{x["quote"]}"' + (f" CHECK: {x['check']}" if x["check"] else ""),
        }
        for x in m.tasks
    ]
    written = [
        write_text(out / "minutes.md", minutes_md(m, day, t, model.name)),
        write_csv(out / "tasks.csv", rows, ["Title", "Assigned to", "Due date", "Notes"]),
        write_text(out / "follow-up.txt", follow_up(m)),
    ]
    return m, written


def main() -> None:
    p = parser("Turn a meeting transcript into decisions, owned tasks and a follow-up email. Never sends.", SAMPLE)
    p.add_argument("--transcript", type=Path, help=".vtt, .txt or .docx")
    p.add_argument("--date", type=date.fromisoformat, help="meeting date (default: today)")
    args = p.parse_args()
    if args.sample:
        path, day = SAMPLE / "ops-meeting-2026-07-13.vtt", args.date or SAMPLE_DATE
    elif args.transcript:
        path, day = args.transcript, args.date or date.today()
    else:
        p.error("choose --sample or --transcript")
    model = model_for(args, offline)
    try:
        m, written = run(read_transcript(path), day, model, args.out)
    except BadAnswer as e:
        sys.exit(f"The model's answer couldn't be read ({e}). Try again.")
    unowned = sum(1 for x in m.tasks if not x["owner"])
    done(model, written, f"{len(m.decisions)} decisions, {len(m.tasks)} tasks, {unowned} without an owner.")


if __name__ == "__main__":
    main()
