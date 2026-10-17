# Customer RFQ intake

Turns a quotes mailbox into a clean list, the day requests arrive. A model reads each email; plain code checks what it read against your own records, and anything that doesn't check out goes to a person.

The full playbook, worked through at Summit Mechanical with an architecture diagram and a value calculator: **https://pathmode.com/playbooks/rfq-intake/**

## What it does

- Reads every email in the mailbox and sorts it: a new quote request, a follow-up, a reply to a quote you sent, a service call sent to the wrong address, or something else.
- For each quote request, the model pulls out the customer, sites, equipment, quantities and deadline, **quoting the words each one came from**.
- Code then matches all of it to your own records (customers, sites, equipment), exactly or not at all. When two units could fit, it asks the customer instead of guessing.
- It runs the checks. Anything that fails one goes to the **needs review** queue for a person: quoted words that aren't in the email, equipment that isn't yours, an attachment it can't read, instructions aimed at an AI, a deadline that doesn't make sense, an answer it couldn't use.
- It writes a dashboard, the lists as spreadsheets, and a drafted question for each request that's missing something.

## What it doesn't do

Send anything, change the mailbox, or price anything. A person sends every question and writes every quote.

**Risk: reads one mailbox, read-only. Drafts only.**

## Try it

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
# Replay a recorded run: the answers a real model (Claude Sonnet 5.5) gave on the sample, free
python3 rfq-intake/rfq_intake.py --sample --replay rfq-intake/sample-data/recorded-run.json

# The offline stand-in: no model at all. It only knows the sample's phrasings.
python3 rfq-intake/rfq_intake.py --sample --dry-run

# A real model: an API account whose terms say your data isn't used for training
export PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=...   # or ANTHROPIC_API_KEY=...
python3 rfq-intake/rfq_intake.py --sample
```

Then open `out/dashboard.html`. With the sample, `out/score.md` scores the run against the answer key.

## The sample: Summit's quotes@ mailbox, September 2025

Summit Mechanical is a fictional commercial HVAC contractor, from a [simulation of the whole business](https://pathmode.com/community/meetups/understand-the-business/the-practice-business/). The simulation has no incoming quote requests, so `pathmode-corpus/simulation/scripts/playbook_rfq.py` writes them from its real customers, sites and equipment. Everything else in the mailbox is real simulated email.

- `mailbox/`: 80 emails. 52 quote requests, in every shape (clear, vague, which-unit-is-it, bid invitations with a CSV or only a PDF, new prospects, a typo'd serial, one with instructions for "any AI assistant"), plus 12 replies to quotes, 8 service calls, 5 sales pitches and 3 follow-ups.
- `records/`: customers, sites, equipment and contacts, as exported from Summit's field-service system (1,406 customers, 5,473 sites, 24,180 units).
- `answer-key.csv`: what each email really is, and what should happen to it.
- `recorded-run.json`: a real model's answers, for `--replay`.

## Getting the email: Microsoft 365

`graph_mailbox.py` copies new email from one Microsoft 365 mailbox into a folder, read-only, using Microsoft Graph. Run it on a schedule, then run `rfq_intake.py` on the folder. The setup (an app registration with *Mail.Read*, limited to the one mailbox) is at the top of the file. It's tested here against a stand-in for Graph, not a live tenant: try it on a test mailbox first.

On another mail system, anything that saves messages as `.eml` files works.

## Use it on your own business

- `--mailbox mail/` (a folder of .eml files) and `--records records/` with `customers.csv` (Customer ID, Name), `sites.csv` (Site ID, Customer ID, Site, Address), `equipment.csv` (Equipment ID, Site ID, Type, Make, Model, Serial, Installed) and `contacts.csv` (Customer ID, Name, Email).
- If your requests aren't HVAC equipment, change what `EXTRACT` asks the model for, and what `records.py` matches it against. The checks and the piles stay the same.
- Build your own answer key from a month of real email, labeled by hand. It's the only way to know how often it's right.

## Files

| File | What |
|---|---|
| `rfq_intake.py` | Reads the mailbox, asks the model, checks, sorts, and writes the outputs. |
| `records.py` | Your records, and the matching that has to be exact. |
| `dashboard.py` | The HTML dashboard. Everything from an email is escaped. |
| `graph_mailbox.py` | Copies new email out of a Microsoft 365 mailbox, read-only. |
| `instructions.md` | The same job as instructions for a chat assistant, to try by hand. |
| `sample-data/` | Summit's mailbox, records, answer key and recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
