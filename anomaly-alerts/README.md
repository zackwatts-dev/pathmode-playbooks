# Anomaly alerts

A morning brief for every store of a restaurant group: what's leaking (the kitchen, the bar, the register, the cash, the invoices, the timeclock), weeks before the period closes. Code and machine learning find what's unusual; an AI reads the managers' log for each flag, says whether the log explains it (quoting the entry), and otherwise writes a plain explanation and a next step; code checks every answer. Each general manager, the director of operations and the controller get their own list. Nothing here contacts anyone or changes a record.

The full playbook, worked through at Ironbark Tavern & Grill (a simulated twelve-store group) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/anomaly-alerts/**

## What it does

Each morning (on Mondays, after the Sunday counts, for the week too), looking back 90 days so it knows which flags are already open:

1. **Builds the picture** (code), from the nightly exports, as they stood that morning:
   - the register, by employee over 28 days: voids after the check printed on cash checks; employee-meal and manager discounts on guest checks of two or more; whole-check comps by who approved them (the office's party package excepted);
   - each closing manager's cash over/short over 28 days;
   - every invoice line against that month's price list (or the latest one before it);
   - punches against the schedule: edited punches that add an hour or more, by who edited them; a store's shifts running longer than its own previous eight weeks, beyond the change at every store, two Mondays running;
   - each store's weekly actual usage (last count, plus what was delivered, less this count) against theoretical (product mix times recipes), valued at what the last eight weeks' invoices paid.
2. **Finds what's unusual** (no AI):
   - **rules** for what's exact: a price over the list, a punch edited to add hours, whole-check comps;
   - **baselines:** an employee's rate at least 1.2 points of their sales above the group's typical rate, with at least $150 and four occurrences in 28 days; a store's kitchen gap $300 a week over the group's best-run quarter of stores in three of the last four weeks, or $300 a week over its own last eight weeks four weeks running, or one week $1,500 over; the bar the same at $150 a week;
   - **attribution:** a regression of each bar's weekly gap on each bartender's hours over twelve weeks (non-negative coefficients), naming a bartender whose shifts explain at least $50 a week at twice the store's typical bartender;
   - a one-week jump that reverses the next week (a miscount) isn't flagged unless it's large.
3. **Reads** (AI), for each new flag and each flag whose dollars a week have grown by half, by dollars a week, at most six a store and forty in all a morning. The AI gets the flag and its records as of that morning, with employees by id. For a one-off kitchen flag (the only kind one event can explain) it also gets the store's log for those days, with names taken out. It writes a plain explanation and a next step, and says whether the log explains the flag, quoting the entry.
4. **Checks the answer** (code). It must cite at least one record, every record it cites must exist, and every amount must be one of the records' amounts (not an id or a date). It may not name anyone, accuse, call anything theft or fraud, or state a cause as fact. An explanation by the log is used only if the entry is one it was given, the words it quotes are in that entry and name an event that could account for a kitchen gap (a cooler, an outage, a recount), and the entry isn't addressed to an AI. Anything that fails goes to a person, with the flag, unexplained.
5. **Writes the briefs:** `briefs/gm-NN.html` for each general manager (register, kitchen, bar and hours at their store), `briefs/director.html` (every store, plus edited punches and any log entry addressed to an AI), `briefs/controller.html` (invoice overcharges and cash), and `dashboard.html` (everything). Also `flags.csv`, a line in `run-log.jsonl`, and with an answer key `score.md` and `score.json`.

## What it doesn't do

- **It doesn't accuse anyone.** A flag is a pattern worth a look. The tool never contacts anyone, changes a record or disciplines anyone.
- **It doesn't send anything.** The briefs are files, in folders only their owners can open.
- **It doesn't let the log excuse a pattern.** Only a one-off kitchen gap can be put down to an event in the log, and only when the words are found there.
- **It doesn't see deliveries.** Exports show what was invoiced, not what arrived, so a short delivery looks like a kitchen gap.

## Try it

```sh
# No AI: every flag listed, none explained by the log
python3 anomaly-alerts/anomaly_alerts.py --sample --dry-run

# Replay the recorded run: what a real model (Claude Sonnet 5.5) answered on the sample, free
python3 anomaly-alerts/anomaly_alerts.py --sample --replay anomaly-alerts/sample-data/recorded-run.json

# The held-back year (fiscal 2025), scored once with the code frozen at fc52471
python3 anomaly-alerts/anomaly_alerts.py --data anomaly-alerts/holdout-2025 --replay anomaly-alerts/holdout-2025/recorded-run.json

# A real model
ANTHROPIC_API_KEY=... python3 anomaly-alerts/anomaly_alerts.py --sample

# The tests (no AI, free)
python3 -m pytest anomaly-alerts
```

It needs Python 3.11+, numpy and scikit-learn (`pip install -r anomaly-alerts/requirements.txt`, pinned with hashes).

## The sample

One year of Ironbark Tavern & Grill's records (the simulation's fiscal 2024, January 1 to December 29) and the twelve weeks of history before it, from a detailed simulation of a twelve-store group in the Kansas City metro (`records/`, about 8 MB zipped). The answer key (`answer-key/`) holds every problem that was running, who or what it involved, when it started, when the group's current way of working stopped it, and its loss by week; and every honest odd day (a cooler failure, a catering order, a snowstorm) and whether the manager wrote it down. One store's log carries an entry addressed to an AI.

## Results

| Measure | Limit | Sample year (2024) | Next year, held back (2025) |
|---|---|---|---|
| Losses stopped (if each problem stops two weeks after its first flag) | at least 50% | 74% ($270,975 of $366,353) | 78% ($289,449 of $369,735) |
| False alarms a store a week | at most 0.20 | 0.061 | 0.082 |
| Answers that accused or named someone | 0 | 0 | 0 |
| Real problems the log "explained" away | at most 1 | 0 | 0 |

Median days from a problem's start to its first flag: 19 (2024) and 17 (2025), against 121 and 126 until the current way of working stopped it. The thresholds were set before the held-back year was generated, and the code frozen (commit fc52471) before it was recorded.

## Before you run this on your own data

- **Map your exports** to the files in `records/`. Most POS systems export checks, adjustments with approvers, and product mix; most back-office systems export counts, recipes and invoices.
- **Score it on a period you know,** with the problems you already found as the answer key, before trusting it on one you don't.
- **Set the thresholds with your managers.** The ones here are tuned to Ironbark's sample and checked on a held-back year; yours will differ.

## Files

| File | What it is |
|---|---|
| `anomaly_alerts.py` | The pipeline: exports, detectors, the AI's reading and its checks, scoring |
| `alerts_dashboard.py` | The briefs and the dashboard |
| `design.md` | The design, one page |
| `plan.md` | The plan an AI wrote from it, unedited |
| `release-thresholds.json` | What counts as good enough, set before the held-back year was run |
| `tests/` | The rules, the as-of check, the scoring and the checks on the AI's answers, without calling the AI |
| `sample-data/` | Fiscal 2024: the exports, the answer key and the recorded run |
| `holdout-2025/` | Fiscal 2025, held back: the exports, the answer key and its recorded run, scored once with the code frozen |
