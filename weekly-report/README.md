# Weekly numbers report

Calculates the week's numbers in code, then has the model write a short summary, and checks every number in that summary against the calculation.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/weekly-report/**

## What it does

- Calculates revenue, jobs completed, revenue per job and callback rate for the week, the week before and the four-week average, by branch.
- Gives the model those numbers, not your raw rows.
- Extracts every number from the model's summary and checks it. If one doesn't match, the report says so at the top.

## What it doesn't do

- Let the model do arithmetic.
- Explain causes the data doesn't show (the instructions forbid it).

**Rung 2: it reads a file you give it.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 weekly-report/weekly_report.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Jobs:** `--jobs jobs.csv --week-ending 2026-07-12`, one row per job with Date, Branch, Type, Revenue, Completed, Callback, Hours. Rename your export's columns, or change `COLUMNS` at the top of the script.
- Change or add metrics in `compute()`. The checking works for any number you add.

It writes `out/report.md` and `out/metrics.json`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `weekly_report.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
