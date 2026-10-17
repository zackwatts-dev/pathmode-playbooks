# Anomaly alerts

Finds the problems hiding in a month of jobs (money that leaked between systems, and the habits behind it), explains the top ones, and gives each owner a short list. The AI explains; it doesn't detect.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/anomaly-alerts/**

## What it does

- **Rules** reconcile records across systems: parts used but not billed, invoices credited to stay under the not-to-exceed (NTE) amount, increases approved in a customer's portal but never recorded, visits with no hours (a blank time entry, or none at all).
- **Baselines** compare each technician with their branch peers, using the median and MAD so one extreme value can't hide the rest. A flag also needs at least three occurrences and a rate at least 5 points above peers, so one repeat in a branch where most have none isn't a pattern.
- **A machine-learning model** (scikit-learn's Isolation Forest) looks for technicians whose combination of habits, over the 90 days ending on the run's end date (`--tech-window`), is unusual. There's no quota: a technician is flagged only if the model finds them clearly unusual (`--tech-threshold`, 0.55, where 0.5 is average) and at least one problem habit (parts recorded late, slow paperwork, missing hours, repeat visits) is material: well above typical, by enough, at least three times. A month with nothing unusual flags nobody. Each flag is worded as a pattern worth a conversation. Slow paperwork needs the time each entry was made: in the sample every time entry carries its visit's date, so it can't be seen there, and the service manager's summary says so.
- **An alert budget:** up to 12 flags per owner per run are investigated and sent: the most money first, then other record problems, technician patterns last. Every flag stays on the full list.
- **An AI investigator** explains each budgeted flag from the records behind it. Technicians appear by ID only, and only in the service manager's flags: the controller's records carry no technician IDs. It can't change, rank or dismiss a flag. Code checks every explanation: its shape first (a malformed answer goes to a person); then every record it cites or mentions must be in the records; its numbers must be the records' amounts and quantities, not the digits of an ID or a date; and it may not name a person or accuse or discipline anyone. An explanation that fails goes to a person, and its text isn't carried into any output.
- **Each owner gets only their own flags:** a dashboard, a digest draft (addressed from `recipients.csv`: `Owner,To`), a flag list and a review queue. The controller's (`dashboard.html`, `flags.csv`, `review-queue.csv`) have no technician signals or IDs; the service manager's are named `-service-manager`, plus `summary-service-manager.md`. The shared `summary.md` has job-flag counts only. And a run log.

## What it doesn't do

Change anything in any system, send anything, or decide anything about a person. Technician flags are signals for a manager to look into.

## Try it

```sh
pip install --require-hashes -r anomaly-alerts/requirements.txt   # scikit-learn, pinned and hash-checked

# Replay a recorded run: a real model's explanations (Claude Sonnet 5.5), free
python3 anomaly-alerts/anomaly_alerts.py --sample --replay anomaly-alerts/sample-data/recorded-run.json

# The offline stand-in: no model at all
python3 anomaly-alerts/anomaly_alerts.py --sample --dry-run

# Also run the model over individual jobs (it flags big installs: unusual, not wrong)
python3 anomaly-alerts/anomaly_alerts.py --sample --dry-run --model-jobs
```

Then open `out/dashboard.html` (the controller's) and `out/dashboard-service-manager.html`. With the sample, `out/score.md` scores the run against the answer key. It says what it can't prove: the "hours not logged" answer key uses the rule's own definition, so that row checks the plumbing, not the rule; and callbacks, the largest problem in the answer key, aren't checked by this playbook. An investigated flag counts as real only when its problem matches the answer key's problem for that job (or that technician's habit). A replay that has no recorded answer for a flag sends it to a person and says how many.

## The sample: Summit's September 2025

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_anomaly.py`), with August as history: jobs, visits, time entries, parts used, technicians' notes, invoices and invoice lines, portal NTE records, technicians. `answer-key.csv` (jobs) and `tech-answer-key.csv` (technicians' habits) come from the simulation's hidden truth, never from the exports.

## Running it for real

`run.sh` runs weekly, after the nightly exports. Most jobs are invoiced days after they're done, so a week-only window would check them before their invoice exists and never again. So each run re-checks every job completed in the last 45 days (`--lookback`, the default with `--data`), and `flag-history.csv` in the output folder remembers what was already reported: only new flags are investigated and sent, and the rest stay on the list as still open. Keep the outputs where each owner can open only their own files. Have owners fill in the `decision` and `reason` columns of their `flags*.csv`, and use those marks to tune `--tech-threshold`, the baselines' threshold and `--budget`. Put each owner's address in `recipients.csv` in the exports folder (or pass `--recipients`); the sample's is in `sample-data/`. Re-run the answer key after any change, including a new model version.

## Before you run this on your own data

- **Your exports won't look like Summit's.** The column names, the job-to-invoice match (by job number) and the "Credit to NTE" line are Summit's; map yours first.
- **Dates and hours:** ISO dates and timestamps, `9/5/2025` (read month first) and hours as `1.5` or `1:30` are read. Anything else is listed in `unreadable.csv` and counted in the summary, and a job whose completion date can't be read isn't checked until it's fixed.
- **Amounts:** plain numbers and `$1,200.50` are read. Parentheses for negatives, other currencies and words aren't.
- **Duplicates:** an invoice exported twice is counted once. Duplicate invoice lines are dropped only if the export has a line ID column; without one, two identical lines both count.
- **Slow paperwork needs a real entry timestamp.** If your time entries carry the visit's date, as Summit's do, that habit can't be seen.
- **Weekly runs need the look-back and the history file.** Without them, most unbilled parts are checked before the invoice exists. Keep `flag-history.csv` between runs.
- **Not covered:** callbacks (repeat work from a misdiagnosis or a temporary fix, the largest problem in Summit's answer key) and parts on jobs that were never invoiced ($8,303 in the sample). Those need rules nobody has written yet.
- **The thresholds are Summit's.** The baselines' limits, `--tech-threshold`, the 90-day `--tech-window` and the budget were tuned on one simulated month. Tune them with your owners' marks.
- **The explanation checks are text patterns.** A name, an ID or an accusation written in a way they don't recognize can get through; owners still read every explanation before acting.

## Files

| File | What |
|---|---|
| `anomaly_alerts.py` | The detectors, the budget, the investigation and its checks, the outputs. |
| `alerts_dashboard.py` | One dashboard per owner. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `requirements.txt` | scikit-learn and its dependencies, pinned by version and hash (from `requirements.in` with `uv pip compile --generate-hashes`). |
| `sample-data/` | Summit's exports, answer keys, digest recipients and the recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
