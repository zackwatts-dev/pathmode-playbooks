import json
from pathlib import Path

import applicant_screening as aps

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(aps.__file__).parent / "sample-data"
REQ = (SAMPLE / "requirements.md").read_text()
MUST, NICE = aps.requirements(REQ)


def app(name):
    return (SAMPLE / "applications" / name).read_text()


def test_requirements_are_parsed():
    assert len(MUST) == 4 and len(NICE) == 3
    assert MUST[0].startswith("EPA Section 608")


def test_redaction_removes_identity_and_education_years_but_keeps_work_history():
    text = aps.redact(app("c-okafor.txt"))
    assert "Chris Okafor" not in text and "chris.okafor@" not in text and "480-555-0190" not in text
    assert "1998" not in text and "[year removed]" in text
    assert "2017 to present" in text  # work dates are needed to judge experience
    assert "1420 W Elliot Rd" not in aps.redact(app("a-garcia.txt"))


def test_met_without_real_evidence_becomes_unclear():
    answer = [{"requirement": r, "status": "met", "evidence": "10 years at Carrier", "ask": ""} for r in MUST + NICE]
    r = aps.check("x.txt", app("b-nguyen.txt"), MUST, NICE, ScriptedModel([json.dumps(answer)]))
    assert all(c["status"] == "unclear" for c in r.checks)
    assert all("isn't in the application" in c["note"] for c in r.checks)


def test_injection_is_flagged_and_does_not_help():
    r = aps.check("d-patel.txt", app("d-patel.txt"), MUST, NICE, OfflineModel(aps.offline))
    assert any("instructions aimed at an AI" in f for f in r.flags)
    assert not any(c["status"] == "met" for c in r.checks if c["must"])


def test_personal_traits_in_the_answer_are_flagged():
    answer = [{"requirement": MUST[0], "status": "unclear", "evidence": "", "ask": "Is the applicant too young?"}]
    r = aps.check("x.txt", app("e-thompson.txt"), MUST, NICE, ScriptedModel([json.dumps(answer)]))
    assert any("personal trait" in f for f in r.flags)


def test_missing_answers_default_to_unclear():
    r = aps.check("x.txt", app("e-thompson.txt"), MUST, NICE, ScriptedModel(["[]"]))
    assert [c["status"] for c in r.checks] == ["unclear"] * 7


def test_dry_run_lists_by_file_name_with_no_ranking(tmp_path):
    results, _ = aps.run(REQ, list((SAMPLE / "applications").glob("*.txt")), OfflineModel(aps.offline), tmp_path)
    assert [r.file for r in results] == sorted(r.file for r in results)
    md = (tmp_path / "checklists.md").read_text()
    assert "Not a ranking" in md
    garcia = next(r for r in results if r.file == "a-garcia.txt")
    assert [c["status"] for c in garcia.checks if c["must"]] == ["met"] * 4
