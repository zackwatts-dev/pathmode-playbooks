# Queue replay inputs

Model input for a counterfactual quoting-queue model. The RFQ intake tool does not use these files.

`decision_date` is truth: the working day each buyer decided, from the simulation's truth database
(`rfq_truth.decision_day` mapped through `dim_date`). Nobody at Wendlow could see it. `outcome` and `quote_sent_on`
are what actually happened, for comparison with the replay.

## rfqs.csv

Every request the estimators had to price: the new-part RFQs and annual re-quotes received 2024-01-01 to
2024-12-31, plus those received earlier and not yet quoted on the morning of 2024-01-01 (`in_queue_on_start` = 1 if
already keyed into the ERP by then, 0 if still unread in quotes@). RFQs screened out in the window are included, with
outcome `screened out`: they were read and keyed, never priced. Screened-out RFQs from before the window are left out.

- `kind`: `new` (a buyer's RFQ for new parts) or `requote` (the annual price review of a repeat part, raised inside
  Wendlow when it reorders). The engine stops raising re-quotes while the backlog is over 2 weeks,
  so a replay with a shorter queue would see more of them than these.
- `tier`: key, regular or occasional. Key accounts' new RFQs go to the front of the queue; everything else joins
  the back.
- `stated_due`: the date the buyer's email states, blank for the ~40% that state none and for re-quotes. A
  labeled stand-in (Assume), the same rule the mailbox uses, drawn per RFQ: 55% at the decision day or the working
  day before it; 30% padded, 2-5 working days before the decision; 15% late, 1-3 working days after the decision
  (the buyer awards once enough quotes are in). Never before the RFQ arrived.
- `stated_due_rule` (truth): which of the three it was (at decision, padded, late), blank where no date is stated.
- `decision_date` (truth, new RFQs only). A quote sent after it is too late.
- `lines`, `weld_family` (1 if any line is family 3, 4 or 6).
- `expected_quote_hours`: the deterministic part of the engine's `quote_hours`:
  0.6 x (1 + 0.3 x (lines - 1)) x 1.5 if weld_family x 0.3 for a re-quote, with complexity taken
  as 1 and no noise. The engine also multiplies by a lognormal(0, 0.5) draw (median 1, mean about 1.13), by the
  square root of the largest part complexity, and by 1.3 when a junior prices a weld-family request. The
  senior estimator in this window is Frankie Trimble; the 1.3 applies to the weld_family rows a junior prices
  (the engine gives the senior about 75% of them while he has hours).
- `quote_sent_on`: when the quote actually went out (blank if never).
- `outcome`: for new RFQs, from truth: won, lost, lost late, no award, screened out. For re-quotes, the status the
  ERP recorded: won (price accepted) or lost (the customer re-sourced the part).
- `missing`: what the request arrived without (revision, quantity or drawing), blank if nothing. At Wendlow this was
  found only when an estimator opened the request to price it; the question to the buyer went out then, and the
  request waited for the answer.
- `answer_days`: how many working days the buyer took to answer that question (from the mail log: the question out,
  the reply in). A replay asking on arrival uses the same buyer's same delay.

## capacity.csv

Estimator hours available per working day. Each estimator employed that day (`hr_employees`: hired_on <= day <=
terminated_on, since the engine lets a leaver work her last day) and not absent gives
4.5 hours if senior, 6.0 if junior (`ESTIMATOR_HOURS`).

- `absent`: inferred, because `hr_timecards` covers only the shop floor. An estimator counts as absent on a day she
  sent no quote at all (new or re-quote) while the queue held work; her hours that day are 0. A quote longer than a
  day's hours could also leave a day empty, which is rare at these sizes. With two estimators,
  a day without quotes can also be one where the other estimator held the head of the queue (the engine works the
  queue head first and stops when a quote is left half done), so treat inferred absences on two-estimator days as
  approximate.
- `helper_quotes`, `helpers`: quotes sent that day by sales or engineering staff (`erp_quotes.estimator_id`), and
  who. The engine brings in up to two helpers, 3.0 hours a day each, on any day the backlog is over
  2 weeks, where backlog weeks = queued quote hours / 10.5 / 5 (the
  two-estimator standard, whatever the actual staffing; a request not yet started counts 1.5 hours). Helpers'
  hours are not in `estimator_hours`.
- Past 3 weeks of backlog, occasional customers' new RFQs are declined (they show as screened out).
