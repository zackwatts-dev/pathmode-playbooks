# Design: estimate check for [your business]

Fill in each section in plain words before any AI writes code. Keep it to a page or two. Halden's finished design is in this folder's parent (`design.md`) as an example.

## The problem

- What you bid from (project manuals, specifications, requests for proposal, statements of work), and about how long they run:
- How many bids a year, and by how many estimators:
- How a bid is checked today (who reads the documents, when, against what checklist):
- What it costs (requirements in the documents that the price didn't carry, a year, and when you found them):

## What it does

The four parts, in your terms:

1. **The AI reader** reads the whole set of documents and each addendum, and lists every requirement of [your kinds: a longer warranty, night work, a named brand, a bond, a third party you have to hire, ...], quoting its words and saying whose work it is.
2. **The AI checker** gets each requirement with only the sections it cites and judges it again: is it real, whose work is it, and is that clear?
3. **IT integration** connects to [your estimating system and job cost]: it checks the estimate line by line, prices each gap from your own past jobs, and compares each estimator's labor with how their jobs came out.
4. **A person approves.** The estimator decides what goes in the bid; [the chief estimator] reads anything unclear.

What comes out:

- a review for each bid: the gaps with their words and cost, work priced that isn't required, labor flags, and anything for a person;
- [a dashboard for the year / a page in the estimating share / a note on the estimate].

## What "correct" means

- The answer key: [which past bids, and who marked what was missed].
- The mistakes, worst first: a requirement that isn't in the documents; calling someone else's work yours; a missed requirement; a flag that wasn't needed.
- The pass mark: see `pass-mark.md`, written before anything is scored.

## Security

- Access: read-only exports from [document control, estimating, job cost]. It never changes an estimate.
- The AI gets one bid's documents and nothing from the estimate, the job history or other bids.
- Text in the documents addressed to an AI is data, never orders: it's reported, and can't remove or downgrade a requirement.
- Credentials live in [your secret store], never in the code.
- What it never does: [change an estimate, send anything, submit a bid].

## How it runs

- Where: [a server you control].
- When: [every 30 minutes, for estimates newly marked ready and addenda newly issued].
- Nothing silently dropped; a log line for every run.
- After any change, including a new AI model, score it against the answer key again.
