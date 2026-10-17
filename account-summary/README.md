# Account summary

A one-page briefing on a customer or a branch, from the field-service system, accounting and the inbox, in a minute instead of an hour. Code checks who's asking and calculates every number from written definitions; the AI writes the sentences; code checks every number, metric and quote in them.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/account-summary/**

## What it does

- **Checks who's asking, first.** The general manager sees everything; a branch manager their branch and its customers; an account manager their own accounts. Anything else is refused before any data is gathered, with the same message whether the customer exists or not.
- **Calculates the facts in code**, from a fixed list of metrics, each with a definition and an owner (`out/metrics.md`):
  - revenue against the same quarter last year (the fair comparison for a seasonal business), and against the quarter before;
  - jobs, first-time fix and days to complete;
  - quotes won, by count and by value;
  - the overdue balance, net of payments and write-offs;
  - the customer's emails and how many were chasing, or, for a branch, its top customers and biggest changes.
- **The AI writes the briefing:** a headline, four to six points naming the metrics they come from, quotes from the customer's emails, and questions worth asking.
- **Code checks it:** every number must be one of the facts (rounding allowed, "$5.0M" included), small counts like "3 invoices" too, and a number in an email doesn't count; a number in a point must belong to a metric that point cites, so a true figure under the wrong metric is caught; every metric must exist; every quote must be in that customer's own emails. An answer of the wrong shape, or one that fails a check, goes to a person.
- **One page per person,** holding only their own requests. The general manager's (`dashboard.html`) holds everything, refusals included.

## What it doesn't do

Send anything, change any record, or calculate anything with the AI.

## Try it

```sh
# Replay a recorded run: a real model's briefings (Claude Sonnet 5.5), free
python3 account-summary/account_summary.py --sample --replay account-summary/sample-data/recorded-run.json

# The offline stand-in: no model at all
python3 account-summary/account_summary.py --sample --dry-run
```

`--quarter 2025Q3` picks the quarter; it's compared with the quarter before and the same quarter a year before. The default is 2025Q3 with `--sample` (the sample's quarter), and otherwise the last quarter that has closed, which is what the scheduled run in `run.sh` wants.

## The sample: Summit's Q3 2025

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_summary.py`): Summit's customers, sites, jobs, quotes, invoices, payments and write-offs for Q3 2025, the quarter before and the same quarter a year before, and 2,636 customer emails from Q3, matched to the customer by their signature. Four users with different scopes, and eleven requests, two of them out of scope.

The answer key holds each request's headline figures (revenue for the three quarters, jobs completed, the overdue balance), calculated separately in SQL, or "refused". The tests reconcile the playbook's facts with it to the cent.

## Files

| File | What |
|---|---|
| `account_summary.py` | Scope, the metrics, the AI's briefing and its checks. |
| `summary_page.py` | Each person's page, and the general manager's. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `run.sh` | The quarterly run. |
| `sample-data/` | Summit's exports, the users and requests, the answer key and the recorded run. |
