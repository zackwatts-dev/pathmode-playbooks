from datetime import date
from pathlib import Path

import late_invoices as li

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(li.__file__).parent / "sample-data"
AS_OF = date(2025, 10, 31)


def sample():
    return li.load(SAMPLE / "ar-aging.csv", SAMPLE / "payment-history.csv", SAMPLE / "replies")


def sorted_sample(tmp_path):
    accounts, _ = li.run(sample(), OfflineModel(li.offline), tmp_path, AS_OF)
    return {a.customer: a for a in accounts}


def test_customers_waiting_on_us_are_not_chased(tmp_path):
    by = sorted_sample(tmp_path)
    # 88 days overdue, but they asked for a W-9: we're the hold-up, so no call and no reminder.
    assert by["Avondale Holdings"].action == "answer"
    assert "W-9" in by["Avondale Holdings"].why
    assert by["Sahuarita Diner"].action == "answer"  # "Was INV-237568 paid?"
    assert not by["Avondale Holdings"].draft


def test_a_questioned_charge_is_resolved_first(tmp_path):
    by = sorted_sample(tmp_path)
    assert by["Sahuarita Unified School District"].action == "resolve"  # "covered under our agreement?"
    assert by["Rita Ranch Bakery"].action == "resolve"  # "two trip charges"
    assert not by["Sahuarita Unified School District"].draft


def test_the_rules_sort_the_rest(tmp_path):
    by = sorted_sample(tmp_path)
    assert by["Hometown Bank"].action == "call"  # 108 days overdue
    assert by["FitLife Gyms"].action == "personal"  # usually 24 days late
    assert by["Sedona Real Estate Group"].action == "personal"  # large balance
    assert by["Tanque Verde Realty Partners"].action == "automatic"
    assert by["Rita  Ranch Hardware"].action == "small"  # $25.44 left of a short payment


def test_records_problems_are_flagged(tmp_path):
    by = sorted_sample(tmp_path)
    assert any(
        "same customer as Oro Valley Unified School District Inc" in f
        for f in by["Oro Valley Unified School District"].flags
    )
    assert any("no due date on INV-240514" in f for f in by["FitLife Gyms"].flags)
    # An invoice with no due date isn't counted as overdue: it can't be.
    assert all(i.due for i in by["FitLife Gyms"].overdue(AS_OF))


def test_draft_amounts_come_from_the_ledger_not_the_model():
    a = sample()["Sedona Real Estate Group"]
    li.decide(a, AS_OF, 20, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["Hi,\n\nPlease pay.\n\n{{INVOICES}}\n\nThanks"]), "Summit")
    assert "- Total: $13,368.17" in a.draft
    assert "Invoice INV-232109" in a.draft
    assert not a.flags


def test_invented_numbers_in_a_draft_are_flagged():
    a = sample()["Sedona Real Estate Group"]
    li.decide(a, AS_OF, 20, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["You owe $9,999 plus a 15% late fee. {{INVOICES}}"]), "Summit")
    assert any("$9,999" in f and "15%" in f for f in a.flags)


def test_missing_placeholder_still_gets_the_invoice_list():
    a = sample()["Sedona Real Estate Group"]
    li.decide(a, AS_OF, 20, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["Hi, just checking in."]), "Summit")
    assert "Invoice INV-232109" in a.draft


def test_a_promise_is_waited_on_then_called():
    a = sample()["Hometown Bank"]
    li.read_reply(a, ScriptedModel(['{"kind": "promise", "promised_date": "2025-11-07", "note": ""}']))
    li.decide(a, AS_OF, 20, 5000, 60)
    assert a.action == "wait"
    li.decide(a, date(2025, 11, 10), 20, 5000, 60)
    assert a.action == "call" and "hasn't arrived" in a.why


def test_a_bad_promised_date_is_flagged_not_trusted():
    a = sample()["Hometown Bank"]
    li.read_reply(a, ScriptedModel(['{"kind": "promise", "promised_date": "November 7th", "note": ""}']))
    assert a.reading is None and any("isn't a real date" in f for f in a.flags)


def test_outputs(tmp_path):
    li.run(sample(), OfflineModel(li.offline), tmp_path, AS_OF)
    summary = (tmp_path / "summary.md").read_text()
    assert "Nothing was sent" in summary and "Over 90 days" in summary
    assert "**$507,030.18**" in summary  # Tucson's overdue total on October 31, 2025
    assert "Fix these records first" in summary
    assert (tmp_path / "actions.csv").exists()
    assert list((tmp_path / "drafts").glob("*.txt"))
