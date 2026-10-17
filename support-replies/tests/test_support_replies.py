import json
from pathlib import Path

import support_replies as sr

from common.fake import OfflineModel, ScriptedModel

SAMPLE = Path(sr.__file__).parent / "sample-data"
SECTIONS = sr.load_docs(SAMPLE / "docs")
SEARCH = sr.Search(SECTIONS)


def test_docs_split_into_sections():
    ids = {s.id for s in SECTIONS}
    assert "warranty#our-labor-warranty" in ids and "billing#how-to-pay" in ids


def test_search_finds_the_right_section():
    assert SEARCH.top("same repair failed again within 90 days")[0][1].id == "warranty#our-labor-warranty"
    assert SEARCH.top("Does the service agreement cover parts?")[0][1].id.startswith("service-agreements")


def test_nothing_close_means_no_model_call():
    model = ScriptedModel([])
    r = sr.answer_one("Do you install solar panels?", SEARCH, model, "Summit", 2.0)
    assert not r.covered and not model.calls


def test_citations_must_be_real_and_present():
    q = "How do I pay my invoice?"
    fake = ScriptedModel([json.dumps({"covered": True, "answer": "By card.", "citations": ["made-up#x"]})])
    r = sr.answer_one(q, SEARCH, fake, "Summit", 0.5)
    assert not r.covered
    assert any("weren't given" in f for f in r.flags) and any("without citing" in f for f in r.flags)


def test_numbers_must_come_from_the_cited_section():
    q = "How long is the labor warranty?"
    fake = ScriptedModel(
        [
            json.dumps(
                {
                    "covered": True,
                    "answer": "Our labor warranty is 180 days.",
                    "citations": ["warranty#our-labor-warranty"],
                }
            )
        ]
    )
    r = sr.answer_one(q, SEARCH, fake, "Summit", 0.5)
    assert any("180" in f for f in r.flags)


def test_sample_dry_run(tmp_path):
    questions = (SAMPLE / "questions.txt").read_text().splitlines()
    replies, _ = sr.run(questions, SECTIONS, OfflineModel(sr.offline), tmp_path, "Summit", 2.0)
    by_q = {r.question[:20]: r for r in replies}
    assert not by_q["Do you install solar"].covered
    assert "Not covered" in (tmp_path / "answers.md").read_text()
