import json
from datetime import date

import inherited_records as ir

from common.fake import OfflineModel, ScriptedModel

REC = ir.Records.load(ir.SAMPLE)


def ticket(tid, when, location, notes, read):
    t = ir.Ticket({"Ticket": tid, "Date": when.isoformat(), "Location": location, "Notes": notes}, when)
    t.read = read
    return t


def where(name, number=None, street=None):
    return {"name": name, "street_number": number, "street": street}


def unit(family, number, serial=None, make=None, model=None):
    return {"family": family, "number": number, "serial": serial, "make": make, "model": model}


def blank(loc, units=(), done=(), rec=(), agreement=None):
    return {
        "location": loc,
        "units": list(units),
        "work_done": list(done),
        "recommended": list(rec),
        "agreement": agreement,
    }


def test_dates_and_amounts_as_rimview_wrote_them():
    for s in ("3/14/24", "3/14/2024", "2024-03-14", "Mar 14 2024", "14-Mar-24"):
        assert ir.parse_date(s) == date(2024, 3, 14), s
    assert ir.money("4.2k") == 4200 and ir.money("$1,360.00/yr") == 1360 and ir.money(None) is None


def test_whatever_the_ai_copies_must_be_in_the_ticket():
    answer = blank(
        where("Cafe", "12", "Main St"),
        units=[unit("rtu", 1, serial="123456789", make="Carrier")],
        rec=[{"family": "rtu", "number": 1, "work": "compressor", "quoted": "$5,000", "evidence": "Recommend cmpr"}],
        agreement={"visits_per_year": 4, "price": "1,200", "renews": "6/1/25", "evidence": "PM agmt 1,200"},
    )
    t = ir.Ticket(
        {
            "Ticket": "T1",
            "Date": "1/2/24",
            "Location": "Cafe - 12 Main St",
            "Notes": "RTU-1 Carrier s/n 123456789. Recommend cmpr - quoted $4,800.",
        }
    )
    ir.read_ticket(t, ScriptedModel([json.dumps(answer)]))
    assert t.read["units"][0]["serial"] == "123456789"
    assert t.read["recommended"][0]["quoted"] is None  # $5,000 isn't in it
    assert t.read["agreement"] is None
    assert any("quoted amount" in p for p in t.problems) and any("agreement" in p for p in t.problems)
    made_up = blank(where("Cafe"), units=[unit("rtu", 1, serial="999999999")])
    t2 = ir.Ticket({"Ticket": "T2", "Date": "1/2/24", "Location": "Cafe", "Notes": "RTU-1 no cool, reset."})
    ir.read_ticket(t2, ScriptedModel([json.dumps(made_up)]))
    assert t2.read["units"][0]["serial"] is None and any("isn't in the ticket" in p for p in t2.problems)


def test_routine_work_on_no_unit_isnt_a_problem_but_an_unknown_kind_is():
    t = ir.Ticket({"Ticket": "T3", "Date": "1/2/24", "Location": "Cafe", "Notes": "PM done, filters all units."})
    ans = blank(
        where("Cafe"), units=[unit("chiller", 1)], done=[{"family": None, "number": None, "work": "maintenance"}]
    )
    ir.read_ticket(t, ScriptedModel([json.dumps(ans)]))
    assert t.problems == ["a unit with an unknown kind (chiller)"]


def test_mistyped_serials_and_addresses_are_recognized():
    assert ir.near("123456789", "123456798") and ir.near("123456789", "123456780")
    assert not ir.near("123456789", "123465798") and not ir.near("12345678", "123456789")
    assert ir.same_address("2503 beaver st", "2503 baver st")
    assert not ir.same_address("2503 beaver st", "2504 beaver st")


def test_tickets_without_an_address_join_the_one_place_they_name():
    review = []
    ts = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("Kachina Eye Care #102", "4613", "Fourth St"))),
        ticket("B", date(2024, 1, 2), "", "", blank(where("Kachina Eye Care #103", "88", "Elm St"))),
        ticket("C", date(2024, 1, 3), "", "", blank(where("KACHINA EYE CARE 102"))),
        ticket("D", date(2024, 1, 4), "", "", blank(where("Kachina Eye Care"))),
    ]
    locs = ir.group(ts, review)
    assert len(locs) == 2 and ts[2].location == ts[0].location
    assert ts[3].location is None and review and "could be any of" in review[0]["why"]


def test_one_unit_however_its_serial_was_typed_and_your_record_settles_it():
    p = ir.Location("R01")
    site = next(s for s, es in REC.equipment.items() if es)
    real = REC.equipment[site][0]
    p.site = site
    typo = real["Serial"][:-2] + real["Serial"][-1] + real["Serial"][-2]
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial=typo)])),
        ticket("B", date(2024, 2, 1), "", "", blank(where("x"), units=[unit("rtu", 1)])),
        ticket("C", date(2024, 3, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial=real["Serial"])])),
    ]
    us = ir.units_at(p, REC)
    assert (
        len(us) == 1 and us[0].serial == real["Serial"] and us[0].summit == real["Equipment ID"] and not us[0].problems
    )


def test_without_your_record_a_tie_goes_to_a_person():
    p = ir.Location("R01")
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="123456789")])),
        ticket("B", date(2024, 2, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="123456798")])),
    ]
    us = ir.units_at(p, REC)
    assert len(us) == 1 and any("two ways" in x for x in us[0].problems)


def test_a_replaced_unit_is_retired_and_its_successor_is_new():
    p = ir.Location("R01")
    p.tickets = [
        ticket(
            "A", date(2023, 5, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="111111111", make="York")])
        ),
        ticket(
            "B",
            date(2024, 5, 1),
            "",
            "",
            blank(
                where("x"),
                units=[unit("rtu", 1, serial="222222222", make="York")],
                done=[{"family": "rtu", "number": 1, "work": "replace unit", "per_quote": True}],
            ),
        ),
    ]
    old, new = ir.units_at(p, REC)
    assert old.replaced_on == date(2024, 5, 1) and not new.replaced_on and not old.problems
    # A second serial for the same tag, with no replacement on record, is a question, not an answer.
    p.tickets[1].read["work_done"] = []
    old, new = ir.units_at(p, REC)
    assert not old.replaced_on and old.problems


def test_quoted_work_is_open_until_a_later_ticket_says_it_was_done_per_the_quote():
    p = ir.Location("R01")
    rec = {"family": "rtu", "number": 1, "work": "compressor", "quoted": "4.2k", "evidence": "Recommend cmpr"}
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="111111111")], rec=[rec])),
        ticket(
            "B",
            date(2024, 3, 1),
            "",
            "",
            blank(where("x"), done=[{"family": "rtu", "number": 1, "work": "compressor", "per_quote": False}]),
        ),
    ]
    us = ir.units_at(p, REC)
    _, open_ = ir.promises(p, us)
    assert [(o["serial"], o["quoted"]) for o in open_] == [("111111111", 4200)]  # a repair isn't the quoted job
    p.tickets[1].read["work_done"][0]["per_quote"] = True
    assert ir.promises(p, us)[1] == []


def test_the_latest_agreement_wins_and_a_renewal_keeps_the_visits():
    p = ir.Location("R01")
    first = {"visits_per_year": 4, "price": "1,200", "renews": "6/1/25", "evidence": "x"}
    renewal = {"visits_per_year": None, "price": "1,290", "renews": "6/1/26", "evidence": "x"}
    p.tickets = [
        ticket("A", date(2023, 6, 1), "", "", blank(where("x"), agreement=first)),
        ticket("B", date(2024, 9, 1), "", "", blank(where("x"), agreement=renewal)),
    ]
    a, _ = ir.promises(p, [])
    assert a["visits a year"] == 4 and a["annual price"] == 1290 and a["renews"] == date(2026, 6, 1)


def test_the_offline_run_scores_against_the_answer_keys(tmp_path):
    r, _ = ir.run(ir.SAMPLE, OfflineModel(ir.offline), tmp_path)
    s = ir.score(r, ir.SAMPLE)
    assert s["grouped"] == s["tickets"] and s["locs"] == s["true_locs"]
    assert s["loc_ok"] + s["loc_asked"] == s["locs"]  # right, or sent to a person: never wrong
    assert (tmp_path / "merge" / "equipment.csv").exists() and (tmp_path / "review.csv").exists()


def test_the_page_escapes_what_came_from_the_tickets():
    from records_page import page

    r = ir.Result(
        [], [ir.Location("R01", names=__import__("collections").Counter({"<script>x</script>": 1}))], [], [], [], []
    )
    html = page(r, REC, "scripted")
    assert "<script>x" not in html and "&lt;script&gt;" in html


def test_an_ai_that_changes_its_mind_goes_to_a_person():
    one = json.dumps(blank(where("Cafe")))
    t = ir.Ticket({"Ticket": "T9", "Date": "1/2/24", "Location": "Cafe", "Notes": "No cool, reset."})
    ir.read_ticket(t, ScriptedModel([one + "\n\nWait, corrected:\n\n" + one]))
    assert t.read is None and "two different readings" in t.problems[0]


def test_a_ticket_with_no_name_doesnt_make_every_place_a_match():
    review = []
    ts = [
        ticket("A", date(2024, 1, 1), "", "", blank(where(None, "7074", "Beaver St"))),
        ticket("B", date(2024, 1, 2), "", "", blank(where("PetPoint Supply 107", "12", "Elm St"))),
        ticket("C", date(2024, 1, 3), "", "", blank(where("petpoint supply 107"))),
    ]
    ir.group(ts, review)
    assert ts[2].location == ts[1].location and not review
