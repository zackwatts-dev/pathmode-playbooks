# ruff: noqa: E501  (fixture rows read better on one line)
"""The quote desk's additions (design.md, steps 2, 5, 6 and 7; plan.md): attachments read, the history brief and
fast-track for repeat parts, bid odds, the queue order with them, and the desk in the queue replay. No AI is called."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import desk
import replay_queue as rq
import rfq_intake as ri

AS_OF = date(2024, 5, 1)


# --- attachments --------------------------------------------------------------------------------------------------
def eml(tmp: Path, body: str, attachments: list[tuple[str, str, bytes]]) -> Path:
    msg = EmailMessage()
    msg["From"] = "Kim Buyer <kbuyer@lutzairsystems.example>"
    msg["To"] = "quotes@wendlow.example"
    msg["Subject"] = "RFQ"
    msg["Date"] = "Mon, 06 May 2024 09:00:00 -0400"
    msg.set_content(body)
    for name, kind, data in attachments:
        main, sub = kind.split("/")
        msg.add_attachment(data, maintype=main, subtype=sub, filename=name)
    p = tmp / "a.eml"
    p.write_bytes(bytes(msg))
    return p


def test_a_parts_list_attachment_is_read_and_its_words_count_as_evidence(tmp_path):
    csv_text = b"Item,Part number,Rev,Description,Qty,Need by\n1,LUT-11111,A,bracket,25,2024-06-03\n"
    m = ri.read_mail(
        eml(tmp_path, "Parts list attached, please quote.", [("Lutz_RFQ_1_parts.csv", "text/csv", csv_text)])
    )
    row = next(ln for ln in m.source.splitlines() if "LUT-11111" in ln)
    assert row.split() == ["1", "LUT-11111", "A", "bracket", "25", "2024-06-03"]
    assert "Lutz_RFQ_1_parts.csv" in m.attachments and "Lutz_RFQ_1_parts.csv" in m.documents


def test_a_parts_list_is_laid_out_in_columns_so_its_cells_are_checked_like_a_table():
    t = ri.csv_as_table("Item,Part number,Rev,Qty\n1,LUT-11111,A,25\n")
    head, row = t.splitlines()
    assert head.index("Rev") == row.index("A") and head.index("Qty") == row.index("25")


def test_a_drawing_named_for_a_part_is_listed_not_read(tmp_path):
    m = ri.read_mail(
        eml(tmp_path, "pls quote LUT-11111 rev A qty 5", [("LUT-11111_revA.pdf", "application/pdf", b"%PDF-1.4 x")])
    )
    assert "[Attachment not read: LUT-11111_revA.pdf]" in m.source


def test_an_rfq_form_pdf_is_read_when_its_text_can_be_extracted(tmp_path, monkeypatch):
    monkeypatch.setattr(
        ri, "pdf_text", lambda data: "REQUEST FOR QUOTATION\nItem Part number Rev Qty\n1 LUT-22222 B 40\n"
    )
    m = ri.read_mail(
        eml(tmp_path, "See our RFQ form attached.", [("Lutz_RFQ_7.pdf", "application/pdf", b"%PDF-1.4 x")])
    )
    assert "1 LUT-22222 B 40" in m.source


def test_an_rfq_form_that_cant_be_read_goes_to_a_person(tmp_path, monkeypatch):
    monkeypatch.setattr(ri, "pdf_text", lambda data: None)
    m = ri.read_mail(
        eml(tmp_path, "See our RFQ form attached.", [("Lutz_RFQ_7.pdf", "application/pdf", b"%PDF-1.4 x")])
    )
    assert "[Attachment could not be read: Lutz_RFQ_7.pdf]" in m.source


# --- history: the brief, fast-track and bid odds ------------------------------------------------------------------
def history(tmp: Path) -> desk.History:
    q = tmp / "quote-history.csv"
    j = tmp / "job-history.csv"
    with q.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "customer_id",
                "part_number",
                "quote_id",
                "kind",
                "sent_on",
                "quantity",
                "unit_price",
                "est_hours",
                "status",
                "status_date",
            ]
        )
        w.writerow([6, "LUT-11111", 1, "new", "2022-03-01", 20, 41.5, 3.2, "won", "2022-03-20"])
        w.writerow([6, "LUT-11111", 2, "requote", "2023-04-01", 25, 43.0, 0.9, "won", "2023-04-05"])
        for i in range(10):  # a customer who almost never awards us anything
            w.writerow(
                [9, f"NOP-{i:05d}", 100 + i, "new", "2023-01-10", 5, 10.0, 1.0, "lost" if i else "won", "2023-02-01"]
            )
        for i in range(30):  # everyone else wins about 40%
            w.writerow(
                [
                    20 + i,
                    f"OTH-{i:05d}",
                    200 + i,
                    "new",
                    "2023-01-10",
                    5,
                    10.0,
                    1.0,
                    "won" if i % 5 < 2 else "lost",
                    "2023-02-01",
                ]
            )
    with j.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "part_number", "job_id", "completed_on", "quantity", "est_hours", "actual_hours"])
        w.writerow([6, "LUT-11111", 900, "2023-06-01", 25, 10.0, 12.5])
    return desk.History.load(tmp)


def test_the_history_brief_gives_the_last_quote_and_how_the_last_job_ran(tmp_path):
    b = desk.brief(history(tmp_path), "6", "LUT-11111", AS_OF)
    assert (
        b.last_quoted == date(2023, 4, 1) and b.last_price == 43.0 and b.last_quantity == 25 and b.last_status == "won"
    )
    assert b.quotes == 2 and b.won == 2 and b.jobs == 1 and abs(b.actual_over_estimate - 1.25) < 1e-9


def test_history_after_the_day_it_runs_is_never_used(tmp_path):
    b = desk.brief(history(tmp_path), "6", "LUT-11111", date(2023, 1, 1))
    assert b.last_quoted == date(2022, 3, 1) and b.jobs == 0


def test_fast_track_needs_the_same_revision_a_recent_quote_and_a_job(tmp_path):
    h = history(tmp_path)
    assert desk.fast_track(desk.brief(h, "6", "LUT-11111", AS_OF), "repeat")
    assert not desk.fast_track(desk.brief(h, "6", "LUT-11111", AS_OF), "repeat, new revision (B)")
    assert not desk.fast_track(desk.brief(h, "6", "LUT-11111", date(2023, 5, 1)), "repeat")  # no job yet
    assert not desk.fast_track(desk.brief(h, "6", "LUT-11111", date(2027, 5, 1)), "repeat")  # quote too old
    assert not desk.fast_track(desk.brief(h, "6", "NEW-00001", AS_OF), "new")


def test_bid_odds_pull_a_thin_record_toward_the_shop_and_flag_only_a_long_poor_one(tmp_path):
    h = history(tmp_path)
    poor = desk.odds(h, "9", AS_OF)
    assert poor.closed == 10 and poor.low and poor.rate < h.shop_rate(AS_OF)
    thin = desk.odds(h, "6", AS_OF)  # one closed new quote, won: not enough to call it either way
    assert not thin.low
    assert desk.odds(h, "999", AS_OF).rate == round(h.shop_rate(AS_OF), 3)


# --- the queue order -----------------------------------------------------------------------------------------------
def item(ref, due, stated=False, low=False, key=False):
    return ri.QueueItem(ref, ref, "C", key, datetime(2024, 5, 6, 9), date(2024, 5, 6), due, stated, 1.0, low_odds=low)


def test_a_low_odds_request_without_a_stated_due_date_waits_behind_the_others():
    d = date(2024, 5, 14)
    order = sorted([item("low", d, low=True), item("ok", d + timedelta(days=3))], key=ri.order_key)
    assert [i.ref for i in order] == ["ok", "low"]


def test_a_low_odds_request_with_a_stated_due_date_keeps_its_place():
    d = date(2024, 5, 14)
    order = sorted([item("low", d, stated=True, low=True), item("ok", d + timedelta(days=3))], key=ri.order_key)
    assert [i.ref for i in order] == ["low", "ok"]


def test_a_fast_track_request_is_quoted_in_a_fraction_of_the_time():
    assert (
        abs(desk.desk_hours(2.0, fast=True) - 2.0 * desk.FAST_TRACK) < 1e-9 and desk.desk_hours(2.0, fast=False) == 2.0
    )


# --- the desk in the queue replay -----------------------------------------------------------------------------------
MON = date(2030, 5, 6)


def cap(n, per_day):
    out, d = [], MON
    while len(out) < n:
        if d.weekday() < 5:
            out.append(rq.Day(d, per_day))
        d += timedelta(days=1)
    return out


def r(id_, hours, kind="new", rate=0.4, received=MON):
    return rq.Request(id_, kind, "regular", received, 1, False, hours, win_rate=rate)


def test_the_desk_quotes_re_quotes_in_less_time():
    reqs = [r("rq1", 2.0, kind="requote")]
    intake = rq.replay(reqs, cap(5, 1.0), "intake")
    desk_ = rq.replay(reqs, cap(5, 1.0), "desk")
    assert desk_.requote_sent["rq1"] < intake.requote_sent["rq1"]


def test_the_desk_puts_a_low_odds_request_behind_a_likely_one():
    reqs = [r("poor", 1.0, rate=0.05), r("good", 1.0, rate=0.5, received=MON + timedelta(days=1))]
    out = rq.replay(reqs, cap(5, 1.0), "desk", shop_rate=0.4, reorder_low=True)  # off by default (desk.REORDER)
    assert out.sent["good"] <= out.sent["poor"]


def test_expected_wins_weight_each_on_time_quote_by_its_customers_record():
    reqs = [r("a", 1.0, rate=0.5), r("b", 1.0, rate=0.1)]
    sent = {"a": MON, "b": MON}
    truth = {"a": rq.Truth(MON, "won", MON), "b": rq.Truth(MON - timedelta(days=1), "lost late", MON)}
    assert abs(rq.expected_wins(sent, truth, {x.id: x for x in reqs}) - 0.5) < 1e-9


def test_the_desk_still_prices_new_requests_before_re_quotes():
    reqs = [r("rq1", 1.0, kind="requote"), r("new", 1.0)]
    out = rq.replay(reqs, cap(5, 2.0), "desk")
    assert out.sent["new"] == MON and out.requote_sent["rq1"] >= out.sent["new"]


def test_low_odds_reorder_nothing_unless_switched_on():
    reqs = [r("poor", 1.0, rate=0.05), r("good", 1.0, rate=0.5, received=MON + timedelta(days=1))]
    out = rq.replay(reqs, cap(5, 1.0), "desk", shop_rate=0.4)
    assert out.sent["poor"] <= out.sent["good"] and not desk.REORDER


# --- Added after the desk's first held-back month failed (holdout-2024-11/score-at-de9a6b7.md) --------------------
import pytest  # noqa: E402


@pytest.mark.parametrize(
    "quote",
    [
        "what's your price on 18 now?",
        "18 per release",
        "We need 18 of LUT-11111",
        "LUT-11111 | A | bracket | 18 | December 2",
    ],
)
def test_the_only_bare_number_in_the_parts_words_is_its_quantity(quote):
    assert ri.quantity_in_quote(18, "LUT-11111", quote, "bracket", "A")


@pytest.mark.parametrize("quote", ["18 per release, 30 a year", "ship June 18", "18.5 in long"])
def test_a_number_that_could_be_something_else_isnt_proof(quote):
    # Two bare numbers, a revision, a date or a size: not the only reading, so not proof.
    assert not ri.quantity_in_quote(18, "LUT-11111", quote)


def test_a_date_written_without_separators_is_read():
    found, problems = ri.read_dates("need 20DEC24", date(2024, 11, 6))
    assert found == [date(2024, 12, 20)] and not problems


def test_closing_this_rfq_out_says_quotes_are_due():
    assert ri.DUE_WORDS.search("We're closing this RFQ out Tue, Nov 12.")


def test_common_column_names_are_known_table_headers():
    for cell, name in [
        ("Customer Part", "part"),
        ("Order Qty", "qty"),
        ("Dock Date", "date"),
        ("Rev Level", "rev"),
        ("Part Description", "desc"),
        ("QTY REQ'D", "qty"),
        ("P/N", "part"),
    ]:
        assert ri._header(cell) == name, cell


def test_a_pipe_table_splits_into_cells_and_a_revision_after_a_pipe_counts():
    assert [c[2] for c in ri._cells("LUT-11111 | A | bracket | 25 | 2024-12-26")] == [
        "LUT-11111",
        "A",
        "bracket",
        "25",
        "2024-12-26",
    ]
    assert ri.revision_in_quote("A", "LUT-11111", "LUT-11111 | A | bracket | 25")


def test_the_16th_of_december_is_december_not_the_next_16th():
    found, _ = ri.read_dates("need it the 16th of December", date(2024, 11, 14))
    assert found == [date(2024, 12, 16)]


def test_a_value_in_a_sentence_about_one_part_belongs_to_it():
    text = "We need 276 of LUT-21398 at revision A (bracket), delivered 20DEC24. We need 33 of LUT-24767 (plate), delivered 11DEC24."
    span = (text.index("20DEC24"), text.index("20DEC24") + 7)
    assert ri.owner(span, text, ri._clauses(text)) == ri.squash("LUT-21398")


# --- Added after the desk's second held-back month failed (holdout-2024-12/score-at-caffb9e.md) -------------------
def test_a_quantity_written_x116_and_a_revision_after_a_slash_count():
    assert ri.quantity_in_quote(116, "STO-66875", "STO-66875/A bracket x116 by 12/20")
    assert ri.revision_in_quote("A", "STO-66875", "STO-66875/A bracket x116")


def test_a_year_first_date_is_read():
    found, _ = ri.read_dates("needed by 2025/02/03", date(2024, 12, 4))
    assert found == [date(2025, 2, 3)]


@pytest.mark.parametrize("text", ["Bids accepted through 12/4.", "Final day for quotes: Fri 12/6."])
def test_more_ways_of_saying_quotes_are_due(text):
    assert ri.DUE_WORDS.search(text)


def test_the_next_release_of_a_part_isnt_a_release_quantity_but_releases_of_50_are():
    assert not ri.ANNUAL.search("Next release of LUT-11111 rev A is 24 pieces")
    assert ri.ANNUAL.search("releases of 50 through the year")
