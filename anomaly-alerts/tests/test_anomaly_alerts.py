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
    assert flagged >= 5 and real >= flagged * 2 // 3


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


# --- small made-up branches, to test the detectors on cases the sample doesn't have --------------------------

SEPT = aa.SAMPLE_START, aa.SAMPLE_END


def branch(techs, visits=20, wo=lambda t, i: f"{t}{i:03d}"):
    """A made-up branch: each technician gets `visits` repair visits, one job each, on their own equipment.
    `techs` maps a tech ID to its habits: hours per visit, blank (empty time entries), unlogged (no time entry
    at all), repeat (repairs followed by another job on the same equipment within 30 days)."""
    jobs, by_wo, hours, people = {}, {}, {}, {}
    for t, h in techs.items():
        people[t] = {"Tech ID": t, "Name": f"Tech {t}", "Branch": "PHX", "Title": "Technician", "Hired": ""}
        for i in range(visits):
            w, v, eq = wo(t, i), f"{t}{i:03d}", f"E{t}-{i}"
            job = {"WO": w, "Equipment ID": eq, "Branch": "Phoenix", "Created": "2025-09-01", "NTE": ""}
            jobs[w] = {**job, "Completed": "2025-09-05", "Type": "repair"}
            by_wo[w] = [{"Visit": v, "WO": w, "Tech ID": t, "Date": "2025-09-05", "Outcome": "Completed"}]
            if i < h.get("repeat", 0):
                jobs[f"{w}R"] = {**job, "WO": f"{w}R", "Created": "2025-09-15", "Completed": "", "Type": "repair"}
            if i >= h.get("unlogged", 0):
                logged = "" if i < h.get("blank", 0) else str(h.get("hours", 3.0))
                hours[v] = [{"Visit": v, "Tech ID": t, "Date": "2025-09-05", "Hours": logged}]
    return aa.Data(jobs, by_wo, hours, {}, {}, {}, {}, {}, people, {})


def ordinary(n=30, **odd):
    """n technicians with ordinary, slightly varied hours; `odd` gives some of them a habit."""
    return {str(t): {"hours": 2.6 + (t % 7) * 0.15, **odd.get(f"t{t}", {})} for t in range(1, n + 1)}


def test_a_month_where_nobody_is_unusual_flags_no_technician():
    assert aa.tech_model(branch(ordinary())) == []


def test_an_odd_mix_with_nothing_material_to_discuss_flags_nobody():
    # The longest jobs in the branch: unusual to the model, but nothing to talk about.
    assert aa.tech_model(branch(ordinary(t5={"hours": 7.5}))) == []


def test_a_material_habit_is_flagged_as_a_pattern_worth_a_conversation():
    flags = aa.tech_model(branch(ordinary(t5={"blank": 6})))
    assert [fl.subject for fl in flags] == ["T5"]
    assert "a pattern worth a conversation" in flags[0].detail and "visits with no hours 30%" in flags[0].detail


def test_money_comes_first_and_people_last():
    for owner in ("Controller", "Service manager"):
        mine = [fl for fl in FLAGS if fl.owner == owner]
        people = [fl.subject.startswith("T") for fl in mine]
        assert people == sorted(people)  # every job flag before any technician flag
        values = [fl.value or 0 for fl in mine if not fl.subject.startswith("T")]
        assert values == sorted(values, reverse=True)
    assert not aa.within_budget(FLAGS, 12)[-1].subject.startswith("T")  # the sample's budget goes to jobs


def test_robust_z_stays_sensible_when_most_values_are_zero():
    z = aa.robust_z({**{c: 0 for c in "abcdefghi"}, "j": 1})
    assert 1 < z["j"] < 10 and z["a"] == 0
    assert aa.robust_z({**{c: 0 for c in "abcdefghi"}, "j": 0.05}, floor=0.02)["j"] == 2.5
    assert aa.robust_z({c: 4 for c in "abcde"}) == {c: 0.0 for c in "abcde"}


def test_one_repeat_in_a_branch_with_none_is_not_flagged():
    data = branch(ordinary(20, t3={"repeat": 1}))
    period = [wo for wo, j in data.jobs.items() if j["Completed"]]
    assert aa.baselines(data, period) == []
    data = branch(ordinary(20, t3={"repeat": 6}))
    assert [fl.subject for fl in aa.baselines(data, period)] == ["T3"]


def test_a_visit_with_no_time_entry_at_all_counts_as_no_hours():
    data = branch(ordinary(5, t2={"unlogged": 1}), visits=3)
    flags = aa.rules(data, sorted(data.jobs, key=aa.id_key))
    assert [(fl.check, fl.subject) for fl in flags] == [("hours not logged", "2000")]


def test_alphanumeric_job_numbers_dont_stop_the_run():
    data = branch(ordinary(), wo=lambda t, i: f"WO-{t}-{i}")
    aa.detect(data, *SEPT)  # used to crash sorting the job numbers as integers
    assert sorted(["WO-100", "WO-99", "WO-9"], key=aa.id_key) == ["WO-9", "WO-99", "WO-100"]
    assert sorted(["10", "9", "100"], key=aa.id_key) == ["9", "10", "100"]


def test_the_digest_goes_to_the_configured_recipient_not_a_built_in_one():
    fls = [first("parts not billed")]
    msg = aa.digest("Controller", fls, *SEPT, {"Controller": "Ana Ruiz <ana@example.com>"})
    assert msg["To"] == "Ana Ruiz <ana@example.com>"
    msg = aa.digest("Controller", fls, *SEPT, {})
    assert msg["To"] is None and "No recipient set" in msg.get_content() and "summitmech" not in msg.as_string()
    assert aa.load_recipients(aa.SAMPLE / "recipients.csv")["Service manager"].endswith("@summitmech.example>")


def answer(**changes):
    a = {"what_happened": "Parts were not billed.", "likely_cause": "x", "action": "y", "evidence": []}
    return json.dumps({**a, **changes})


def fresh(check):
    from dataclasses import replace

    return replace(first(check), status=aa.NOT_INVESTIGATED, explanation=None, problems=[])


def test_a_null_evidence_list_goes_to_a_person_without_stopping_the_run():
    fl = fresh("parts not billed")
    aa.investigate(fl, DATA, ScriptedModel([answer(evidence=None)]))
    assert fl.status == aa.CHECK_FAILED and fl.problems == ["cites no records"]


def test_an_answer_with_wrong_types_or_missing_fields_goes_to_a_person():
    fl = fresh("parts not billed")
    for bad in (
        answer(action={"step": "call"}, evidence=[f"WO{fl.subject}"]),
        answer(evidence=f"WO{fl.subject}"),
        answer(evidence=[123]),
        json.dumps({"what_happened": "Parts were not billed.", "evidence": [f"WO{fl.subject}"]}),
        "[]",
    ):
        fl.status, fl.problems = aa.NOT_INVESTIGATED, []
        aa.investigate(fl, DATA, ScriptedModel([bad]))
        assert fl.status == aa.CHECK_FAILED and fl.problems[0].startswith("couldn't get an explanation"), bad


def test_every_recorded_answer_is_well_formed():
    answers = json.loads((aa.SAMPLE / "recorded-run.json").read_text())["answers"]
    for text in answers.values():
        aa.valid_answer(aa.parse_json(text))
