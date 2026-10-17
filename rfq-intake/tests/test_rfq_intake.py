import json
from pathlib import Path

import graph_mailbox as gm
import rfq_intake as rq
from records import Records

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

SAMPLE = Path(rq.__file__).parent / "sample-data"
RECORDS = Records.load(SAMPLE / "records")
KEY = {row["file"]: row for row in read_csv(SAMPLE / "answer-key.csv")}
MAILS = {m.file: m for m in rq.read_mailbox(SAMPLE / "mailbox")}


def first(kind):
    return next(MAILS[f] for f, k in KEY.items() if k["kind"] == kind)


def answer(**kw):
    base = {"kind": "new request", "customer": "", "request_type": "replace", "sites": [], "units": [], "quote_due": ""}
    return json.dumps({**base, **kw})


def test_the_whole_sample_matches_the_answer_key(tmp_path):
    # The offline stand-in knows the sample's phrasings, so this checks the pipeline and the rules, not a model.
    results, _ = rq.run(
        list(MAILS.values()),
        RECORDS,
        OfflineModel(rq.offline),
        tmp_path,
        rq.SAMPLE_AS_OF,
        answer_key=SAMPLE / "answer-key.csv",
    )
    assert "80 of 80" in (tmp_path / "score.md").read_text()
    assert {r.status for r in results} == {rq.READY, rq.INFO, rq.REVIEW, rq.NOT_RFQ}


def test_a_serial_that_isnt_ours_goes_to_a_person():
    mail = first("serial not in records")
    k = KEY[mail.file]
    real = RECORDS.units[k["equipment_ids"]]
    typo = next(w for w in mail.text.split() if w.rstrip(".").isdigit() and len(w) > 6).rstrip(".")
    r = rq.process(mail, ScriptedModel([answer(units=[{"what": "unit", "serial": typo, "quote": typo}])]), RECORDS)
    assert r.status == rq.REVIEW
    assert any(real.serial in x for x in r.reasons)  # it suggests the right one, but doesn't use it


def test_words_the_email_doesnt_contain_go_to_a_person():
    mail = first("replace, unit named")
    fake = answer(units=[{"what": "rooftop unit", "serial": "", "quote": "replace all four units on the roof"}])
    r = rq.process(mail, ScriptedModel([fake]), RECORDS)
    assert r.status == rq.REVIEW and any("aren't in the email" in x for x in r.reasons)


def test_instructions_aimed_at_the_assistant_stop_it_whatever_the_model_says():
    mail = first("instructions to the assistant")
    r = rq.process(mail, ScriptedModel([json.dumps({"kind": "reply to our quote"})]), RECORDS)
    assert r.status == rq.REVIEW and "assistant" in r.reasons[0]


def test_when_several_units_could_fit_it_asks_instead_of_guessing(tmp_path):
    mail = first("replace, which unit?")
    results, _ = rq.run([mail], RECORDS, OfflineModel(rq.offline), tmp_path, rq.SAMPLE_AS_OF)
    r = results[0]
    assert r.status == rq.INFO and not any(ln.unit for ln in r.lines)
    assert r.questions[0].startswith("Which ")
    draft = next((tmp_path / "questions").glob("*.eml")).read_text()
    assert "nameplate" in draft and mail.sender in draft


def test_an_unusable_answer_is_kept_not_lost():
    r = rq.process(first("replace, unit named"), ScriptedModel(["Sure! Here's what I found..."]), RECORDS)
    assert r.status == rq.FAILED and r.reasons


def test_the_score_catches_a_confident_wrong_match(tmp_path):
    mail = first("replace, only unit")
    k = KEY[mail.file]
    other = (
        next(s for s in RECORDS.customers[k["customer_id"]].sites if s.id != k["site_ids"])
        if len(RECORDS.customers[k["customer_id"]].sites) > 1
        else None
    )
    if other is None:  # the customer has one site: pick a different unit at it instead
        return
    wrong = answer(sites=[{"name": other.name, "address": "", "quote": mail.text.split()[0]}], units=[])
    results, _ = rq.run(
        [mail], RECORDS, ScriptedModel([wrong]), tmp_path, rq.SAMPLE_AS_OF, answer_key=SAMPLE / "answer-key.csv"
    )
    text = (tmp_path / "score.md").read_text()
    assert "0 of 1" in text


def test_the_dashboard_escapes_what_strangers_wrote(tmp_path):
    mail = first("replace, unit named")
    mail.subject = "<script>alert(1)</script>"
    rq.run([mail], RECORDS, ScriptedModel(["not json"]), tmp_path, rq.SAMPLE_AS_OF)
    page = (tmp_path / "dashboard.html").read_text()
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "Needs a person first" in page


def test_graph_mailbox_only_reads_and_remembers_where_it_stopped(tmp_path):
    calls = []
    pages = {
        "first": {
            "value": [{"id": "AAA11111", "receivedDateTime": "2025-09-01T15:00:00Z", "subject": "Quote"}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/next",
        },
        "next": {"value": [{"id": "BBB22222", "receivedDateTime": "2025-09-02T16:00:00Z", "subject": "RFQ"}]},
    }

    def fetch(req):
        calls.append((req.get_method(), req.full_url))
        if req.full_url.endswith("/$value"):
            return b"From: a@b.example\nSubject: x\n\nhello\n"
        return json.dumps(pages["next" if req.full_url.endswith("/next") else "first"]).encode()

    saved = gm.save("quotes@summit.example", "token", tmp_path, fetch)
    assert len(saved) == 2 and all(p.suffix == ".eml" for p in saved)
    assert (tmp_path / ".last-fetched").read_text() == "2025-09-02T16:00:00Z"
    assert {m for m, _ in calls} == {"GET"}
    calls.clear()
    gm.save("quotes@summit.example", "token", tmp_path, fetch)
    assert "receivedDateTime+gt+2025-09-02T16" in calls[0][1]


def test_the_recorded_run_replays_and_the_two_gaps_it_found_stay_closed(tmp_path):
    # A real model's answers, recorded. Its first pass let two requests through that it shouldn't have:
    # "a new split system for Vail Commons" (the model called it 'unclear', so no unit was matched) and
    # "some new equipment" (nothing to quote). Both were gaps in the checks; these keep them closed.
    mails = list(MAILS.values())
    model = rq.Replay(SAMPLE / "recorded-run.json", mails)
    results, _ = rq.run(mails, RECORDS, model, tmp_path, rq.SAMPLE_AS_OF, answer_key=SAMPLE / "answer-key.csv")
    assert "80 of 80" in (tmp_path / "score.md").read_text()
    by = {r.mail.file: r for r in results}
    vail = next(f for f in by if "Vail Commons" in MAILS[f].text and KEY[f]["kind"] == "replace, only unit")
    assert by[vail].lines[0].unit is not None
    vague = next(f for f in by if "some new equipment" in MAILS[f].text)
    assert by[vague].status == rq.INFO
