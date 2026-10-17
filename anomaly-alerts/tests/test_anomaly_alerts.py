import json
import re
import shutil
from collections import defaultdict
from datetime import date
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
    flagged, real, known, matching = scored["techs"]
    assert flagged >= 5 and real >= flagged * 2 // 3 and matching >= flagged // 2


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
    listed = aa.read_csv(tmp_path / "flags.csv") + aa.read_csv(tmp_path / "flags-service-manager.csv")
    assert len(listed) == len(flags)


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


def test_the_recorded_run_replays_to_the_published_numbers(tmp_path):
    model = aa.Replay(aa.SAMPLE / "recorded-run.json")
    flags, _ = aa.run(DATA, model, tmp_path, aa.SAMPLE_START, aa.SAMPLE_END, answer_key=KEY)
    top = aa.within_budget(flags, 12)
    assert all(fl.status != aa.NOT_INVESTIGATED for fl in top) and model.misses == 0
    assert (tmp_path / "alerts" / "controller.eml").exists()
    scored = aa.score(flags, top, KEY)
    assert len(flags) == 742
    table = {r["problem"]: (r["real"], r["caught"], r["flags"], r["flags that were real"]) for r in scored["rows"]}
    assert table == {
        "unbilled parts": (244, 215, 215, 215),
        "written down to NTE": (223, 223, 223, 223),
        "NTE increase not recorded": (59, 59, 59, 59),
        "hours not logged": (237, 237, 237, 237),
    }
    assert scored["techs"] == (8, 6, 39, 4)  # flagged, with a known habit, of all known, flagged for that habit
    assert scored["top"] == (24, 24)
    assert "$8,303.18" in scored["md"] and "1,195 jobs" in scored["md"]
    failed = {fl.id: fl.problems for fl in top if fl.status == aa.CHECK_FAILED}
    assert sum(fl.status == aa.EXPLAINED for fl in top) == 20
    # Three work out a number of days themselves; one names a technician on the controller's flag.
    # Each of the four worked out a number of days (or hours) itself, which isn't in the records.
    assert sorted(failed) == ["F-hours-295904", "F-parts-297291", "F-parts-300553", "F-parts-300637"]
    assert all(len(p) == 1 and p[0].startswith("uses numbers not in the records") for p in failed.values())


def test_the_dashboard_escapes_what_it_shows(tmp_path):
    fl = fresh("hours not logged")
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


# --- what the explanation check must catch, and what each owner may see ---------------------------------------

RECORDED = json.loads((aa.SAMPLE / "recorded-run.json").read_text())


class Recorded(aa.Replay):
    """The recorded run, with some flags' answers replaced."""

    def __init__(self, **override):
        super().__init__(aa.SAMPLE / "recorded-run.json")
        self.answers = {**self.answers, **{k.replace("_", "-"): v for k, v in override.items()}}


ACCUSATION = {
    "what_happened": "Technician Sean Thomas (T1) took the compressor home and resold it… loss $234,960 on INV-234960.",
    "likely_cause": "Theft.",
    "action": "Fire Sean Thomas today, refund $5k.",
    "evidence": ["WO297291", "INV-234960"],
}


def outputs(folder: Path, owner: str) -> str:
    suffix = aa.OWNER_SUFFIX[owner]
    names = [f"dashboard{suffix}.html", f"flags{suffix}.csv", f"review-queue{suffix}.csv"]
    names.append(f"alerts/{owner.lower().replace(' ', '-')}.eml")
    return "\n".join((folder / n).read_text() for n in names)


def test_a_made_up_accusation_goes_to_a_person_and_reaches_no_one(tmp_path):
    model = Recorded(F_parts_297291=json.dumps(ACCUSATION))
    flags, _ = aa.run(DATA, model, tmp_path, *SEPT, answer_key=KEY)
    fl = next(x for x in flags if x.id == "F-parts-297291")
    assert fl.status == aa.CHECK_FAILED
    problems = " | ".join(fl.problems)
    for why in ("mentions a technician", "names a person", "accuses or disciplines", "234,960", "5k"):
        assert why in problems, why
    for owner in aa.OWNER_SUFFIX:
        text = outputs(tmp_path, owner)
        assert "Sean Thomas" not in text and "resold" not in text and "Fire " not in text


def test_numbers_in_the_prose_must_be_amounts_not_the_digits_of_an_id_or_a_date():
    fl = fresh("parts not billed")
    for bad, token in (
        ("The write-off is $234,960.", "234,960"),  # INV-234960's digits
        ("We lost $5k.", "5k"),
        ("About 2,025 dollars.", "2,025"),  # a date's year
    ):
        text = answer(what_happened=bad, evidence=[aa.job_label(fl.subject)]).replace("INV", "INV")
        fl.problems, fl.status = [], aa.NOT_INVESTIGATED
        aa.investigate(fl, DATA, ScriptedModel([text]))
        assert fl.status == aa.CHECK_FAILED and token in " ".join(fl.problems), bad


def test_an_id_mentioned_in_the_prose_must_be_in_the_records():
    fl = fresh("parts not billed")
    aa.investigate(
        fl,
        DATA,
        ScriptedModel([answer(what_happened="Same as WO999999 and INV-1.", evidence=[aa.job_label(fl.subject)])]),
    )
    assert fl.status == aa.CHECK_FAILED and "WO999999" in " ".join(fl.problems)


def test_records_mentioned_by_number_and_dates_are_not_amounts():
    fl = fresh("hours not logged")
    b = aa.bundle(DATA, fl)
    tech = sorted(aa.record_ids(b)["tech"])[0]
    visit = sorted(aa.record_ids(b)["visit"])[0]
    done = DATA.jobs[fl.subject]["Completed"]
    text = f"On September 19, 2025 ({done}), {visit} by techs {tech} and {tech}: job {fl.subject}."
    aa.investigate(fl, DATA, ScriptedModel([answer(what_happened=text, evidence=[aa.job_label(fl.subject)])]))
    assert fl.status == aa.EXPLAINED, fl.problems


def test_a_name_or_a_disciplinary_step_goes_to_a_person_even_on_a_technician_flag():
    fl = fresh("unusual technician pattern")
    cite = [f"T{fl.subject[1:]}"]
    for text, why in (
        ("Talk to Maria Delgado about it.", "names a person"),
        (f"Discipline {fl.subject} for this.", "accuses or disciplines"),
        (f"Write him up: {fl.subject} has been stealing parts.", "accuses or disciplines"),
    ):
        fl.problems, fl.status = [], aa.NOT_INVESTIGATED
        aa.investigate(fl, DATA, ScriptedModel([answer(what_happened=text, evidence=cite)]))
        assert fl.status == aa.CHECK_FAILED and any(why in p for p in fl.problems), text
    fl.problems, fl.status = [], aa.NOT_INVESTIGATED
    aa.investigate(fl, DATA, ScriptedModel([answer(what_happened="Check the fire alarm panel job.", evidence=cite)]))
    assert fl.status == aa.EXPLAINED, fl.problems


def test_the_controllers_records_carry_no_technician_ids():
    b = aa.bundle(DATA, fresh("parts not billed"))
    assert not aa.record_ids(b)["tech"] and '"Tech ID"' not in json.dumps(b)
    assert aa.record_ids(aa.bundle(DATA, fresh("hours not logged")))["tech"]


TECH_REF = re.compile(r"\bT\d+\b|\btech(?:nician)?s?\s*(?:ID\s*)?\d+", re.IGNORECASE)


def test_each_owner_sees_only_their_own_flags_and_the_shared_files_hold_no_technicians(tmp_path):
    flags, _ = aa.run(DATA, aa.Replay(aa.SAMPLE / "recorded-run.json"), tmp_path, *SEPT, answer_key=KEY)
    names = [t["Name"] for t in DATA.techs.values()]
    controller = outputs(tmp_path, "Controller")
    shared = (tmp_path / "summary.md").read_text()
    for text in (controller, shared):
        assert not TECH_REF.search(text), TECH_REF.search(text).group()
        assert not [n for n in names if n in text]
        assert "hours not logged, " not in text and "unusual technician pattern" not in text
    assert {r["owner"] for r in aa.read_csv(tmp_path / "flags.csv")} == {"Controller"}
    sm = aa.read_csv(tmp_path / "flags-service-manager.csv")
    assert {r["owner"] for r in sm} == {"Service manager"} and any(r["subject"].startswith("T") for r in sm)
    assert "unusual technician pattern" in (tmp_path / "summary-service-manager.md").read_text()


def test_the_hours_detail_says_what_the_invoice_did_for_each_job():
    hours = [fl for fl in FLAGS if fl.check == "hours not logged"]
    uninvoiced = [fl for fl in hours if not DATA.invoices.get(fl.subject)]
    assert len(uninvoiced) == 50 and all(fl.detail.endswith("not invoiced yet") for fl in uninvoiced)
    assert not [fl for fl in hours if "default" in fl.detail]
    for fl in hours:
        if DATA.invoices.get(fl.subject):
            labor = sum(float(ln["Qty"]) for ln in DATA.job_lines(fl.subject) if ln["Type"] == "labor")
            assert fl.detail.endswith(f"bills {labor:g} h of labor" if labor else "has no labor line"), fl.detail


def test_a_weekly_run_with_a_look_back_lets_no_job_fall_between_windows(tmp_path):
    weeks = [date(2025, 9, d) for d in (7, 14, 21, 28)]
    history, reported, without = tmp_path / "history.csv", {}, set()
    for end in weeks:
        seen_by = DATA.as_of(date.fromordinal(end.toordinal() + 1))  # the export is cut the next morning
        start = date.fromordinal(end.toordinal() - 6)
        flags, _ = aa.run(seen_by, OfflineModel(aa.offline), tmp_path / "out", start, end, lookback=45, history=history)
        new = [fl.id for fl in flags if aa.is_new(fl, end)]
        assert not set(new) & set(reported), "a flag was reported as new twice"
        reported.update(dict.fromkeys(new, end))
        without |= {fl.id for fl in aa.detect(seen_by, start, end) if fl.check == "parts not billed"}
    last = DATA.as_of(date(2025, 9, 29))
    once = {fl.id for fl in aa.detect(last, date(2025, 8, 15), date(2025, 9, 28)) if fl.check == "parts not billed"}
    assert len(once) > 150 and once <= set(reported)  # every unbilled part the exports could show was reported
    assert len(without) < len(once) // 3  # a week-only window checks most jobs before they're invoiced


def test_technician_habits_are_measured_over_a_window_ending_on_the_runs_end_date():
    aug = {fl.subject for fl in aa.tech_model(DATA, until=date(2025, 8, 31))}
    sep = {fl.subject for fl in aa.tech_model(DATA, until=date(2025, 9, 30))}
    assert aug and sep and aug != sep
    _, _, counts = aa.tech_features(DATA, date(2025, 8, 1), date(2025, 8, 31))
    august = defaultdict(int)
    for vs in DATA.visits.values():
        for v in vs:
            august[v["Tech ID"]] += "2025-08-01" <= v["Date"] <= "2025-08-31"
    assert counts and all(c["visits"] == august[t] for t, c in counts.items())


def test_paperwork_lag_is_reported_as_invisible_when_entries_carry_the_visit_date(tmp_path):
    assert not aa.lag_visible(DATA)
    aa.run(DATA, OfflineModel(aa.offline), tmp_path, *SEPT, budget=0)
    assert "Paperwork lag can't be seen" in (tmp_path / "summary-service-manager.md").read_text()
    data = branch(ordinary(5), visits=3)
    entry = next(iter(data.hours.values()))[0]
    entry["Date"] = "2025-09-09"
    assert aa.lag_visible(data)


def test_the_investigated_count_needs_the_answer_keys_problem_not_just_any():
    key = {r["WO"]: r for r in aa.read_csv(KEY)}
    wo = next(w for w, r in key.items() if r["Problems"] == "hours not logged")
    wrong = aa.Flag("F-x", "NTE increase not recorded", "rule", wo, "x")
    right = aa.Flag("F-y", "hours not logged", "rule", wo, "x")
    assert aa.score([wrong, right], [wrong, right], KEY)["top"] == (2, 1)
    md = aa.score(FLAGS, [], KEY)["md"]
    assert "same definition as the rule; this checks the plumbing" in md
    assert "Not checked by this playbook:** 1,195 jobs with callback" in md


def sample_copy(tmp_path: Path) -> Path:
    return Path(shutil.copytree(aa.SAMPLE, tmp_path / "exports"))


def rewrite(path: Path, change):
    rows = aa.read_csv(path)
    rows = change(rows)
    aa.write_csv(path, rows, list(rows[0]))


def test_a_duplicated_invoice_or_line_doesnt_double_the_write_down(tmp_path):
    folder = sample_copy(tmp_path)
    fl = first("written down to NTE")
    inv = DATA.invoices[fl.subject][0]["Invoice"]
    rewrite(folder / "invoices.csv", lambda rows: rows + [r for r in rows if r["Invoice"] == inv])
    rewrite(
        folder / "invoice-lines.csv",
        lambda rows: (
            [{**r, "Line ID": str(i)} for i, r in enumerate(rows)]
            + [{**r, "Line ID": str(i)} for i, r in enumerate(rows) if r["Invoice"] == inv]
        ),
    )
    again = aa.Data.load(folder)
    flags = aa.rules(again, [fl.subject])
    assert next(x for x in flags if x.check == "written down to NTE").value == fl.value


def test_job_numbers_with_letters_can_be_cited():
    data = branch(ordinary(5, t2={"unlogged": 1}), visits=3, wo=lambda t, i: f"WO-{t}-{i}A")
    fl = aa.rules(data, sorted(data.jobs, key=aa.id_key))[0]
    assert fl.subject == "WO-2-0A"
    text = answer(what_happened="WO-2-0A had a visit, V2000, with no hours.", evidence=["WO-2-0A", "v2000"])
    aa.investigate(fl, data, ScriptedModel([text]))
    assert fl.status == aa.EXPLAINED, fl.problems
    aa.investigate(fl, data, OfflineModel(aa.offline))
    assert fl.status == aa.EXPLAINED, fl.problems


def test_dates_and_hours_in_other_formats_are_read_or_listed_for_a_person(tmp_path):
    assert aa.parse_date("9/5/2025") == aa.parse_date("2025-09-05T14:30:00") == "2025-09-05"
    assert aa.parse_date("9/5/25") == "2025-09-05" and aa.parse_date("") == "" and aa.parse_date("Sept 5th") is None
    assert aa.parse_hours("1:30") == "1.5" and aa.parse_hours("2.25") == "2.25" and aa.parse_hours("lots") is None
    folder = sample_copy(tmp_path)
    jobs = aa.read_csv(folder / "jobs.csv")
    a, b, c = [w for w in sorted(DATA.jobs) if DATA.jobs[w]["Completed"].startswith("2025-09")][:3]

    def change(rows):
        for r in rows:
            if r["WO"] == a:
                r["Completed"] = "9/5/2025"
            if r["WO"] == b:
                r["Completed"] = r["Completed"] + "T16:45:00"
            if r["WO"] == c:
                r["Completed"] = "Sept 5th"
        return rows

    rewrite(folder / "jobs.csv", change)
    rewrite(
        folder / "time-entries.csv", lambda rows: [{**r, "Hours": "1:30"} if i == 0 else r for i, r in enumerate(rows)]
    )
    data = aa.Data.load(folder)
    assert data.jobs[a]["Completed"] == "2025-09-05" and data.jobs[b]["Completed"] == DATA.jobs[b]["Completed"]
    assert data.unreadable == [{"file": "jobs.csv", "row": c, "column": "Completed", "value": "Sept 5th"}]
    flags, _ = aa.run(data, OfflineModel(aa.offline), tmp_path / "out", *SEPT, budget=1)
    assert flags and "1 values couldn't be read" in (tmp_path / "out" / "summary.md").read_text()
    assert aa.read_csv(tmp_path / "out" / "unreadable.csv")[0]["row"] == c
    assert len(jobs) == len(data.jobs)


def test_a_replay_with_no_answer_for_a_flag_says_so(tmp_path):
    model = aa.Replay(aa.SAMPLE / "recorded-run.json")
    del model.answers["F-parts-297291"]
    flags, _ = aa.run(DATA, model, tmp_path, *SEPT, answer_key=KEY)
    assert model.misses == 1
    for name in ("summary.md", "score.md"):
        assert "1 items had no recorded answer" in (tmp_path / name).read_text()


def test_a_date_after_a_technician_isnt_read_as_another_technician():
    found = [m.group() for m in aa.TECH_MENTION.finditer("Visit V358490 (tech 43, 2025-09-05) has no hours")]
    assert found == ["tech 43"]
    found = [m.group() for m in aa.TECH_MENTION.finditer("techs 201 and 125 both visited")]
    assert found == ["techs 201 and 125"]
