import csv
import shutil
from datetime import date, timedelta

import pytest
import replay_queue as rq

MON = date(2030, 5, 6)


def req(id_, due, hours, lines=1, tier="regular", received=MON, kind="new", weld=False):
    # expected_hours is the work; lines set the tool's own estimate: 0.6 x (1 + 0.3 per extra line)
    return rq.Request(id_, kind, "c", tier, received, due, lines, weld, hours)


def capacity(n, per_day):
    out, d = [], MON
    while len(out) < n:
        if d.weekday() < 5:
            out.append(rq.Day(d, per_day, junior_hours=per_day))
        d += timedelta(days=1)
    return out


def test_the_old_removal_beats_first_come_first_served_and_the_tool_now_only_flags():
    """Three requests: first come, first served gets one quote out on time; the first design's order, with the
    at-risk one taken out, gets two. The tool as decided keeps every request and only flags."""
    tue = MON + timedelta(days=1)
    big = req("big", tue, 2.4, lines=11)  # 0.6 x (1 + 0.3 x 10) = 2.4 h in the tool's forecast too
    urgent = req("urgent", MON, 0.6)
    small = req("small", tue, 0.6)
    reqs, cap = [big, urgent, small], capacity(10, 1.2)
    truth = {r.id: rq.Truth(r.stated_due, "lost", None) for r in reqs}
    a = rq.replay(reqs, cap, "a")
    old = rq.replay(reqs, cap, "b-old", requote_reserve=0.0)  # no re-quotes here, so nothing to hold back
    b = rq.replay(reqs, cap, "b", requote_reserve=0.0)
    assert rq.on_time(a.sent, truth) == 1
    assert rq.on_time(old.sent, truth) == 2 and old.removed == ["big"] and old.sent["big"] is None
    assert b.removed == [] and "big" in b.flagged and all(s is not None for s in b.sent.values())


def test_new_requests_go_ahead_of_re_quotes_in_every_policy_but_wendlows():
    rq_ = req("r", None, 3.0, kind="requote")
    new = req("n", None, 0.5, received=MON + timedelta(days=1))
    cap = capacity(10, 1.0)
    for policy in ("d", "b", "c"):
        assert rq.replay([rq_, new], cap, policy, requote_reserve=0.0).sent["n"] == MON + timedelta(days=1)
    assert rq.replay([rq_, new], cap, "a").sent["n"] > MON + timedelta(days=2)


def test_the_junior_factor_only_on_welded_work_a_junior_prices():
    weld = req("w", None, 1.0, weld=True)
    assert rq.work_hours(weld, 1.0) == pytest.approx(1.3)
    assert rq.work_hours(weld, 1.0, junior=False) == pytest.approx(1.0)
    senior_day = [rq.Day(MON, 10.0, senior=True, junior=False)]
    out = rq.replay([weld], senior_day, "a")
    assert out.sent["w"] == MON


def test_wendlows_rule_declines_occasional_customers_past_three_weeks_and_key_first_is_a_variant():
    filler = [req(f"f{i}", None, 6.0) for i in range(120)]  # unstarted, 1.5 h each: over three weeks of backlog
    late = MON + timedelta(days=1)
    key, occ = req("key", None, 0.5, tier="key", received=late), req("occ", None, 0.5, tier="occasional", received=late)
    fifo = rq.replay([*filler, key, occ], capacity(200, 6.0), "a", helpers=False)
    assert fifo.declined == ["occ"] and fifo.sent["key"] > late + timedelta(days=20)
    first = rq.replay([*filler, key, occ], capacity(200, 6.0), "a", helpers=False, key_first=True)
    assert first.sent["key"] == late


def test_typing_saved_comes_off_new_requests_only():
    new, again = req("n", None, 1.0), req("r", None, 1.0, kind="requote")
    assert rq.work_hours(new, 1.0, 1 / 6) == pytest.approx(1.0 - 1 / 6)
    assert rq.work_hours(again, 1.0, 1 / 6) == pytest.approx(1.0)
    assert rq.work_hours(req("w", None, 1.0, weld=True), 2.0) == pytest.approx(2.0 * 1.3)
    with pytest.raises(ValueError, match="isn't one of"):
        rq.replay([new], capacity(1, 1.0), "z")


def test_the_replay_is_deterministic():
    reqs, truth, cap = rq.load(rq.DATA)
    d = rq.drawn(reqs, 3)
    assert d == rq.drawn(reqs, 3) and d != rq.drawn(reqs, 4)
    assert rq.replay(d, cap, "b").sent == rq.replay(d, cap, "b").sent


def test_the_policies_never_see_the_decision_date(tmp_path):
    """Change every decision date: what each policy does (its order, flags and send dates) doesn't move."""
    shutil.copytree(rq.DATA, tmp_path / "d")
    path = tmp_path / "d" / "rfqs.csv"
    rows = list(csv.DictReader(path.open()))
    for i, r in enumerate(rows):
        if r["decision_date"]:
            moved = date.fromisoformat(r["decision_date"]) + timedelta(days=(i % 7) * 3 - 9)
            r["decision_date"] = moved.isoformat()
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    orig, moved = rq.load(rq.DATA), rq.load(tmp_path / "d")
    assert orig[0] == moved[0]  # the requests the policies get are identical
    for policy in rq.POLICIES:
        x, y = rq.replay(rq.drawn(orig[0], 1), orig[2], policy), rq.replay(rq.drawn(moved[0], 1), moved[2], policy)
        assert (x.sent, x.flagged, x.declined) == (y.sent, y.flagged, y.declined)
    assert "decision" not in rq.Request.__dataclass_fields__


def test_the_calibration_factor_is_fitted_on_wendlows_rule_alone_to_within_two_percent():
    reqs, truth, cap = rq.load(rq.DATA)
    scale, fitted = rq.calibrate(reqs, cap, truth, seeds=4)
    target = rq.actual_on_time(truth, reqs)
    assert target == 199 and abs(fitted - target) <= 0.02 * target and 0.5 < scale < 2


def test_the_win_rate_and_the_value_parameters():
    rate, won, lost = rq.win_rate(rq.all_rows(rq.DATA))
    assert (won, lost) == (61, 121) and rate == pytest.approx(61 / 182)
    assert (rq.REVENUE_PER_WIN, rq.MARGIN, rq.TYPING_MINUTES) == (34_000, 0.27, 10)


def test_the_report_says_it_is_a_model_and_gives_every_policy_with_its_value(tmp_path, monkeypatch):
    res = rq.run(rq.DATA, seeds=3)
    text = rq.report(res)
    assert text.startswith("# Queue replay: a model, not a measurement")
    assert f"**{res['calibration']['factor']:g}**" in text and "Re-quotes' median wait" in text
    for p in rq.POLICIES:
        assert rq.NAMES[p] in text
    b = res["policies"]["b"]
    rate = res["parameters"]["win_rate_on_time"]["rate"]
    expect = b["extra_awarded_on_time_mean"] * rate * 34_000 * 0.27  # per window, "no award" RFQs left out
    assert abs(b["margin_window"] - expect) <= 0.01 * abs(expect) + 100 and "year_factor" not in res
    assert 0 < b["late_made_on_time_share"] <= 1 and b["requote_extra_wait_days"] > 0
    assert b["net_margin_window"] == pytest.approx(b["margin_window"] - b["requote_extra_wait_days"] * 5.31, abs=200)
    assert abs(b["margin_per_month"] - b["margin_window"] / res["months"]) <= 200  # both rounded to $100
    assert "two such windows in the decade's last four years" in text and "no award" in text
    assert res["policies"]["b"]["removed_mean"] == 0 and res["policies"]["b-old"]["removed_mean"] > 0
    # another window through --data: here a copy of the sample, as the 2021 holdout would be
    shutil.copytree(rq.DATA, tmp_path / "w")
    monkeypatch.setattr(
        "sys.argv", ["replay_queue.py", "--data", str(tmp_path / "w"), "--out", str(tmp_path / "o"), "--seeds", "2"]
    )
    rq.main()
    assert (tmp_path / "o" / "replay.md").exists() and (tmp_path / "o" / "replay.json").exists()


def test_no_award_rfqs_count_for_nothing():
    truth = {"x": rq.Truth(MON, "no award", None), "y": rq.Truth(MON, "won", None), "r": rq.Truth(None, "won", None)}
    assert rq.awarded(truth) == {"y"}


def test_the_requote_delay_is_counted_in_working_days():
    r = req("r", None, 1.0, kind="requote")
    out = rq.Outcome({}, requote_sent={"r": MON + timedelta(days=7)})  # Monday to the next Monday
    assert rq.requote_wait_days(out, [r], MON + timedelta(days=30)) == 5
