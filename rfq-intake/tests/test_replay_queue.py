import shutil
from datetime import date, timedelta

import replay_queue as rq

MON = date(2030, 5, 6)


def req(id_, hours, missing="", answer_days=0, received=MON, kind="new", tier="regular"):
    return rq.Request(id_, kind, tier, received, 1, False, hours, missing, answer_days)


def capacity(n, per_day):
    out, d = [], MON
    while len(out) < n:
        if d.weekday() < 5:
            out.append(rq.Day(d, per_day))
        d += timedelta(days=1)
    return out


TUE, THU = MON + timedelta(days=1), MON + timedelta(days=3)


def test_today_requests_are_read_on_mondays_and_thursdays_and_the_question_waits_until_opened():
    """Arriving on a Tuesday, today it's read on Thursday and the gap found when it's opened, after two hours of work
    ahead of it at an hour and a half a day. Read every morning, by a person or by AI, it's asked about on Tuesday."""
    ahead = req("ahead", 2.0)
    gap = req("gap", 0.5, missing="drawing", answer_days=2, received=TUE)
    cap = capacity(15, 1.5)
    today = rq.replay([ahead, gap], cap, "today")
    daily = rq.replay([ahead, gap], cap, "daily")
    intake = rq.replay([ahead, gap], cap, "intake")
    assert today.asked["gap"] >= THU
    assert daily.asked["gap"] == TUE and intake.asked["gap"] == TUE
    assert intake.sent["gap"] <= daily.sent["gap"] < today.sent["gap"]


def test_a_request_with_nothing_missing_is_never_asked_about():
    out = rq.replay([req("ok", 0.5)], capacity(3, 1.0), "today")
    assert out.asked == {} and out.sent["ok"] == MON


def test_read_on_arrival_a_request_waiting_on_its_answer_is_passed_over_not_blocking():
    gap = req("gap", 0.5, missing="quantity", answer_days=3)
    ready = req("ready", 0.5)
    out = rq.replay([gap, ready], capacity(10, 2.0), "daily")
    assert out.sent["ready"] == MON and out.sent["gap"] == MON + timedelta(days=3)


def test_new_requests_come_before_re_quotes_in_every_way_of_working():
    rq_ = req("requote", 1.0, kind="requote")
    new = req("new", 1.0, received=MON)
    for p in rq.POLICIES:
        out = rq.replay([rq_, new], capacity(5, 2.0), p)
        assert out.sent["new"] == MON and out.requote_sent["requote"] > MON


def test_keying_costs_the_same_hours_read_daily_or_twice_a_week_and_ai_intake_saves_most_of_it():
    reqs = [req(f"r{i}", 0.5) for i in range(12)]
    cap = capacity(10, 1.0)
    today, daily, intake = (rq.replay(reqs, cap, p, keying_minutes=10) for p in ("today", "daily", "intake"))
    assert max(intake.sent.values()) < max(daily.sent.values()) <= max(today.sent.values())
    none = rq.replay(reqs, cap, "daily", keying_minutes=0)
    assert max(none.sent.values()) <= max(intake.sent.values())  # intake still pays its checks and hand-keyed share


def test_ai_intake_reads_on_a_day_nobody_is_in_but_a_person_sends_the_question_the_next_day_someone_is():
    gap = req("gap", 0.5, missing="revision", answer_days=1)
    cap = [rq.Day(MON, 0.0)] + capacity(6, 1.0)[1:]
    assert rq.replay([gap], cap, "intake").asked["gap"] == TUE
    assert rq.replay([gap], cap, "daily").asked["gap"] == TUE


def test_the_requests_ai_intake_sends_to_a_person_are_read_by_hand_the_next_morning_someone_is_in(monkeypatch):
    monkeypatch.setattr(rq, "TO_A_PERSON", 1.0)  # every request to a person: intake is a person reading daily
    reqs = [req(f"r{i}", 0.5, missing="quantity" if i % 3 == 0 else "", answer_days=2) for i in range(9)]
    cap = [rq.Day(MON, 0.0)] + capacity(10, 1.0)[1:]
    intake, daily = rq.replay(reqs, cap, "intake"), rq.replay(reqs, cap, "daily")
    assert intake.asked == daily.asked and intake.sent == daily.sent


def test_screened_requests_are_keyed_but_never_priced():
    screened = rq.Request("s", "new", "regular", MON, 1, False, 1.0, screened=True)
    out = rq.replay([screened, req("ok", 0.5)], capacity(3, 1.0), "today")
    assert "s" not in out.sent and out.sent["ok"] == MON


def test_the_calibration_matches_the_status_quo_and_the_report_says_it_is_a_model(tmp_path, monkeypatch):
    res = rq.run(rq.DATA, seeds=2)
    assert abs(res["calibration"]["today_model_on_time"] - res["on_time_in_the_records"]) <= max(
        2, 0.02 * res["on_time_in_the_records"]
    )
    text = rq.report(res)
    assert "A model, not a measurement" in text
    for p in rq.POLICIES:
        assert rq.NAMES[p] in text
    x = res["policies"]["intake"]
    assert (
        abs(x["margin_value"] - x["extra_on_time"] * res["win_rate"] * rq.REVENUE_PER_WIN * rq.MARGIN)
        <= 0.01 * abs(x["margin_value"]) + 400
    )
    shutil.copytree(rq.DATA, tmp_path / "w")
    monkeypatch.setattr(
        "sys.argv", ["replay_queue.py", "--data", str(tmp_path / "w"), "--out", str(tmp_path / "o"), "--seeds", "1"]
    )
    rq.main()
    assert (tmp_path / "o" / "replay.md").exists() and (tmp_path / "o" / "replay.json").exists()
