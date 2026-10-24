# Go-live checklist

## Before it runs for real

- [ ] It passed the pass mark on your own past bids, including the part held back (`pass-mark.md`).
- [ ] It runs on a server you control, on a schedule, with a log line for every run.
- [ ] Access to document control, estimating and job cost is read-only. Checked, not assumed.
- [ ] The AI key is in the server's secret store, nowhere else.
- [ ] The reviews land where only estimating can open them.
- [ ] Someone gets an alert if no run appears for a working day, or the pile sent to a person suddenly doubles.
- [ ] Today's numbers are written down: requirements found missed at buyout or in the field, a year, and what they cost.

## The first month: one estimator

- [ ] One estimator who wants it gets a review on every bid.
- [ ] They mark every flag real or not, and every clause sent to a person gets an answer.
- [ ] Each mark becomes a case in the answer key.
- [ ] Extend to the other estimators only when the marks have stayed clean for [a month of bids].

## After the switch

- [ ] Every bid: the estimator reads the review before the number is set.
- [ ] Every flag marked real or not; the running count of wrong flags kept.
- [ ] Monthly: wrong flags and clauses sent to a person read together. A new kind of clause? A spec writer whose wording keeps confusing it?
- [ ] Whenever the AI model or a prompt changes: score against the answer key again before it goes back into service.
- [ ] After six to twelve months: measure the same numbers as before go-live, and decide to keep it, extend it, or stop.
