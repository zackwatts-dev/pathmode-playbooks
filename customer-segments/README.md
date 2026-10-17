# Customer segments

Groups customers by how they actually behave, tests whether anything about them can be predicted, and lists the customers likely to pay late next year, with reasons. Machine learning does the finding; the AI does the explaining; every prediction has to beat a one-line rule before anyone trusts it.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/customer-segments/**

## What it does

- **Features** from two years of records up to a cutoff date, and nothing after it, for customers who existed at the cutoff:
  - spend and trend;
  - jobs per site, and the repair, repeat-visit and slow-job shares;
  - days since the last job;
  - days late on invoices due in the last 12 months (an invoice still unpaid at the cutoff counts by the days since it was due);
  - whether they have any decided quotes, and if so their approval rate and speed;
  - agreement coverage, sites and tenure.
  - Only events dated on or before the cutoff count: a job completed after it was still open, a quote decided after it was still waiting.
  - A value a customer doesn't have stays empty: no decided quotes means no approval rate, not a made-up 50%. Averages leave those customers out and say how many.
- **Segments:** k-means, with the number of segments chosen by silhouette score.
- **Predictions, tested:** for "who'll pay more than 20 days late next year?" and "who'll leave next year?":
  - a logistic regression trained on 70% of customers and tested on the other 30%;
  - compared with a one-line rule on the same customers;
  - the verdict: the model, the rule, or "not predictable from these records".
  - "who'll leave" is only tested and reported: nobody is listed or scored for it.
- **The late-payment list:** everyone ranked with the method that won, by a score for ranking (not a probability). When the model wins on the sample, each customer's score comes from cross-validation, so no customer is scored by a model that saw their outcome. If the verdict is "not predictable" or "not enough examples", there's no list.
- **The AI** names each segment and suggests how to treat it, and explains each customer on the late-payment list, from their numbers only. The AI never sees names or contact details. Code checks:
  - every number is one it was shown, and of the right kind ("$5k" must be a spend, "88 days" a day count, "40%" a share; no calendar years);
  - every direction ("faster", "higher", "slow-paying"), in the segment's name and description, against the segment's averages and all customers';
  - talk of bankruptcy, fraud, lawsuits or ending the relationship.
  - Words that fail go to a person, and the dashboards show them as held, not as ready.
- **Two sets of files:** for the team, `dashboard.html` (segments and the tested predictions; the map names no one), `segments.csv`, `customers.csv` (segments and features, with no late-payment measure) and `review-queue.csv`. For billing only, in `billing/`: `dashboard-billing.html`, `customers.csv` (with days late), `late-payment-list.csv`, `late-scores.csv` and `review-queue.csv`.

## What it doesn't do

Change anyone's terms, send anything, or decide anything about a customer.

## Try it

```sh
pip install --require-hashes -r customer-segments/requirements.txt   # scikit-learn, pinned and hash-checked

# Replay a recorded run: a real model's explanations (Claude Sonnet 5.5), free
python3 customer-segments/customer_segments.py --sample --replay customer-segments/sample-data/recorded-run.json

# The offline stand-in: no model at all
python3 customer-segments/customer_segments.py --sample --dry-run
```

## The sample: Summit's customers, 2023 and 2024

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_segments.py`): 1,207 customers active at the end of 2024, with their sites, agreements, jobs, quotes, invoices and payments for 2023 and 2024.

The answer keys come from the simulation's hidden truth, never from the exports:
- each customer's hidden behavior (how late they really pay, how price-sensitive they are);
- who paid more than 20 days late in 2025;
- who left in 2025.

## Without an answer key (a real company)

A real company has no answer key, so the predictions learn from history: features as they stood a year before the cutoff, and what happened in the year after (paid more than 20 days late on average; no job or invoice at all, for "left"). They're tested on 30% of last year's customers, and the winner scores this year's. That's the default when there are no answer-key files; `--from-history` does it on the sample too, where the 2025 answer key then only scores the list.

On the sample, learned from 2024, the late-payment rule wins again (0.94 against 0.94; 20 of the top 25 against the model's 19), and 25 of the top 25 on the list paid more than 20 days late in 2025. "Who'll leave" says "not enough examples": the sample holds only customers still active at the end of 2024, so it has almost no one who left in 2024. A real company's exports include its former customers.

## Before you run this on your own data

- **Column names are Summit's.** Map your exports to these files and headers (`customers.csv` with `Since`, `invoices.csv` with `Due`, and so on); nothing guesses at other names.
- **Amounts** are read as plain numbers or as `$1,225.42` and `(12.50)`. Anything else (words, ranges, other currencies) isn't read: the row is left out and listed in `review-queue.csv`.
- **A decided quote with no decision date** is left out and listed, not guessed at. Quote statuses other than Accepted, Declined and Sent aren't understood.
- **Sites carry no date** in most exports, so a site counts once a job or an agreement on or before the cutoff shows it existed (or by its own `Added`/`Created` date, if your export has one). A site with no activity at all isn't counted.
- **Exports taken after the cutoff:** jobs completed and quotes decided after it are treated as still open, but a status that was changed without a date (a cancelled job, a merged customer) can't be undone. Export as close to the cutoff as you can.
- **"Left" has no date in the records,** so it means no job or invoice for a year. Your exports must include former customers, or "who'll leave" can't be tested.
- **The direction check reads plain comparisons** ("faster than", "lower repair share", "slow-paying"). A claim worded another way ("rarely on time") isn't caught; a person still reads the segment names before they're used.
- **The recorded run belongs to the sample as it was recorded.** Change the features or the data and re-record: answers that no longer fit are caught by the checks or counted as "no recorded answer", but nothing replaces them.

## Files

| File | What |
|---|---|
| `customer_segments.py` | Features, segments, the tested predictions, the AI's explanations and their checks. |
| `segments_dashboard.py` | The two dashboards, with a 2D map of the customers. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `requirements.txt` | scikit-learn and its dependencies, pinned by version and hash. |
| `sample-data/` | Summit's exports, the answer keys and the recorded run. |
| `tests/` | Tests that run offline: leakage (events planted after the cutoff change nothing; the answer keys are never read for features), sanity (segment sizes; made-up data where the right verdict is known), the checks, and the recorded run. `pytest` from the repository root. |
