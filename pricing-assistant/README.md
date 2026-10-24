# Pricing assistant

A price on every equipment quote. An AI reads each quote request (an email, or the notes from a call) and lists each item with the words that ask for it. Code checks every item against the catalog, works out the agreed price, and suggests the extra discount with the most expected margin, from a win model trained on the distributor's own quotes. When the customer replies, the AI says what kind of reply it is and reads any competitor price; code decides to match, hold or ask the sales manager. The account manager decides and sends. Nothing here changes a price in the ERP or sends anything.

The full playbook, worked through at Hartwell Supply (a simulated twelve-branch HVAC/R distributor) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/pricing-assistant/**

## What it does

For each new quote request:

1. **Reads the request** (AI): each item with its words quoted, its quantity, and its part number or equipment details (maker, type, tonnage, SEER2, refrigerant) as written; any competitor price, deadline or job name.
2. **Checks the reading** (code). An item is accepted only when its words are found in the request, its quantity is a number standing alone in them (not part of "2.5 ton"), and it matches exactly one product. A detail counts only if the words say it, so the AI can't settle a match by adding one. No match, or more than one, becomes a question for the customer ("which refrigerant, R-410A or R-454B?"). Text addressed to an AI is reported and does nothing.
3. **Works out the agreed price** (code): list, less the customer's agreed discount, less the month's markdown.
4. **Suggests the extra discount** (code and statistics). A logistic win model, trained on the three years of quotes closed before that day (won, and lost on price; expired quotes and cancelled jobs are left out), gives the chance of winning at each extra discount from 0% to 5% from the customer's trade, size and past wins, the quote's size and how much of it is marked down. It suggests the one with the most expected margin. Clearance prices are final, so the extra applies to the other lines; no line goes below cost plus 5%; over 3% needs the sales manager.
5. **Writes a note** (AI) for the account manager, one sentence from facts code gives it. A note with any number that isn't one of the facts is replaced by a plain one.

For each reply: the AI reads its kind and any competitor price (the amount must be in the words it quotes). Code works out the extra discount that matches; it matches only within the account manager's 3% and only when that earns more expected margin than holding, offers the sales manager anything up to 5%, and holds otherwise. The AI drafts the answer with code's numbers.

It writes `drafts.md` (each request's lines, prices, suggestion, note and questions), `suggestions.csv`, `replies.csv`, `to-a-person.csv`, `runs.csv`, `dashboard.html`, and with an answer key `score.md`.

## Try it

```sh
pip install -r pricing-assistant/requirements.txt
python3 pricing-assistant/pricing_assistant.py --sample --dry-run      # no AI: a rule-based stand-in reads
python3 pricing-assistant/pricing_assistant.py --sample --replay pricing-assistant/sample-data/recorded-run.json
ANTHROPIC_API_KEY=... python3 pricing-assistant/pricing_assistant.py --sample
python3 -m pytest pricing-assistant
```

A run trains a win model for each month of the year and prices every quote in it, which takes about a minute.

## The sample

Hartwell's 2024, with the three years before it (`records/`): customers, products, the month's markdowns, sales by customer and year, and every quote with its lines (about 217,000 quotes). Forty requests and 25 replies, each written from one of 2024's real quotes and how it really ended (`requests/`, `replies/`). Six requests leave out a detail that two products differ by, so they need a question. One request carries a line addressed to an AI.

The answer key (`answer-key/`) holds what each request truly asks for, each reply's kind and competitor price, and for every quote of the year what only the simulation knows: the competitor's price, the customer's true sensitivity to price and whether the contractor's own job went ahead. The money test uses it: every quote of the year, priced at the suggestion and at what the account manager gave, both scored with the simulation's own chances of winning. A real company doesn't have those; it would prove the gain with a split trial, half its quotes priced the old way and half the new.

## Results

| Measure | Limit | Sample (2024) |
|---|---|---|
| Wrong items | 0 | 0 |
| Items found | at least 95% | 100% (87 of 87) |
| Questions that were needed, asked | at least 80% | 6 of 6 |
| Questions that weren't needed | at most 10% of requests | 0 |
| Text addressed to an AI, missed | 0 | 0 |
| Reply kinds right | at least 90% | 25 of 25 |
| Competitor prices in replies, wrong | 0 | 0 of 7 |
| Margin gained, points on won quotes | at least 0.5 | 1.09 ($670,754 on $61.5M) |

The thresholds (`release-thresholds.json`) were set after the sample was recorded and before the held-back year was generated. Of the gain, $404K is residential customers, who were given about 1.9 points extra and buy almost as often without it; the rest is mixed and commercial customers, priced closer to what wins them. With every customer's true sensitivity known, the most there was is $972,756.

## Files

| File | What it is |
|---|---|
| `pricing_assistant.py` | The pipeline: the reading and its checks, the agreed price, the win model, the suggestion, replies, scoring |
| `pricing_dashboard.py` | The dashboard |
| `design.md` | The design, one page |
| `plan.md` | The plan an AI wrote from it, unedited |
| `release-thresholds.json` | What counts as good enough, set before the held-back year was generated |
| `tests/` | Every rule and check, without calling the AI |
| `sample-data/` | The sample year: exports, requests, replies, answer key, recorded run |
