# Design: customer segments for Summit Mechanical

## The problem

Summit treats its 1,200 customers by the labels in its system (national chain, property manager, single site), not by how they behave. Some pay late every time; some approve every quote; some call constantly and spend little. Nobody can see the groups, so every customer gets the same terms, the same reminders and the same sales approach. And every few months someone suggests "AI to predict which customers will leave", and nobody knows whether that would work.

## What it does

1. **Features.** For each customer, from two years of records up to a cutoff date, and nothing after it:
   - spend and how it's trending;
   - jobs per site, and the share that were repairs, repeat visits or slow;
   - days since their last job;
   - how late they paid on invoices due in the last 12 months (counting any still unpaid);
   - whether they have decided quotes, and if so how often they approve and how long they take (no quotes: no value, not a made-up one);
   - how many sites, how much is under agreement, and years as a customer.
2. **Segments.** k-means clustering groups customers by behavior. The number of groups is chosen by how well they separate (the silhouette score), not by hand.
3. **Predictions, each tested before it's trusted.** For each question ("who'll pay more than 20 days late next year?", "who'll leave next year?"):
   - a logistic regression is trained on 70% of customers and tested on the other 30%;
   - on the same 30%, it's compared with a one-line rule;
   - the verdict is the model, the rule, or "not predictable from these records";
   - without an answer key, the examples come from history: features as they stood a year before the cutoff, and what happened in the year after;
   - only the late-payment question produces a list, and only if the verdict is the model or the rule. "Who'll leave" is tested and reported, and nobody is scored for it.
4. **The AI explains.** It names each segment, says who's in it and how to treat them, and explains each customer on the late-payment list, using only the numbers it's given. Code checks every number and what it measures, and every "higher", "faster" or "slow-paying" against the data.
5. **Two dashboards:** for the team, a 2D map of the customers by segment (no names), the segments with their treatment, and the tested predictions with their verdicts; for billing, the same plus the late-payment list.

## Inputs

Exports for two years up to the cutoff: customers, sites, agreements, jobs, quotes, invoices and payments. Answer keys (from the simulation only): each customer's hidden behavior, who paid late in 2025, and who left in 2025. A real company has none, so its predictions learn from the year before.

## What "correct" means

- **Segments:** they line up with real differences in behavior the system doesn't record (the hidden answer key).
- **Predictions:** they beat a simple rule on customers the model never saw. If they don't, use the rule, or say it can't be predicted.
- **No leakage:** no feature uses anything after the cutoff, or the outcome it predicts. Only customers who existed at the cutoff, and only events dated on or before it.
- Every number in the AI's words comes from the data.

## Security and privacy

- **Customer data stays on Summit's server.** The AI sees only averages for segments, and one customer's numbers at a time for the list: no contacts, no addresses.
- **Lists of customers labelled "likely to pay late" are sensitive.** Only billing sees them, and the scores behind them: they're written to a billing-only folder. The team's map and files name no one on the list.
- **Pinned packages:** scikit-learn and its dependencies, by exact version and hash.

## How it runs

- Quarterly, after the books close.
- Segments and predictions are re-tested every run. If a prediction stops beating the rule, the dashboard says so.
- A log line every run.
