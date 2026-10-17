# Anomaly alerts

Finds the problems hiding in a month of jobs (money that leaked between systems, and the habits behind it), explains the top ones, and gives each owner a short list. The AI explains; it doesn't detect.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/anomaly-alerts/**

## What it does

- **Rules** reconcile records across systems: parts used but not billed, invoices credited to stay under the not-to-exceed (NTE) amount, increases approved in a customer's portal but never recorded, visits with no hours.
- **Baselines** compare each technician with their branch peers, using the median and MAD so one extreme value can't hide the rest.
- **A machine-learning model** (scikit-learn's Isolation Forest) flags the technicians whose combination of habits is least typical, and says which habits stand out.
- **An alert budget:** up to 12 flags per owner per run are investigated and sent. Every flag stays on the full list.
- **An AI investigator** explains each budgeted flag from the records behind it. Technicians appear by ID only. It can't change, rank or dismiss a flag. Code checks every explanation: the records it cites must exist, and its numbers must come from them.
- **One dashboard per owner:** the controller's has no technician signals. Plus a digest draft per owner, a full flag list, and a run log.

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

Then open `out/dashboard.html` (the controller's) and `out/dashboard-service-manager.html`. With the sample, `out/score.md` scores the run against the answer key.

## The sample: Summit's September 2025

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_anomaly.py`), with August as history: jobs, visits, time entries, parts used, technicians' notes, invoices and invoice lines, portal NTE records, technicians. `answer-key.csv` (jobs) and `tech-answer-key.csv` (technicians' habits) come from the simulation's hidden truth, never from the exports.

## Running it for real

`run.sh` checks the previous week's jobs. Schedule it weekly, after the nightly exports. Keep the outputs where only each owner can open their own dashboard. Have owners fill in the `decision` and `reason` columns of `flags.csv`, and use those marks to tune `--contamination`, the baselines' threshold and `--budget`. Re-run the answer key after any change, including a new model version.

## Files

| File | What |
|---|---|
| `anomaly_alerts.py` | The detectors, the budget, the investigation and its checks, the outputs. |
| `alerts_dashboard.py` | One dashboard per owner. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `requirements.txt` | scikit-learn and its dependencies, pinned by version and hash (from `requirements.in` with `uv pip compile --generate-hashes`). |
| `sample-data/` | Summit's exports, answer keys and the recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
