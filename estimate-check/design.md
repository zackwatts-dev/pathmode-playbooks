# Design: an estimate check for Wendlow Fabrication & Machine

## The problem

Our quotes are priced from the shop's hour standards, through each estimator's eye. Some kinds of work take longer than we quote: weldments especially, where the welding runs well over what the standards say. We find out after the job, when the hours are clocked, and by then the price is agreed. Because we win most often where we're cheapest, the jobs we underquote are the ones we win. About 80 new-part quotes a month go out, and nobody has time to compare each one with what similar work actually took.

## What it does

For every quote line waiting to go out:
1. **Find comparable finished work** (plain code, no AI). For each work center on the line, take operations at the same work center, on parts of the same family and material, in a similar quantity band, finished in the last three years and **before the quote was prepared**, and only from **the first time each part was made** (`run_number` 1). These are new parts, and repeat jobs run faster as the floor learns, so comparing with repeats would make light quotes look fine. Need at least 20. If there aren't enough, drop the material and quantity conditions and try again; if there still aren't 20, the line gets "not enough history".
2. **Work out what history says** (code). For each work center: the median of clocked hours over estimated hours across the comparable operations, and the hours the line would take at that ratio. Then the labor cost both ways at the shop rates.
3. **Sort the line** (code):
   - **check this:** history says the line's labor runs at least 10% over the estimate. Show the work centers that drive it, the suggested hours, the dollar gap, and the evidence (how many operations, from when).
   - **may be priced high:** history says the line's labor runs at least 15% under. We may be losing work we could win. For information; it doesn't hold the quote.
   - **looks right:** neither.
   - **not enough history:** a person checks it.
4. **Write the note** (AI). For each quote with a line to check, an AI model (OpenAI's API) writes a short note to the estimator in plain English from the evidence code computed. Code then checks every number in the note appears in that evidence. A note that fails the check is replaced by a plain one code writes. The AI sees the evidence and nothing else.
5. **A one-page HTML dashboard:** the count in each pile; the lines to check first, largest dollar gap first, with their notes; the same by estimator and by part family; the total labor the quotes would under-recover if sent as they are.

It's decision support. The estimator decides, and the tool never changes a quote.

## Inputs

All exported from our ERP and shop-floor system:
- `quotes-to-check.csv`: quote lines waiting to go out (customer, estimator, part, family, material, quantity, price).
- `quote-hours.csv`: each line's setup and run hours by work center.
- `job-history.csv`: finished operations with estimated and clocked hours (first-time work, not rework), and which run of the part each job was (1 for its first).
- `shop-rates.csv`: the hourly rate for each work center.
- `answer-key.csv`: for the test month, whether each line was really light (the work took 10% or more labor than estimated), from information the shop only has later.

## What "correct" means

- The answer key defines it. Every run is scored against it.
- Mistakes aren't equal. **A light line marked "looks right"** is the worst: we send a price that loses money and probably win the job. **A line flagged that was fine** costs the estimator a few minutes. **Not enough history** goes to a person and counts as neither.
- No hindsight: a test proves no operation finished on or after the quote's date is used.
- Every rule above has a test. Tests run without calling the AI, so they're free and repeatable.

## Security

- **Access:** read-only, to the exported files. It can't change the ERP, a quote or a price.
- **Credentials:** from the environment or a secret store, never in the code.
- **The AI** gets the computed evidence for one quote and nothing else: no files, no tools, no customer contacts. Its note only counts once code has checked it.
- **Everything shown is escaped** on the dashboard.
- **No third-party packages:** Python's standard library only.

## How it runs

- Each evening, over the quotes saved that day but not yet sent, on a server we control. Estimators see the dashboard first thing.
- At most 100 notes to the AI per run. Over the limit, the lines are still sorted; the notes are code-written.
- Nothing is silently dropped. A line with hours for a work center we have no rate for, or with no hours at all, goes to a person.
- Every run adds a line to a log: when, which model, how many lines, how many in each pile.
- Only the estimating team and the general manager see the output.
- After any change, including a new model version or new hour standards, re-run the answer key before going live.
