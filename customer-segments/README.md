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

In production you'd train each prediction on last year's outcomes, then score this year. The sample uses held-out customers instead, so the answer key can test it.

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
