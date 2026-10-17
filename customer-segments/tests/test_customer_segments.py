import csv
import json
import random
import shutil
from datetime import date
from types import SimpleNamespace

import customer_segments as cs
import pytest
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

CUSTS = cs.build_features(cs.SAMPLE, cs.SAMPLE_CUTOFF)
LIST = list(CUSTS.values())


def test_no_feature_looks_past_the_cutoff():
    # Build again with an earlier cutoff: nothing dated after it may change the result for that date.
    early = cs.build_features(cs.SAMPLE, date(2024, 6, 30))
    c = next(iter(early.values()))
    assert all(v is not None for v in c.x.values())
    # Every job, invoice and payment counted is on or before the cutoff: days since last job can't be negative.
    assert min(c.x["days_since_job"] for c in early.values()) >= 0


def test_segments_are_chosen_by_silhouette_and_cover_everyone():
    seg = cs.segment(LIST)
    assert seg["k"] == max(seg["silhouette"], key=seg["silhouette"].get)
    assert {c.cluster for c in LIST} == set(range(seg["k"]))


def test_one_segment_recovers_the_hidden_late_payers():
    cs.segment(LIST)
    behavior = {
        r["Customer ID"]: float(r["Pays late by (days)"]) for r in read_csv(cs.SAMPLE / "answer-key-behavior.csv")
    }
    by = {}
    for c in LIST:
        if c.id in behavior:
            by.setdefault(c.cluster, []).append(behavior[c.id])
    means = sorted(sum(v) / len(v) for v in by.values())
    assert means[-1] > 3 * means[len(means) // 2]  # one group pays far later than the typical group


def test_predictions_are_tested_against_a_rule_and_churn_is_not_predictable():
    preds = cs.predictions(LIST, cs.SAMPLE)
    assert preds["late"]["verdict"] != "not predictable from these records"
    assert preds["late"]["rule_hits"] > 5 * preds["late"]["base_hits"]
    assert preds["churn"]["verdict"] == "not predictable from these records"


def test_invented_numbers_in_a_segment_name_go_to_a_person():
    profs = cs.profiles(LIST)[:1]
    cs.name_segments(
        profs,
        ScriptedModel(
            [json.dumps({"name": "Big spenders", "who": "They spend $987,654 a year.", "treat": ["Call them."]})]
        ),
    )
    assert profs[0]["problems"] and "987,654" in profs[0]["problems"][0]


def test_a_will_pay_late_verdict_goes_to_a_person():
    c = LIST[0]
    cs.explain(c, ScriptedModel([json.dumps({"why": "They will pay late.", "action": "Ask for a deposit."})]))
    assert any("signal, not a verdict" in p for p in c.problems)


def test_the_ai_sees_no_contact_details():
    seen = []

    class Spy:
        name = "spy"

        def complete(self, system, user, max_tokens=2000):
            seen.append(user)
            return json.dumps({"why": "x", "action": "y"})

    cs.explain(LIST[0], Spy())
    assert LIST[0].name not in seen[0] and "@" not in seen[0]


def test_with_an_answer_key_the_model_scores_each_customer_out_of_fold():
    test = {**cs.predictions(LIST, cs.SAMPLE)["late"], "verdict": "use the model"}  # as if the model had won
    cs.score_late(LIST, test)
    x, y = cs.matrix(test["known"], cs.NAMES), test["y"]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=cs.SEED)
    oof = cross_val_predict(cs.new_model(), x, y, cv=folds, method="predict_proba")[:, 1]
    in_sample = cs.new_model().fit(x, y).predict_proba(x)[:, 1]
    got = [c.late_score for c in test["known"]]
    assert got == [round(float(v), 3) for v in oof]
    assert got != [round(float(v), 3) for v in in_sample]


def test_the_ai_is_told_a_late_payment_score_not_a_chance_and_not_of_leaving():
    seen = []

    class Spy:
        name = "spy"

        def complete(self, system, user, max_tokens=2000):
            seen.append(user)
            return json.dumps({"why": "x", "action": "y"})

    cs.explain(LIST[0], Spy())
    assert "late-payment score (0 to 1, for ranking; not a probability)" in seen[0]
    assert "chance" not in seen[0] and "leaving" not in seen[0]


def test_the_late_payment_list_is_labelled_as_late_payment_everywhere(tmp_path):
    cs.run(cs.SAMPLE, OfflineModel(cs.offline), tmp_path, cs.SAMPLE_CUTOFF)
    billing = (tmp_path / "billing" / "dashboard-billing.html").read_text()
    assert "actually paid more than 20 days late in 2025" in billing and "left in 2025" not in billing
    assert (tmp_path / "billing" / "late-payment-list.csv").exists() and not (tmp_path / "at-risk.csv").exists()


def test_the_spend_trend_works_for_a_cutoff_outside_december():
    mid = [c for c in cs.build_features(cs.SAMPLE, date(2024, 6, 30)).values() if c.x["spend"]]
    trend = sum(c.x["trend"] for c in mid) / len(mid)
    assert 0.3 < trend < 0.7  # about half the year's spend falls in its last six months, not almost none


def test_a_leap_day_cutoff_works():
    assert cs.months_before(date(2024, 2, 29), 12) == date(2023, 2, 28)
    assert cs.months_before(date(2024, 8, 31), 6) == date(2024, 2, 29)
    assert cs.months_before(date(2024, 12, 31), 6) == date(2024, 6, 30)
    assert cs.build_features(cs.SAMPLE, date(2024, 2, 29))


def test_history_labels_come_from_the_year_after_and_only_from_customers_who_existed():
    start, end = date(2023, 12, 31), date(2024, 12, 31)
    late, left = cs.history_labels(cs.SAMPLE, start, end)
    since = {r["Customer ID"]: date.fromisoformat(r["Since"]) for r in read_csv(cs.SAMPLE / "customers.csv")}
    assert all(since[cid] <= start for cid in [*late, *left])
    assert 50 < sum(late.values()) < len(late) / 2


def test_without_an_answer_key_it_learns_from_last_years_history(tmp_path):
    # The sample's answer key is still there, but only to score the list: the predictions learn from history.
    custs, _, top, *_ = cs.run(cs.SAMPLE, OfflineModel(cs.offline), tmp_path, cs.SAMPLE_CUTOFF, answer_key=False)
    page = (tmp_path / "dashboard.html").read_text()
    assert "Learned from history (features to 2023-12-31, outcomes to 2024-12-31)" in page
    late = {
        r["Customer ID"]: int(r["Paid late (over 20 days)"]) for r in read_csv(cs.SAMPLE / "answer-key-late-2025.csv")
    }
    assert sum(late.get(c.id, 0) for c in top) >= 20  # the 2025 answer key agrees with a list learned from 2024


def test_a_company_without_answer_keys_still_gets_a_tested_late_payment_list(tmp_path):
    data = tmp_path / "exports"
    data.mkdir()
    for f in cs.SAMPLE.glob("*.csv"):
        if not f.name.startswith("answer-key"):
            shutil.copy(f, data)
    _, _, top, *_ = cs.run(data, OfflineModel(cs.offline), tmp_path / "out", cs.SAMPLE_CUTOFF, answer_key=False)
    page = (tmp_path / "out" / "dashboard.html").read_text()
    assert len(top) == 25 and "Who will pay more than 20 days late next year?" in page
    assert "not enough examples in the records to test it" in page  # leaving: the sample holds no ex-customers
    assert not (tmp_path / "out" / "score.md").exists()


def test_a_malformed_segment_answer_goes_to_a_person_and_the_run_goes_on():
    profs = cs.profiles(LIST)[:4]
    answers = [
        json.dumps({"name": "Quiet accounts", "who": "Mostly small customers.", "treat": None}),  # null list: []
        json.dumps({"name": 7, "who": "x", "treat": []}),
        json.dumps({"name": "Busy sites", "who": "x", "treat": [{"do": "call"}]}),
        json.dumps(["not", "an", "object"]),
    ]
    cs.name_segments(profs, ScriptedModel(answers))
    assert profs[0]["ai"]["treat"] == [] and not profs[0]["problems"]
    assert all(p["ai"] is None and "couldn't name it" in p["problems"][0] for p in profs[1:])


def test_a_malformed_explanation_goes_to_a_person_and_the_run_goes_on():
    for answer in [
        {"why": None, "action": "Call."},
        {"why": ["late"], "action": "Call."},
        {"why": "Late.", "action": 3},
    ]:
        c = cs.Customer("x", "X", "single_site", "PHX", x=dict(LIST[0].x))
        cs.explain(c, ScriptedModel([json.dumps(answer)]))
        assert c.explanation is None and "couldn't explain it" in c.problems[0]


# --- the recorded run, replayed: the published numbers, and what it must never do --------------------------------


@pytest.fixture(scope="module")
def replayed(tmp_path_factory):
    out = tmp_path_factory.mktemp("replay")
    model = cs.Replay(cs.SAMPLE / "recorded-run.json")
    custs, profs, top, written, note = cs.run(cs.SAMPLE, model, out, cs.SAMPLE_CUTOFF)
    return SimpleNamespace(custs=custs, profs=profs, top=top, written=written, note=note, out=out, model=model)


def test_the_recorded_run_replays_with_the_published_numbers(replayed):
    score = (replayed.out / "score.md").read_text()
    assert len(replayed.profs) == 7 and len(replayed.top) == 25
    assert "Model: 0.98; the rule (pays_late): 0.99" in score and "In the top 25: model 23, rule 23" in score
    assert "Model: 0.62; the rule (days_since_job): 0.64" in score and "model 3, rule 1" in score
    assert "**25 actually paid more than 20 days late** in 2025" in score
    slow = max(replayed.profs, key=lambda p: p["pays_late"])
    assert (slow["customers"], slow["pays_late"]) == (60, 43.03)


def test_the_team_files_name_no_one_with_a_late_payment_measure(replayed):
    on_list = {c.name for c in replayed.top}
    for f in (f for f in replayed.out.iterdir() if f.is_file()):
        text = f.read_text()
        if f.name != "customers.csv":  # the team's customer file names everyone, so it's checked by its columns
            assert not [n for n in on_list if n in text], f.name
        assert "late_score" not in text and "late_risk" not in text, f.name
    page = (replayed.out / "dashboard.html").read_text()
    assert not [c.name for c in replayed.custs if f"<title>{c.name}" in page]  # the map's labels: segments only
    header = next(csv.reader((replayed.out / "customers.csv").open()))
    assert header[:3] == ["customer", "name", "segment"]
    assert not [h for h in header if "late" in h or h in cs.LATE_MEASURES]
    billing = next(csv.reader((replayed.out / "billing" / "customers.csv").open()))
    assert "pays_late" in billing


def test_the_late_payment_list_and_scores_are_only_in_the_billing_folder(replayed):
    billing = replayed.out / "billing"
    assert {f.name for f in billing.iterdir()} == {
        "customers.csv",
        "dashboard-billing.html",
        "late-payment-list.csv",
        "late-scores.csv",
        "review-queue.csv",
    }
    assert all(c.name in (billing / "late-payment-list.csv").read_text() for c in replayed.top)
    assert not (replayed.out / "late-payment-list.csv").exists()


def test_replay_counts_and_reports_items_with_no_recorded_answer(replayed, tmp_path):
    assert replayed.model.misses == 0 and "0 items had no recorded answer" in replayed.note
    data = json.loads((cs.SAMPLE / "recorded-run.json").read_text())
    for key in [k for k in data["answers"] if k.startswith("customer:")][:3]:
        del data["answers"][key]
    stale = tmp_path / "stale.json"
    stale.write_text(json.dumps(data))
    model = cs.Replay(stale)
    _, _, top, _, note = cs.run(cs.SAMPLE, model, tmp_path / "out", cs.SAMPLE_CUTOFF)
    assert model.misses == 3 and "3 items had no recorded answer" in note
    assert "3 items had no recorded answer" in (tmp_path / "out" / "score.md").read_text()
    missed = [c for c in top if any("no recorded answer" in p for p in c.problems)]
    assert len(missed) == 3 and all(c.explanation is None for c in missed)


def test_a_recorded_name_that_fails_its_check_is_held_for_a_person(replayed):
    held = [p for p in replayed.profs if p["problems"]]
    assert sorted(p["segment"] for p in held) == [1, 3]
    page = (replayed.out / "dashboard.html").read_text()
    assert all(f"<b>{cs.shown_name(p)}</b>" in page for p in replayed.profs)
    assert all(cs.shown_name(p).endswith("(to be named)") for p in held)
    assert "Held for a person" in page
    slow = max(replayed.profs, key=lambda p: p["pays_late"])
    assert cs.shown_name(slow) == "Late-Paying Small Sites"


def test_the_summary_says_the_list_is_the_rules_when_the_rule_won(replayed):
    assert "ranked by the rule (days late in the last 12 months)" in replayed.note
    assert "predictions learned from" not in replayed.note
    billing = (replayed.out / "billing" / "dashboard-billing.html").read_text()
    assert "Ranked by the rule" in billing and "not a probability" in billing


def test_everyone_on_the_replayed_list_paid_late_in_the_last_12_months(replayed):
    assert all(c.x["pays_late"] > 20 for c in replayed.top)


# --- features: cutoff-clean, honest about missing values ------------------------------------------------------


def write_exports(folder, extra=None):
    """A tiny set of exports: two customers with one site and one job each, plus whatever rows a test adds."""
    files = {
        "customers.csv": (
            ["Customer ID", "Name", "Segment", "Branch", "Terms (days)", "Uses portal", "Since"],
            [["A", "Alpha Co", "single_site", "PHX", "30", "1", "2015-01-01"]]
            + [["B", "Beta Co", "single_site", "PHX", "30", "1", "2015-01-01"]],
        ),
        "sites.csv": (
            ["Site ID", "Customer ID", "Site", "Branch"],
            [["S1", "A", "Alpha", "PHX"], ["S2", "B", "Beta", "PHX"]],
        ),
        "agreements.csv": (["Agreement ID", "Site ID", "Customer ID", "Tier", "Start", "End", "Billing"], []),
        "jobs.csv": (
            ["WO", "Customer ID", "Site ID", "Equipment ID", "Type", "Created", "Completed", "Status"],
            [["1", "A", "S1", "E1", "repair", "2024-06-01", "2024-06-02", "Completed"]]
            + [["2", "B", "S2", "E2", "repair", "2024-06-01", "2024-06-02", "Completed"]],
        ),
        "quotes.csv": (["Quote", "Customer ID", "Type", "Amount", "Sent", "Status", "Decided", "Unit installed"], []),
        "invoices.csv": (["Invoice", "Customer ID", "Date", "Due", "Amount", "Source"], []),
        "payments.csv": (["Invoice", "Paid", "Amount"], []),
    }
    for name, rows in (extra or {}).items():
        files[name][1].extend(rows)
    folder.mkdir(exist_ok=True)
    for name, (head, rows) in files.items():
        with (folder / name).open("w", newline="") as f:
            csv.writer(f).writerows([head, *rows])
    return folder


def test_an_unpaid_overdue_invoice_counts_as_late_and_only_the_last_12_months_count(tmp_path):
    data = write_exports(
        tmp_path / "x",
        {
            "invoices.csv": [
                ["I1", "A", "2024-09-01", "2024-10-01", "1000", "job"],  # never paid: 91 days late at the cutoff
                ["I2", "B", "2023-02-01", "2023-03-01", "500", "job"],  # paid 92 days late, but in 2023
                ["I3", "B", "2024-11-01", "2024-12-01", "500", "job"],  # paid 4 days late
            ],
            "payments.csv": [["I2", "2023-06-01", "500"], ["I3", "2024-12-05", "500"]],
        },
    )
    x = cs.build_features(data, cs.SAMPLE_CUTOFF)
    assert x["A"].x["pays_late"] == 91.0
    assert x["B"].x["pays_late"] == 4.0
    assert cs.rule_score(x["A"]) > cs.rule_score(x["B"])


def test_customers_without_decided_quotes_get_no_made_up_approval_rate_or_speed():
    none = [c for c in LIST if not c.x["has_quotes"]]
    assert len(none) > 100
    assert all(c.x["approves"] is None and c.x["decides_days"] is None for c in none)
    cs.segment(LIST)
    for p in cs.profiles(LIST):
        members = [c for c in LIST if c.cluster == p["segment"] and c.x["decides_days"] is not None]
        assert p["n"]["decides_days"] == len(members)
        if members:
            assert p["decides_days"] == round(sum(c.x["decides_days"] for c in members) / len(members), 2)


def test_the_ai_is_told_how_many_customers_had_no_quotes():
    seen = []

    class Spy:
        name = "spy"

        def complete(self, system, user, max_tokens=2000):
            seen.append(user)
            return json.dumps({"name": "x", "who": "x", "treat": []})

    cs.segment(LIST)
    profs = cs.profiles(LIST)
    cs.name_segments(profs, Spy())
    assert any("n/a (no decided quotes)" in u for u in seen)
    c = next(c for c in LIST if not c.x["has_quotes"])
    cs.explain(c, Spy())
    assert '"n/a (no decided quotes)"' in seen[-1]


def test_events_after_the_cutoff_change_no_feature(tmp_path):
    """The exports are taken after the cutoff: plant what happened next, and nothing may change."""
    data = tmp_path / "exports"
    data.mkdir()
    for f in cs.SAMPLE.glob("*.csv"):
        if not f.name.startswith("answer-key"):
            shutil.copy(f, data)

    def edit(name, change=None, add=()):
        rows = list(csv.DictReader((data / name).open()))
        head = list(rows[0])
        if change:
            change(rows)
        rows += [dict(zip(head, r, strict=True)) for r in add]
        with (data / name).open("w", newline="") as f:
            w = csv.DictWriter(f, head)
            w.writeheader()
            w.writerows(rows)

    def decide_one(rows):  # a quote still waiting at the cutoff, accepted in January
        q = next(r for r in rows if r["Status"] == "Sent" and r["Sent"] >= "2024-11-01")
        q.update(Status="Accepted", Decided="2025-01-10")

    def complete_one(rows):  # a job open at the cutoff for weeks, completed in January
        j = next(r for r in rows if not r["Completed"] and r["Created"] <= "2024-11-30")
        j.update(Completed="2025-01-10", Status="Completed")

    def end_one(rows):  # an agreement that ran past the cutoff and ended in March
        next(r for r in rows if not r["End"]).update(End="2025-03-01")

    invoices = {r["Invoice"]: r for r in read_csv(data / "invoices.csv")}
    paid = {r["Invoice"] for r in read_csv(data / "payments.csv")}
    unpaid = next(i for i, r in invoices.items() if i not in paid and "2024-10-01" <= r["Due"] <= "2024-12-31")
    edit("customers.csv", add=[["NEW", "Joined Later Co", "single_site", "PHX", "30", "1", "2025-01-05"]])
    edit("sites.csv", add=[["S-NEW", "1", "New site, opened 2025", "PHX"]])
    edit(
        "jobs.csv", complete_one, add=[["999999", "1", "S-NEW", "", "repair", "2025-01-03", "2025-01-04", "Completed"]]
    )
    edit("quotes.csv", decide_one)
    edit("agreements.csv", end_one)
    edit("invoices.csv", add=[["LATE-1", "1", "2025-01-02", "2025-02-01", "900", "job"]])
    edit("payments.csv", add=[["LATE-1", "2025-01-30", "900"], [unpaid, "2025-01-15", invoices[unpaid]["Amount"]]])

    planted = cs.build_features(data, cs.SAMPLE_CUTOFF)
    assert "NEW" not in planted
    assert {cid: c.x for cid, c in planted.items()} == {cid: c.x for cid, c in CUSTS.items()}


def test_features_never_read_the_answer_keys(tmp_path):
    data = tmp_path / "exports"
    data.mkdir()
    for f in cs.SAMPLE.glob("*.csv"):
        if not f.name.startswith("answer-key"):
            shutil.copy(f, data)
    assert {k: c.x for k, c in cs.build_features(data, cs.SAMPLE_CUTOFF).items()} == {k: c.x for k, c in CUSTS.items()}


def test_amounts_with_dollars_and_commas_are_read_and_unreadable_rows_go_to_a_person(tmp_path):
    data = write_exports(
        tmp_path / "x",
        {
            "invoices.csv": [
                ["I1", "A", "2024-09-01", "2024-10-01", "$1,225.42", "job"],
                ["I2", "A", "2024-09-01", "2024-10-01", "about 300", "job"],
            ],
            "quotes.csv": [["Q1", "B", "repair", "500", "2024-05-01", "Accepted", "", ""]],  # accepted, but when?
        },
    )
    problems = []
    x = cs.build_features(data, cs.SAMPLE_CUTOFF, problems)
    assert x["A"].x["spend"] == 1225.42
    assert x["B"].x["approves"] is None
    assert {p["which"] for p in problems} == {"invoice I2", "quote Q1"}


def test_a_customer_who_joined_after_the_cutoff_isnt_a_customer_yet(tmp_path):
    data = write_exports(
        tmp_path / "x", {"customers.csv": [["C", "Later Co", "single_site", "PHX", "30", "1", "2025-02-01"]]}
    )
    assert set(cs.build_features(data, cs.SAMPLE_CUTOFF)) == {"A", "B"}


# --- sanity: segments, and verdicts on made-up data where the right answer is known ---------------------------


def test_segment_count_and_sizes_are_reasonable():
    seg = cs.segment(LIST)
    sizes = [sum(c.cluster == k for c in LIST) for k in range(seg["k"])]
    assert 3 <= seg["k"] <= 7
    assert min(sizes) >= 0.03 * len(LIST) and max(sizes) <= 0.3 * len(LIST)


def made_up(seed: int = 1, n: int = 600) -> list:
    rng = random.Random(seed)
    custs = []
    for i in range(n):
        x = {name: rng.random() for name in cs.NAMES}
        x.update(pays_late=rng.uniform(0, 60), has_quotes=1, days_since_job=rng.uniform(0, 400))
        custs.append(cs.Customer(str(i), f"C{i}", "single_site", "PHX", x=x))
    return custs


def test_a_random_outcome_comes_out_not_predictable():
    custs, rng = made_up(), random.Random(2)
    labels = {c.id: int(rng.random() < 0.3) for c in custs}
    assert cs.evaluate(custs, labels, "pays_late")["verdict"] == cs.NOT_PREDICTABLE


def test_a_simple_threshold_comes_out_use_the_rule():
    custs = made_up()
    labels = {c.id: int(c.x["pays_late"] > 40) for c in custs}
    assert cs.evaluate(custs, labels, "pays_late")["verdict"] == cs.USE_RULE


def test_a_combined_signal_comes_out_use_the_model():
    custs = made_up()
    labels = {c.id: int(c.x["repair_share"] + c.x["trend"] > 1.1) for c in custs}
    assert cs.evaluate(custs, labels, "pays_late")["verdict"] == cs.USE_MODEL


def test_no_named_list_when_late_payment_isnt_predictable(tmp_path, monkeypatch):
    real = cs.predictions

    def unpredictable(custs, folder):
        preds = real(custs, folder)
        preds["late"]["verdict"] = cs.NOT_PREDICTABLE
        return preds

    monkeypatch.setattr(cs, "predictions", unpredictable)
    _, _, top, _, note = cs.run(cs.SAMPLE, OfflineModel(cs.offline), tmp_path, cs.SAMPLE_CUTOFF)
    assert top == [] and "no late-payment list" in note
    assert len(read_csv(tmp_path / "billing" / "late-payment-list.csv")) == 0
    assert len(read_csv(tmp_path / "billing" / "late-scores.csv")) == 0
    assert "No list this time" in (tmp_path / "billing" / "dashboard-billing.html").read_text()
    assert "No late-payment list" in (tmp_path / "score.md").read_text()


# --- checks on the AI's words -----------------------------------------------------------------------------------


def slow_segment():
    cs.segment(LIST)
    profs = cs.profiles(LIST)
    return max(profs, key=lambda p: p["pays_late"]), profs


def name_it(answer):
    """The slow-paying segment's problems, when the AI gives every segment this answer."""
    slow, profs = slow_segment()
    cs.name_segments(profs, ScriptedModel([json.dumps(answer)] * len(profs)))
    return slow["problems"]


def test_the_fastest_payers_in_the_slow_paying_segment_go_to_a_person():
    problems = name_it({"name": "Valued Accounts", "who": "These are the fastest payers we have.", "treat": ["Call."]})
    assert any('"fastest ... pays_late"' in p for p in problems)


def test_a_segment_name_is_checked_for_direction_and_numbers():
    assert any(
        '"Fast-Paying"' in p for p in name_it({"name": "Fast-Paying Accounts", "who": "Customers.", "treat": []})
    )
    assert any("$5k" in p for p in name_it({"name": "$5k Spenders", "who": "Customers.", "treat": []}))


def test_a_true_direction_passes():
    slow, _ = slow_segment()
    days = slow["pays_late"]
    answer = {"name": "Slow-Paying Accounts", "who": f"They pay later than most, {days} days on average.", "treat": []}
    assert name_it(answer) == []


def customer(**x):
    return cs.Customer("x", "X", "single_site", "PHX", x={**LIST[0].x, **x})


def test_a_share_written_as_days_goes_to_a_person():
    c = customer(approves=0.88, pays_late=31.5)
    cs.explain(c, ScriptedModel([json.dumps({"why": "They may pay 88 days late.", "action": "Call them."})]))
    assert any("88 as days" in p for p in c.problems)


def test_made_up_money_and_years_go_to_a_person():
    c = customer(spend=94400.36)
    why = "They may owe $8M, they spend $5k a month, and they've been a customer since 1999."
    cs.explain(c, ScriptedModel([json.dumps({"why": why, "action": "Call."})]))
    text = " ".join(c.problems)
    assert "$8M" in text and "$5k" in text and "1999" in text


def test_talk_of_bankruptcy_or_fraud_goes_to_a_person():
    for why, action in [
        ("They may be heading for bankruptcy.", "Call."),
        ("Late payment may point to fraud.", "Call."),
        ("They may pay late.", "Consider a lawsuit."),
        ("They may pay late.", "Stop doing business with them."),
    ]:
        c = customer()
        cs.explain(c, ScriptedModel([json.dumps({"why": why, "action": action})]))
        assert any("a person decides what to say" in p for p in c.problems), (why, action)


def test_words_that_fail_a_check_are_held_not_shown(tmp_path):
    from segments_dashboard import dashboard

    cs.segment(LIST)
    profs = cs.profiles(LIST)
    for p in profs:
        p["ai"], p["problems"] = {"name": "Big spenders", "who": "They spend $987,654.", "treat": []}, ["bad number"]
    names = {p["segment"]: cs.shown_name(p) for p in profs}
    seg = {"k": len(profs), "silhouette": {}, "points": [(0.0, 0.0)] * len(LIST)}
    page = dashboard(LIST, profs, seg, {}, [], names, "test", None)
    assert "$987,654" not in page.split("Needs a person first")[1].split("</section>")[1]
    assert "Big spenders" not in [n for n in names.values()]


def test_faster_decisions_are_checked_against_customers_who_had_quotes():
    # The high-agreement segment holds most of the customers with no decided quotes. Filled with 0 days, it looked
    # fastest to decide; over the customers who had quotes, it's slower than average, and "faster" is caught.
    cs.segment(LIST)
    profs = cs.profiles(LIST)
    loyal = max(profs, key=lambda p: p["agreement"])
    overall = cs.overall_profile(profs)
    assert loyal["n"]["decides_days"] < loyal["customers"] / 2
    assert loyal["decides_days"] > overall["decides_days"]
    answer = {"name": "Loyal Agreement Sites", "who": "They make faster quote decisions than most.", "treat": []}
    cs.name_segments(profs, ScriptedModel([json.dumps(answer)] * len(profs)))
    assert any('"faster ... decides_days"' in p for p in loyal["problems"])


def test_a_threshold_is_not_read_as_a_comparison():
    assert cs.claimed_directions("Share of jobs open more than 21 days. They may pay more than 20 days late.") == []
