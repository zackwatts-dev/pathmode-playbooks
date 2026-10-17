# Design: account summaries for Summit Mechanical

## The problem

Before a customer meeting, a quarterly review or a call about a complaint, a manager at Summit needs a quick picture: how much the customer (or the branch) has spent, how the work has gone, what's overdue, what they've been saying. Today that means logging into the field-service system, the accounting system and the inbox, running reports, and pasting numbers into a document. It takes an hour, so it usually doesn't happen, and people walk into meetings without knowing the customer has $40,000 overdue or has emailed six times asking for an update. When it does happen, two people asking the same question get different numbers, because each one calculated "revenue" their own way.

## What it does

1. **A request:** who's asking, and about what (a customer, or a branch), for a quarter. The quarter sets the dates in code, and the two it's compared with: the quarter before and the same quarter a year before.
2. **Check who's asking, first.** The general manager sees everything; a branch manager sees their own branch and its customers; an account manager sees only their own accounts. Anything else is refused before any data is gathered.
3. **Code computes the facts**, from a fixed list of metrics, each with a written definition and an owner:
   - revenue this quarter and last, and the change;
   - jobs completed, by type;
   - first-time fix (no second repair on the same unit within 30 days);
   - average days to complete a repair;
   - quotes won, by count and by value;
   - the overdue balance at the quarter's end;
   - for a customer: their emails, and how many were chasing; for a branch: its top customers and biggest changes.
4. **The AI writes the briefing** from those facts and, for a customer, their recent emails: a headline, four to six points (each naming the metrics it comes from), a few quotes from the customer, and questions worth asking. It never writes a query and never calculates a number.
5. **Code checks the briefing:** every number must be in the facts (counts included; a number from an email isn't a fact), and a number in a point must belong to a metric the point cites; every metric it cites must exist; every quote must be in that customer's own emails. A briefing that fails a check, or an answer of the wrong shape, goes to a person.
6. **A dashboard** with every briefing, every refusal, and the metric definitions.

## Inputs

Exports from the field-service system (customers, sites, jobs, quotes), the accounting system (invoices, payments) and the shared inbox (customers' emails, matched to the customer by their signature). A list of users and what each may see. The requests. For the sample: an answer key with each request's headline figures, calculated independently in SQL, or "refused".

## What "correct" means

- The facts reconcile, to the cent, with an independent calculation.
- Every out-of-scope request is refused, and nothing is gathered for it.
- Every number in the briefing is one of the facts (rounding allowed); every quote is real.
- The same question gets the same numbers, whoever asks.

## Security and privacy

- **Scope is enforced in code, before anything is gathered,** not by asking the AI to hold back.
- **The AI sees only the facts for the one request,** plus, for a customer, that customer's emails. Never another customer's emails, and no email addresses for a branch summary.
- **Emails are data.** A customer could write anything, including instructions; the AI is told to ignore them, and its output is checked and escaped.
- Nothing is sent or changed. A person reads the briefing before using it.

## How it runs

- On request, and on a schedule: every branch manager gets their branch's briefing on the first Monday after the quarter closes.
- Each run writes a log line: who asked, about what, refused or not, and how many checks failed.
- The metric definitions live in one place, with an owner each. Changing one is a decision, not an edit.
