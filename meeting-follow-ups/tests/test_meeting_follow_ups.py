import json
from datetime import date
from pathlib import Path

import meeting_follow_ups as mf

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(mf.__file__).parent / "sample-data"
DAY = date(2026, 7, 13)


def transcript():
    return mf.read_transcript(SAMPLE / "ops-meeting-2026-07-13.vtt")


def test_reads_vtt_speakers():
    t = transcript()
    assert t.speakers == ["Rosa Martinez", "Jake Thompson", "Ann Lee"]
    assert "Jake Thompson: Yes, Wednesday morning works." in t.text


def test_reads_name_colon_text(tmp_path):
    path = tmp_path / "t.txt"
    path.write_text("Rosa: Let's start.\nAnn Lee: I can do it.\n")
    assert mf.read_transcript(path).speakers == ["Rosa", "Ann Lee"]


def test_checks_owners_dates_and_quotes():
    answer = {
        "decisions": [{"decision": "Buy a boat", "quote": "we will buy a boat today"}],
        "tasks": [
            {
                "task": "Pull the PM customer list",
                "owner": "Ann",
                "due": "2026-07-17",
                "quote": "I can pull the list of PM customers",
            },
            {"task": "Compare van lease", "owner": "", "due": "", "quote": "compare it with the lease option"},
            {"task": "Order parts", "owner": "Bob", "due": "2026-07-01", "quote": "order the parts"},
            {"task": "Call Tom", "owner": "Rosa", "due": "Friday", "quote": "I'll call Tom myself today"},
        ],
    }
    m = mf.extract(transcript(), DAY, ScriptedModel([json.dumps(answer)]))
    checks = [x["check"] for x in m.tasks]
    assert checks[0] == ""
    assert "nobody owns this" in checks[1] and "no due date" in checks[1]
    assert "Bob wasn't a speaker" in checks[2] and "before the meeting" in checks[2]
    assert "not found in the transcript" in checks[2]
    assert "'Friday' isn't a date" in checks[3]
    assert any("Buy a boat" in f for f in m.flags)


def test_dry_run_finds_the_unowned_van_task(tmp_path):
    m, _ = mf.run(transcript(), DAY, OfflineModel(mf.offline), tmp_path)
    van = [x for x in m.tasks if "van" in x["task"].lower() or "lease" in x["task"].lower()]
    assert van and van[0]["owner"] == ""
    ann = [x for x in m.tasks if x["owner"].startswith("Ann")]
    assert ann and ann[0]["due"] == "2026-07-17"  # "by Friday"
    assert "Check these first" in (tmp_path / "minutes.md").read_text()
    assert (tmp_path / "tasks.csv").read_text().startswith("Title,Assigned to,Due date,Notes")
