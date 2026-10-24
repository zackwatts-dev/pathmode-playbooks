# Pricing assistant

A price on every equipment quote. An AI reads each quote request (an email, or the notes from a call) and lists each item with the words that ask for it. Code checks every item against the catalog, works out the agreed price, and suggests the extra discount with the most expected margin, from a win model trained on the distributor's own quotes. When the customer replies, the AI says what kind of reply it is and reads any competitor price; code decides to match, hold or ask the sales manager. The account manager decides and sends. Nothing here changes a price in the ERP or sends anything.

The full playbook, worked through at Hartwell Supply (a simulated twelve-branch HVAC/R distributor) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/pricing-assistant/**

## What it does

For each new quote request:

1. **Reads the request** (AI): each item with its words quoted, its quantity, and its part number or equipment details (maker, type, tonnage, SEER2, refrigerant) as written; any competitor price, deadline or job name.
2. **Checks the reading** (code). An item is accepted only when its words are found in the request, its quantity is written in them or on the item's own line (never part of "2.5 ton"), and it matches exactly one product. Sizes, ratings, maker and refrigerant count only if the words say them (a tonnage only when written as one, "3 ton" or "3T"), so the AI can't settle a match by adding one. The kind of unit can come from the AI ("HP" is a heat pump) only with the customer's words for it cited and found. Anything that matches no product, or more than one, becomes a question for the customer ("which refrigerant, R-410A or R-454B?"). Two items run together become a question too. Any line naming a part number or a tonnage that the reading left out is read again, once; if it's still unread, it goes to a person by name. Text addressed to an AI is reported and does nothing.
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

| Measure | Limit | Sample (2024) | Held back: 2025 | 2023 | 2022 | 2021 | 2020 |
|---|---|---|---|---|---|---|---|
| Wrong items | 0 | 0 | 0 | 0 | **5** | 0 | 0 |
| Items found | at least 95% | 87 of 87 | **81 of 97** | **61 of 86** | **82 of 87** | 89 of 90 | 86 of 89 |
| Questions that were needed, asked | at least 80% | 6 of 6 | **1 of 6** | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |
| Questions that weren't needed | at most 10% of requests | 0 | **5** | **11** | 0 | 1 | 2 |
| Text addressed to an AI, missed | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Reply kinds right | at least 90% | 25 of 25 | 25 of 25 | 25 of 25 | 25 of 25 | 25 of 25 | 25 of 25 |
| Competitor prices in replies, wrong | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Margin gained, points on won quotes | at least 0.5 | 1.09 | 1.16 | 0.98 | 1.02 | 1.01 | 1.02 |
| The same, in dollars | | $670,754 | $734,644 | $538,604 | $701,030 | $751,910 | $728,034 |
| Code it was scored with | | | b28cb0b | bd5939c | 9f5ac0e | 510ae5b | 998aebf |

Bold is a release threshold missed. The thresholds (`release-thresholds.json`) were set after the sample was recorded and before any held-back year was generated, and never changed. Their note mentions only 2025, the first held-back year, because it was written then.

**Five held-back tests.** Each held-back year's requests, replies and answer key were generated after the code froze, in wording written after that, recorded once and scored once. Each kept its score (`score-at-<commit>.md`).

- **2025: failed.** Quantities written "x1" or "times 1." were rejected, and "AC unit" and "outdoor unit" weren't known as condensers.
- **2023: failed.** Contractor shorthand ("HP", "AH", "cond") became questions, and "410" and "454" without the letter weren't read as refrigerants.
- **2022: failed, with five wrong items.** "Heat pump condenser" was priced as a straight condenser: the AI had it right, and code's word check overruled it. Before running this year we had said its result would be final. After it failed, Hartwell's owner chose to fix it and test once more.
- **2021: passed.** Then an independent review of the code and the page found the checks weaker than the page claimed:
  - a tonnage could be borrowed from the quantity;
  - a quantity could be a tonnage's number;
  - a maker's name could pass as the customer's word for the unit;
  - a reply on a quote with clearance lines could restate a slightly different price;
  - a second read could price an item twice;
  - the drafts' markdowns came from a monthly schedule rather than the price file of the day.

  These were fixed with new tests and the code frozen again (998aebf), so 2021 no longer counts as untouched.
- **2020: passed** everything.

Every failure was in code's checks on the AI's reading, never in the reading itself or the price. Each fix came with a new test, and no earlier test changed. A held-back year that failed became development data: its requests were read again to check the fixes (not committed, since it no longer counts as a test). The quotes of 2021–23 were already in the sample's history files, with only their requests, replies and answer keys new. 2020's quotes aren't in the sample's files.

The margin gained held in every year, between 0.98 and 1.16 points. Most of it is residential customers, who are given about 1.9 points extra and buy almost as often without it. The rest is mixed and commercial customers, priced closer to what wins them. With every customer's true sensitivity known, the most there was is about $0.8 to $1.2 million a year, and the model gets about 60 to 75% of it.

## Files

| File | What it is |
|---|---|
| `pricing_assistant.py` | The pipeline: the reading and its checks, the agreed price, the win model, the suggestion, replies, scoring |
| `pricing_dashboard.py` | The dashboard |
| `design.md` | The design, one page |
| `plan.md` | The plan an AI wrote from it, unedited |
| `release-thresholds.json` | What counts as good enough, set before any held-back year was generated |
| `tests/` | Every rule and check, without calling the AI |
| `sample-data/` | The sample year: exports, requests, replies, answer key, recorded run |
| `holdout-2025/`, `holdout-2023/`, `holdout-2022/`, `holdout-2021/`, `holdout-2020/` | The five held-back years, each with its recorded run and its score at the code it was tested with |
