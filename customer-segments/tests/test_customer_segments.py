import json
from datetime import date

import customer_segments as cs

from common.fake import ScriptedModel
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
