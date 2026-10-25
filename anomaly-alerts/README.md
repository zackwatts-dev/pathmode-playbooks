# Anomaly alerts

A morning brief for every store of a restaurant group: what's leaking (the kitchen, the bar, the register, the cash, the invoices, the timeclock), weeks before the period closes. Code and machine learning find what's unusual; an AI reader writes a plain explanation and a next step for each flag and, for a one-off kitchen jump, says whether the managers' log explains it (quoting the entry); AI checkers read the log again and the answer's words, and code compares and checks every answer. Each general manager, the director of operations and the controller get their own list. Nothing here contacts anyone or changes a record.

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
3. **Reads** (AI), for each new flag and each flag whose dollars a week have grown by half, by dollars a week, at most six a store and forty in all a morning. The AI reader gets the flag and its records as of that morning, with employees by id. For a one-off kitchen jump (one week's usage $1,500 or more over, the only one-off the detectors raise) it also gets the store's log for those days, with names taken out. It writes a plain explanation and a next step, and says whether a log entry explains the flag, quoting it.
4. **Checks the answer** (code, then two AI checkers).
   - **Code checks what it can check exactly:** at least one record cited, every record cited exists, every amount one of the records' amounts (not an id or a date), no name from the employee list, and for a log explanation an entry it was given whose words are really there. Code also looks for log entries addressed to an AI with a pattern list; such an entry can never explain a flag.
   - **The log checker** gets the flag, its records and the same log, never the reader's answer, and names the entry it finds explaining the flag, or none, and any entries addressed to an AI. The flag counts as explained only if both name the same entry. Where they differ, it stays up for the general manager with both readings noted.
   - **The language checker** gets only the answer's explanation and next step, and says whether they accuse anyone, name anyone, state a cause as fact or suggest discipline, quoting the words. Any of those sends the flag to a person.
   - Anything that fails, or a checker answer that can't be used, goes to a person, with the flag, unexplained.
5. **Writes the briefs:** `briefs/gm-NN.html` for each general manager (register, kitchen, bar and hours at their store), `briefs/director.html` (every store, plus edited punches and any log entry addressed to an AI), `briefs/controller.html` (invoice overcharges and cash), and `dashboard.html` (everything). Also `flags.csv`, a line in `run-log.jsonl`, and with an answer key `score.md` and `score.json`.

## What it doesn't do

- **It doesn't accuse anyone.** A flag is a pattern worth a look. The tool never contacts anyone, changes a record or disciplines anyone.
- **It doesn't send anything.** The briefs are files, in folders only their owners can open.
- **It doesn't let the log excuse a pattern.** Only a one-off kitchen jump can be put down to an event in the log, only when the words are found there, and only when the log checker, reading without the reader's answer, names the same entry.
- **It sees a note in the log only when it reads that log.** A log is read only for a one-off kitchen jump; a note addressed to an AI on a day no such flag reads is found only if code's pattern list recognizes it.
- **It doesn't see deliveries.** Exports show what was invoiced, not what arrived, so a short delivery looks like a kitchen gap.

## Try it

```sh
# No AI: every flag listed, none explained by the log
python3 anomaly-alerts/anomaly_alerts.py --sample --dry-run

# Replay the recorded run: what a real model (Claude Sonnet 5.5) answered and checked on the sample, free
python3 anomaly-alerts/anomaly_alerts.py --sample --replay anomaly-alerts/sample-data/recorded-run.json

# The held-back year (fiscal 2023, in new log wording), scored once with the code frozen at f5ddd56
python3 anomaly-alerts/anomaly_alerts.py --data anomaly-alerts/holdout-2023 --answer-key anomaly-alerts/holdout-2023/answer-key \
  --replay anomaly-alerts/holdout-2023/recorded-run.json

# A real model
ANTHROPIC_API_KEY=... python3 anomaly-alerts/anomaly_alerts.py --sample

# The tests (no AI, free)
python3 -m pytest anomaly-alerts
```

It needs Python 3.11+, numpy and scikit-learn (`pip install -r anomaly-alerts/requirements.txt`, pinned with hashes).

## The sample

One year of Ironbark Tavern & Grill's records (the simulation's fiscal 2024, January 1 to December 29) and the twelve weeks of history before it, from a detailed simulation of a twelve-store group in the Kansas City metro (`records/`, about 8 MB zipped). The answer key (`answer-key/`) holds every problem that was running, who or what it involved, when it started, when the group's current way of working stopped it, and its loss by week; and every honest odd day (a cooler failure, a catering order, a snowstorm) and whether the manager wrote it down. One store's log carries an entry addressed to an AI.

`holdout-2025/` (fiscal 2025) and `holdout-2023/` (fiscal 2023 after its first twelve weeks, every log entry in other managers' words) are the held-back years, each with its answer key and recorded run.

## Results

The thresholds (`release-thresholds.json`) were set before any held-back year was generated, and haven't changed.

| Measure | Limit | Held back: fiscal 2023, new log wording | Sample: fiscal 2024 | Fiscal 2025 |
|---|---|---|---|---|
| Losses stopped (if each problem stops two weeks after its first flag) | at least 50% | **73%** ($199,083 of $272,105) | 74% ($270,975 of $366,353) | 78% ($289,449 of $369,735) |
| False alarms a store a week | at most 0.20 | **0.098** | 0.061 | 0.082 |
| Shown answers that accuse anyone | 0 | **0** | 0 | 0 |
| Real problems the log "explained" away | at most 1 | **0** | 0 | 0 |

Median days from a problem's start to its first flag: 14 (2023), 19 (2024) and 17 (2025), against 98, 121 and 126 until the current way of working stopped it.

**Which year to trust.** Fiscal 2025 was the first held-back year: scored once at fc52471, before the checkers existed, and it passed (its recording at that commit is `holdout-2025/recorded-run-at-fc52471.json`; `recorded-run.json` there now also holds the checkers' answers, recorded for development). Adding the checkers changed the code, so 2025 became development data, with 2024. Its log used the same wording as the sample's (only its note addressed to an AI was new), so it couldn't test a checker that reads the log. Fiscal 2023 (after its first twelve weeks, which serve as history) was generated after the code froze at f5ddd56, with every log entry re-rendered in other managers' words written by an AI that never saw this code, recorded once (304 calls, none reused) and scored once (`holdout-2023/score-at-f5ddd56.md`). It's the result to trust, with two limits: its last twelve weeks are the same records the sample uses as history (only the log reworded), and $193,220 of its $272,105 in losses come from problems, and people, that also ran in the sample year the thresholds were tuned on. So it tests the new wording and the frozen code fully, and the thresholds less than a separate year would. Its log was re-rendered from a second set of sentence templates (6,033 of 6,034 entries), not freely rewritten.

**What 2023 didn't test well.** No flag that year met an honest logged event, so nothing was explained by the log either way; the log-reading is shown working on 2024 (six one-off kitchen jumps read with the log: five explained, each with the right entry, and one where the two readings named different entries and the flag stayed up). And 2023's note addressed to an AI sat in a log no reading was given, in wording code's pattern list doesn't recognize, so it went unreported. It changed nothing.

**How the checkers were built.** They replaced word lists that judged prose: the event words a log entry had to use (only kitchen events had any, so a bar or labor one-off could never be explained) and the accusation patterns. They were developed on 2024 and 2025 (both already scored). The language checker's prompt was changed once, after it called next steps that ask a manager to check something accusations (`sample-data/dev-checker-run-1.json`). "Shown answers that accuse" is measured with the old accusation patterns, kept in the scorer only; the system doesn't use them.

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
