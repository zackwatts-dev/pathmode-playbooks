# Customer RFQ intake

Turns a quotes mailbox into a clean list, the day requests arrive. A model reads each email; plain code checks what it read against your own records, and anything that doesn't check out goes to a person.

The full playbook, worked through at Summit Mechanical with an architecture diagram and a value calculator: **https://pathmode.com/playbooks/rfq-intake/**

## What it does

- Reads every email in the mailbox and sorts it: a new quote request, a follow-up, a reply to a quote you sent, a service call sent to the wrong address, or something else.
- For each quote request, the model pulls out the customer, sites, equipment, quantities and deadline, **quoting the words each one came from**.
- Code then matches all of it to your own records (customers, sites, equipment), exactly or not at all. When two units could fit, it asks the customer instead of guessing.
- It runs the checks. Anything that fails one goes to the **needs review** queue for a person: quoted words that aren't in the email, a serial, model or quantity that isn't in the words quoted for it, equipment that isn't yours, an attachment it can't read, an email with no text it can read, instructions aimed at an AI, a deadline that doesn't make sense or has no words from the email behind it, an answer it couldn't use.
- It reads HTML-only email as text. Logos and signature images (inline, or under 100 KB) are ignored; any other attachment it can't read (a PDF, a spreadsheet, a photo) goes to a person.
- It writes a dashboard, the lists as spreadsheets, and a drafted question for each request that's missing something.
- Every run adds a line to `out/runs.csv` (when, which model, how many in each pile). No more than `--max-emails` (default 200) go to the model per run; the rest are listed for a person and picked up next time.

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
- `recorded-run.json`: a real model's answers, for `--replay`. They were recorded before the instructions asked for each serial and model to be inside its quote, so six of them, which give the serial or model in the next sentence, now go to a person: the replay scores 74 of 80, with nothing let through wrong. The offline stand-in (`--dry-run`) scores 80 of 80.

## Getting the email: Microsoft 365

`graph_mailbox.py` copies new email from one Microsoft 365 mailbox into a folder, read-only, using Microsoft Graph. Run it on a schedule, then run `rfq_intake.py` on the folder. The setup (an app registration with *Mail.Read*, limited to the one mailbox) is at the top of the file. It picks up from the time of the last message it saved, and remembers the ids saved at that time, so two messages that arrive in the same second are neither skipped nor saved twice. When Graph throttles it (HTTP 429 or 503), it waits as long as Graph asks (up to two minutes) and tries again, up to five times. It's tested here against a stand-in for Graph, not a live tenant: try it on a test mailbox first.

On another mail system, anything that saves messages as `.eml` files works.

## Running it for real

`run.sh` is one scheduled run: copy new email out of the mailbox, then sort it and rebuild the dashboard. Schedule it every 15 minutes, for example with cron:

```
*/15 * * * * /srv/pathmode-playbooks/rfq-intake/run.sh >> /srv/quote-intake/cron.log 2>&1
```

With `--remember` (which `run.sh` uses), each email is read by the AI once. Its answer is checked for shape before it's kept in `out/answers/`, later runs reuse it, and only new email costs anything. A kept answer that's damaged or the wrong shape is read again, never trusted. The checks and matching run again every time, so a fix to the records takes effect on the next run.

## Before it goes live

The repo covers the email limit, the "couldn't process" list, the run log, the spot checks and the tests. Yours to add: a server or scheduled job you control, the secret in a secret store, access to the outputs limited to the people who need them, deleting saved email on a schedule, and an alert if runs stop or the review pile jumps. Re-run the answer key after any change, including a new model version.

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
