# Late invoices

Decides which overdue customers your accounting software's automatic reminders can handle, and which need a person. Then it drafts the personal follow-ups.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/late-invoices/**

## What it does

- Applies plain, readable rules: leave it to the automatic reminder, send a personal email, call, wait for a promised date, or resolve a dispute first.
- Reads customer replies into "promise, by when" or "dispute, about what".
- Drafts personal follow-ups in which every invoice number and amount is inserted by code. Any number the model adds on its own is flagged.

## What it doesn't do

- Send anything, change your books, or add late fees.
- Replace your software's reminders. Turn those on first.

**Rung 2: it works with files you export. A person sends every email.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 late-invoices/late_invoices.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Aging report:** `--aging ar-aging.csv` with columns Customer, Contact, Email, Invoice, Invoice date, Due date, Amount, Balance (dates as YYYY-MM-DD). Export from QuickBooks (Accounts receivable aging detail) or Xero (Aged Receivables Detail), then rename columns to match.
- **Payment history (optional, but it's what spots repeat-late customers):** `--history paid.csv` with Customer, Invoice, Due date, Paid date.
- **Customer replies (optional):** `--replies folder/` of .txt or .eml files.
- Change the thresholds with `--late-days`, `--large` and `--call-after`.

It writes `out/summary.md` (overdue by age, and what to do), `out/actions.csv` and `out/drafts/`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `late_invoices.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
