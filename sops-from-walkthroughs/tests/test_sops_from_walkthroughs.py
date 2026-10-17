import json
from datetime import date
from pathlib import Path

import sops_from_walkthroughs as sw

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(sw.__file__).parent / "sample-data"
TRANSCRIPT = (SAMPLE / "walkthrough-closing-a-ticket.txt").read_text()


def test_steps_not_in_the_walkthrough_are_marked():
    answer = {
        "title": "Close out a ticket",
        "steps": [
            {"step": "Open the dispatch board", "quote": "I open the dispatch board and filter"},
            {"step": "Call the customer to confirm", "quote": "call every customer to confirm satisfaction"},
        ],
    }
    sop = sw.build(TRANSCRIPT, ScriptedModel([json.dumps(answer)]))
    assert [s["grounded"] for s in sop["steps"]] == [True, False]
    md = sw.sop_md(sop, "Ann Lee", date(2026, 7, 13), "scripted")
    assert "Call the customer to confirm** *(not in the walkthrough" in md
    assert "Review by:** January 11, 2027" in md


def test_dry_run_finds_steps_and_the_single_point_of_failure():
    sop = sw.build(TRANSCRIPT, OfflineModel(sw.offline))
    assert len(sop["steps"]) >= 4 and all(s["grounded"] for s in sop["steps"])
    assert any("nobody else" in x for x in sop["single_points_of_failure"])
    md = sw.sop_md(sop, "Ann Lee", date(2026, 7, 13), "offline")
    assert "Only one person knows this" in md
