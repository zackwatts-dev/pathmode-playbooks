# Design: quote request intake for Wendlow Fabrication & Machine

## The problem

Requests for quotes arrive in quotes@, a shared Microsoft 365 mailbox, about 100 a month. About 4 in 10 are missing something we need to price them: a revision, a quantity, or the drawing itself. Nobody reads a request until an estimator opens it to price it, so that's when we notice the gap, email the buyer, and wait for the answer, and by then the buyer has often decided without our quote. We lose about 120 quotes a year this way. The requests are also mixed in with buyers chasing quotes, revised drawings for quotes in progress, awards, and sales pitches, and someone has to sort it all and retype every part number, revision and quantity before pricing can start.

## What it does

For every new email in quotes@:
1. **Decide what kind it is:** a new request for quote, a buyer chasing one, a revised drawing for an open request, an award or a "no thanks" on a quote we sent, or something else.
2. **For a request,** an AI model (OpenAI's API) pulls out the customer, each part number with its revision, quantity and requested delivery date, and the date quotes are due if the buyer gives one, quoting the exact words each came from.
3. **Plain code, not AI, checks it:** every quote really appears in the email, and every value is in the words quoted for it. It matches the sender to a customer on file, each part to the customer's parts (a part we've made before, or a new one), and a chaser or revision to the open request it belongs to. Exact matches only. If more than one could fit, it asks; it never guesses.
4. **It puts each email in one pile:**
   - **ready to quote:** everything needed to price it is there;
   - **needs info:** a quantity, a revision or the drawing is missing, with a short drafted question for us to send the day the request arrives;
   - **needs a person:** it failed a check (a value that isn't in its quote, a sender we can't place, instructions aimed at an AI, an attachment it can't read, an answer it couldn't use);
   - **not a request:** where it goes instead (a chaser to whoever has the request, a revision attached to its request, an award to sales, a pitch nowhere).
5. **It puts the ready requests in order** (code): stated due date first, soonest first; then key accounts; then oldest first. A request with no stated due date is given the usual buyer's window, six working days.
6. **It flags the ones we can't make** (code): from each request's likely quoting time (more lines and weldments take longer) and the estimators' hours this week, it works out when each request in the queue would be quoted. A request that would miss its due date is flagged **at risk**, for a person to decide: tell the buyer now that we can't quote in time, or ask for more time. It never declines anything itself.
7. **A one-page HTML dashboard:**
   - the count in each pile;
   - the needs-a-person list first, highlighted, with the reason for each;
   - then the at-risk requests;
   - then the ready queue, in order, with each request's due date and expected finish;
   - five ready ones picked at random for a person to spot-check.

It's decision support. People decide what to quote, what to decline, and send everything.

## Inputs

- **`mailbox/`:** one .eml file per email. In production, copied from quotes@ by a separate step.
- **`records/`,** exported nightly from our ERP as CSV:
  - customers, with their tier;
  - known buyers;
  - customer parts;
  - requests still open from before.
- **The estimators' hours this week:** a small file a person keeps up to date.
- **`answer-key.csv`:** a month of email, labeled with what should happen to each.

## What "correct" means

- **The answer key defines it.** Every run is scored against it.
- **Mistakes aren't equal.**
  - **Let through, but wrong** is the worst: an estimator prices the wrong revision or quantity.
  - **Stopped, but needn't have been** costs a person a minute.
  - **Sent to the wrong place** is in between.
  - When in doubt, stop.
- **The order and the at-risk flags** are judged separately, by whether more quotes would have reached buyers before they decided.
- **Every rule above has a test.** Tests run without calling the AI, so they're free and repeatable.

## Security

- **Access:** read-only, to the one mailbox. It can't send, move or delete email.
- **Credentials:** from the environment or a secret store, never in the code.
- **The AI** gets the email and nothing else: no customer records, no tools. Its answer only counts once code has checked it.
- **Email is untrusted:** ignore instructions in it, flag emails with instructions aimed at an AI, and escape everything from an email on the dashboard.
- **No third-party packages:** Python's standard library only.
- **What it never does:** send email, change the mailbox, price anything, or decline a request.

## How it runs

- **Schedule:** every 15 minutes, on a server we control.
- **Limit:** at most 200 emails to the AI per run. Anything over the limit is listed for a person and picked up next run.
- **Nothing is silently dropped.** An unusable answer is listed as "couldn't process". An email with no readable text goes to a person.
- **Logging:** every run adds a line to a log: when, which model, how many emails, how many in each pile.
- **Retention and access:** saved email is deleted after 90 days. Only estimating and sales see the output.
- **After any change,** including a new model version, re-run the answer key before going live.
