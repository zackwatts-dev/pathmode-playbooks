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


def test_today_the_question_goes_out_only_when_the_request_is_opened():
    """Two hours of work ahead of it at an hour a day: today the gap is found on Wednesday, when it's opened, and the
    answer comes two working days later. Asked on arrival, the answer is back before the estimator gets to it."""
    ahead = req("ahead", 2.0)
    gap = req("gap", 0.5, missing="drawing", answer_days=2)
    cap = capacity(10, 1.0)
    today = rq.replay([ahead, gap], cap, "today")
    ask = rq.replay([ahead, gap], cap, "ask")
    assert today.asked["gap"] == MON + timedelta(days=2)  # opened on Wednesday, after "ahead" is done
    assert ask.asked["gap"] == MON
    assert ask.sent["gap"] < today.sent["gap"]


def test_a_request_with_nothing_missing_is_never_asked_about():
    out = rq.replay([req("ok", 0.5)], capacity(3, 1.0), "today")
    assert out.asked == {} and out.sent["ok"] == MON


def test_with_intake_a_request_waiting_on_its_answer_is_passed_over_not_blocking():
    gap = req("gap", 0.5, missing="quantity", answer_days=3)
    ready = req("ready", 0.5)
    out = rq.replay([gap, ready], capacity(10, 1.0), "ask")
    assert out.sent["ready"] == MON and out.sent["gap"] == MON + timedelta(days=3)


def test_new_requests_come_before_re_quotes_in_every_way_of_working():
    rq_ = req("requote", 1.0, kind="requote")
    new = req("new", 1.0, received=MON)
    for p in rq.POLICIES:
        out = rq.replay([rq_, new], capacity(5, 1.0), p)
        assert out.sent["new"] == MON and out.requote_sent["requote"] > MON


def test_intake_saves_the_retyping_and_nothing_else_does():
    reqs = [req(f"r{i}", 0.5) for i in range(6)]
    cap = capacity(5, 1.0)
    today = rq.replay(reqs, cap, "today", typing_minutes=10)
    intake = rq.replay(reqs, cap, "intake", typing_minutes=10)
    assert max(intake.sent.values()) < max(today.sent.values())


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
