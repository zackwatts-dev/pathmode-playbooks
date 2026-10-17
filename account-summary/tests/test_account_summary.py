import json

import account_summary as asum

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

DATA = asum.Data.load(asum.SAMPLE)
REQUESTS = {r["Request"]: r for r in read_csv(asum.SAMPLE / "requests.csv")}


def briefing(rid, answer):
    r = REQUESTS[rid]
    b = asum.Briefing(r, refused=asum.authorize(DATA, r["User"], r["Kind"], r["Subject"]))
    model = ScriptedModel([json.dumps(answer)])
    if not b.refused:
        b.facts = asum.facts(DATA, r["Kind"], r["Subject"])
        asum.write(b, DATA, model)
    return b, model


def good(points, **more):
    return {"headline": "Steady quarter.", "points": points, "customers_say": [], "worth_asking": []} | more


def test_the_facts_reconcile_with_the_answer_key(tmp_path):
    briefings, _ = asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path)
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
    f = asum.facts(DATA, "customer", REQUESTS["Q04"]["Subject"])
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
    mail = asum.emails_for(DATA, REQUESTS["Q04"]["Subject"])
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
    b = asum.Briefing(r)
    b.facts = asum.facts(DATA, "customer", r["Subject"])
    asum.write(b, DATA, ScriptedModel(["not json"]))
    assert b.status == "needs review"


def test_the_page_escapes_what_the_ai_wrote(tmp_path):
    from summary_page import page

    b, _ = briefing("Q04", good([{"text": "<script>alert(1)</script>", "metrics": ["revenue"]}]))
    html = page([b], DATA, "scripted")
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
    asum.run(asum.SAMPLE, OfflineModel(asum.offline), tmp_path)
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
