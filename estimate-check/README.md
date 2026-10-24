# Estimate check

A spec check before each bid goes out. An AI reader reads the whole project manual and its addenda and lists every requirement that costs the mechanical contractor money, each with its words quoted and its status (in the base bid, an alternate, by others, doesn't apply, deleted by an addendum). Code checks every quote is really there; an AI checker judges each requirement again from only the sections it cites, and anything the two read differently, or the checker finds unclear, goes to the chief estimator. Code then checks the estimate prices each requirement, prices what's missing from the company's own completed jobs, and compares each estimator's labor with how their past jobs came out. The estimator decides. Nothing here changes an estimate or sends anything.

The full playbook, worked through at Halden Mechanical (a simulated commercial mechanical subcontractor in Columbus, Ohio) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/estimate-check/**

## What it does

For each estimate when it's marked ready, and again for each addendum issued after that:

1. **Gathers the bid** (code): the manual's sections and the addenda issued so far, the estimate by cost code, its labor rate.
2. **Reads the documents** (AI): one read of the whole manual, then one read of each later addendum against the list so far. Fifteen kinds of requirement: an independent TAB agency, commissioning support, seismic restraints, an extended warranty, a named manufacturer, an insulation upgrade, night or phased work, prevailing wage, a bond, BIM coordination, controls, water treatment, temporary heat, an IAQ flush-out, firestopping.
3. **Checks the reading** (code, then the AI checker). A requirement passes code's check only if its quote is found word for word (six words or more) in the section or addendum it names, its kind is on the list, and a status other than base bid quotes its own words. A deletion must quote an addendum. A section with text addressed to an AI can't supply a downgrade, and the text is reported. Then each requirement that passed goes to the model again, as the checker, with only the sections and addenda it cites (never the rest of the manual, nothing from the estimate), asked a different question: is it really that kind, what is its status, and is that clear? Code compares the two. A different kind or status, one the checker says isn't real, or one it finds unclear goes to the chief estimator with both readings and the checker's reason. An answer from the checker that can't be used accepts nothing from that read. At most 80 calls a working day (a read and its check).
4. **Checks the estimate** (code): a line on the requirement's cost code with an amount, or a line whose description names it; for prevailing wage, a labor rate 20% over the month's usual or a prevailing wage line; for a named manufacturer, the equipment line names it and doesn't say "or equal"; for upgraded insulation, the insulation line names the thickness or jacket. What isn't priced is a gap. Work priced that the documents give to others, or that an addendum deleted, is "priced but not required".
5. **Prices each gap** (code): the median cost of that kind of requirement as a share of base cost on completed jobs before the bid date, of the same building type when there are eight or more, otherwise all types, with the quartiles as a range.
6. **Checks the labor** (code): for each system, an estimator's median actual-to-estimated hours over the last three years against the company's, flagged when it runs 5% or more over on at least 65% of 12 or more of their jobs.
7. **Writes** `dashboard.html` (the year's bids with the most to add), `reviews.csv`, `gaps.csv`, `runs.csv`, and with an answer key `score.md`.

## Try it

```sh
python3 estimate-check/estimate_check.py --sample --dry-run      # no AI: a keyword stand-in reads
python3 estimate-check/estimate_check.py --sample --replay estimate-check/sample-data/recorded-run.json
python3 estimate-check/estimate_check.py --data estimate-check/holdout-2023 --replay estimate-check/holdout-2023/recorded-run.json
ANTHROPIC_API_KEY=... python3 estimate-check/estimate_check.py --sample
python3 -m pytest estimate-check
```

Standard library only. A real read of one manual (about 35,000 words) takes about half a minute.

## The sample

Every bid Halden submitted in one year (342, the simulation's 2024), with each project manual's full text and its addenda, the estimates by cost code, and the jobs completed by then for history (`records/`). The answer key (`answer-key/`) holds every requirement-like clause, its status, its true cost and whether the estimate priced it; each bid's true cost and every competitor's bid; and each estimate's true labor hours. One manual carries a line addressed to an AI.

## Results

With the AI checker, frozen at commit bf7bf0d before the second held-back bids were generated:

| Measure | Limit | Sample year (342 bids) | Held back (40 bids, 2023) |
|---|---|---|---|
| Missed requirements found as gaps, share of their cost | at least 80% | 91% (212 of 222, $1,766,472 of $1,949,563) | 95% (12 of 13, $139,091 of $146,653) |
| The rest: sent to the chief estimator with the clause, or missed silently | | 10 sent, 0 silent | 0 sent, 1 silent ($7,562) |
| Wrong gaps a bid | at most 0.35 | 0.03 | 0.03 |
| Gaps not in the documents | at most 1 | 0 | 0 |
| Priced but not required, wrong | 0 | 0 (15 right of 17) | 0 (3 of 3) |
| Clauses sent to the chief estimator, a bid | at most 0.5 | 0.44 | 0.23 |
| Readings that failed | 0 | 0 | 0 |

**The held-back test.** 40 bids due in 2023, chosen at random by code (seed 2023), rendered in wording written after the freeze (the simulation's `sim/text_heldout2.py`, a construction manager's bid-package voice the code had never seen), with a new line addressed to an AI. Recorded once and scored once (`holdout-2023/score-at-bf7bf0d.md`). Every threshold was met. The line addressed to an AI was caught by the AI reader; code's own pattern didn't match the new wording, which is why both look. The pass mark for clauses sent to a person was added with the checker, before the sample was recorded with it; every earlier threshold is unchanged (`release-thresholds.json`).

**The one silent miss** was a controls requirement in the base bid. Both AI calls read it right; code then counted the equipment line "Johnson Controls or equal" as a controls line, because the words that mark a controls line include "control". It's a bug in the estimate check, not the reading, and it's left in: the code is frozen, and a fix needs a new held-back set.

**What the checker changed.** Before it (code checks only, frozen at 40e5098), the sample year found all 222 missed requirements but carried 0.19 wrong gaps a bid, 3 of them for requirements not in the documents; on 40 held-back bids due in 2025, all 19, with 0.03 wrong gaps a bid. That held-back result stands as scored (`holdout-2025/recorded-run.json`, from that code). With the checker, wrong gaps on the sample fell to 0.03 a bid and none are outside the documents. Most of what it stops are conditions read as requirements ("provide seismic restraints where required by the building code", a bond the Owner "reserves the right to require"), which now reach the chief estimator as a question instead of the estimator as a cost. A rule in code that checked a status's quoted words against a word list is gone: that judgment is the checker's.

**Developing the checker on the 2025 bids.** Those 40 bids had been scored once already, so they were used as development data for the checker. Its first run (`holdout-2025/dev-checker-run.json`) sent 80 clauses to a person: the prompt defined "real" as a requirement on the mechanical contractor, so the checker rejected clauses the reader had rightly called by others or doesn't apply. The prompt now asks whether the words are about that kind of requirement, whatever its status, and states the reading conventions an estimator uses (a specific requirement governs a general one; a Division 22 or 23 instruction is the mechanical contractor's). The second run (`dev-checker-run-2.json`): 18 of 19 found as gaps, the other sent to a person, 14 clauses to a person in all. Then the sample was recorded, the code froze, and the 2023 bids were generated.

**A fix after the first held-back test.** Reviewing the sample after that test, we found that a named manufacturer's premium and an insulation upgrade were priced from past jobs' whole equipment and insulation lines, so seven gaps were priced at $1.8 million (their true cost was $37,000). They're now priced by a rule, a share of the estimate's own line (8% and 45%), with a test. The fix touches pricing only, not the reading.

**Pricing the gaps in.** Pricing each bid again with every gap added (and markup), against the same competitors and the same general contractor's choice, the sample year's margin goes up by $334,000 (by $390,000 with the labor flags too): better prices on jobs Halden won anyway, less six jobs that went to a competitor. On a 40-bid test year a couple of flipped jobs decide it: in 2023, two jobs that were profitable even with their misses would have gone to a competitor, and the margin goes down by $573,000. The check tells the estimator what the documents require and what it costs; how much of it to carry is a pricing decision. The labor flags are right about the direction four times in five, but add little to the margin.

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
| `holdout-2025/` | The first 40 held-back bids: exports, answer key, the recorded run scored once at 40e5098 (before the checker), and the checker's two development runs |
| `holdout-2023/` | The second 40 held-back bids: exports, answer key, the recorded run, and its score at bf7bf0d |
| `templates/` | A design, a pass mark, an answer key and a go-live checklist to fill in for your own version |
