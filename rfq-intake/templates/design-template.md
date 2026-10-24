# Design: quote intake for [your business]

Fill in each section in plain words before any AI writes code. Keep it to a page or two. Wendlow's finished design is in this folder's parent (`design.md`) as an example.

## The problem

- Where requests for quotes arrive (which mailbox, about how many a week):
- What they're usually missing (quantity, version, drawing, specification, something else):
- How the inbox is worked today (who reads it, how often, how long each request takes to type in):
- What it costs (requests lost because the quote came too late, a year):

## What it does

The four parts, in your terms:

1. **The AI reader** reads each email and its attachments and pulls out: [the customer, each item, its version, quantity, dates, ...], copying the exact words each came from.
2. **The AI checker** checks every value against the email, and flags anything unclear or left out.
3. **IT integration** matches each request to your records: [customer list, items on file, open requests, history], exported from [your business system].
4. **A person approves.** People send every question and every quote.

What comes out:

- the piles: ready to quote, needs information (question drafted), needs a person (with the reason), not a request;
- [an import file for your business system / a list / a dashboard];
- [anything else: history for repeat items, the order to price them in, requests at risk of missing their date].

## What "correct" means

- The answer key: [which month or two of email, labeled by whom].
- The mistakes, worst first: let through but wrong; sent to the wrong place; stopped but needn't have been.
- The pass mark: see `pass-mark.md`, written before anything is scored.

## Security

- Access: read-only, to [the one mailbox]. It can't send, move or delete email.
- The AI gets the email and nothing else. Your records stay in your systems.
- Instructions inside an email are data, never orders, and send the email to a person.
- Credentials live in [your secret store], never in the code.
- What it never does: [send email, change the mailbox, write to the business system, price, decline].

## How it runs

- Where: [a server you control].
- How often: [every 15 minutes].
- Nothing silently dropped; a log line for every run.
- After any change, including a new AI model, score it against the answer key again.
