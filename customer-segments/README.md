# Customer segments

Groups customers by how they actually behave, tests whether anything about them can be predicted, and lists the customers likely to pay late next year, with reasons. Machine learning does the finding; the AI does the explaining; every prediction has to beat a one-line rule before anyone trusts it.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/customer-segments/**

## What it does

- **Features** from two years of records up to a cutoff date, and nothing after it:
  - spend and trend;
  - jobs per site, and the repair, repeat-visit and slow-job shares;
  - days since the last job;
  - how late they pay;
  - quote approval rate and speed;
  - agreement coverage, sites and tenure.
- **Segments:** k-means, with the number of segments chosen by silhouette score.
- **Predictions, tested:** for "who'll pay more than 20 days late next year?" and "who'll leave next year?":
  - a logistic regression trained on 70% of customers and tested on the other 30%;
  - compared with a one-line rule on the same customers;
  - the verdict: the model, the rule, or "not predictable from these records".
  - "who'll leave" is only tested and reported: nobody is listed or scored for it.
- **The late-payment list:** everyone ranked by their chance of paying more than 20 days late next year, with the method that won. When the model wins on the sample, each customer's score comes from cross-validation, so no customer is scored by a model that saw their outcome.
- **The AI** names each segment and suggests how to treat it, and explains each customer on the late-payment list, from their numbers only. Code checks every number. The AI never sees names or contact details.
- **Two dashboards:** segments and the tested predictions for everyone (`dashboard.html`), plus the late-payment list for billing only (`dashboard-billing.html`).

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

On the sample, learned from 2024, the late-payment rule wins again, and 25 of the top 25 paid more than 20 days late in 2025. "Who'll leave" says "not enough examples": the sample holds only customers still active at the end of 2024, so it has almost no one who left in 2024. A real company's exports include its former customers.

## Files

| File | What |
|---|---|
| `customer_segments.py` | Features, segments, the tested predictions, the AI's explanations and their checks. |
| `segments_dashboard.py` | The two dashboards, with a 2D map of the customers. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `requirements.txt` | scikit-learn and its dependencies, pinned by version and hash. |
| `sample-data/` | Summit's exports, the answer keys and the recorded run. |
| `tests/` | Tests that run offline, including leakage checks: `pytest` from the repository root. |
