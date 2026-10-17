from datetime import date
from pathlib import Path

import weekly_report as wr

from common.fake import OfflineModel, ScriptedModel
from common.util import read_csv

SAMPLE = Path(wr.__file__).parent / "sample-data"
ROWS = read_csv(SAMPLE / "jobs.csv")
END = date(2026, 7, 12)

TINY = [
    {
        "Date": "2026-07-06",
        "Branch": "A",
        "Type": "repair",
        "Revenue": "100",
        "Completed": "yes",
        "Callback": "yes",
        "Hours": "1",
    },
    {
        "Date": "2026-07-07",
        "Branch": "A",
        "Type": "repair",
        "Revenue": "300",
        "Completed": "yes",
        "Callback": "no",
        "Hours": "2",
    },
    {
        "Date": "2026-07-08",
        "Branch": "B",
        "Type": "repair",
        "Revenue": "0",
        "Completed": "no",
        "Callback": "no",
        "Hours": "1",
    },
    {
        "Date": "2026-06-30",
        "Branch": "A",
        "Type": "repair",
        "Revenue": "200",
        "Completed": "yes",
        "Callback": "no",
        "Hours": "1",
    },
]


def test_metrics_are_computed_in_code():
    m = wr.compute(TINY, END)
    assert m["revenue"] == 400 and m["revenue_last_week"] == 200 and m["revenue_change_pct"] == 100.0
    assert m["jobs_completed"] == 2 and m["jobs_not_completed"] == 1
    assert m["revenue_per_job"] == 200 and m["callback_rate_pct"] == 50.0
    assert m["revenue_4wk_avg"] == 50.0


def test_a_made_up_number_is_caught():
    m = wr.compute(TINY, END)
    text, bad = wr.report(m, "Revenue doubled to $400, and margins reached 38%.", "scripted")
    assert bad == ["38%"] and "Check the summary" in text


def test_correct_numbers_pass():
    m = wr.compute(TINY, END)
    _, bad = wr.report(m, "Revenue was $400, up 100% on last week's $200, from 2 completed jobs.", "scripted")
    assert bad == []


def test_sample_dry_run(tmp_path):
    text, bad, _ = wr.run(ROWS, END, OfflineModel(wr.offline), tmp_path)
    assert bad == [] and "Weekly report: July 6 to July 12, 2026" in text
    m = wr.compute(ROWS, END)
    assert m["by_branch"]["Mesa"]["revenue_change_pct"] < 0  # Mesa was slow in the sample's last week


def test_the_model_gets_numbers_not_raw_rows():
    model = ScriptedModel(["Fine week."])
    wr.run(TINY, END, model, Path("/tmp/wr-test"))
    assert '"revenue": 400' in model.calls[0][1] and "J2" not in model.calls[0][1]
