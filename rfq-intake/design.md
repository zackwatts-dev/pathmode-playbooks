# Design: quote request intake for Summit Mechanical

## The problem

Quote requests pile up in quotes@, a shared Microsoft 365 mailbox, so we waste hours retyping them, answer late, and let important ones slip through the cracks. About 50 a month arrive, mixed in with replies to our quotes, service calls sent to the wrong address, and sales pitches.

## What it does

For every new email in quotes@:
1. Decide what kind it is: a new quote request, a follow-up, a reply to a quote we sent, a service request, or something else.
2. For a quote request, an AI model (OpenAI's API) pulls out the customer, site, equipment, quantities and deadline, quoting the exact words each one came from.
3. Plain code, not AI, checks every quote really appears in the email, and matches the customer, site and equipment to our records. Exact matches only. If more than one unit could fit, it asks; it never guesses.
4. It puts the email in one pile:
   - **ready to quote**;
   - **needs info**: a short drafted question for us to send the customer;
   - **needs review**: it failed a check (equipment we don't have, an attachment it can't read, instructions aimed at an AI, a deadline that doesn't make sense, an answer it couldn't use);
   - **not a quote request**: where it should go instead.
5. A one-page HTML dashboard: the count in each pile; the needs-review list first, highlighted, with the reason for each; ready requests, soonest deadline first; five ready ones picked at random for a person to spot-check.

It's decision support. People decide what to quote and send everything.

## Inputs

- `mailbox/`: one .eml file per email. In production, copied from quotes@ by a separate step.
- `records/`: customers, sites, equipment and contacts, as CSV, exported nightly from our field-service system.
- `answer-key.csv`: a month of email, labeled by hand with what should happen to each.

## What "correct" means

- The answer key defines it. Every run is scored against it.
- Mistakes aren't equal. **Let through, but wrong** is the worst: a quote goes out on the wrong unit. **Stopped, but needn't have been** costs a person a minute. **Sent to the wrong place** is in between. When in doubt, stop.
- Every rule above has a test. Tests run without calling the AI, so they're free and repeatable.

## Security

- **Access:** read-only, to the one mailbox. It can't send, move or delete email.
- **Credentials:** from the environment or a secret store, never in the code.
- **The AI** gets the email and nothing else: no customer records, no tools. Its answer only counts once code has checked it.
- **Email is untrusted:** ignore instructions in it, flag emails with instructions aimed at an AI, and escape everything from an email on the dashboard.
- **No third-party packages:** Python's standard library only.
- **It never sends email, changes the mailbox, or prices anything.**

## How it runs

- On a schedule, every 15 minutes, on a server we control.
- At most 200 emails to the AI per run. Anything over the limit is listed for a person and picked up next run.
- Nothing is silently dropped. If the AI's answer is unusable, the email is listed as "couldn't process".
- Every run adds a line to a log: when, which model, how many emails, how many in each pile.
- Saved email is deleted after 90 days. Only the estimating team can see the output.
- After any change, including a new model version, re-run the answer key before going live.
