# Design: a pricing assistant for Summit Mechanical

## The problem

Pricing takes too long, and it's inconsistent. When a technician finds the problem on site, the customer asks "how much?", and the office takes an hour, or a day, to answer. Two estimators price the same job differently, and the written sales guidance (agreement discounts, callbacks, school districts, portal limits) gets applied from memory, or not at all. On replacements, estimators negotiate on instinct: some give away margin, others lose jobs they could have won.

## What it does

**Mode 1: price a repair.** For each technician's diagnosis:
1. The AI reads the diagnosis and picks the matching task from the flat-rate book, quoting the words.
2. The AI reads the written sales guidance and picks the clauses that apply to this customer, with a reason each.
3. Code checks both: the task must exist and fit the unit; every clause's condition must hold (an agreement on file, a recent repair, a school district). A rule the code can see for itself but the AI missed goes to a person.
4. Code works out the price: list prices, flat-rate hours, each clause's effect. The AI never writes a number into a price.
5. Out comes a quote draft for a person to send. Anything that failed a check goes to a person first.

**Mode 2: negotiate a replacement.** For an open replacement quote:
1. The AI writes each reply to the customer: trade before discounting, small steps, warm and plain.
2. Code holds the lines: never below the floor (the AI is never told it); never beyond the estimator's 5% authority, even when handing it up (going further is the manager's decision); no more than 2% off in one round; never back up; only concessions the guidance allows; no promises it forbids; no cost or floor in any message; the price in the message must be the offer. A reply that breaks a line is blocked, even if it also asks for a manager.
3. A customer who tries to instruct the assistant, wants more than the authority allows, or mentions a competitor's price goes to a person.
4. By default every reply is a draft a person sends. Only with `--autonomous`, in the demo, does it bargain on its own, against simulated buyers.

## Inputs

The price book (part costs from supplier bills, list prices), labor and trip rates, the flat-rate task book (from hours technicians actually logged), the written sales guidance, repair requests (the customer's facts and the technician's diagnosis), recent repairs to each unit, and open replacement quotes with their list price, cost and floor.

## What "correct" means

- **Repairs:** the right task and the right clauses, against an answer key from real September jobs. A wrong price sent to a customer is the expensive mistake; a quote stopped for a person costs a minute.
- **Negotiation:** never below the floor, and the floor never revealed, ever: these are absolute. Then deals won, the share of list price kept, and what buyers would still have paid (money left on the table).
- Every rule has a test that runs without calling the AI, including scripted answers that try to break each line.

## Security

- The AI never sees costs, floors or margins. Those stay in code.
- The AI has no tools. It can't look anything up, send anything, or change a price book.
- Customers' messages are data. Instructions in them are flagged, and the conversation goes to a person.
- What the assistant says can bind the company, so a person sends every message by default.
- The buyers' hidden ceilings, used only in the simulation, live in a separate file the seller's code never reads.

## How it runs

- Repair pricing on demand, as diagnoses come in from the field; negotiation drafts as customers reply.
- Every quote and every offer is logged with the clauses and checks behind it.
- Price book and guidance updated monthly; re-run the answer key after any change, including a new model version.
