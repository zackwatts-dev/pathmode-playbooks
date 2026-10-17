# Design: customer segments for Summit Mechanical

## The problem

Summit treats its 1,200 customers by the labels in its system (national chain, property manager, single site), not by how they behave. Some pay late every time; some approve every quote; some call constantly and spend little. Nobody can see the groups, so every customer gets the same terms, the same reminders and the same sales approach. And every few months someone suggests "AI to predict which customers will leave", and nobody knows whether that would work.

## What it does

1. **Features.** For each customer, from two years of records up to a cutoff date, and nothing after it:
   - spend and how it's trending;
   - jobs per site, and the share that were repairs, repeat visits or slow;
   - days since their last job;
   - how late they pay;
   - how often they approve quotes, and how long they take;
   - how many sites, how much is under agreement, and years as a customer.
2. **Segments.** k-means clustering groups customers by behavior. The number of groups is chosen by how well they separate (the silhouette score), not by hand.
3. **Predictions, each tested before it's trusted.** For each question ("who'll pay more than 20 days late next year?", "who'll leave next year?"):
   - a logistic regression is trained on 70% of customers and tested on the other 30%;
   - on the same 30%, it's compared with a one-line rule;
   - the verdict is the model, the rule, or "not predictable from these records".
4. **The AI explains.** It names each segment, says who's in it and how to treat them, and explains each customer on the late-payment list, using only the numbers it's given. Code checks every number.
5. **A dashboard:** a 2D map of the customers by segment, the segments with their treatment, the tested predictions with their verdicts, and the late-payment list.

## Inputs

Exports for two years up to the cutoff: customers, sites, agreements, jobs, quotes, invoices and payments. Answer keys (from the simulation): each customer's hidden behavior, who paid late in 2025, and who left in 2025.

## What "correct" means

- **Segments:** they line up with real differences in behavior the system doesn't record (the hidden answer key).
- **Predictions:** they beat a simple rule on customers the model never saw. If they don't, use the rule, or say it can't be predicted.
- **No leakage:** no feature uses anything after the cutoff, or the outcome it predicts.
- Every number in the AI's words comes from the data.

## Security and privacy

- **Customer data stays on Summit's server.** The AI sees only averages for segments, and one customer's numbers at a time for the list: no contacts, no addresses.
- **Lists of customers labelled "likely to pay late" are sensitive.** Only billing sees them.
- **Pinned packages:** scikit-learn and its dependencies, by exact version and hash.

## How it runs

- Quarterly, after the books close.
- Segments and predictions are re-tested every run. If a prediction stops beating the rule, the dashboard says so.
- A log line every run.
