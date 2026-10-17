# Late invoices

Decides which overdue customers your accounting software's automatic reminders can handle, and which need a person. Then it drafts the personal follow-ups.

The full playbook, worked through on Summit Mechanical's books, with a cost calculator and the risks: **https://pathmode.com/playbooks/late-invoices/**

## What it does

- Reads customer emails about invoices and finds the customers who are **waiting on you** (a W-9, line items, a resent invoice, a new billing address, "was our payment received?") or **questioning a charge**. Chasing those customers makes things worse.
- Applies plain, readable rules to everyone else: an automatic reminder, a personal email, a call, wait for a promised date, or a small leftover to ask about or write off.
- Flags the records problems that make invoices late on their own: the same customer under two account names, and invoices with no due date.
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

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. It only knows the phrasings in the sample emails; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account whose terms say your data isn't used for training.

## The sample: Summit's Tucson branch, October 31, 2025

Summit Mechanical is a fictional commercial HVAC contractor. Its books come from a simulation of the whole business ([about Summit](https://pathmode.com/community/meetups/understand-the-business/the-practice-business/)), so they have the mess real books have. The sample is the Tucson branch's receivables on October 31, 2025:

- `ar-aging.csv`: 1,906 open invoices. Contacts are filled in where the customer has emailed Summit.
- `payment-history.csv`: 11,174 invoices paid in the year before.
- `replies/`: the 45 billing emails Tucson customers sent in October, one file each. `customer-emails.txt` has the same emails in one file.

The result, as `summary.md` shows it: $507,030 overdue across 157 customers. 84% of it is under 30 days late. 21 customers (about $124,000) are waiting on Summit or questioning a charge, and nine customers have two accounts each.

## Use it on your own data

- **Aging report:** `--aging ar-aging.csv` with columns Customer, Invoice, Due date, Amount, Balance (dates as YYYY-MM-DD), and optionally Contact and Email. Most accounting software exports an aging detail report; rename its columns to match.
- **Payment history (optional, but it's what spots repeat-late customers):** `--history paid.csv` with Customer, Invoice, Due date, Paid date.
- **Customer emails (optional):** `--replies folder/` of .txt or .eml files.
- Change the rules with `--late-days`, `--large`, `--call-after` and `--small`.

It writes `out/summary.md` (overdue by age, who needs what, records to fix), `out/actions.csv` and `out/drafts/`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `late_invoices.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Summit's Tucson files, exported from the simulation. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
