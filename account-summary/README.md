# Account summary

A one-page briefing on a customer or a branch, from the field-service system, accounting and the inbox, in a minute instead of an hour. Code checks who's asking and calculates every number from written definitions; the AI writes the sentences; code checks every number, metric and quote in them.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/account-summary/**

## What it does

- **Checks who's asking, first.** The general manager sees everything; a branch manager their branch and its customers; an account manager their own accounts. Anything else is refused before any data is gathered, with the same message whether the customer exists or not. A branch manager's briefing on a customer counts only their branch's work (jobs, invoices, sites), and says so: Summit's customers often have work at more than one branch.
- **Calculates the facts in code**, from a fixed list of metrics, each with a definition and an owner (`out/metrics.md`):
  - revenue against the same quarter last year (the fair comparison for a seasonal business), and against the quarter before;
  - jobs, first-time fix and days to complete;
  - quotes won, by count and by value;
  - the overdue balance, net of payments and write-offs;
  - the customer's emails and how many were chasing, or, for a branch, its top customers and biggest changes.
- **The AI writes the briefing:** a headline, four to six points naming the metrics they come from, quotes from the customer's emails, and questions worth asking.
- **Code checks it:** every number must be one of the facts (rounding allowed, "$5.0M" included), small counts like "3 invoices" too, and a number in an email doesn't count. It must be the right kind of figure (a dollar amount must be money, not the 282 that's a count of days), going the right way ("rose 2.0%" can't be a fall of 2.0%), in the right quarter (this year's and last year's revenue can't be swapped). A number in a point must belong to a metric that point cites, and a point citing more than three metrics goes to a person. The headline and the questions are checked the same way, against every fact. "Doubled", "tripled", "halved" and "nothing is overdue" are checked against the facts. Every metric must exist; every quote must be in that customer's own emails. An answer of the wrong shape, or one that fails a check, goes to a person.
- **One folder per person,** `out/<user>/`, holding only their own requests: `dashboard.html` and `summaries/`. The general manager's holds everything, refusals included, and `requests.csv`. Text from the AI and from emails is escaped on the page and made inert in the markdown.
- **A log line per request** in `out/runs.csv`: who asked, about what, refused or not, and how many checks failed.

## What it doesn't do

Send anything, change any record, or calculate anything with the AI.

## Try it

```sh
# Replay a recorded run: a real model's briefings (Claude Sonnet 5.5), free
python3 account-summary/account_summary.py --sample --replay account-summary/sample-data/recorded-run.json

# The offline stand-in: no model at all
python3 account-summary/account_summary.py --sample --dry-run
```

The replay: 11 requests, 8 ready, 2 refused, and 1 for a person: Q05, whose briefing uses a percentage the AI worked out itself and a figure from the customer's own email, neither of them a fact. Q05 and Q06 are Dana's briefings on Tucson customers with work at other branches too; they count Tucson's work only, and say so. A replay with no recorded answer for a request says how many.

`--standard` adds the scheduled run's requests: each branch manager's own branch, for the quarter.

`--quarter 2025Q3` picks the quarter; it's compared with the quarter before and the same quarter a year before. The default is 2025Q3 with `--sample` (the sample's quarter), and otherwise the last quarter that has closed, which is what the scheduled run in `run.sh` wants.

## The sample: Summit's Q3 2025

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_summary.py`): Summit's customers, sites, jobs, quotes, invoices, payments and write-offs for Q3 2025, the quarter before and the same quarter a year before, and 2,636 customer emails from Q3, matched to the customer by their signature. Four users with different scopes, and eleven requests, two of them out of scope.

The answer key holds each request's headline figures (revenue for the three quarters, jobs completed, the overdue balance), calculated separately in SQL, or "refused". It's separate arithmetic, not a separate source: it reads the same exported invoices (already matched to a customer and a branch), with the same definition of overdue and the same scope rule, and it doesn't cover first-time fix, days to complete, quotes, emails or the words. The tests reconcile the playbook's facts with it to the cent, and also check that a customer's branch shares add up to the whole and the branches to every invoice.

11 of 11 requests match it. For a branch manager's customer briefing (Q05, Q06) the key counts the same part as the briefing: that branch's work for the customer. In the recorded run, 8 briefings pass every check; Q05 goes to a person, because its words use two numbers the AI worked out (55% and $519.59).

## Before you run this on your own data

- **The checks read numbers, not words.** Amounts in words ("forty thousand"), ranges ("$40-50K") and fractions ("a third") aren't read, so they're neither checked nor caught. Beyond "doubled", "tripled", "halved" and "nothing is overdue", a claim made in words ("the best quarter ever") isn't checked: reading the briefing is still a person's job.
- **Direction and quarter are read from nearby words.** "Fell 2.0%" and "$5.1M in Q3 2024" are checked; a sentence built another way ("the drop, at 2.0%, ...") may not be pinned to a direction or a quarter, and then only the value and its kind are checked. Money must be written with a $ (or as "5.0M"); a bare "5,000,999" is read as a count and goes to a person.
- **The metrics are Summit's.** Revenue is invoiced by invoice date; overdue nets payments and write-offs; a customer belongs to one home branch, and a quote to the customer's home branch. Your definitions, owners and columns will differ: change `METRICS` and `facts()` together, with each owner's say, and update the definitions test.
- **Each invoice and job needs a branch and a customer.** Summit's exports already carry them; if yours don't, that matching is the hard part, and it's yours to do before this runs.
- **Missing data is skipped or flagged, not repaired.** A request from an unknown user is refused; a repair with no created date is left out of days to complete and the briefing goes to a person; quotes worth $0 give no value rate. A blank or non-numeric amount in payments, write-offs, invoices or quotes stops the run.
- **Scope is three rules** (everything, a branch, a list of accounts) in `authorize()`. Anything else (regions, deputies, shared accounts) needs a rule and a test of its own.
- **Each person's folder must be readable by that person only.** The code writes `out/<user>/`; your web server or file share has to enforce who reads it. `out/runs.csv` names who asked about which customer: it's for whoever runs this.
- **Emails are matched to a customer by their signature.** A wrong match puts one customer's words in another's briefing; check how your inbox is matched before you rely on the quotes.

## Files

| File | What |
|---|---|
| `account_summary.py` | Scope, the metrics, the AI's briefing and its checks. |
| `summary_page.py` | Each person's page, and the general manager's. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `run.sh` | The quarterly run. |
| `sample-data/` | Summit's exports, the users and requests, the answer key and the recorded run. |
