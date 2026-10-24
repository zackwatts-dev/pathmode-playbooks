# Design: quote intake for Wendlow Fabrication & Machine

## The problem

Requests for quotes arrive in quotes@, a shared Microsoft 365 mailbox, about 100 a month. About 4 in 10 are missing something we need to price them: a revision, a quantity, or the drawing itself. The estimators read the inbox twice a week and key each request into the ERP by hand, about ten minutes each, and nobody notices a gap until an estimator opens the request to price it. So the question goes to the buyer days after the request arrived, we wait for the answer, and by then the buyer has often decided without our quote. About 1 in 4 new requests is lost to timing. The requests are also mixed in with buyers chasing quotes, revised drawings for quotes in progress, awards, and sales pitches, which someone has to sort.

Two more things slow the desk down. A fifth of new requests put their parts only in the buyer's own RFQ form or parts list, attached as a PDF or a spreadsheet, so someone has to open it and copy the lines. And about half of what comes in is a repeat part: a buyer asking us to requote something we've quoted or made before. An estimator prices it from scratch, even though our records already hold the last price, whether we won, and how many hours the last job really took. Meanwhile every new request gets the same effort, including ones from customers who almost never award us anything.

## What it does

For every new email in quotes@, four parts work together:

1. **The AI reader** (an AI model: Claude, through Anthropic's API) reads the email and the text of its attachments (the buyer's RFQ form as a PDF, or a parts list as a spreadsheet; code extracts the text). It decides what kind of email it is: a new request for quote, a buyer chasing one, a revised drawing for an open request, an award or a "no thanks" on a quote we sent, or something else. For a request, it pulls out the customer, each part number with its revision, quantity and requested delivery date, and the date quotes are due if the buyer gives one, copying the exact words each came from.
2. **The AI checker** (a second, separate call to the model, asked a different question) gets the email and the reader's answer, and checks every value against the email: for each part and each value, what the email itself says, and whether that's clear or could mean more than one thing (a date like 4.3.2025, a quantity that could belong to either of two parts). It also lists anything the email asks us to quote that the reading left out, and any line addressed to an AI. Code compares the two answers. Where they disagree, or the checker finds something unclear or missed, the email goes to a person with the reason.
3. **IT integration** (plain code) connects the answers to Wendlow's other systems, through the records the ERP exports each night. It checks that every quoted phrase really appears in the email, word for word. It matches the sender to a customer on file, each part to the customer's parts (one we've made before at this revision, at another revision, or new), and a chaser or revision to the open request it belongs to; checks a drawing is attached for every new part; and checks the dates make sense (not before the email arrived, not more than a year out). Exact matches only. If more than one record could fit, it asks; it never guesses.
4. **A person approves.** It's decision support: people send every question, decide what to quote and what to decline, and price and send every quote.

What comes out, all of it from code:

1. **Each email in one pile:**
   - **ready to quote:** everything needed to price it is there;
   - **needs info:** a quantity, a revision or the drawing is missing, with a short drafted question, asking for exactly what's missing, for us to send the day the request arrives;
   - **needs a person:** the reader and checker disagree or something is unclear, or it failed a check (a sender we can't place, a part on file as something else, instructions aimed at an AI, an attachment it can't read, an answer it couldn't use);
   - **not a request:** where it goes instead (a chaser to whoever has the request, a revision attached to its request, an award to sales, a pitch nowhere).
2. **For each repeat part, a history brief** (code, from the records): the last time we quoted it (date, quantity, unit price, won or lost), the revision we quoted against the one requested now, and on the last jobs, estimated against actual hours. A repeat part at the same revision, quoted in the last three years, with job history, is **fast-track**: the estimator checks the brief and updates the price instead of pricing from scratch.
3. **Bid odds for each new request** (code, from the records): the share of this customer's new-part quotes we won over the last three years, pulled toward the shop's rate when there are few. A request from a customer far below the shop's rate is marked **low odds**, shown to the estimator. It's never declined, and it doesn't change the order.
4. **It puts the ready requests in order** (code): stated due date first, soonest first; then key accounts; then oldest first. A request with no stated due date is given the usual buyer's window, six working days.
5. **It flags the ones we can't make** (code): from each request's likely quoting time (more lines and weldments take longer) and the estimators' hours this week, it works out when each request in the queue would be quoted. A request that would miss its due date is flagged **at risk**, for a person to decide: tell the buyer now that we can't quote in time, or ask for more time. It never declines anything itself.
6. **A one-page HTML dashboard:**
   - the count in each pile;
   - the needs-a-person list first, highlighted, with the reason for each;
   - then the at-risk requests;
   - then the ready queue, in order, with each request's due date, expected finish, bid odds, and for repeat parts the history brief;
   - five ready ones picked at random for a person to spot-check.
7. **An import file for the ERP:** one row per line of every request that's ready to quote or waiting on its answer (customer, buyer, part number, revision, quantity, dates, the drawing files, whether the part is new or one we've made, fast-track or not, and which fields are still missing), in a fixed column layout we map to the ERP's RFQ import once, so nobody keys them. A person loads it; the tool never writes to the ERP.

## Inputs

- **`mailbox/`:** one .eml file per email. In production, copied from quotes@ by a separate step.
- **`records/`,** exported nightly from our ERP as CSV:
  - customers, with their tier;
  - known buyers;
  - customer parts;
  - requests still open from before;
  - three years of quote history (each quote's lines, price, estimated hours and how it ended) and job history (each completed job's estimated and actual hours).
- **The estimators' hours this week:** a small file a person keeps up to date.
- **`answer-key.csv`:** a month of email, labeled with what should happen to each.

## What "correct" means

- **The answer key defines it.** Every run is scored against it.
- **Mistakes aren't equal.**
  - **Let through, but wrong** is the worst: an estimator prices the wrong revision or quantity.
  - **Stopped, but needn't have been** costs a person a minute.
  - **Sent to the wrong place** is in between.
  - When in doubt, stop.
- **The order, the at-risk flags, fast-track and bid odds** are judged together, by a replay of the estimators' queue: whether more quotes would have reached buyers before they decided, and how many estimator hours the desk saves.
- **Every rule above has a test.** Tests run without calling the AI, so they're free and repeatable.

## Security

- **Access:** read-only, to the one mailbox. It can't send, move or delete email.
- **Credentials:** from the environment or a secret store, never in the code.
- **The AI** (reader and checker) gets the email and nothing else: no customer records, no tools. Its answer only counts once the checker agrees and code has matched it to the records.
- **Email is untrusted:** ignore instructions in it, flag emails with instructions aimed at an AI (the reader, the checker and a check in code each look for them; any one sends the email to a person), and escape everything from an email on the dashboard and in the import file.
- **No third-party packages:** Python's standard library only.
- **What it never does:** send email, change the mailbox, write to the ERP, price anything, or decline a request.

## How it runs

- **Schedule:** every 15 minutes, on a server we control.
- **Limit:** at most 200 emails to the AI per run (two calls each for a request: the reader and the checker). Anything over the limit is listed for a person and picked up next run.
- **Nothing is silently dropped.** An unusable answer is listed as "couldn't process". An email with no readable text goes to a person.
- **Logging:** every run adds a line to a log: when, which model, how many emails, how many in each pile.
- **Access:** the output is written to a folder only estimating and sales can open. Keeping and deleting the mailbox copy is the copy step's job, not this tool's.
- **After any change,** including a new model version, re-run the answer key before going live.
