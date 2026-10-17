from datetime import date
from pathlib import Path

import late_invoices as li

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(li.__file__).parent / "sample-data"
AS_OF = date(2026, 7, 13)


def sample():
    return li.load(SAMPLE / "ar-aging.csv", SAMPLE / "payment-history.csv", SAMPLE / "replies")


def test_rules_sort_the_sample_ledger():
    accounts, _ = li.run(sample(), OfflineModel(li.offline), Path("/tmp/li-test"), AS_OF)
    by = {a.customer: a for a in accounts}
    assert by["Canyon Offices"].action == "none"  # not due yet
    assert by["Tempe Lofts"].action == "automatic"  # usually on time
    assert by["Desert Palms Plaza"].action == "automatic"
    assert by["Saguaro Retail Group"].action == "resolve"  # disputed in their reply
    assert by["Lee Family Restaurants"].action == "call"  # promised July 3, still unpaid
    assert by["Riverside Medical Group"].action == "wait"  # promised July 24
    assert by["Valley Unified School District"].action == "personal"  # usually late
    assert any("terms" in f for f in by["Riverside Medical Group"].flags)


def test_draft_amounts_come_from_the_ledger_not_the_model():
    accounts = sample()
    a = accounts["Valley Unified School District"]
    li.decide(a, AS_OF, 5, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["Hi,\n\nPlease pay.\n\n{{INVOICES}}\n\nThanks"]), "Summit")
    assert "Invoice 88120, due June 14: $8,400.00" in a.draft
    assert not a.flags


def test_invented_numbers_in_a_draft_are_flagged():
    a = sample()["Valley Unified School District"]
    li.decide(a, AS_OF, 5, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["You owe $9,999 plus a 15% late fee. {{INVOICES}}"]), "Summit")
    assert any("$9,999" in f and "15%" in f for f in a.flags)


def test_missing_placeholder_still_gets_the_invoice_list():
    a = sample()["Valley Unified School District"]
    li.decide(a, AS_OF, 5, 5000, 60)
    li.draft_email(a, AS_OF, ScriptedModel(["Hi, just checking in."]), "Summit")
    assert "Invoice 88120" in a.draft


def test_a_bad_promised_date_is_flagged_not_trusted():
    a = sample()["Lee Family Restaurants"]
    li.read_reply(a, ScriptedModel(['{"kind": "promise", "promised_date": "July 3rd", "note": ""}']))
    assert a.promise is None and any("isn't a real date" in f for f in a.flags)


def test_outputs(tmp_path):
    _, written = li.run(sample(), OfflineModel(li.offline), tmp_path, AS_OF)
    summary = (tmp_path / "summary.md").read_text()
    assert "Nothing was sent" in summary and "Over 90 days" in summary
    assert (tmp_path / "actions.csv").exists()
    assert list((tmp_path / "drafts").glob("*.txt"))
