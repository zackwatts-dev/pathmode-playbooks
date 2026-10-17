# Pricing assistant

Prices a repair in minutes from a technician's diagnosis, and negotiates a replacement quote within limits. The AI reads and writes; code does the math and holds the lines.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/pricing-assistant/**

## What it does

**Price a repair.** The AI reads the diagnosis and picks the task from the flat-rate book, quoting the words. It reads the written sales guidance and picks the clauses that apply. Code checks both:
- the task must exist and fit the unit;
- every clause's condition must hold;
- a rule the code can see for itself, but the AI missed, goes to a person.

Then code works out the price. The AI never writes a number into a price.

**Negotiate a replacement.** The AI writes each reply, trading before discounting. Code holds the lines:
- never below the floor (the AI never sees it);
- never beyond the estimator's 5% authority;
- no more than 2% off a round, and never back up;
- only the concessions the guidance allows, and none of the promises it forbids;
- no cost or floor in a message, and the price in the message must be the offer.

A customer who tries to instruct the assistant, or wants more than the authority allows, goes to a person.

## What it doesn't do

Send anything. By default every negotiation reply is a draft for a person (`--drafts`). It only bargains on its own against the simulated buyers in `sample-data/buyer-simulator/`.

## Try it

```sh
# Replay a recorded run: a real model's answers (Claude Sonnet 5.5), for repairs and negotiations, free
python3 pricing-assistant/pricing_assistant.py --sample --replay pricing-assistant/sample-data/recorded-run.json

# The offline stand-in, with simulated negotiations
python3 pricing-assistant/pricing_assistant.py --sample --dry-run --negotiate
```

Then open `out/dashboard.html`. With the sample, `out/score.md` scores the run against the answer key.

## The sample: Summit's pricing

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_pricing.py`):
- **`price-book.csv`:** each part's cost (from supplier bills, July to September 2025) and list price (from invoices).
- **`rates.csv` and `tasks.csv`:** labor and trip rates, and flat-rate hours (the median hours technicians logged on one-part repairs).
- **`sales-guidance.md`:** fictional, written the way a sales manager would.
- **`repair-requests.csv` and `unit-history.csv`:** 20 real September repairs, and recent repairs to the same units.
- **`replacement-quotes.csv`:** 8 open replacement quotes, with cost (55% of list, from the simulation's brief) and a floor (cost ÷ 0.75, a fictional 25% minimum margin).
- **`buyer-simulator/buyers.csv`:** each buyer's style and hidden ceiling, from the simulation's hidden price sensitivity. Only the simulator reads it.
- **`repair-answer-key.csv`:** the right task and clauses for each repair, worked out independently.

## Files

| File | What |
|---|---|
| `pricing_assistant.py` | Pricing, negotiation, the checks, the simulated buyers, the outputs. |
| `pricing_dashboard.py` | The dashboard. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `sample-data/` | Summit's price book, guidance, requests, quotes, answer key and recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
