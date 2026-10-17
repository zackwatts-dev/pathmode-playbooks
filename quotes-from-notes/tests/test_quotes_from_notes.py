import json
from datetime import date
from pathlib import Path

import pytest
import quotes_from_notes as qn

from common.fake import OfflineModel, ScriptedModel
from common.util import BadAnswer

SAMPLE = Path(qn.__file__).parent / "sample-data"
NOTES = (SAMPLE / "call-notes.md").read_text()
PRICES = qn.load_prices(SAMPLE / "price-list.csv")


def answer(lines, **extra):
    return json.dumps(
        {"customer": "Lee", "contact": "Marcus", "site": "Gilbert", "scope_summary": "s", "lines": lines, **extra}
    )


def test_code_does_the_math_with_list_prices():
    model = ScriptedModel(
        [
            answer(
                [
                    {"code": "RTU-10T", "quantity": 2, "quote": "Two rooftop units, both 10 ton"},
                    {"code": "LAB-INST", "quantity": 32, "quote": "2 techs, so 32 hours"},
                ]
            )
        ]
    )
    q = qn.build(NOTES, PRICES, model, tax_rate=0.05)
    assert q.subtotal == 2 * 14800 + 32 * 135
    assert q.tax == round(q.subtotal * 0.05, 2)
    assert not q.flags


def test_a_price_from_the_model_is_ignored():
    model = ScriptedModel([answer([{"code": "RTU-10T", "quantity": 1, "unit_price": 1, "quote": "both 10 ton"}])])
    assert qn.build(NOTES, PRICES, model, 0).subtotal == 14800


def test_items_off_the_list_or_not_in_the_notes_are_flagged():
    model = ScriptedModel(
        [
            answer(
                [
                    {"code": "GOLD-PLATING", "quantity": 1, "quote": "x"},
                    {"code": "PERMIT", "quantity": 1, "quote": "permit pulled by the city"},
                    {"code": "THERM-PROG", "quantity": "a few", "quote": "Wants new thermostats too"},
                ]
            )
        ]
    )
    q = qn.build(NOTES, PRICES, model, 0)
    assert [li.code for li in q.lines] == ["PERMIT"]
    assert any("isn't on your price list" in f for f in q.flags)
    assert any("PERMIT" in f and "isn't clearly in your notes" in f for f in q.flags)
    assert any("no usable quantity" in f for f in q.flags)


def test_unreadable_answer_raises():
    with pytest.raises(BadAnswer):
        qn.build(NOTES, PRICES, ScriptedModel(["I'd suggest two units."]), 0)


def test_dry_run_on_the_sample(tmp_path):
    q = qn.build(NOTES, PRICES, OfflineModel(qn.offline), 0)
    codes = {li.code: li.quantity for li in q.lines}
    assert codes["RTU-10T"] == 2 and codes["LAB-INST"] == 32 and codes["CRANE-HALF"] == 1
    md = qn.quote_md(q, date(2026, 7, 13))
    assert "Lee Family Restaurants" in md and "**Total:**" in md
    assert "Before you send" in qn.check_md(q)
    pytest.importorskip("docx")
    assert qn.write_docx(q, tmp_path / "quote.docx", date(2026, 7, 13)).exists()
