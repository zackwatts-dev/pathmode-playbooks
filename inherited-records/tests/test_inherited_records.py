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


def test_units_installed_together_with_serials_one_apart_stay_two_units():
    p = ir.Location("R01")
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="441700631")])),
        ticket("B", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 2, serial="441700632")])),
        ticket("C", date(2024, 2, 1), "", "", blank(where("x"), units=[unit("rtu", 2, serial="441700632")])),
    ]
    us = ir.units_at(p, REC)
    assert sorted((u.number, u.serial) for u in us) == [(1, "441700631"), (2, "441700632")]
    assert not any(u.problems for u in us)


def test_a_serial_one_mistyping_from_two_units_is_kept_and_goes_to_a_person():
    p = ir.Location("R01")
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="441700631")])),
        ticket("B", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 2, serial="441700633")])),
        ticket("C", date(2024, 2, 1), "", "", blank(where("x"), units=[unit("rtu", None, serial="441700632")])),
    ]
    us = ir.units_at(p, REC)
    assert len(us) == 3 and any("one mistyping from" in x for x in us[2].problems)


def test_the_same_serial_on_two_tags_is_one_unit_and_a_question():
    p = ir.Location("R01")
    p.tickets = [
        ticket("A", date(2024, 1, 1), "", "", blank(where("x"), units=[unit("rtu", 1, serial="441700631")])),
        ticket("B", date(2024, 2, 1), "", "", blank(where("x"), units=[unit("rtu", 2, serial="441700631")])),
    ]
    us = ir.units_at(p, REC)
    assert len(us) == 1 and any("written on both" in x for x in us[0].problems)


def town(name, number, street, town_):
    return {"name": name, "street_number": number, "street": street, "town": town_}


def test_the_same_street_address_in_another_town_is_another_place():
    review = []
    ts = [
        ticket("A", date(2024, 1, 1), "", "", blank(town("Cafe Mesa", "100", "W Main St", "Mesa"))),
        ticket("B", date(2024, 1, 2), "", "", blank(town("Cafe Phoenix", "100", "W Main St", "Phoenix, AZ 85001"))),
        ticket("C", date(2024, 1, 3), "", "", blank(town("cafe phoenix", "100", "W Main Street", None))),
        ticket("D", date(2024, 1, 4), "", "", blank(town("Cafe", "100", "W Main St", None))),
    ]
    locs = ir.group(ts, review)
    assert len(locs) == 2 and ts[0].location != ts[1].location
    assert locs[1].town == "phoenix" and any("same street address" in x for x in locs[1].problems)
    assert ts[2].location == ts[1].location  # no town, but its name says which
    assert ts[3].location is None and "could be any of" in review[0]["why"]


def records(*sites):
    """Your records, with these (site, customer, name, address) sites."""
    by_addr, towns = {}, {}
    for sid, _, _, address in sites:
        street, _, town_ = address.partition(",")
        number, _, name = street.partition(" ")
        by_addr.setdefault(ir.addr_key(number, name), []).append(sid)
        towns[sid] = ir.town_key(town_)
    sites_ = {sid: {"Site ID": sid, "Customer ID": c, "Site": n, "Address": a} for sid, c, n, a in sites}
    customers = {c: {"Customer ID": c, "Name": n} for _, c, n, _ in sites}
    return ir.Records(customers, sites_, by_addr, towns, {}, [])


def test_a_site_in_another_town_isnt_matched_by_its_street_alone():
    rec = records(("S1", "C1", "Cafe", "100 W Main St, Mesa"), ("S2", "C2", "Diner", "100 W Main St, Phoenix"))
    p = ir.Location("R01")
    p.addresses["100 w main st"] += 1
    p.towns["phoenix"] += 1
    ir.match(p, rec)
    assert p.site == "S2" and not p.problems
    # No town written, and your sites at this street address are in two towns: a person says which.
    q = ir.Location("R02")
    q.addresses["100 w main st"] += 1
    q.names["cafe"] += 1
    ir.match(q, rec)
    assert q.site is None and any("a person says which" in x for x in q.problems)
    # Only your site in Mesa, but the ticket says Tempe: not your site.
    r = ir.Location("R03")
    r.addresses["100 w main st"] += 1
    r.towns["tempe"] += 1
    ir.match(r, records(("S1", "C1", "Cafe", "100 W Main St, Mesa")))
    assert r.site is None and any("another town" in x for x in r.problems)


def test_year_refrigerant_tag_and_visits_must_be_in_the_ticket_too():
    notes = "RTU-1 Carrier s/n 123456789 mfd 2015 R-410A. Signed PM agreement - quarterly, $1,200/yr, renews 6/1/25."
    t = ir.Ticket({"Ticket": "T1", "Date": "1/2/24", "Location": "Cafe - 12 Main St", "Notes": notes})
    u = unit("rtu", 1, serial="123456789") | {"install_year": 2015, "refrigerant": "R410A"}
    agreement = {
        "visits_per_year": 4,
        "price": "$1,200",
        "renews": "6/1/25",
        "evidence": "PM agreement - quarterly, $1,200/yr, renews 6/1/25",
    }
    ir.read_ticket(t, ScriptedModel([json.dumps(blank(where("Cafe"), units=[u], agreement=agreement))]))
    assert t.read["units"][0]["install_year"] == 2015 and t.read["units"][0]["refrigerant"] == "R410A"
    assert t.read["agreement"]["visits_per_year"] == 4 and not t.problems
    wrong = unit("rtu", 1, serial="123456789") | {"install_year": 2005, "refrigerant": "R-22"}
    other = unit("rtu", 2, serial="123456789")
    agreement["visits_per_year"] = 12
    t2 = ir.Ticket({"Ticket": "T2", "Date": "1/2/24", "Location": "Cafe - 12 Main St", "Notes": notes})
    ir.read_ticket(t2, ScriptedModel([json.dumps(blank(where("Cafe"), units=[wrong, other], agreement=agreement))]))
    assert t2.read["units"] == [wrong | {"install_year": None, "refrigerant": None}]  # RTU-2 isn't in it
    assert t2.read["agreement"]["visits_per_year"] is None
    assert len(t2.problems) == 4 and any("refrigerant R-22" in x for x in t2.problems)


def test_a_malformed_answer_sends_the_ticket_to_a_person_without_stopping_the_batch():
    notes = "RTU-2 no cool, reset."
    nulls = blank(where("Cafe")) | {"units": None, "work_done": None, "recommended": None}
    t = ir.Ticket({"Ticket": "T1", "Date": "1/2/24", "Location": "Cafe", "Notes": notes})
    ir.read_ticket(t, ScriptedModel([json.dumps(nulls)]))
    assert t.read["units"] == [] and t.read["work_done"] == [] and not t.problems
    bad = [
        blank(where("Cafe"), units=[unit("rtu", [2])]),
        blank(where("Cafe"), units=[unit("rtu", "two")]),
        blank(where("Cafe")) | {"units": {"family": "rtu"}},
        blank(where("Cafe"), units=["rtu 2"]),
        blank(where("Cafe"), agreement="quarterly"),
        blank(where("Cafe"), done=[{"family": "rtu", "number": 2, "work": "belt", "per_quote": "yes"}]),
        blank({"name": ["Cafe"]}),
    ]
    for answer in bad:
        t = ir.Ticket({"Ticket": "T2", "Date": "1/2/24", "Location": "Cafe", "Notes": notes})
        ir.read_ticket(t, ScriptedModel([json.dumps(answer)]))
        assert t.read is None and t.problems[0].startswith("couldn't read it"), answer


def test_every_merge_row_says_whether_its_ready_or_which_review_items_it_waits_on(tmp_path):
    import csv

    r, _ = ir.run(ir.SAMPLE, OfflineModel(ir.offline), tmp_path)
    items = {x["item"]: x for x in csv.DictReader((tmp_path / "review.csv").open())}
    waiting = 0
    for name in ("locations", "equipment", "agreements", "open-quotes"):
        for row in csv.DictReader((tmp_path / "merge" / f"{name}.csv").open()):
            assert row["review"] == "ready" or row["review"].startswith("needs review: item "), row
            waits = row["review"].removeprefix("needs review: item ").replace(" (its location)", "")
            refs = waits.split(", ") if row["review"] != "ready" else []
            assert all(n in items for n in refs)
            waiting += bool(refs)
    assert waiting
    for p in r.locations:  # a location with a question on it isn't ready
        assert (p.status == "ready") == (not p.problems and not any(t.problems for t in p.tickets))
    for u in r.units:
        assert u.status != "ready" or not u.problems


# --- the recorded run, replayed: the published numbers, and the properties every row must have ----------------------

import csv  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="module")
def replayed(tmp_path_factory):
    out = tmp_path_factory.mktemp("replay")
    model = ir.Replay(ir.SAMPLE / "recorded-run.json")
    r, _ = ir.run(ir.SAMPLE, model, out)
    rows = {n: list(csv.DictReader((out / "merge" / f"{n}.csv").open())) for n in ("agreements", "open-quotes")}
    rows |= {n: list(csv.DictReader((out / "merge" / f"{n}.csv").open())) for n in ("locations", "equipment")}
    return r, model, out, rows


def test_the_recorded_run_keeps_its_published_numbers(replayed):
    r, model, out, _ = replayed
    s = ir.score(r, ir.SAMPLE)
    assert (s["grouped"], s["tickets"], s["locs"]) == (295, 296, 31)
    assert (s["loc_ok"], s["loc_asked"], s["loc_split"]) == (25, 5, 1)
    assert (s["unit_ok"], s["units"], s["ag_ok"], s["o_ok"], s["o_wrong"]) == (92, 92, 16, 14, 0)
    assert sum(o["quoted"] for o in r.open_quotes) == 96270 and sum(a["annual price"] for a in r.agreements) == 38640
    assert len(r.review) == 30 and model.misses == 0
    assert "0 items had no recorded answer" in (out / "score.md").read_text()


def test_agreement_and_quote_rows_say_whether_theyre_ready(replayed):
    _, _, _, rows = replayed
    assert rows["agreements"] and rows["open-quotes"]
    for row in rows["agreements"] + rows["open-quotes"]:
        assert row["review"] == "ready" or row["review"].startswith("needs review: item "), row


def test_every_row_at_a_location_with_a_question_waits_on_it(replayed):
    r, _, _, rows = replayed
    asked = {x["which"]: x["item"] for x in reversed(r.review) if x["what"] == "location"}
    for name in ("equipment", "agreements", "open-quotes"):
        for row in rows[name]:
            if row["location"] in asked:
                assert f"{asked[row['location']]} (its location)" in row["review"], row
    r21 = [row for row in rows["equipment"] if row["location"] == "R21"]
    assert r21 and all(row["review"].startswith("needs review") for row in r21)


def test_a_unit_with_no_serial_is_counted_as_extra(replayed):
    r, _, _, _ = replayed
    s = ir.score(r, ir.SAMPLE)
    assert s["extra_units"] == 1 and s["extra_units_asked"] == 1  # R30's rtu 1, sent to a person
    assert "1 extra (1 of them sent to a person)" in s["md"]


def test_the_dashboard_counts_active_units_and_says_so(replayed):
    r, model, _, _ = replayed
    from records_page import page

    html = page(r, REC, model.name)
    active = sum(1 for u in r.units if not u.replaced_on)
    assert f"<b>{active}</b>Active units" in html


def test_a_replay_that_misses_says_how_many(tmp_path):
    path = tmp_path / "recording.json"
    data = json.loads((ir.SAMPLE / "recorded-run.json").read_text())
    for key in list(data["answers"])[:3]:
        del data["answers"][key]
    path.write_text(json.dumps(data))
    model = ir.Replay(path)
    ir.run(ir.SAMPLE, model, tmp_path / "out")
    assert model.misses == 3 and "3 items had no recorded answer" in (tmp_path / "out" / "score.md").read_text()


# --- what the AI copies is checked against the ticket, and where in it --------------------------------------------


def read(notes, answer, location="Cafe"):
    t = ir.Ticket({"Ticket": "T1", "Date": "1/2/24", "Location": location, "Notes": notes})
    ir.read_ticket(t, ScriptedModel([json.dumps(answer)]))
    return t


def test_a_location_the_ai_made_up_isnt_matched_to_your_site():
    made_up = town("Joe's Diner", "8729", "State Route 89A", "Sedona")
    t = read("No cool, reset breaker.", blank(made_up), location="Joe's Diner")
    loc = t.read["location"]
    assert loc["name"] == "Joe's Diner" and loc["street_number"] is None and loc["street"] is None
    assert loc["town"] is None and any("address 8729" in x for x in t.problems)
    review = []
    locs = ir.group([t], review)
    ir.match(locs[0], REC)
    assert locs[0].site != "20"


def test_a_different_route_number_or_direction_is_a_different_street():
    assert not ir.same_address("8729 state route 87", "8729 state route 89a")
    assert not ir.same_address("500 n fourth st", "500 s fourth st")
    assert not ir.same_address("500 north fourth st", "500 s fourth st")
    assert ir.same_address("500 n fourth st", "500 north furth st")  # a typo, and N written out


def test_each_unit_value_is_a_whole_word_in_what_the_ticket_says_about_that_unit():
    t = read("RTU-1 Carrier s/n 111222333.", blank(where("Cafe"), units=[unit("rtu", 1, "1222", make="s", model="n")]))
    assert t.read["units"][0] | {} == unit("rtu", 1) | {"install_year": None, "refrigerant": None}
    assert len(t.problems) == 3
    notes = "RTU-1 Carrier s/n 111111111 mfd 2010 R-22. RTU-2 Trane s/n 222222222 mfd 2018 R-410A."
    swapped = [
        unit("rtu", 1, "222222222", "Trane") | {"install_year": 2018, "refrigerant": "R-410A"},
        unit("rtu", 2, "111111111", "Carrier") | {"install_year": 2010, "refrigerant": "R-22"},
    ]
    t = read(notes, blank(where("Cafe"), units=swapped))
    assert all(u[f] is None for u in t.read["units"] for f in ("serial", "make", "install_year", "refrigerant"))
    right = [
        unit("rtu", 1, "111111111", "Carrier") | {"install_year": 2010, "refrigerant": "R-22"},
        unit("rtu", 2, "222222222", "Trane") | {"install_year": 2018, "refrigerant": "R-410A"},
    ]
    t = read(notes, blank(where("Cafe"), units=right))
    assert not t.problems and t.read["units"][1]["serial"] == "222222222"


def test_a_quote_needs_its_amount_in_words_that_quote_something():
    notes = "No cool. Found bad cont. on RTU2, replaced. Billed $218. Will call back."
    rec = {"family": "rtu", "number": 2, "work": "contactor", "quoted": "$218", "evidence": "call back"}
    t = read(notes, blank(where("Cafe"), rec=[rec]))
    assert t.read["recommended"] == [] and any("don't recommend or quote" in x for x in t.problems)
    rec = {"family": "rtu", "number": 2, "work": "compressor", "quoted": "$218", "evidence": "Recommend comp"}
    t = read("RTU2 billed $218. Recommend comp - quoted 3860.", blank(where("Cafe"), rec=[rec]))
    assert t.read["recommended"][0]["quoted"] is None and any("quoted amount $218" in x for x in t.problems)
    rec = {"family": "rtu", "number": 2, "work": "compressor", "quoted": "$3-4k", "evidence": "Recommend comp, $3-4k"}
    t = read("RTU2 no cool. Recommend comp, $3-4k.", blank(where("Cafe"), rec=[rec]))
    assert t.read["recommended"][0]["quoted"] is None and any("isn't one amount" in x for x in t.problems)


def test_a_done_per_quote_that_doesnt_name_the_work_keeps_the_quote_open_for_a_person():
    p = ir.Location("R01")
    rec = {
        "family": "rtu",
        "number": 2,
        "work": "compressor",
        "quoted": "3860",
        "evidence": "Recommend comp - quoted 3860",
    }
    first = read("Not cooling on rtu #2. Recommend comp - quoted 3860.", blank(where("x"), rec=[rec]))
    done_ = {"family": "rtu", "number": 2, "work": "compressor", "per_quote": True}
    later = read("Replaced capacitor on rtu #2 per quote, tested ok.", blank(where("x"), done=[done_]))
    assert later.read["work_done"][0]["per_quote"] is None and later.problems
    first.when, later.when = date(2024, 1, 1), date(2024, 3, 1)
    later.row["Ticket"] = "T2"
    p.tickets = [first, later]
    _, open_ = ir.promises(p, [])
    assert [o["quoted"] for o in open_] == [3860] and "T2 may be this work" in open_[0]["check"]
    # Said in so many words, it closes the quote.
    sure = read("Installed cmpr on rtu #2 per quote, tested ok.", blank(where("x"), done=[dict(done_)]))
    sure.when = date(2024, 3, 1)
    p.tickets = [first, sure]
    assert ir.promises(p, [])[1] == []


def test_renewal_dates_and_prices_are_read_or_sent_to_a_person():
    assert ir.renewal_date("March 1, 2026") == (date(2026, 3, 1), "")
    assert ir.renewal_date("Mar 1, 2026")[0] == date(2026, 3, 1) and ir.renewal_date("1-Aug-25")[0] == date(2025, 8, 1)
    assert ir.renewal_date("01/03/26")[0] is None and "more than one way" in ir.renewal_date("01/03/26")[1]
    assert ir.renewal_date("next spring")[0] is None and ir.renewal_date("next spring")[1]
    assert ir.annual("$290/mo") == (3480, "") and ir.annual("$600 per quarter") == (2400, "")
    assert ir.annual("$1,200/yr") == (1200, "") and ir.annual("$95 per visit")[0] is None
    p = ir.Location("R01")
    terms = {"visits_per_year": 12, "price": "$290/mo", "renews": "01/03/26", "evidence": "x"}
    p.tickets = [ticket("A", date(2024, 1, 1), "", "", blank(where("x"), agreement=terms))]
    a, _ = ir.promises(p, [])
    assert a["annual price"] == 3480 and a["renews"] is None and "more than one way" in a["check"]


# --- units: replacements and near serials -------------------------------------------------------------------------


def test_a_replacement_isnt_retired_on_its_own_install_date():
    p = ir.Location("R01")
    swap = {"family": "rtu", "number": 1, "work": "replace unit", "per_quote": True}
    p.tickets = [
        ticket("A", date(2023, 5, 1), "", "", blank(where("x"), units=[unit("rtu", 1, "111111111")])),
        ticket("B", date(2024, 5, 1), "", "", blank(where("x"), units=[unit("rtu", 1, "222222222")], done=[swap])),
        ticket("C", date(2024, 9, 1), "", "", blank(where("x"), units=[unit("rtu", 1, "333333333")])),
    ]
    old, new, third = ir.units_at(p, REC)
    assert old.replaced_on == date(2024, 5, 1) and not new.replaced_on and not third.replaced_on
    assert any("another serial (333333333)" in x for x in new.problems)  # no replacement after it: a question


def test_replacing_the_rtu_without_saying_which_goes_to_a_person():
    p = ir.Location("R01")
    swap = {"family": "rtu", "number": None, "work": "replace unit", "per_quote": False}
    p.tickets = [
        ticket("A", date(2023, 5, 1), "", "", blank(where("x"), units=[unit("rtu", 1, "111111111")])),
        ticket("B", date(2023, 5, 1), "", "", blank(where("x"), units=[unit("rtu", 3, "333333333")])),
        ticket("C", date(2024, 5, 1), "", "", blank(where("x"), units=[unit("rtu", None, "444444444")], done=[swap])),
    ]
    us = ir.units_at(p, REC)
    assert not any(u.replaced_on for u in us)
    assert any("without saying which" in x for x in p.problems)
    assert any("a person says which" in x for x in us[-1].problems)


def test_a_near_serial_thats_another_of_your_records_is_that_unit_not_a_typo():
    rec = ir.Records.load(ir.SAMPLE)
    rec.equipment["2218"] = rec.equipment["2218"] + [
        {"Equipment ID": "90002", "Site ID": "2218", "Family": "rtu", "Serial": "323010763", "Make": "Lennox"}
    ]
    p = ir.Location("R01")
    p.site = "2218"
    p.tickets = [
        ticket("A", date(2023, 1, 5), "", "", blank(where("x"), units=[unit("rtu", 1, "323010762")])),
        ticket("B", date(2023, 3, 1), "", "", blank(where("x"), units=[unit("rtu", None, "323010763")])),
    ]
    us = ir.units_at(p, rec)
    assert sorted(u.summit for u in us) == ["90002", "9365"]


def test_an_unnumbered_near_serial_goes_to_a_person():
    p = ir.Location("R01")
    p.tickets = [
        ticket("A", date(2023, 1, 5), "", "", blank(where("x"), units=[unit("rtu", 1, "441700631")])),
        ticket("B", date(2023, 3, 1), "", "", blank(where("x"), units=[unit("rtu", None, "441700632")])),
    ]
    us = ir.units_at(p, REC)
    assert len(us) == 2 and any("one mistyping from" in x for x in us[1].problems)
    # "The boiler", the only one here, with a serial one mistyping from its own: the same boiler.
    p.tickets = [
        ticket("A", date(2023, 1, 5), "", "", blank(where("x"), units=[unit("boiler", None, "441700631")])),
        ticket("B", date(2023, 3, 1), "", "", blank(where("x"), units=[unit("boiler", None, "441700632")])),
    ]
    assert len(ir.units_at(p, REC)) == 1
