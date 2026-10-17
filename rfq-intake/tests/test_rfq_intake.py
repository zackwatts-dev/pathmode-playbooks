import json
import urllib.error
import urllib.parse
from email.message import EmailMessage
from pathlib import Path

import graph_mailbox as gm
import pytest
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


def customer_sites(k):
    return RECORDS.customers[k["customer_id"]].sites


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
    # Needs a customer with more than one site, so there's a wrong site to send the request to.
    mail = next(
        (MAILS[f] for f, k in KEY.items() if k["kind"] == "replace, only unit" and len(customer_sites(k)) > 1), None
    )
    if mail is None:
        pytest.skip("no 'replace, only unit' email in the sample is from a customer with more than one site")
    k = KEY[mail.file]
    other = next(s for s in customer_sites(k) if s.id != k["site_ids"])
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
    assert "receivedDateTime+ge+2025-09-02T16" in calls[0][1]


def test_the_recorded_run_replays_and_the_two_gaps_it_found_stay_closed(tmp_path):
    # A real model's answers, recorded. Its first pass let two requests through that it shouldn't have:
    # "a new split system for Vail Commons" (the model called it 'unclear', so no unit was matched) and
    # "some new equipment" (nothing to quote). Both were gaps in the checks; these keep them closed.
    mails = list(MAILS.values())
    model = rq.Replay(SAMPLE / "recorded-run.json", mails)
    results, _ = rq.run(mails, RECORDS, model, tmp_path, rq.SAMPLE_AS_OF, answer_key=SAMPLE / "answer-key.csv")
    # These answers were recorded before the instructions asked for each serial and model to be in its quote.
    # Six of them put the serial or model in the next sentence instead, so those six now go to a person:
    # stopped, not let through. Nothing is let through wrong.
    groups = rq.score(results, SAMPLE / "answer-key.csv")["groups"]
    assert len(groups["right"]) == 74 and not groups["let through, wrong"] and not groups["wrong pile"]
    stopped = {f.split(":")[0] for f in groups["stopped, needn't have been"]}
    by = {r.mail.file: r for r in results}
    assert len(stopped) == 6 and all(any("isn't in the words quoted" in x for x in by[f].reasons) for f in stopped)
    vail = next(f for f in by if "Vail Commons" in MAILS[f].text and KEY[f]["kind"] == "replace, only unit")
    assert by[vail].lines[0].unit is not None
    vague = next(f for f in by if "some new equipment" in MAILS[f].text)
    assert by[vague].status == rq.INFO


def test_a_flood_of_email_is_capped_and_kept_and_every_run_is_logged(tmp_path):
    mails = list(MAILS.values())
    results, _ = rq.run(mails, RECORDS, OfflineModel(rq.offline), tmp_path, rq.SAMPLE_AS_OF, max_emails=10)
    over = [r for r in results if r.status == rq.FAILED]
    assert len(results) == 80 and len(over) == 70 and "limit of 10" in over[0].reasons[0]
    rq.run(mails[:5], RECORDS, OfflineModel(rq.offline), tmp_path, rq.SAMPLE_AS_OF)
    log = read_csv(tmp_path / "runs.csv")
    assert [row["emails"] for row in log] == ["80", "5"]


def test_on_a_schedule_each_email_is_read_by_the_ai_once(tmp_path):
    mails = list(MAILS.values())[:10]
    first = OfflineModel(rq.offline)
    rq.run(mails, RECORDS, first, tmp_path, rq.SAMPLE_AS_OF, remember=True)
    assert len(first.calls) == 10
    again = OfflineModel(rq.offline)
    results, _ = rq.run(list(MAILS.values())[:12], RECORDS, again, tmp_path, rq.SAMPLE_AS_OF, remember=True)
    assert len(again.calls) == 2 and len(results) == 12  # only the two new emails cost anything


# --- the model's answer is checked for shape before it's kept or used ----------------------------------------


def offline_answer(mail, **changes):
    a = json.loads(rq.offline("", rq.prompt(mail)))
    return {**a, **changes}


def test_null_lists_in_an_answer_become_empty_before_the_answer_is_kept(tmp_path):
    mail = first("replace, unit named")
    fake = json.dumps({"kind": "new request", "customer": None, "sites": None, "units": None, "quote_due": None})
    results, _ = rq.run([mail], RECORDS, ScriptedModel([fake]), tmp_path, rq.SAMPLE_AS_OF, remember=True)
    assert results[0].status in (rq.INFO, rq.REVIEW)
    kept = json.loads((tmp_path / "answers" / f"{mail.file}.json").read_text())
    assert kept["sites"] == [] and kept["units"] == [] and kept["customer"] == ""


def test_a_malformed_answer_goes_to_a_person_and_isnt_kept(tmp_path):
    mail = first("replace, unit named")
    for bad in (
        {"kind": "new request", "units": "two rooftop units"},
        {"kind": "new request", "units": [{"what": "RTU", "quantity": "a couple", "quote": "the RTU"}]},
        {"kind": "new request", "sites": [{"name": ["Main St"], "quote": "Main St"}]},
        {"kind": None},
    ):
        results, _ = rq.run([mail], RECORDS, ScriptedModel([json.dumps(bad)]), tmp_path, rq.SAMPLE_AS_OF, remember=True)
        assert results[0].status == rq.FAILED and "couldn't process" in results[0].reasons[0]
        assert not (tmp_path / "answers" / f"{mail.file}.json").exists()


def test_a_damaged_kept_answer_is_read_again_instead_of_crashing_every_run(tmp_path):
    mail = first("replace, unit named")
    kept = tmp_path / "answers" / f"{mail.file}.json"
    kept.parent.mkdir(parents=True)
    kept.write_text(json.dumps({"kind": "new request", "sites": None, "units": [{"quantity": {"n": 1}}]}))
    model = OfflineModel(rq.offline)
    results, _ = rq.run([mail], RECORDS, model, tmp_path, rq.SAMPLE_AS_OF, remember=True)
    assert len(model.calls) == 1 and results[0].status == rq.READY
    assert rq.checked(json.loads(kept.read_text()))  # replaced by a good answer


# --- reading email: HTML bodies, signature images, nothing to read --------------------------------------------


def eml(tmp_path, name="m.eml", text=None, html=None, attach=()):
    msg = EmailMessage()
    msg["From"], msg["Subject"], msg["Date"] = "Pat <pat@example.com>", "Quote", "Tue, 02 Sep 2025 10:00:00 -0700"
    if text is not None:
        msg.set_content(text)
    if html is not None:
        msg.add_alternative(html, subtype="html") if text is not None else msg.set_content(html, subtype="html")
    for filename, maintype, subtype, size, cid in attach:
        msg.add_attachment(b"x" * size, maintype=maintype, subtype=subtype, filename=filename)
        if cid:
            part = msg.get_payload()[-1]
            part.replace_header("Content-Disposition", f'inline; filename="{filename}"')
            part["Content-ID"] = "<image001@example.com>"
    path = tmp_path / name
    path.write_bytes(bytes(msg))
    return path


def test_an_html_only_email_reaches_the_model_with_its_words(tmp_path):
    html = (
        "<html><head><style>p{color:red}</style></head><body><p>Please quote replacing the RTU</p>"
        "<p>at Main&nbsp;St.<br>Thanks</p><script>alert(1)</script></body></html>"
    )
    mail = rq.read_mail(eml(tmp_path, html=html))
    assert "Please quote replacing the RTU\n" in mail.text and "at Main St." in mail.text
    assert "color" not in mail.text and "alert" not in mail.text and "<p>" not in mail.text
    both = rq.read_mail(eml(tmp_path, "both.eml", text="Plain words.", html="<p>HTML words</p>"))
    assert both.text == "Plain words."  # the plain-text copy wins when there is one


def test_an_email_with_nothing_readable_goes_to_a_person_not_to_not_a_quote_request(tmp_path):
    for mail in (
        rq.read_mail(eml(tmp_path, "empty.eml", html="<html><body><img src='cid:x'></body></html>")),
        rq.read_mail(eml(tmp_path, "pdf.eml", text="", attach=[("RFQ.pdf", "application", "pdf", 500, False)])),
    ):
        model = ScriptedModel([json.dumps({"kind": "other"})])
        r = rq.process(mail, model, RECORDS)
        assert r.status == rq.REVIEW and "no text we could read" in r.reasons[0] and not model.calls


def test_signature_images_dont_send_an_email_to_review(tmp_path):
    small, inline = ("image001.png", "image", "png", 4_000, False), ("logo.png", "image", "png", 300_000, True)
    mail = rq.read_mail(eml(tmp_path, text="Please quote the RTU.", attach=[small, inline]))
    assert mail.unread == [] and "image001" not in mail.text
    photo, pdf = ("nameplate.jpg", "image", "jpeg", 300_000, False), ("M-001.pdf", "application", "pdf", 4_000, False)
    mail = rq.read_mail(eml(tmp_path, "b.eml", text="Please quote the RTU.", attach=[small, photo, pdf]))
    assert mail.unread == ["nameplate.jpg", "M-001.pdf"]


# --- every value the model pulled out must be in the words it quoted for it -------------------------------------


def test_a_model_number_not_in_its_quote_goes_to_a_person():
    mail = first("replace, unit named")
    a = offline_answer(mail)
    assert rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS).status == rq.READY
    a["units"][0]["quote"] = "replacing the Copeland walk-in"
    r = rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS)
    assert r.status == rq.REVIEW and any("model COWA94C isn't in the words quoted" in x for x in r.reasons)


def test_a_serial_not_in_its_quote_goes_to_a_person():
    with_serial = (
        m
        for f, m in MAILS.items()
        if KEY[f]["kind"] == "replace, unit named" and KEY[f]["expected_status"] == rq.READY and "serial" in m.text
    )
    mail = next(m for m in with_serial if offline_answer(m)["units"][0]["serial"])
    a = offline_answer(mail)
    serial = a["units"][0]["serial"]
    assert rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS).status == rq.READY
    a["units"][0]["quote"] = a["units"][0]["quote"].split(serial)[0].rsplit("?", 1)[0]
    r = rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS)
    assert r.status == rq.REVIEW and any(f"serial {serial} isn't in the words quoted" in x for x in r.reasons)


def test_a_quantity_not_in_its_quote_goes_to_a_person():
    mail = first("replace, unit named")
    a = offline_answer(mail)
    a["units"][0]["quantity"] = 3
    r = rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS)
    assert r.status == rq.REVIEW and any("quantity 3 isn't in the words quoted" in x for x in r.reasons)
    assert rq.quantity_in_quote(2, "two 4-ton split systems") and rq.quantity_in_quote(4, "RTU-1,Rooftop,7.5,4")
    assert rq.quantity_in_quote(1, "a new mini split") and not rq.quantity_in_quote(2, "a couple of units")


def test_a_deadline_with_no_words_behind_it_goes_to_a_person():
    mail = first("replace, unit named")
    r = rq.process(mail, ScriptedModel([json.dumps(offline_answer(mail, due_quote=""))]), RECORDS)
    assert r.status == rq.REVIEW and r.quote_due is None
    assert any("no words from the email to back it" in x for x in r.reasons)


def test_a_one_word_quote_isnt_evidence():
    mail = first("replace, unit named")
    a = offline_answer(mail)
    a["units"][0] |= {"quote": "walk-in", "model": ""}
    r = rq.process(mail, ScriptedModel([json.dumps(a)]), RECORDS)
    assert r.status == rq.REVIEW and any("aren't in the email" in x for x in r.reasons)


# --- graph_mailbox: same-second messages, throttling -------------------------------------------------------------


def graph(pages, calls, fail=None):
    def fetch(req):
        calls.append(req.full_url)
        if fail and fail(req):
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {"Retry-After": "7"}, None)
        if req.full_url.endswith("/$value"):
            return b"From: a@b.example\nSubject: x\n\nhello\n"
        page = pages.pop(0) if pages else []
        # Apply the time filter the way Graph does, so a wrong filter shows up as a skipped message.
        query = urllib.parse.parse_qs(urllib.parse.urlparse(req.full_url).query).get("$filter", [""])[0].split()
        if query:
            op, since = query[1], query[2]
            page = [m for m in page if m["receivedDateTime"] > since or (op == "ge" and m["receivedDateTime"] == since)]
        return json.dumps({"value": page}).encode()

    return fetch


def test_graph_mailbox_doesnt_skip_or_repeat_two_messages_in_the_same_second(tmp_path):
    same = "2025-09-02T16:00:00Z"
    calls = []
    first_run = [[{"id": "AAA11111", "receivedDateTime": same, "subject": "one"}]]
    assert len(gm.save("q@x.example", "t", tmp_path, graph(first_run, calls))) == 1
    # The second message arrived in the same second, after the first run listed the inbox.
    both = [
        [
            {"id": "AAA11111", "receivedDateTime": same, "subject": "one"},
            {"id": "BBB22222", "receivedDateTime": same, "subject": "two"},
        ]
    ]
    saved = gm.save("q@x.example", "t", tmp_path, graph(both, calls))
    assert [p.name.split("-")[-1] for p in saved] == ["BBB22222.eml"]
    assert "receivedDateTime+ge+" in calls[-2]


def test_graph_mailbox_waits_as_asked_when_throttled_then_gives_up(tmp_path):
    calls, waits = [], []
    tries = {"n": 0}

    def once(req):
        tries["n"] += 1
        return tries["n"] == 1

    pages = [[{"id": "AAA11111", "receivedDateTime": "2025-09-02T16:00:00Z", "subject": "one"}]]
    saved = gm.save("q@x.example", "t", tmp_path / "a", graph(pages, calls, once), sleep=waits.append)
    assert len(saved) == 1 and waits == [7.0]
    waits.clear()
    with pytest.raises(urllib.error.HTTPError):
        gm.save("q@x.example", "t", tmp_path / "b", graph([], [], lambda req: True), sleep=waits.append)
    assert len(waits) == gm.RETRIES - 1 and not (tmp_path / "b" / ".last-fetched").exists()


def test_dates_are_written_without_format_codes_windows_lacks():
    # strftime's "%-d" (day without a leading zero) is glibc-only: it fails on Windows.
    for f in ("rfq_intake.py", "dashboard.py"):
        assert "%-" not in (Path(rq.__file__).parent / f).read_text()
    assert rq.long_date(rq.SAMPLE_AS_OF) == "October 1, 2025"
