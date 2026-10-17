# Pricing assistant

Prices a repair in minutes from a technician's diagnosis, and negotiates a replacement quote within limits. The AI reads and writes; code does the math and holds the lines.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/pricing-assistant/**

## What it does

**Price a repair.** The AI reads the diagnosis and picks the task from the flat-rate book, quoting the words. It reads the written sales guidance and picks the clauses that apply. Code checks both:
- the task must exist and fit the unit, and the words it quoted must name the task's part;
- when the job record lists the parts used, the task's part must be one of them: if the note and the record disagree, a person decides;
- every clause's condition must hold, and a rule the code can see for itself, but the AI missed, goes to a person;
- the note for the customer may not mention an amount, a percent other than the agreement discount, or a promise.

Then code works out the price. The AI never writes a number into a price. A price book row code can't read (zero, negative, "N/A") isn't used: the repairs that need it go to a person.

**Negotiate a replacement.** The AI writes each reply, trading before discounting. Code holds the lines:
- never below the floor (the AI never sees it);
- never beyond the estimator's 5% authority, even when it hands the deal to a manager (going further is the manager's decision, made by a person);
- no more than 2% of the list price off in a round, and never back up;
- only the concessions the guidance allows. Anything else that sounds like a promise (a warranty, a guarantee, something free or at no charge, a date, years of cover) goes to a person, even the manufacturer's warranty;
- no cost or floor in a message, however it's written;
- the message must state the offer, and no lower price; a percent, a price in words ("fourteen thousand") or a format code can't read ("14.418,87") goes to a person.

A reply that breaks any of these is blocked and goes to a person, even if the AI also asked for a manager.

A customer who tries to instruct the assistant, claims to speak for Summit or to carry its approval, or wants more than the authority allows, goes to a person.

## What it doesn't do

Send anything. For real customers, `--replies` reads their messages from a CSV and drafts one checked reply per quote for a person to send, with no simulator. The negotiation demo stops each conversation at its first checked reply too; it only bargains on its own with `--autonomous`, against the simulated buyers in `sample-data/buyer-simulator/`.

## Try it

```sh
# Replay a recorded run: a real model's answers (Claude Sonnet 5.5), for repairs and negotiations, free
python3 pricing-assistant/pricing_assistant.py --sample --replay pricing-assistant/sample-data/recorded-run.json --autonomous

# The offline stand-in, with simulated negotiations
python3 pricing-assistant/pricing_assistant.py --sample --dry-run --negotiate --autonomous

# Without --autonomous, each negotiation stops at one drafted reply for a person

# Real customers' replies (Quote, From, Message, Offer): one checked draft each, no simulator
python3 pricing-assistant/pricing_assistant.py --sample --dry-run --replies pricing-assistant/sample-data/customer-replies.csv
```

Then open `out/dashboard.html`, or `out/summary.md` for the counts. With the sample, `out/score.md` scores the run against the answer key. If a replay asks for something the recording doesn't have, the item goes to a person and the summary says "N items had no recorded answer".

## The sample: Summit's pricing

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_pricing.py`):
- **`price-book.csv`:** each part's cost (from supplier bills, July to September 2025) and list price (from invoices).
- **`rates.csv` and `tasks.csv`:** labor and trip rates, and flat-rate hours (the median hours technicians logged on one-part repairs).
- **`sales-guidance.md`:** fictional, written the way a sales manager would.
- **`repair-requests.csv` and `unit-history.csv`:** 20 real September repairs, and recent repairs to the same units. `Parts used` is the part on the job record (optional: when it's there, code checks the task against it; the AI never sees it).
- **`customer-replies.csv`:** three made-up customer replies, to try `--replies`.
- **`replacement-quotes.csv`:** 8 open replacement quotes, with cost (55% of list, from the simulation's brief) and a floor (cost ÷ 0.75, a fictional 25% minimum margin).
- **`buyer-simulator/buyers.csv`:** each buyer's style and hidden ceiling, from the simulation's hidden price sensitivity. Only the simulator reads it.
- **`repair-answer-key.csv`:** the right task and clauses for each repair, worked out independently.

## Before you run this on your own data

- **Prices and dates must be plain.** Prices like `64.30` or `$1,539.30` and dates like `2025-09-05` or `9/5/2025` (month first) are read. Anything else (`1.539,30`, `5 Sept`, `N/A`, zero or negative) isn't guessed: that price book row isn't used, and the repairs or quotes that depend on it go to a person. An unreadable labor or trip rate stops the run.
- **An install year must be four digits.** `unknown` or blank means the age is unknown, so the "over 15 years" replacement offer can't fire on age alone (R-22 still triggers it).
- **The agreement tiers are Summit's.** `none`, `full`, `pm_labor`, `pm_only`, in any capitals; any other tier goes to a person. Yours will differ: change `AGREEMENTS` and `CLAUSES`, and the guidance, together.
- **The task check is only as good as the job record.** Without a `Parts used` column, the only check that the task is right is that the quoted words name its part. Jobs with several parts aren't priced as more than one task.
- **The promise check is deliberately blunt.** Any mention of a warranty, a guarantee, "free", "no charge", a date or years of cover goes to a person, including true statements like "the manufacturer's warranty". Expect a person to read many replies at first; widen the allowed phrasings in `CONCESSION_WORDS` only on purpose.
- **Prices written some ways aren't read, they're stopped.** Percents, fractions, number words and unfamiliar formats in a reply go to a person. Ranges ("$15–16k") and amounts in a currency other than dollars aren't understood.
- **The impersonation check matches wording, not identity.** "Summit's sales manager approved…" is caught; a forged email from a real colleague's address isn't. Approvals should come through your own systems, never through the customer's thread.
- **Replies are one CSV, by hand.** `--replies` takes the thread for each quote as rows; connecting it to your mailbox or CRM is yours to build, and it must stay drafts-only.

## Files

| File | What |
|---|---|
| `pricing_assistant.py` | Pricing, negotiation, the checks, the simulated buyers, the outputs. |
| `pricing_dashboard.py` | The dashboard. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `sample-data/` | Summit's price book, guidance, requests, quotes, sample customer replies, answer key and recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
