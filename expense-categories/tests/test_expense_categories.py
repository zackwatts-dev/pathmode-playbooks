import json
from pathlib import Path

import expense_categories as ec

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

SAMPLE = Path(ec.__file__).parent / "sample-data"
CHART = read_csv(SAMPLE / "chart-of-accounts.csv")
RULES = read_csv(SAMPLE / "rules.csv")


def txns():
    return [
        ec.Txn(i, r["Date"], r["Description"], float(r["Amount"]))
        for i, r in enumerate(read_csv(SAMPLE / "transactions.csv"), 1)
    ]


def test_rules_run_first_and_the_model_never_sees_them(tmp_path):
    model = OfflineModel(ec.offline)
    result, _, _ = ec.run(txns(), CHART, RULES, model, tmp_path)
    shell = next(t for t in result if t.description.startswith("SHELL"))
    assert (shell.account, shell.source) == ("Fuel", "rule")
    assert "SHELL OIL" not in model.calls[0][1]


def test_accounts_off_the_chart_and_low_confidence_go_to_review(tmp_path):
    items = [ec.Txn(1, "2026-07-01", "MYSTERY LLC", -50.0), ec.Txn(2, "2026-07-01", "HOME DEPOT #1", -80.0)]
    model = ScriptedModel(
        [
            json.dumps(
                [
                    {"id": 1, "account": "Miscellaneous", "confidence": 0.95, "reason": "?"},
                    {"id": 2, "account": "tools and small equipment", "confidence": 0.4, "reason": "hardware store"},
                ]
            )
        ]
    )
    _, review, _ = ec.run(items, CHART, [], model, tmp_path)
    assert [t.id for t in review] == [1, 2]
    assert "isn't on your chart" in review[0].note
    assert review[1].account == "Tools and small equipment" and "not sure" in review[1].note


def test_always_review_large_transfers_and_meals(tmp_path):
    result, review, _ = ec.run(txns(), CHART, RULES, OfflineModel(ec.offline), tmp_path)
    notes = {t.description: t.note for t in review}
    assert "large amount" in notes["FERGUSON ENT #1032"]  # matched a rule, but still over the threshold
    assert "transfer to a person" in notes["ZELLE TO J MARTINEZ"]
    assert "Meals" in notes["OLIVE GARDEN 1182"]


def test_suggests_rules_from_confident_answers():
    items = [ec.Txn(i, "2026-07-01", f"DISCOUNT TIRE #{i}", -100.0, "Vehicle repairs", "ai", 0.95) for i in (1, 2)]
    assert ec.suggested_rules(items, RULES, 0.9) == [
        {"If description contains": "DISCOUNT TIRE", "Account": "Vehicle repairs", "Seen": 2}
    ]


def test_merchant_names():
    assert ec.merchant("AMZN MKTP US*2K4LL81") == "AMZN MKTP US"
    assert ec.merchant("SHELL OIL 57442 CHANDLER AZ") == "SHELL OIL"


def test_unreadable_model_answer_sends_everything_to_review(tmp_path):
    items = [ec.Txn(1, "2026-07-01", "MYSTERY LLC", -50.0)]
    _, review, _ = ec.run(items, CHART, [], ScriptedModel(["sorry"]), tmp_path)
    assert review and "no suggestion" in review[0].note
