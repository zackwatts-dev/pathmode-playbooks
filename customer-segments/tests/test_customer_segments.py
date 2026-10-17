import json
import shutil
from datetime import date

import customer_segments as cs
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


def test_the_recorded_run_replays(tmp_path):
    custs, profs, top, _ = cs.run(cs.SAMPLE, cs.Replay(cs.SAMPLE / "recorded-run.json"), tmp_path, cs.SAMPLE_CUTOFF)
    assert len(top) == 25 and all(p.get("ai") or p.get("problems") for p in profs)
    assert "actually paid more than 20 days late" in (tmp_path / "score.md").read_text()


def test_with_an_answer_key_the_model_scores_each_customer_out_of_fold():
    test = {**cs.predictions(LIST, cs.SAMPLE)["late"], "verdict": "use the model"}  # as if the model had won
    cs.score_late(LIST, test)
    x, y = cs.matrix(test["known"], cs.NAMES), test["y"]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=cs.SEED)
    oof = cross_val_predict(cs.new_model(), x, y, cv=folds, method="predict_proba")[:, 1]
    in_sample = cs.new_model().fit(x, y).predict_proba(x)[:, 1]
    got = [c.late_risk for c in test["known"]]
    assert got == [round(float(v), 3) for v in oof]
    assert got != [round(float(v), 3) for v in in_sample]


def test_the_ai_is_told_the_chance_of_paying_late_not_of_leaving():
    seen = []

    class Spy:
        name = "spy"

        def complete(self, system, user, max_tokens=2000):
            seen.append(user)
            return json.dumps({"why": "x", "action": "y"})

    cs.explain(LIST[0], Spy())
    assert "chance of paying more than 20 days late" in seen[0] and "leaving" not in seen[0]


def test_the_late_payment_list_is_labelled_as_late_payment_everywhere(tmp_path):
    cs.run(cs.SAMPLE, OfflineModel(cs.offline), tmp_path, cs.SAMPLE_CUTOFF)
    billing = (tmp_path / "dashboard-billing.html").read_text()
    assert "actually paid more than 20 days late in 2025" in billing and "left in 2025" not in billing
    assert (tmp_path / "late-payment-list.csv").exists() and not (tmp_path / "at-risk.csv").exists()


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
    custs, _, top, _ = cs.run(cs.SAMPLE, OfflineModel(cs.offline), tmp_path, cs.SAMPLE_CUTOFF, answer_key=False)
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
    _, _, top, _ = cs.run(data, OfflineModel(cs.offline), tmp_path / "out", cs.SAMPLE_CUTOFF, answer_key=False)
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
