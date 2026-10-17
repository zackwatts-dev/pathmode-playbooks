import json
from datetime import date
from pathlib import Path

import rfq_intake as rq

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

SAMPLE = Path(rq.__file__).parent / "sample-data"
CATALOG = rq.Catalog(read_csv(SAMPLE / "catalog.csv"))
AS_OF = date(2026, 7, 13)


def requests():
    return {r.file: r for r in rq.read_requests(SAMPLE / "requests")}


def answer(**kw):
    base = {
        "is_rfq": True,
        "customer": "Desert Palms Plaza",
        "contact": "Dana Ortiz",
        "site": "2150 W Ray Rd",
        "quote_due": "2026-07-17",
        "needed_by": "",
        "items": [],
        "questions": [],
    }
    return json.dumps({**base, **kw})


def test_catalog_matches_by_code_alias_and_words():
    assert CATALOG.match("RTU-10T", "")[1] == "code"
    row, how = CATALOG.match("6 - 4L440 belts", "")
    assert (row["Code"], how) == ("BELT-A42", "alias")
    row, how = CATALOG.match("20 x 25 x 2 MERV13 pleated", "")
    assert row["Code"] == "FLT-20252-M13"
    assert CATALOG.match("new unit for the break room", "") == (None, "none")


def test_missing_quantity_and_unknown_item_become_questions():
    req = requests()["03-vague.eml"]
    model = ScriptedModel(
        [
            answer(
                site="",
                items=[
                    {"requested": "wifi thermostats", "quantity": None, "quote": "a couple of the wifi thermostats"},
                    {
                        "requested": "new unit for the break room",
                        "quantity": None,
                        "quote": "maybe a new unit for the break room",
                    },
                ],
            )
        ]
    )
    it = rq.intake(req, model, CATALOG)
    assert it.status == "needs info"
    assert any("How many wifi thermostats" in q for q in it.questions)
    assert any("model, size or part number" in q and "break room" in q and "how many" in q for q in it.questions)
    assert any("job site" in q for q in it.questions)


def test_items_not_in_the_email_and_bad_dates_are_flagged():
    req = requests()["01-filters.eml"]
    model = ScriptedModel(
        [
            answer(
                quote_due="Friday",
                items=[
                    {"requested": "20x25x2 MERV 13", "quantity": 24, "quote": "24 x 20x25x2 MERV 13"},
                    {"requested": "air purifier", "quantity": 2, "quote": "two air purifiers for the lobby"},
                ],
            )
        ]
    )
    it = rq.intake(req, model, CATALOG)
    assert it.lines[0].code == "FLT-20252-M13" and not it.lines[0].checks
    assert any("not found in the email" in c for c in it.lines[1].checks)
    assert it.quote_due is None and any("isn't a date" in n for n in it.notes)


def test_a_complete_request_is_ready_to_quote():
    req = requests()["01-filters.eml"]
    model = ScriptedModel(
        [
            answer(
                items=[
                    {"requested": "20x25x2 MERV 13", "quantity": 24, "quote": "24 x 20x25x2 MERV 13"},
                    {"requested": "16x20x2 MERV 13", "quantity": 12, "quote": "12 x 16x20x2 MERV 13"},
                ]
            )
        ]
    )
    it = rq.intake(req, model, CATALOG)
    assert it.status == "ready to quote" and it.quote_due == date(2026, 7, 17)


def test_not_an_rfq_is_set_aside():
    it = rq.intake(requests()["05-not-an-rfq.eml"], ScriptedModel(['{"is_rfq": false}']), CATALOG)
    assert it.status == "not a quote request" and not it.questions


def test_unreadable_answer_goes_to_a_person():
    it = rq.intake(requests()["01-filters.eml"], ScriptedModel(["Sure, looks like filters."]), CATALOG)
    assert it.status == "needs info" and any("read this one yourself" in n for n in it.notes)


def test_sample_dry_run(tmp_path):
    results, _ = rq.run(list(requests().values()), CATALOG, OfflineModel(rq.offline), tmp_path, AS_OF)
    by = {r.request.file: r for r in results}
    assert by["01-filters.eml"].status == "ready to quote"
    assert by["04-repeat-parts.eml"].status == "ready to quote"
    assert {li.code for li in by["04-repeat-parts.eml"].lines} == {"BELT-A42", "CAP-45-5", "THERM-PROG"}
    assert by["02-bid-invitation.eml"].quote_due == date(2026, 7, 22)
    assert by["03-vague.eml"].status == "needs info"
    assert by["05-not-an-rfq.eml"].status == "not a quote request"
    summary = (tmp_path / "summary.md").read_text()
    assert "Nothing was sent or priced" in summary
    assert (tmp_path / "questions" / "03-vague.eml").exists()
    assert not (tmp_path / "questions" / "01-filters.eml").exists()
