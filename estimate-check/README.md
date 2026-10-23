# Estimate check

A spec check before each bid goes out. An AI reads the whole project manual and its addenda and lists every requirement that costs the mechanical contractor money, each with its words quoted and its status (in the base bid, an alternate, by others, doesn't apply, deleted by an addendum). Code checks every quote is really there, checks the estimate prices each requirement, prices what's missing from the company's own completed jobs, and compares each estimator's labor with how their past jobs came out. The estimator decides. Nothing here changes an estimate or sends anything.

The full playbook, worked through at Halden Mechanical (a simulated commercial mechanical subcontractor in Columbus, Ohio) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/estimate-check/**

## What it does

For each estimate when it's marked ready, and again for each addendum issued after that:

1. **Gathers the bid** (code): the manual's sections and the addenda issued so far, the estimate by cost code, its labor rate.
2. **Reads the documents** (AI): one read of the whole manual, then one read of each later addendum against the list so far. Fifteen kinds of requirement: an independent TAB agency, commissioning support, seismic restraints, an extended warranty, a named manufacturer, an insulation upgrade, night or phased work, prevailing wage, a bond, BIM coordination, controls, water treatment, temporary heat, an IAQ flush-out, firestopping.
3. **Checks the reading** (code). A requirement is accepted only if its quote is found word for word (six words or more) in the section or addendum it names, its kind is on the list, and a status other than base bid quotes words that say so ("by the Owner", "where required", "delete"...). A deletion must quote an addendum. A section with text addressed to an AI can't supply a downgrade, and the text is reported. Anything that fails goes to the chief estimator.
4. **Checks the estimate** (code): a line on the requirement's cost code with an amount, or a line whose description names it; for prevailing wage, a labor rate 20% over the month's usual or a prevailing wage line; for a named manufacturer, the equipment line names it and doesn't say "or equal"; for upgraded insulation, the insulation line names the thickness or jacket. What isn't priced is a gap. Work priced that the documents give to others, or that an addendum deleted, is "priced but not required".
5. **Prices each gap** (code): the median cost of that kind of requirement as a share of base cost on completed jobs before the bid date, of the same building type when there are eight or more, otherwise all types, with the quartiles as a range.
6. **Checks the labor** (code): for each system, an estimator's median actual-to-estimated hours over the last three years against the company's, flagged when it runs 5% or more over on at least 65% of 12 or more of their jobs.
7. **Writes** `dashboard.html` (the year's bids with the most to add), `reviews.csv`, `gaps.csv`, `runs.csv`, and with an answer key `score.md`.

## Try it

```sh
python3 estimate-check/estimate_check.py --sample --dry-run      # no AI: a keyword stand-in reads
python3 estimate-check/estimate_check.py --sample --replay estimate-check/sample-data/recorded-run.json
python3 estimate-check/estimate_check.py --data estimate-check/holdout-2025 --replay estimate-check/holdout-2025/recorded-run.json
ANTHROPIC_API_KEY=... python3 estimate-check/estimate_check.py --sample
python3 -m pytest estimate-check
```

Standard library only. A real read of one manual (about 35,000 words) takes about half a minute.

## The sample

Every bid Halden submitted in one year (342, the simulation's 2024), with each project manual's full text and its addenda, the estimates by cost code, and the jobs completed by then for history (`records/`). The answer key (`answer-key/`) holds every requirement-like clause, its status, its true cost and whether the estimate priced it; each bid's true cost and every competitor's bid; and each estimate's true labor hours. One manual carries a line addressed to an AI.

## Results

| Measure | Limit | Sample year (342 bids) | Held back (40 bids, 2025) |
|---|---|---|---|
| Missed requirements found, share of their cost | at least 80% | 100% (222 of 222, $1,949,563) | 100% (19 of 19, $89,969) |
| Wrong gaps a bid | at most 0.35 | 0.19 | 0.03 |
| Gaps not in the documents | at most 1 | 3 | 0 |
| Priced but not required, wrong | 0 | 0 (15 right of 17) | 0 (1 of 1) |
| Readings that failed | 0 | 0 | 0 |

The thresholds were set and the code frozen (commit 40e5098) after the sample was recorded and before the held-back bids were generated. Those 40 were chosen at random by code (seed 2025) and written in new wording (the simulation's `sim/text_heldout.py`), with a new line addressed to an AI; both lines were caught and ignored. The sample's 100% is on wording the code was written against; the held-back result is the one to trust.

**A fix after the held-back test.** Reviewing the sample after the test, we found that a named manufacturer's premium and an insulation upgrade were priced from past jobs' whole equipment and insulation lines, so seven gaps were priced at $1.8 million (their true cost was $37,000). They're now priced by a rule, a share of the estimate's own line (8% and 45%), with a test. The fix touches pricing only, not the reading: both runs were re-scored from the same recorded answers, and nothing found or flagged changed. The sample's gaps are now priced at $1.84 million against $1.95 million true; the held-back bids' at $80,083 against $89,969.

**Pricing the gaps in isn't free.** Pricing each bid again with every flag added (and markup), against the same competitors and the same general contractor's choice, the year's margin moves by between -$469K and +$333K depending on how gaps are priced and whether the labor flags are used: a handful of jobs flip to a competitor, and in this simulation most of them stayed profitable even with the miss. The check tells the estimator what the documents require and what it costs; whether to carry it is a pricing decision. A keyword search in place of the AI finds almost as many misses but calls everything required, and on the same replay loses $465K. The labor flags are right about the direction four times in five, but add nothing to the margin here.

## Files

| File | What it is |
|---|---|
| `estimate_check.py` | The pipeline: the reading and its checks, the estimate check, pricing from history, labor, scoring |
| `estimate_dashboard.py` | The dashboard |
| `design.md` | The design, one page |
| `plan.md` | The plan an AI wrote from it, unedited |
| `release-thresholds.json` | What counts as good enough, set before the held-back bids were generated |
| `tests/` | Every rule and check, without calling the AI |
| `sample-data/` | The sample year: exports, answer key, recorded run |
| `holdout-2025/` | The 40 held-back bids: exports, answer key, recorded run, scored once with the code frozen |
