import json

import account_summary as asum

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

DATA = asum.Data.load(asum.SAMPLE)
REQUESTS = {r["Request"]: r for r in read_csv(asum.SAMPLE / "requests.csv")}
Q = asum.Quarter.parse(asum.SAMPLE_QUARTER)


def briefing(rid, answer):
    r = REQUESTS[rid]
    b = asum.Briefing(r, Q, refused=asum.authorize(DATA, r["User"], r["Kind"], r["Subject"]))
    model = ScriptedModel([json.dumps(answer)])
    if not b.refused:
        b.facts = asum.facts(DATA, r["Kind"], r["Subject"], Q)
        asum.write(b, DATA, model)
    return b, model


def good(points, **more):
    return {"headline": "Steady quarter.", "points": points, "customers_say": [], "worth_asking": []} | more


def test_the_facts_reconcile_with_the_answer_key(tmp_path):
    briefings, _ = asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q)
    scored = asum.score(briefings, asum.SAMPLE)
    assert scored["ok"] == scored["n"] == 11, scored["rows"]


def test_out_of_scope_requests_are_refused_before_anything_is_gathered():
    for rid in ("Q10", "Q11"):
        b, model = briefing(rid, good([]))
        assert b.refused and not b.facts and not model.calls


def test_each_role_sees_only_its_scope():
    tucson = next(c for c, v in DATA.customers.items() if v["Branch"] == "Tucson")
    phoenix = next(c for c, v in DATA.customers.items() if v["Branch"] == "Phoenix")
    assert asum.authorize(DATA, "U2", "customer", tucson) is None
    assert asum.authorize(DATA, "U2", "customer", phoenix)
    assert asum.authorize(DATA, "U3", "region", "Tucson")
    assert asum.authorize(DATA, "U1", "region", "Flagstaff") is None
    priya = DATA.users["U4"]["Covers"].split()
    assert asum.authorize(DATA, "U4", "customer", priya[0]) is None
    assert asum.authorize(DATA, "U4", "region", "Phoenix")  # an account manager never sees a whole branch
    assert asum.authorize(DATA, "U9", "region", "Phoenix") == "unknown user"


def test_numbers_from_the_facts_pass_including_rounded_and_abbreviated():
    f = asum.facts(DATA, "customer", REQUESTS["Q04"]["Subject"], Q)
    pts = [
        {
            "text": f"Revenue was ${f['revenue'] / 1000:.0f}k, down {abs(f['revenue_change']['percent']):.0f}% "
            f"(${abs(f['revenue_change']['amount']):,.0f}).",
            "metrics": ["revenue", "revenue_change"],
        }
    ]
    b, _ = briefing("Q04", good(pts))
    assert not b.problems, b.problems


def test_a_number_the_ai_worked_out_is_caught():
    b, _ = briefing("Q04", good([{"text": "Revenue per job was $1,157.16.", "metrics": ["revenue", "jobs"]}]))
    assert any("numbers that aren't in the facts" in p for p in b.problems)


def test_millions_are_checked_too():
    b, _ = briefing("Q01", good([{"text": "Revenue was $5.0M.", "metrics": ["revenue"]}]))
    assert not b.problems
    b, _ = briefing("Q01", good([{"text": "Revenue was $6.2 million.", "metrics": ["revenue"]}]))
    assert b.problems


def test_citing_a_metric_that_isnt_there_is_caught():
    b, _ = briefing("Q04", good([{"text": "Margins improved.", "metrics": ["margin"]}]))
    assert any("metrics that don't exist" in p for p in b.problems)


def test_quotes_must_be_in_the_customers_own_emails():
    mail = asum.emails_for(DATA, REQUESTS["Q04"]["Subject"], Q)
    e = mail[-1]
    real = " ".join(e["body"].split()[:6])
    ok, _ = briefing(
        "Q04", good([{"text": "Busy.", "metrics": ["emails"]}], customers_say=[{"quote": real, "email": e["id"]}])
    )
    assert not ok.problems, ok.problems
    made_up = {"quote": "we are thinking of switching contractors", "email": e["id"]}
    bad, _ = briefing("Q04", good([{"text": "Busy.", "metrics": ["emails"]}], customers_say=[made_up]))
    assert any("isn't in email" in p for p in bad.problems)
    other = next(x for c, xs in DATA.emails.items() if c != REQUESTS["Q04"]["Subject"] for x in xs)
    stray, _ = briefing(
        "Q04",
        good(
            [{"text": "Busy.", "metrics": ["emails"]}],
            customers_say=[{"quote": other["Body"][:40], "email": other["Email"]}],
        ),
    )
    assert any("isn't this customer's" in p for p in stray.problems)


def test_a_region_briefing_sends_no_emails_and_no_contacts():
    _, model = briefing("Q01", good([{"text": "x", "metrics": ["revenue"]}]))
    sent = model.calls[0][1]
    assert '"emails"' not in sent and "@" not in sent


def test_a_bad_answer_goes_to_a_person_not_a_crash():
    r = REQUESTS["Q04"]
    b = asum.Briefing(r, Q)
    b.facts = asum.facts(DATA, "customer", r["Subject"], Q)
    asum.write(b, DATA, ScriptedModel(["not json"]))
    assert b.status == "needs review"


def test_the_page_escapes_what_the_ai_wrote(tmp_path):
    from summary_page import page

    b, _ = briefing("Q04", good([{"text": "<script>alert(1)</script>", "metrics": ["revenue"]}]))
    html = page([b], DATA, "scripted", Q)
    assert "<script>alert" not in html and "&lt;script&gt;" in html


def test_a_refusal_doesnt_reveal_whether_the_customer_exists():
    phoenix = next(c for c, v in DATA.customers.items() if v["Branch"] == "Phoenix")
    assert asum.authorize(DATA, "U2", "customer", phoenix) == asum.authorize(DATA, "U2", "customer", "999999")
    assert asum.authorize(DATA, "U1", "customer", "999999") == "no such customer or branch"


def test_the_ai_never_sees_another_customers_emails():
    _, model = briefing("Q04", good([{"text": "x", "metrics": ["revenue"]}]))
    sent = model.calls[0][1]
    others = [x["Email"] for c, xs in DATA.emails.items() if c != REQUESTS["Q04"]["Subject"] for x in xs]
    assert not [e for e in others if f'"{e}"' in sent]


def test_each_person_sees_only_their_own_requests(tmp_path):
    asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q)
    priya = (tmp_path / "dashboard-U4.html").read_text()
    dana = (tmp_path / "dashboard-U2.html").read_text()
    for rid, r in REQUESTS.items():
        assert (f"{rid})" in priya) == (r["User"] == "U4"), rid
        assert (f"{rid})" in dana) == (r["User"] == "U2"), rid
    assert "Tucson" not in priya.split("<h2>What each number means")[0].replace("Refused", "")
    everything = (tmp_path / "dashboard.html").read_text()
    assert all(f"{rid})" in everything for rid in REQUESTS)


def test_a_refusal_shows_only_what_was_asked_for():
    b, _ = briefing("Q11", good([]))
    name = DATA.customers[REQUESTS["Q11"]["Subject"]]["Name"]
    assert name not in asum.briefing_md(b, DATA)


def test_the_metric_definitions_change_only_on_purpose():
    """Changing a definition is a decision for its owner, not an edit. Update this only with their say."""
    import hashlib

    assert hashlib.sha256(json.dumps(asum.METRICS, sort_keys=True).encode()).hexdigest()[:16] == "60ca5c7968244ca1"


# --- the quarter ---------------------------------------------------------------------------------------------------


def test_a_quarter_brings_its_own_dates_the_one_before_and_the_same_one_a_year_before():
    q = asum.Quarter.parse("2025Q1")
    assert q.span == (asum.date(2025, 1, 1), asum.date(2025, 3, 31))
    assert q.prior.span == (asum.date(2024, 10, 1), asum.date(2024, 12, 31))
    assert q.last_year.span == (asum.date(2024, 1, 1), asum.date(2024, 3, 31))
    assert (q.label, q.months) == ("Q1 2025", "January to March")
    assert asum.Quarter.parse("q4 2024").end == asum.date(2024, 12, 31)
    assert asum.Quarter.last_closed(asum.date(2026, 1, 5)) == asum.Quarter(2025, 4)


def test_another_quarter_gets_that_quarters_facts_and_says_so_to_the_ai():
    q2 = asum.Quarter.parse("2025Q2")
    key = {r["Request"]: r for r in read_csv(asum.SAMPLE / "answer-key.csv")}
    assert abs(asum.facts(DATA, "region", "Tucson", q2)["revenue"] - float(key["Q01"]["Revenue Q2"])) < 0.02
    r = REQUESTS["Q01"]
    b = asum.Briefing(r, q2)
    b.facts = asum.facts(DATA, r["Kind"], r["Subject"], q2)
    model = ScriptedModel([json.dumps(good([{"text": "x", "metrics": ["revenue"]}]))])
    asum.write(b, DATA, model)
    system = model.calls[0][0]
    assert "for Q2 2025 (April to June)" in system and "Q3 2025" not in system


def test_the_sample_quarter_asks_the_ai_exactly_what_the_recorded_run_asked():
    import hashlib

    text = asum.instructions(Q)
    assert hashlib.sha256(text.encode()).hexdigest()[:16] == "7234c39dd3ff1df0"


def test_the_page_and_the_briefing_name_the_quarter_they_cover():
    from summary_page import page

    q4 = asum.Quarter.parse("2024Q4")
    b = asum.Briefing(REQUESTS["Q01"], q4, facts=asum.facts(DATA, "region", "Tucson", q4))
    assert "Account summaries: Q4 2024" in page([b], DATA, "scripted", q4)
    assert "vs Q4 2023" in page([b], DATA, "scripted", q4)
    assert asum.briefing_md(b, DATA).startswith("# Tucson: Q4 2024")


# --- numbers come from the facts, and from the metric they're said to be ----------------------------------------


def test_a_number_from_a_customers_email_isnt_a_fact():
    b, _ = briefing("Q05", good([{"text": "They were billed $519.59 they dispute.", "metrics": ["overdue"]}]))
    assert any("numbers that aren't in the facts ($519.59)" in p for p in b.problems), b.problems


def test_a_figure_given_under_the_wrong_metric_is_caught():
    # $32.7K is what the quotes were worth, not what's overdue.
    b, _ = briefing("Q04", good([{"text": "About $32.7K is overdue.", "metrics": ["overdue"]}]))
    assert any("metrics it doesn't cite ($32700; it cites overdue)" in p for p in b.problems), b.problems
    ok, _ = briefing("Q04", good([{"text": "Quotes worth about $32.7K were won.", "metrics": ["quotes"]}]))
    assert not ok.problems, ok.problems


def test_a_change_may_name_the_figures_it_is_worked_out_from():
    f = asum.facts(DATA, "region", "Phoenix", Q)
    text = f"Revenue rose {f['revenue_change']['percent']}% (${f['revenue_prior']:,.0f} to ${f['revenue']:,.0f})."
    b, _ = briefing("Q02", good([{"text": text, "metrics": ["revenue_change"]}]))
    assert not b.problems, b.problems


def test_small_counts_are_checked_against_the_facts_too():
    ok, _ = briefing("Q04", good([{"text": "3 invoices are overdue.", "metrics": ["overdue"]}]))
    assert not ok.problems, ok.problems
    made_up, _ = briefing("Q04", good([{"text": "4 invoices are overdue.", "metrics": ["overdue"]}]))
    assert any("aren't in the facts (4)" in p for p in made_up.problems), made_up.problems
    # 12 is how many emails were chasing, not how many invoices are overdue.
    swapped, _ = briefing("Q04", good([{"text": "12 invoices are overdue.", "metrics": ["overdue"]}]))
    assert any("metrics it doesn't cite (12" in p for p in swapped.problems), swapped.problems


def test_only_the_years_being_compared_pass_as_years():
    ok, _ = briefing("Q04", good([{"text": "Revenue fell from 2024 to 2025.", "metrics": ["revenue"]}]))
    assert not ok.problems, ok.problems
    bad, _ = briefing("Q04", good([{"text": "Revenue was the lowest since 2019.", "metrics": ["revenue"]}]))
    assert any("(2019)" in p for p in bad.problems), bad.problems


def test_a_number_thats_part_of_a_name_isnt_read_as_a_figure():
    ask = ["Is the W-9 they asked for holding up INV-221437, and is unit #106 fixed?"]
    b, _ = briefing("Q05", good([{"text": "3 quotes.", "metrics": []}], worth_asking=ask))
    assert all("W-9" not in p and "221437" not in p and "106" not in p for p in b.problems), b.problems


# --- a malformed answer goes to a person -------------------------------------------------------------------------


def test_lists_that_come_back_null_are_treated_as_empty():
    answer = {"headline": "Steady.", "points": [{"text": "Busy.", "metrics": None}], "worth_asking": None}
    b, _ = briefing("Q04", answer | {"customers_say": None})
    assert b.status == "ready", b.problems
    assert b.answer["worth_asking"] == [] and b.answer["customers_say"] == [] and b.answer["points"][0]["metrics"] == []
    assert "Worth asking" not in asum.briefing_md(b, DATA)


def test_an_answer_of_the_wrong_shape_goes_to_a_person_not_a_crash():
    shapes = [
        good(["Revenue was up."]),  # points as strings
        good([{"text": 5, "metrics": ["revenue"]}]),
        good([{"text": "Busy.", "metrics": "revenue"}]),
        good([{"text": "Busy.", "metrics": ["revenue"]}], worth_asking="What changed?"),
        good([{"text": "Busy.", "metrics": ["revenue"]}], worth_asking=[{"q": "What changed?"}]),
        good([{"text": "Busy.", "metrics": ["revenue"]}], customers_say=["we're unhappy"]),
        good([{"text": "Busy.", "metrics": ["revenue"]}], customers_say=[{"quote": "hi there you", "email": 7}]),
        {"points": [{"text": "Busy.", "metrics": ["revenue"]}]},  # no headline
        [{"text": "Busy."}],
    ]
    for answer in shapes:
        b, _ = briefing("Q04", answer)
        assert b.status == "needs review" and b.answer is None, answer
        assert any("couldn't write it" in p for p in b.problems), (answer, b.problems)


def test_one_malformed_answer_doesnt_stop_the_batch(tmp_path):
    def broken(system, user):
        return json.dumps({"headline": "x", "points": ["not a point"], "worth_asking": None})

    briefings, _ = asum.run(asum.SAMPLE, OfflineModel(broken), tmp_path, Q)
    assert [b.status for b in briefings].count("needs review") == 9
    assert (tmp_path / "dashboard.html").exists()
