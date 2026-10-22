# Customer RFQ intake

Sorts a quotes mailbox, reads every request for quote into the fields an estimator needs, checks every value it read, and plans the quoting queue so the requests that will miss their due date show up while there's still time to tell the buyer. A model reads each email, quoting its words for every value; plain code checks those words, matches them to your records, sorts and plans, and anything that doesn't check out goes to a person.

The full playbook, worked through at Wendlow Fabrication & Machine (a simulated Dayton job shop) with the design, the plan an AI wrote from it, and the owner's answers to its questions: **https://pathmode.com/playbooks/rfq-intake/**

## What it does

For every email in the mailbox:

1. **What kind it is** (the model): a new request for quote, a buyer chasing one, a revised drawing for an open request, an award, a lost reply, a vendor's pitch, or something else.
2. **For a request, each value with its own words** (the model): the customer as the email writes it, each part number with its description, revision, quantity and requested date, and the date quotes are due if the buyer gives one. Every value comes with the exact words it came from. The model sees the email and nothing else: no records, no tools. Drawings are listed by name and never opened.
3. **The checks** (code). Every quote must be in the email (subject, body or an attachment's name). Every value must be in the words quoted for it, and not loosely: a quantity needs "qty 24", "24 pcs" or its place in a table row, not a stray 24; a revision needs "rev A", or its place after the part number, not a lone "A"; a date must be the only date in its words and its weekday must match (dates are read as "2024-06-13", "6/7/24", "7.17.24", "14-Jun-24", "Jun. 14", "June 14", "14 June", "Fri 6/14", "the 14th" and "Fri the 14th", the next such date after the email); and a due date's words must be about something the buyer wants back (a quote, bid, pricing, response, "your number", the RFQ) with a deadline word near it (by, due, no later than, NLT, closes, before, or "pricing needed by"), or "submit ... bid". "Parts due", "need parts by" and "ship by" are requested dates. When the email has several parts, the words for one part's description, revision, quantity and date may not name another part, and must name this one or sit next to it in the email: in its clause (its table row, list item, piece of a sentence, its segment of a "/" or "|" line, or its block of "P/N: ... / Qty: ..." lines) or, failing that, its line, within 150 characters, with no other part as near. In a table (columns aligned with spaces or separated by tabs, in any order, a column left out or a cell left empty), each field is read from its own cell in the part's row, by the header above it, whether the model quoted the whole row or one cell. A quantity may be written "12 x bracket". A company with no words quoted for it counts as not given. A value that could be either part's goes to a person, and a line ending in "of", "for", "qty" and the like runs on to the next one ("40 pcs of" / "CRO-90007"). Due words may sit just before a quoted date ("We need pricing by" before "EOD Thu 5/9"). The email's own values for each part are then checked against what was read, with one part or several: a value the model left blank (a missed date can't slip through as ready), a value other than the one the email gives, and values that need a person rather than a reading (two quantities or two delivery dates for one part, quantity breaks, an annual usage, "make that 120", a revision called obsolete or superseded) all go to a person. On a domain shared by sister companies the email has to name the company; a buyer on file is shown as a hint, not used as a match. The injection patterns include "assistant:", "system:", "ignore previous", "approve" and "discount", in the subject and the body.
4. **The matching** (code), exact or not at all:
   - **The customer:** the sender's domain gives the candidates. One candidate is the customer, unless the email names a different customer or the sender is on file for one. Several candidates (sister companies on one domain) need the email to name one of them exactly; a buyer on file for one of them is shown to the person as a hint, not used as a match. Most buyers are new, so the contacts list is only a bonus.
   - **Each part:** a repeat (on file for that customer), a repeat at a new revision, or new. A repeat the email describes as something else than its record ("on file as a cover panel, but the email says clip angle": a reused number, or a typo) goes to a person, and so does a part on file only for another customer. A new part's family comes from its description: every part on file with that description is in one family.
   - **A chaser or revision:** to the open request it belongs to, from the ERP's open RFQs or a request read earlier in the run, by the part it names and the email it replies to. None, two, or the two pointing different ways goes to a person.
5. **One pile for each email** (code), in this order of precedence:
   - **needs a person:** it failed a check, with the reason. A value not in its quote; a sender we can't place; a shared domain the email doesn't resolve; the name and the buyer on file disagreeing; instructions aimed at an AI (a pattern list, or the model's own flag: either sends it to a person, even on an otherwise clean request); a part the email mentions that the model didn't read; a part listed twice; a drawing named at another revision than the email gives; a pitch from a customer's address, or a pitch or "other" that reads like a request; a kind it doesn't sort into; no readable text, too long to read in full, or a file it can't open. An answer it can't use is **couldn't process**, kept for a person and picked up next run;
   - **not a request,** with where it goes: a chaser to estimating, with the request it chases; a revision attached to its request (the ready queue then shows "rev A → rev B"); an award, lost reply or anything else to sales; a pitch nowhere;
   - **needs info:** a quantity or revision missing (or no part at all, only a drawing), with a drafted question in `questions/` for a person to send;
   - **ready to quote:** customer matched, and every line has a part number, revision and quantity. A requested date isn't required. A new part is ready, labeled new.
6. **The ready queue in order** (code): the stated due date, soonest first; then key accounts; then oldest. No stated due date means six working days after the email arrived (Monday to Friday; holidays aren't counted).
7. **The at-risk forecast** (code). Each request's likely quoting time is 0.6 hours × (1 + 0.3 for each extra line) × 1.5 if any line is a weldment or assembly (a repeat's family from its record, a new part's from its description), and × 1.3 more on that welded work when the estimators are junior (`estimator-hours.csv`'s optional `seniority` column; blank means junior). The estimators' hours per working day come from `estimator-hours.csv`, which a person keeps current, less any hours held back for the ERP's annual re-quotes: the last four weeks' average from `requote-hours.csv` when the records have it, otherwise `requote_hours_per_day` in `forecast.json`, which a person sets (default 0, because the recommended order gives re-quotes the hours left over). Working the queue in order, every request stays in the forecast with its expected finish. It starts with the first day of hours on file on or after the run's earliest email (`--plan-from` overrides it), and is run as of each request's arrival, using only what had arrived by then, as a scheduled run would; a request that forecast has quoted after its due date is flagged **at risk: ask the buyer for more time**. The dashboard's queue and expected finishes are the latest run's. Nothing is taken out of the queue and nothing is assumed declined: the flag is information, and a person decides what to say to the buyer. (The first design took at-risk requests out of the forecast, by the Moore–Hodgson rule; the queue replay showed it cost quotes, and the owner dropped it.)
   - **The order rule:** new requests for quotes go ahead of the annual re-quotes. The tool doesn't see re-quotes (the ERP raises them), so this is a process recommendation for the estimators, stated on the dashboard; the replay says it's where most of the gain is.
8. **A one-page dashboard:** the count in each pile; the needs-a-person list first, highlighted, with the reason for each; the at-risk requests with each one's due date and why; the order rule; the ready queue in order with each request's due date and expected finish; what's waiting on the buyer; where the rest went; and five ready requests picked at random to spot-check.

It also writes `requests.csv` (every email, its pile and why), `line-items.csv`, `queue.csv` (the queue in order, then the at-risk requests), `review-queue.csv`, `summary.md`, and with an answer key `score.md`. Every run adds a line to `runs.csv`: when, which model, how many emails, how many in each pile, how many at risk; no email content. At most `--max-emails` (default 200) new emails go to the model per run; the rest are listed in couldn't process and picked up next time. Every email ends up in exactly one pile.

## What it doesn't do

Send, move or delete email, price anything, or decline a request. A person sends every question and every quote, and decides on every at-risk request. Deleting saved email after 90 days is a separate scheduled job, not this program: a read-only program shouldn't hold the power to delete.

**Risk: reads one mailbox, read-only. Level 3.**

## Try it

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
# The offline stand-in: no model at all. Regular expressions for the ways the sample's buyers write.
python3 rfq-intake/rfq_intake.py --sample --dry-run

# Replay a recorded run: the answers a real model (Claude Sonnet 5.5) gave on the sample, free
python3 rfq-intake/rfq_intake.py --sample --replay rfq-intake/sample-data/recorded-run.json

# A real model: an API account whose terms say your data isn't used for training
export ANTHROPIC_API_KEY=...        # or PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=...
python3 rfq-intake/rfq_intake.py --sample

# The queue replay: a model of what the tool's order would have done, March to June 2024
python3 rfq-intake/replay_queue.py
```

Then open `out/dashboard.html`. With `--sample`, `out/score.md` scores the run against the answer key. `--gate` exits with an error if the score breaks `release-thresholds.json` (the owner's go-live limits). If a replay has no recorded answer for an email (because the email or the instructions changed), that email goes to couldn't process and the run says "N emails had no recorded answer". To record a new run (it costs API calls): `python3 tools/record.py rfq-intake`.

## The sample: Wendlow's quotes@ mailbox, May 2024

Wendlow Fabrication & Machine is a fictional job shop, from a simulation of the whole business (`pathmode-corpus/simulations/fabricator/scripts/playbook_rfq.py`). Every new-part RFQ the simulation received in May 2024 is an email from its buyer, written the ways buyers write them (tables, lists, a forwarded engineer's note, a two-line note from a phone with the part only in the drawing's name), with the rest of a quotes inbox around them.

- **`mailbox/`:** 136 emails. 99 new requests (each line with a description; 7 missing a quantity or revision, 8 that need a person: an injection, four from a shared domain that don't name the company, and three where a repeat part number is described as something else), 13 chasers, 5 revised drawings, 8 awards, 4 lost replies, 5 vendor pitches and newsletters, and 2 order questions sent to the wrong address.
- **`records/`:** as exported the morning of May 1: 377 customers with their tier and domain (38 domains shared by sister companies, some named alike down to a comma), 7,355 known buyers, 22,457 customer parts with descriptions, the 10 RFQs still open from April, and the estimators' hours for May (one junior estimator, 6 hours a working day, 0 on a day off).
- **`answer-key.csv`:** what each email is and what should happen to it, with every value, and how each request really ended (truth, named so).
- **`queue-replay/`:** the inputs for the separate queue replay (below).
- **`forecast.json`** (beside the script, not in `sample-data/`): the re-quote hours a day to hold back, 0 by default (April 2024's re-quotes took about 1.6 hours a working day, if your estimators price re-quotes first).

### Results: the recorded run (Claude Sonnet 5.5)

`--replay sample-data/recorded-run.json`: Claude Sonnet 5.5's answers on the regenerated May sample, recorded through the `claude` command line.

- **May (the sample):** 136 of 136 right, **0 let through wrong**. All three release thresholds pass. 1 at risk (an April RFQ already past due).
- **June 2024, 130 emails:** scored blind first at **91 of 130** (0 let through wrong, 39 stopped needlessly: fails the stop threshold). Then used to find wording the checks didn't know, so it's **training data now**: 127 of 130, 0 let through wrong, 3 stopped needlessly. The three: a chaser for an RFQ Wendlow screened out in May (it was never open, so there's nothing to attach it to, and a person should answer), and two parts on file for a sister Eckert company.
- **July 2024, 126 emails:** scored blind first at **83 of 126** (0 let through wrong, 43 stopped needlessly). Then used the same way, so it's **training data now**: 124 of 126, 0 let through wrong, 2 stopped needlessly, both chasers for June RFQs Wendlow screened out.
- **What June and July taught the checks**, each fix tested on made-up examples, not on the months' own emails: more date forms (d-Mon-yy, "Jun. 14", "the 8th", "Mon the 8th", dotted 7.17.24); more quote-due cues (responses requested no later than, RFQ closes, your number back by, submit your bid by, NLT, pricing needed by); item blocks of "P/N: / Qty:" lines and "/" or "|" layouts; table rows read cell by cell by their header (tabs or spaces, any column order, a column missing); "12 x bracket" quantities; a company with no quoted words treated as not given; on a shared domain, the company must be named; and a chaser or revision for a request that's with a person goes with it, instead of stopping on its own.
- **June's 58 at risk** in its first scoring came from a bug: run `--as-of 2024-06-28`, the forecast started on June 28 with one day of hours. It now starts with the hours covering the run's email: 5 at risk, all RFQs carried over from May already past their due dates.

What its first replay found (74 of 136, 1 let through wrong, 61 stopped, 2 couldn't process), and what changed in the checks, not the instructions: the model quotes each value on its own ("qty 16", "rev A") rather than with its part number, so values are tied to parts by where they sit in the email; due words may come just before a quoted date; a company the model read off the sender's address is left to the domain match; a table row's quantity may be quoted from its revision column; a chaser the model read no part for uses the part number the email gives; an answer where the model corrected itself ("Wait, ...") is read from its last JSON object, with a note; and a value the model left blank but the email gives goes to a person (it let ULL-56999 through without its date before). An independent review then added the checks for conflicting and multiple values, wrapped lines, single-part emails, "parts due" dates and more injection patterns.

### Results: the offline stand-in, not a model

These are from `--dry-run`, before any recording. The stand-in was written for the sample's phrasings, so it reads them almost perfectly; it's a test of the checks and the matching, not of a model. A real model's run is the one to judge the reading by.

- **136 emails:** 84 ready to quote, 7 needs info, 8 needs a person, 37 not a request.
- **Against the answer key:** 136 right, **0 let through wrong**, 0 sent to the wrong place, 0 stopped needlessly. Every field the stand-in read (part numbers, revisions, quantities, requested dates, quote due) matches the key on all 99 requests it read.
- **Everything to a person** (the baseline): 15 right, 121 stopped needlessly.
- **Release thresholds:** all pass. 0 let through wrong (at most 0), 0% of the emails the key doesn't stop were stopped (at most 10%), 0% wrong place (at most 5%).
- **The revised drawing whose RFQ went to a person** (a shared domain, unsigned) now goes with that RFQ, to the same person, rather than stopping on its own.
- **At risk: 1,** an RFQ open from April already past its due date. Forecast as each request arrived, with nothing held back for re-quotes, the formula expects 113 hours of quoting for May's queue against 114 estimator hours on file, and no May request is forecast late on arrival. But 40 of the 84 it expected to quote in time were really lost late (with Wendlow's own order, which priced re-quotes in among them, not the tool's). The forecast alone doesn't find the late ones: the order rule (new requests before re-quotes) is what the replay credits.

## The queue replay: a model, not a measurement

`replay_queue.py` asks whether a different order would have got more quotes to buyers before they decided. It replays every request the estimators had to price in a window (new-part RFQs and annual re-quotes, with the queue on its first morning; screened-out RFQs left out), day by day, five ways, each over 20 seeds of the simulation's noise:

- **(a)** Wendlow's rule: one queue, first in, first out, re-quotes included. That's what the records show (every tier waited a median 7 days); modeled with key accounts to the front instead, the calibration needs nearly three times the work per quote and declines RFQs that were in fact quoted.
- **(d)** first in, first out with new requests ahead of the re-quotes: the process change alone, no tool.
- **(b)** the tool's order (due date, key account, oldest), new requests ahead of re-quotes, flags only.
- **(b-old)** the same with the first design's removal, for the record.
- **(c)** (b) plus 10 minutes saved per new RFQ by not retyping its lines (a labeled estimate).

A quote is on time if it went out on or before the buyer's true decision date, which only the scoring sees. One calibration factor on every request's expected quoting hours is fitted on (a) alone, to each window's own actual on-time count; every other policy runs with it. A won quote is worth $34,000 first-year revenue (Wendlow's records, 2022–23) × 27% margin (the middle of the published 22–31%), at the window's on-time win rate.

Value counts only RFQs a buyer awarded to someone (a canceled project can't be won), per window and per month of window: the windows are estimator vacancies of different lengths, and Wendlow had two in the decade's last four years (2021 and 2024). In normal months almost nothing is lost late, so a window's value isn't a yearly one. "Net" subtracts the cost of re-quotes waiting longer than under (a): the old price stays on the part's repeat orders, about $5.31 per re-quote per working day from Wendlow's records (re-quotes sent 2022–23 raised prices 13.9% on about $13,400 a year of repeat revenue per part).

**March to June 2024** (`sample-data/queue-replay/`; 340 new RFQs, 525 re-quotes; 126 really lost late; 32 no award). Calibration factor **1.005**, fitted on (a): 198.7 on time against 199 actual (−0.2%).

| Policy | On time (seed range) | Late quotes made on time (share) | Margin, window | Per month | Re-quotes' extra wait | Net, window | Net, per month |
|---|---:|---:|---:|---:|---:|---:|---:|
| (a) FIFO | 198.7 (189–211) | (127.5 late) | | | | | |
| (d) FIFO, new before re-quotes | 334.7 (327–340) | 122.7 (96%) | $377,400 | $95,700 | +1,259 days | $370,700 | $94,000 |
| (b) the tool, flags only | 338.9 (336–340) | 126.5 (99%) | $389,200 | $98,700 | +1,247 days | $382,600 | $97,100 |
| (b-old) with removal | 314 (306–320) | 102 (80%) | $313,700 | $79,600 | +1,159 days | $307,500 | $78,000 |
| (c) (b), no retyping | 339.4 (336–340) | 126.9 (100%) | $390,400 | $99,000 | +701 days | $386,700 | $98,100 |

**Holdout, March to October 2021** (exported after the owner's decision; 778 new RFQs, 997 re-quotes; 220 really lost late; 80 no award). Calibration **refitted** on this window's own (a): factor **1.154** (against 2024's 1.005), 536 on time against 536 actual (0.0%).

| Policy | On time (seed range) | Late quotes made on time (share) | Margin, window | Per month | Re-quotes' extra wait | Net, window | Net, per month |
|---|---:|---:|---:|---:|---:|---:|---:|
| (a) FIFO | 536 (526–544) | (220.2 late) | | | | | |
| (d) FIFO, new before re-quotes | 772.1 (768–776) | 214.4 (97%) | $650,600 | $81,500 | +2,836 days | $635,500 | $79,600 |
| (b) the tool, flags only | 773.6 (770–778) | 215.9 (98%) | $655,300 | $82,100 | +2,798 days | $640,400 | $80,200 |
| (b-old) with removal | 749.4 (744–757) | 194.2 (88%) | $589,300 | $73,800 | +2,661 days | $575,100 | $72,000 |
| (c) (b), no retyping | 774.2 (768–778) | 216.4 (98%) | $656,600 | $82,300 | +2,163 days | $645,200 | $80,800 |

**What it says.** Both windows agree. Almost all of the gain is the process change, new requests before re-quotes, which needs no software. The tool's order adds little on top: over (d), +3.9 awarded RFQs on time in 2024 (about $12,000 in the window) and +1.6 in 2021 (about $5,000), with seeds where it adds none. The old removal cost 20 to 25 quotes in each window, because it judged requests on stated or default due dates, not on when the buyer really decides; that's why the flags are information only. At the records' $5.31 a day, re-quotes waiting longer costs little; (d)'s gain would be gone only at about $230–300 per re-quote per working day. The tool's case is the intake itself (sorting, checking and the questions), with the order as a small extra.

**Limits of the model.** Every late quote made on time is assumed to win at the average on-time rate, though the requests it recovers may not be average. The re-quote delay is charged only through stale prices, not through customers re-sourcing (about 1 in 20 re-quoted parts in the simulation, late or not). The stated due dates are the generator's assumption (most at or just before the decision, some padded early, some after it), not observed buyer behavior. And key accounts' tier in the files is their tier when the simulation created them: by mid-2016 most had drifted to occasional in the simulation (after late deliveries), which is why the records show no key-first queue. `out/replay/replay.md` has each window's full table; run the holdout with `--data <folder>`.

## Getting the email: Microsoft 365

`graph_mailbox.py` copies new email from one Microsoft 365 mailbox into a folder, read-only, using Microsoft Graph. Run it on a schedule, then run `rfq_intake.py` on the folder. The setup (an app registration with *Mail.Read*, limited to the one mailbox) is at the top of the file. It picks up from the time of the last message it saved, and remembers the ids saved at that time, so two messages that arrive in the same second are neither skipped nor saved twice. When Graph throttles it (HTTP 429 or 503), it waits as long as Graph asks (up to two minutes) and tries again, up to five times. Its first run copies the whole inbox unless you give `--since 2024-05-01T00:00:00Z`; after that it starts from where it stopped. It's tested here against a stand-in for Graph, not a live tenant: try it on a test mailbox first.

On another mail system, anything that saves messages as `.eml` files works.

## Running it for real

`run.sh` is one scheduled run: copy new email out of the mailbox, then sort it and rebuild the dashboard. Schedule it every 15 minutes, for example with cron:

```
*/15 * * * * /srv/pathmode-playbooks/rfq-intake/run.sh >> /srv/quote-intake/cron.log 2>&1
```

With `--remember` (which `run.sh` uses), `out/processed.json` keeps each processed message ID with the checked answer the model gave, so no email goes to the model twice; a revised drawing arrives as a new email. The checks, the matching and the forecast run again every time, so a fix to the records takes effect on the next run.

## Before it goes live

The repo covers the email limit, the couldn't-process list, the run log, the spot-check and the tests. Yours to add, on a go-live checklist a person signs: a server you control, the API key in a secret store, the mailbox app's scope limited to the one mailbox (check it), the output folder open only to estimating and sales, the 90-day deletion of saved email, dashboards and recorded answers as its own scheduled job, and an alert if runs stop or the needs-a-person pile jumps. Re-run the answer key after any change, including a new model version, and don't go live on a run that fails `release-thresholds.json`.

## Before you run this on your own data

- **The columns are Wendlow's.** `customers.csv` needs `customer_id, name, tier, domain` (tier is key, regular or occasional); `contacts.csv` needs `customer_id, name, email`; `customer-parts.csv` needs `customer_id, part_number, revision, family`; `open-rfqs.csv` needs `rfq_id, customer_id, received_on, stated_due, part_numbers, quantities` (lists separated by `;`); `estimator-hours.csv` needs `date, hours`. A missing column, or a row it can't read, stops the load with the file and row.
- **Customers are matched by email domain and the name the email gives**, exactly apart from case and spacing. A buyer writing from Gmail, or a signature that spells the company your records' way only roughly, goes to a person (or, on a domain only one customer has, is matched with a note). If your records have look-alike customers on one domain, the run notes it on each match; merge them if they're the same company.
- **Part numbers are found by `PART_PATTERN`** in `rfq_intake.py` (letters, a dash, digits). The check that the model read every part the email mentions depends on it, so set it to your customers' formats first, and add order or quote number prefixes to `NOT_PARTS`.
- **Families come from `customer-parts.csv`,** a repeat's from its record and a new part's from its description, and only where every part with that description is in one family; the weld families are `WELD_FAMILIES` in `records.py`. A description with no single family counts as not a weldment, with a note.
- **The forecast is only as good as its inputs.** Check the quoting formula against a month of your own quotes; keep `estimator-hours.csv` current, with `seniority` if your estimators are senior; and give it your re-quote load, either a `requote-hours.csv` export (date, hours) or `requote_hours_per_day` in `forecast.json`. With no hours on file from the run's date, nothing is forecast, and the dashboard says so. And judge the flags against how requests really ended before relying on them: on Wendlow's sample they catch few of the late ones.
- **Dates are read in a few forms:** "6/7/24", "06/18/2024", "2024-06-13", "June 6", "6 June", "Fri 5/31", and a weekday on its own ("by Friday"). "End of the month", "next week" or "within 10 days" aren't, so the model can't give a date for them that passes, and the request goes to a person.
- **Drawings are never read.** A revision only on the drawing, or a quantity in a PDF, isn't seen: the request is needs info, with a question. A drawing's file name counts (`ECK-70811_revA.pdf`), and one that names another revision than the email's sends it to a person.
- **One mailbox, one language.** The instructions, the injection patterns and the word lists are English. The injection list is a short pattern list: a reworded instruction can get past it, and then only the model's own flag stands in the way; but nothing the email says can change a pile, because code decides every one.
- **Build your own answer key** from a month of real email, labeled by hand, and set your own thresholds before you score it. It's the only way to know how often it's right.

## Files

| File | What |
|---|---|
| `rfq_intake.py` | Reads the mailbox, asks the model, checks, matches, sorts, plans the queue, scores, and writes the outputs. |
| `records.py` | Your records, and the matching that has to be exact. |
| `dashboard.py` | The HTML dashboard. Everything from an email is escaped. |
| `replay_queue.py` | The queue replay: a counterfactual model of five policies, calibrated on Wendlow's own rule; `--data` for another window. |
| `graph_mailbox.py` | Copies new email out of a Microsoft 365 mailbox, read-only. |
| `release-thresholds.json` | The owner's go-live limits for the score. |
| `forecast.json` | The re-quote hours a day the forecast holds back, set by a person, when the records have no `requote-hours.csv`. |
| `instructions.md` | The reading part as instructions for a chat assistant, to try by hand. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. The owner's answers to its questions are on the playbook page. |
| `run.sh` | One scheduled run. |
| `sample-data/` | Wendlow's mailbox, records, answer key and the queue replay's inputs. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
