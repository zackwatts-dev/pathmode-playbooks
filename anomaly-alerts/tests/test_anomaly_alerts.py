import json
from pathlib import Path

import anomaly_alerts as aa

from common.fake import OfflineModel, ScriptedModel

DATA = aa.Data.load(aa.SAMPLE)
FLAGS = aa.prioritize(aa.detect(DATA, aa.SAMPLE_START, aa.SAMPLE_END))
KEY = aa.SAMPLE / "answer-key.csv"


def first(check):
    return next(fl for fl in FLAGS if fl.check == check)


def test_the_rules_catch_every_known_problem_they_were_written_for():
    scored = aa.score(FLAGS, aa.within_budget(FLAGS, 12), KEY)
    rows = {r["problem"]: r for r in scored["rows"]}
    for problem in ("written down to NTE", "NTE increase not recorded", "hours not logged"):
        assert rows[problem]["caught"] == rows[problem]["real"] > 0
    assert rows["unbilled parts"]["flags that were real"] == rows["unbilled parts"]["flags"]  # no false alarms


def test_the_model_finds_technicians_with_real_habits():
    scored = aa.score(FLAGS, [], KEY)
    flagged, real, known = scored["techs"]
    assert flagged >= 10 and real >= flagged // 2


def test_the_model_over_jobs_finds_unusual_not_wrong():
    period = [wo for wo, j in DATA.jobs.items() if j["Completed"] >= "2025-09-01"]
    jobs = aa.model(DATA, period, {fl.subject for fl in FLAGS})
    key = {r["WO"] for r in aa.read_csv(KEY)}
    # Big installs and routine visits: odd, but nothing wrong with them.
    assert len(jobs) > 20 and not [fl for fl in jobs if fl.subject in key]


def test_the_budget_caps_each_owner_and_hides_nothing(tmp_path):
    flags, _ = aa.run(DATA, OfflineModel(aa.offline), tmp_path, aa.SAMPLE_START, aa.SAMPLE_END, budget=3)
    investigated = [fl for fl in flags if fl.status != aa.NOT_INVESTIGATED]
    assert len(investigated) == 6  # two owners, three each
    assert len(aa.read_csv(tmp_path / "flags.csv")) == len(flags)


def test_an_explanation_citing_records_that_dont_exist_goes_to_a_person():
    fl = first("parts not billed")
    aa.investigate(
        fl,
        DATA,
        ScriptedModel(
            [
                json.dumps(
                    {
                        "what_happened": "Parts were not billed.",
                        "likely_cause": "x",
                        "action": "y",
                        "evidence": ["WO999999999"],
                    }
                )
            ]
        ),
    )
    assert fl.status == aa.CHECK_FAILED and "isn't in the records" in fl.problems[0]


def test_an_explanation_with_invented_numbers_goes_to_a_person():
    fl = first("written down to NTE")
    aa.investigate(
        fl,
        DATA,
        ScriptedModel(
            [
                json.dumps(
                    {
                        "what_happened": "We lost $98,765.43 on this job.",
                        "likely_cause": "x",
                        "action": "y",
                        "evidence": [f"WO{fl.subject}"],
                    }
                )
            ]
        ),
    )
    assert fl.status == aa.CHECK_FAILED and "98,765.43" in " ".join(fl.problems)


def test_an_unusable_answer_leaves_the_flag_standing():
    fl = first("NTE increase not recorded")
    aa.investigate(fl, DATA, ScriptedModel(["I think this is fine."]))
    assert fl.status == aa.CHECK_FAILED


def test_the_recorded_run_replays(tmp_path):
    model = aa.Replay(aa.SAMPLE / "recorded-run.json")
    flags, _ = aa.run(DATA, model, tmp_path, aa.SAMPLE_START, aa.SAMPLE_END, answer_key=KEY)
    assert all(fl.status != aa.NOT_INVESTIGATED for fl in aa.within_budget(flags, 12))
    assert (tmp_path / "alerts" / "controller.eml").exists()


def test_the_dashboard_escapes_what_it_shows(tmp_path):
    fl = first("hours not logged")
    fl.detail, fl.status, fl.problems = "<script>alert(1)</script>", aa.CHECK_FAILED, ["test"]
    from alerts_dashboard import dashboard

    page = dashboard([fl], [fl], DATA, aa.SAMPLE_START, aa.SAMPLE_END, 12, "test", None)
    assert "<script>" not in page and "&lt;script&gt;" in page


def test_robust_z_is_not_fooled_by_one_huge_value():
    z = aa.robust_z({"a": 1, "b": 1.1, "c": 0.9, "d": 1.0, "e": 50})
    assert z["e"] > 10 and abs(z["a"]) < 1


def test_the_sample_files_exist():
    for name in ("jobs.csv", "visits.csv", "invoices.csv", "answer-key.csv", "tech-answer-key.csv"):
        assert Path(aa.SAMPLE / name).exists()
