# Design: supplier agreements for [your business]

Fill in each section in plain words before any AI writes code. Keep it to a page or two. Hartwell's finished design is in this folder's parent (`design.md`) as an example.

## The problem

- Which suppliers have agreements that pay you back, and about how much you buy from them a year:
- What the agreements pay (volume rebates, growth, product-line incentives, co-op or marketing funds, prepaid freight, stock rotation, price protection, ...):
- Where the agreements live (contracts, program sheets, terms pages, amendment letters, reps' emails):
- How the year-end statements are checked today, and by whom:
- What it costs (money earned and not received, co-op that expired, returns left unused, a year):

## What it does

The four parts, in your terms:

1. **The AI reader** reads every agreement, amendment, program sheet and email for one supplier at a time, and returns each term with the exact words it came from, and the supplier's statement line by line.
2. **The AI checker** gets each kind of term with only the document it cites, never the reader's answer, and reads it again. Code compares the two readings on every field the money depends on.
3. **IT integration** connects to [your ERP, accounting and warehouse exports]: it works out what each supplier owes from your own invoices, returns, claims and stock, and compares it with the statement and the claims you've filed.
4. **A person approves.** [Purchasing] reviews every claim and sends it; [who] decides anything informal or unclear.

What comes out:

- the claims, largest first, each with its words, how it was worked out and the records behind it;
- stock that can still go back, the deadlines, and what's waiting for a person;
- a draft letter for each supplier, every figure written by code.

## What "correct" means

- The answer key: [which suppliers and which year, and who worked out what each one truly owed].
- The mistakes, worst first: a claim you shouldn't make (it costs credibility with a supplier you depend on); money missed; an item sent to a person (counts as neither).
- The pass mark: see `pass-mark.md`, written before anything is scored.

## Security

- Access: read-only, to the exported records and the agreement folders. It can't change a record, a payment or a supplier's account, and it can't send anything.
- The AI reader gets one supplier's documents; the checker gets one document and the kind of term; the letter writer gets a supplier's name and the kinds of thing asked for, never an amount.
- Text in a document addressed to an AI is data, never orders: it's reported, and it changes nothing.
- Credentials live in [your secret store], never in the code.
- What it never does: [contact a supplier, send a claim, change a record].

## How it runs

- Where: [a server you control].
- When: [each year once the statements are in, and whenever a new agreement or amendment arrives].
- Nothing silently dropped; a log line for every run.
- After any change, including a new AI model, score it against the answer key again.
