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
    """Q05 and Q06 are Dana's (Tucson's branch manager) briefings on customers with work at other branches too; she
    sees Tucson's part only, and the answer key counts the same part. The whole customer's facts are different."""
    briefings, _ = asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q)
    scored = asum.score(briefings, asum.SAMPLE)
    assert (scored["ok"], scored["n"]) == (11, 11), scored["rows"]
    key = {r["Request"]: r for r in read_csv(asum.SAMPLE / "answer-key.csv")}
    for rid in ("Q05", "Q06"):
        whole = asum.facts(DATA, "customer", REQUESTS[rid]["Subject"], Q)
        assert abs(whole["revenue"] - float(key[rid]["Revenue Q3"])) > 1000


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
    priya = (tmp_path / "U4" / "dashboard.html").read_text()
    dana = (tmp_path / "U2" / "dashboard.html").read_text()
    for rid, r in REQUESTS.items():
        assert (f"{rid})" in priya) == (r["User"] == "U4"), rid
        assert (f"{rid})" in dana) == (r["User"] == "U2"), rid
    assert "Tucson" not in priya.split("<h2>What each number means")[0].replace("Refused", "")
    everything = (tmp_path / "U1" / "dashboard.html").read_text()
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
    assert any("metrics it doesn't cite ($32.7K; it cites overdue)" in p for p in b.problems), b.problems
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
    assert (tmp_path / "U1" / "dashboard.html").exists()


# --- a number must be the right kind of figure, going the right way, in the right quarter ------------------------


def test_a_change_said_to_go_the_wrong_way_is_caught():
    # Tucson's revenue was down 2.0% ($100,919) on the same quarter last year.
    m = ["revenue_vs_last_year"]
    for text in ("Revenue rose 2.0% on Q3 last year.", "Revenue grew by $100,919.", "Revenue was +2.0% on last year."):
        b, _ = briefing("Q01", good([{"text": text, "metrics": m}]))
        assert any("other way" in p or "wrong sign" in p for p in b.problems), (text, b.problems)
    for text in ("Revenue fell 2.0% on Q3 last year.", "Revenue was down $100,919.", "Revenue was -2.0% on last year."):
        b, _ = briefing("Q01", good([{"text": text, "metrics": m}]))
        assert not b.problems, (text, b.problems)


def test_swapped_years_are_caught():
    right = "Revenue was $5,000,999 in Q3 2025 against $5,101,919 in Q3 2024."
    swapped = "Revenue was $5,101,919 in Q3 2025 against $5,000,999 in Q3 2024."
    m = ["revenue_vs_last_year"]
    ok, _ = briefing("Q01", good([{"text": right, "metrics": m}]))
    assert not ok.problems, ok.problems
    bad, _ = briefing("Q01", good([{"text": swapped, "metrics": m}]))
    assert any("wrong quarter" in p for p in bad.problems), bad.problems


def test_a_count_of_days_isnt_money_and_money_isnt_a_percent():
    # Tucson's oldest overdue invoice is 282 days past due; 282 dollars appears nowhere.
    ok, _ = briefing("Q01", good([{"text": "The oldest is 282 days past due.", "metrics": ["overdue"]}]))
    assert not ok.problems, ok.problems
    for text in ("$282 is overdue.", "282% of invoices are overdue."):
        b, _ = briefing("Q01", good([{"text": text, "metrics": ["overdue"]}]))
        assert any("wrong kind of figure" in p for p in b.problems), (text, b.problems)


def test_citing_every_metric_doesnt_switch_off_the_check():
    f = asum.facts(DATA, "region", "Tucson", Q)
    b, _ = briefing("Q01", good([{"text": "$282 is overdue.", "metrics": list(f)}]))
    assert any("one point cites" in p for p in b.problems), b.problems
    assert any("wrong kind of figure" in p and "($282)" in p for p in b.problems), b.problems


def test_the_headline_and_the_questions_are_checked_by_kind_and_direction():
    b, _ = briefing(
        "Q01",
        good(
            [{"text": "Busy.", "metrics": []}], headline="Tucson revenue rose 2.0%.", worth_asking=["Why is $282 owed?"]
        ),
    )
    assert any("'rose'" in p for p in b.problems), b.problems
    assert any("wrong kind of figure" in p and "($282)" in p for p in b.problems), b.problems


def test_claims_in_words_are_checked_against_the_facts():
    b, _ = briefing("Q01", good([{"text": "Revenue tripled, and nothing is overdue.", "metrics": ["revenue_change"]}]))
    assert any("'tripled'" in p for p in b.problems) and any("nothing is overdue" in p for p in b.problems), b.problems
    # Flagstaff really did nearly double on the quarter before (+88.8%), and has money overdue.
    ok, _ = briefing(
        "Q03", good([{"text": "Revenue nearly doubled on the prior quarter.", "metrics": ["revenue_change"]}])
    )
    assert not ok.problems, ok.problems
    head, _ = briefing("Q01", good([{"text": "Busy.", "metrics": []}], headline="No overdue invoices at Tucson."))
    assert any("nothing is overdue" in p for p in head.problems), head.problems


def test_a_billion_is_a_billion():
    # 1.9 is Tucson's days to complete; "$1.9 billion" is money, and nowhere near any of its figures.
    b, _ = briefing("Q01", good([{"text": "Revenue was $1.9 billion.", "metrics": ["revenue"]}]))
    assert any("$1.9 billion" in p for p in b.problems), b.problems


# --- request IDs, and each person's own folder ------------------------------------------------------------------


def sample_with(tmp_path, requests=None, users=None, edit=None):
    """A copy of the sample with some files replaced: requests and users as rows, or edit(name, rows) -> rows."""
    import shutil

    folder = tmp_path / "data"
    shutil.copytree(asum.SAMPLE, folder)
    from common.util import write_csv

    if requests is not None:
        write_csv(folder / "requests.csv", requests, ["Request", "User", "Kind", "Subject"])
    if users is not None:
        write_csv(folder / "users.csv", users, ["User", "Name", "Role", "Scope", "Covers"])
    if edit:
        for name in ("jobs.csv", "quotes.csv"):
            rows = read_csv(folder / name)
            new = edit(name, rows)
            if new is not None:
                write_csv(folder / name, new, list(rows[0]))
    return folder


def test_a_request_id_cant_write_outside_the_output_folder(tmp_path):
    folder = sample_with(
        tmp_path, [{"Request": "../../../escaped", "User": "U1", "Kind": "region", "Subject": "Tucson"}]
    )
    out = tmp_path / "a" / "b" / "out"
    asum.run(folder, OfflineModel(asum.offline), out, Q, answer_key=False)
    written = [p for p in tmp_path.rglob("*escaped*")]
    assert written and all(out in p.parents for p in written), written


def test_duplicate_request_ids_stop_the_run(tmp_path):
    import pytest

    r = {"Request": "Q01", "User": "U1", "Kind": "region", "Subject": "Tucson"}
    folder = sample_with(tmp_path, [r, r | {"Subject": "Phoenix"}])
    with pytest.raises(ValueError, match="Q01"):
        asum.run(folder, OfflineModel(asum.offline), tmp_path / "out", Q, answer_key=False)
    clash = sample_with(tmp_path / "2", [r, r | {"Request": "Q/01"}, r | {"Request": "Q_01"}])
    with pytest.raises(ValueError, match="Q_01"):
        asum.run(clash, OfflineModel(asum.offline), tmp_path / "out", Q, answer_key=False)


def test_each_person_has_their_own_folder_and_no_folder_is_shared(tmp_path):
    asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q)
    assert not (tmp_path / "summaries").exists() and not (tmp_path / "dashboard.html").exists()
    for uid in DATA.users:
        own = sorted(p.stem for p in (tmp_path / uid / "summaries").glob("*.md"))
        expected = sorted(REQUESTS) if uid == "U1" else sorted(k for k, r in REQUESTS.items() if r["User"] == uid)
        assert own == expected, uid
    assert not (tmp_path / "U2" / "requests.csv").exists() and (tmp_path / "U1" / "requests.csv").exists()


def test_markdown_from_the_ai_and_the_emails_is_inert():
    nasty = "See [the portal](http://evil.example) ![x](http://evil.example/p.png) <img src=x onerror=alert(1)>\n# Paid"
    mail = asum.emails_for(DATA, REQUESTS["Q04"]["Subject"], Q)
    b, _ = briefing("Q04", good([{"text": nasty, "metrics": ["emails"]}], headline=nasty, worth_asking=[nasty]))
    b.answer["customers_say"] = [{"quote": nasty, "email": mail[0]["id"]}]
    import re

    text = asum.briefing_md(b, DATA).split("Facts (calculated by code)")[0]
    body = re.sub(r"(?m)^> ", "", text.split("\n", 1)[1])  # a quote's own "> " is ours
    assert not re.search(r"(?<!\\)[\[\]<>!#]", body), text  # nothing unescaped after the title
    assert "\\[the portal\\]" in text and "\\<img" in text and text.count(nasty.split("\n")[0][:20]) == 0


# --- a branch manager sees their branch's work ----------------------------------------------------------------


def test_a_branch_managers_customer_briefing_counts_only_their_branch():
    cid = REQUESTS["Q05"]["Subject"]  # a Tucson customer with jobs and invoices at Phoenix and Flagstaff too
    assert DATA.customers[cid]["Branch"] == "Tucson"
    tucson = sum(
        float(i["Amount"])
        for i in DATA.invoices
        if i["Customer ID"] == cid and i["Branch"] == "Tucson" and asum.within(i["Date"], Q.span)
    )
    b, _ = briefing("Q05", good([{"text": "Busy.", "metrics": ["jobs"]}]))
    assert asum.branch_only(DATA, "U2", "customer") == "Tucson"
    b.facts = asum.facts(DATA, "customer", cid, Q, branch="Tucson")
    assert abs(b.facts["revenue"] - round(tucson, 2)) < 0.01
    whole = asum.facts(DATA, "customer", cid, Q)
    assert whole["revenue"] > b.facts["revenue"] and "work counted" not in whole["customer"]
    assert "Counted: Tucson branch only" in asum.briefing_md(b, DATA)
    assert asum.branch_only(DATA, "U1", "customer") is None and asum.branch_only(DATA, "U4", "customer") is None


def test_the_branch_slices_of_a_customer_add_up_to_the_whole():
    """A check that doesn't lean on the answer key: each branch's share of a customer, worked out separately, adds
    up to the whole customer, and the three branches add up to every invoice in the quarter."""
    for rid in ("Q05", "Q06", "Q08"):
        cid = REQUESTS[rid]["Subject"]
        whole = asum.facts(DATA, "customer", cid, Q)
        parts = [asum.facts(DATA, "customer", cid, Q, branch=br) for br in asum.BRANCHES]
        assert abs(sum(p["revenue"] for p in parts) - whole["revenue"]) < 0.02
        assert abs(sum(p["overdue"]["balance"] for p in parts) - whole["overdue"]["balance"]) < 0.02
        assert sum(p["jobs"]["total"] for p in parts) == whole["jobs"]["total"]
    total = sum(float(i["Amount"]) for i in DATA.invoices if asum.within(i["Date"], Q.span))
    branches = sum(asum.facts(DATA, "region", br, Q)["revenue"] for br in asum.BRANCHES)
    assert abs(total - branches) < 0.05


# --- the run log, the scheduled requests, and data the code can't count -----------------------------------------


def test_the_run_log_says_who_asked_about_what(tmp_path):
    asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q)
    log = read_csv(tmp_path / "runs.csv")
    assert [r["request"] for r in log] == list(REQUESTS)
    q10 = next(r for r in log if r["request"] == "Q10")
    assert (q10["asked_by"], q10["kind"], q10["subject"], q10["status"]) == (
        "Dana Ortiz",
        "region",
        "Phoenix",
        "refused",
    )


def test_standard_adds_each_branch_managers_own_branch(tmp_path):
    briefings, _ = asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path, Q, standard=True)
    extra = {b.request["Request"]: b for b in briefings if b.request["Request"] not in REQUESTS}
    assert sorted(extra) == ["2025Q3-U2", "2025Q3-U3"]
    assert extra["2025Q3-U3"].request["Subject"] == "Phoenix" and extra["2025Q3-U3"].status == "ready"
    assert (tmp_path / "U3" / "summaries" / "2025Q3-U3.md").exists()


def test_an_unknown_user_is_refused_with_a_reason_not_a_crash(tmp_path):
    folder = sample_with(tmp_path, [{"Request": "X1", "User": "U9", "Kind": "region", "Subject": "Tucson"}])
    briefings, _ = asum.run(folder, OfflineModel(asum.offline), tmp_path / "out", Q, answer_key=False)
    assert briefings[0].refused == "unknown user"
    assert "unknown user U9" in (tmp_path / "out" / "U1" / "summaries" / "X1.md").read_text()


def test_a_repair_with_no_created_date_is_left_out_and_flagged(tmp_path):
    cid = REQUESTS["Q04"]["Subject"]

    def blank(name, rows):
        if name != "jobs.csv":
            return None
        hit = next(r for r in rows if r["Customer ID"] == cid and r["Type"] == "repair" and r["Completed"] >= "2025-07")
        hit["Created"] = ""
        return rows

    folder = sample_with(tmp_path, [REQUESTS["Q04"]], edit=blank)
    briefings, _ = asum.run(folder, OfflineModel(asum.offline), tmp_path / "out", Q, answer_key=False)
    b = briefings[0]
    assert b.status == "needs review" and any("no created date" in p for p in b.problems), b.problems
    assert b.facts["days_to_complete"] is not None


def test_quotes_worth_nothing_dont_crash(tmp_path):
    cid = REQUESTS["Q04"]["Subject"]

    def zero(name, rows):
        if name != "quotes.csv":
            return None
        for r in rows:
            if r["Customer ID"] == cid:
                r["Amount"] = "0"
        return rows

    folder = sample_with(tmp_path, [REQUESTS["Q04"]], edit=zero)
    briefings, _ = asum.run(folder, OfflineModel(asum.offline), tmp_path / "out", Q, answer_key=False)
    q = briefings[0].facts["quotes"]
    assert q["decided"] and q["by value"] is None


# --- the recorded run -----------------------------------------------------------------------------------------


RECORDED = asum.SAMPLE / "recorded-run.json"


def test_the_recorded_run_replays_to_the_published_numbers(tmp_path):
    """Q05 and Q06 were recorded again once Dana's customer briefings counted only Tucson's work. Q05's briefing
    worked out two numbers of its own (55% and $519.59), so it goes to a person."""
    model = asum.Replay(RECORDED)
    briefings, _ = asum.run(asum.SAMPLE, model, tmp_path, Q)
    status = {b.request["Request"]: b.status for b in briefings}
    assert [k for k, v in status.items() if v == "ready"] == ["Q01", "Q02", "Q03", "Q04", "Q06", "Q07", "Q08", "Q09"]
    assert [k for k, v in status.items() if v == "needs review"] == ["Q05"]
    assert [k for k, v in status.items() if v == "refused"] == ["Q10", "Q11"]
    assert model.misses == 0
    score = (tmp_path / "score.md").read_text()
    assert score.startswith("# Against the answer key\n\n11 of 11") and "0 items had no recorded answer" in score
    by_id = {b.request["Request"]: b for b in briefings}
    assert "Counted: Tucson branch only" in (tmp_path / "U2" / "summaries" / "Q05.md").read_text()
    assert not (tmp_path / "U4" / "summaries" / "Q05.md").exists()
    # The fixed checks, on the recorded words: flip Tucson's "down 2.0%" to "up", or swap its years, and it's caught.
    q01 = by_id["Q01"]
    flipped = q01.answer | {"headline": q01.answer["headline"].replace("down 2.0%", "up 2.0%")}
    assert flipped["headline"] != q01.answer["headline"]
    b = asum.Briefing(q01.request, Q, facts=q01.facts)
    asum.check(b, flipped, [])
    assert any("'up'" in p for p in b.problems), b.problems
    first = q01.answer["points"][0]
    swapped = first | {
        "text": first["text"].replace(
            "$5,000,999 against $5,101,919 in Q3 2024", "$5,101,919 against $5,000,999 in Q3 2024"
        )
    }
    assert swapped["text"] != first["text"]
    b = asum.Briefing(q01.request, Q, facts=q01.facts)
    asum.check(b, q01.answer | {"points": [swapped]}, [])
    assert any("wrong quarter" in p for p in b.problems), b.problems


def test_a_recording_with_a_missing_answer_says_so(tmp_path):
    data = json.loads(RECORDED.read_text())
    del data["answers"]["request:Q01"]
    stale = tmp_path / "stale.json"
    stale.write_text(json.dumps(data))
    model = asum.Replay(stale)
    briefings, _ = asum.run(asum.SAMPLE, model, tmp_path / "out", Q)
    assert model.misses == 1 and briefings[0].status == "needs review"
    assert "1 items had no recorded answer" in (tmp_path / "out" / "score.md").read_text()
