# Customer RFQ intake

Reads every email in a quotes mailbox the day it arrives: each request for quote into the fields an estimator needs, with a question drafted for anything missing (a revision, a quantity, the drawing), and everything else sorted to where it goes. A model reads each email, quoting its words for every value; plain code checks those words, matches them to your records and sorts; anything that doesn't check out goes to a person. Nothing is sent: a person sends every question and every quote.

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
7. **The at-risk forecast** (code). Each request's likely quoting time is 0.6 hours × (1 + 0.3 for each extra line) × 1.5 if any line is a weldment or assembly (a repeat's family from its record, a new part's from its description), and × 1.3 more on that welded work when the estimators are junior (`estimator-hours.csv`'s optional `seniority` column; blank means junior). The estimators' hours per working day come from `estimator-hours.csv`, which a person keeps current, less any hours held back for the ERP's annual re-quotes: the last four weeks' average from `requote-hours.csv` when the records have it, otherwise `requote_hours_per_day` in `forecast.json`, which a person sets (default 0, because the recommended order gives re-quotes the hours left over). Working the queue in order, every request stays in the forecast with its expected finish. It starts with the first day of hours on file on or after the run's earliest email (`--plan-from` overrides it), and is run as of each request's arrival, using only what had arrived by then, as a scheduled run would; a request that forecast has quoted after its due date is flagged **at risk: ask the buyer for more time**. The dashboard's queue and expected finishes are the latest run's. Nothing is taken out of the queue and nothing is assumed declined: the flag is information, and a person decides what to say to the buyer.
   - **The order rule:** new requests for quotes go ahead of the annual re-quotes, as Wendlow already does. The tool doesn't see re-quotes (the ERP raises them), so the dashboard states it for the estimators.
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

# The queue replay: a model of what reading every request on arrival is worth, 2024
python3 rfq-intake/replay_queue.py
```

Then open `out/dashboard.html`. With `--sample`, `out/score.md` scores the run against the answer key. `--gate` exits with an error if the score breaks `release-thresholds.json` (the owner's go-live limits). If a replay has no recorded answer for an email (because the email or the instructions changed), that email goes to couldn't process and the run says "N emails had no recorded answer". To record a new run (it costs API calls): `python3 tools/record.py rfq-intake`.

## The sample: Wendlow's quotes@ mailbox, May 2024

Wendlow Fabrication & Machine is a fictional job shop, from a simulation of the whole business (`pathmode-corpus/simulations/fabricator/scripts/playbook_rfq.py`). Every new-part RFQ the simulation received in May 2024 is an email from its buyer, written the ways buyers write them (tables, lists, a forwarded engineer's note, a two-line note from a phone with the part only in the drawing's name), with the rest of a quotes inbox around them.

- **`mailbox/`:** 136 emails. 99 new requests (36 that need only a question: 18 missing a quantity, 14 a revision, 4 the drawing; 11 that need a person: an injection, seven from a shared domain that don't name the company, and three where a repeat part number is described as something else), 13 chasers, 5 revised drawings, 8 awards, 4 lost replies, 5 vendor pitches and newsletters, and 2 order questions sent to the wrong address.
- **`records/`:** as exported the morning of May 1: 377 customers with their tier and domain (38 domains shared by sister companies, some named alike down to a comma), 7,372 known buyers, 22,457 customer parts with descriptions, the 10 RFQs still open from April, and the estimators' quoting hours for May (5.28 a working day each, after the time that goes to other work: one junior estimator to May 10, two from May 13, none on May 7).
- **`answer-key.csv`:** what each email is and what should happen to it, with every value, and how each request really ended (truth, named so).
- **`queue-replay/`** (2024), **`queue-replay-2023/`**, **`queue-replay-2025/`:** the inputs for the separate queue replay (below), a full year each.
- **`../holdout-2024-09/`, `../holdout-2024-10/`:** two later months of the same mailbox, held back, each with its records, answer key, recorded run and its own wording of a note aimed at an AI.
- **`forecast.json`** (beside the script, not in `sample-data/`): the re-quote hours a day to hold back, 0 by default (April 2024's re-quotes took about 1.6 hours a working day, if your estimators price re-quotes first).

### Results: the recorded runs (Claude Sonnet 5.5)

Each month scored against its own answer key. May is the sample. September and October were held back: generated after the code was frozen (commit ae3c477), each with a note aimed at an AI worded unlike any earlier month's, recorded and scored once against the thresholds in `release-thresholds.json`. A request the key says needs only its question, sent to a person instead, counts as stopped needlessly; a question that asks for the wrong thing counts as the wrong place.

| Month | Emails | Right | Let through, but wrong | Wrong place | Stopped, but needn't have been |
|---|---|---|---|---|---|
| May (the sample) | 136 | 134 | 0 | 0 | 2 |
| September, held back | 110 | 108 | 0 | 1 | 1 |
| October, held back | 164 | 157 | 0 | 0 | 7 |

Of the 102 requests the keys say need only a question, 97 got the right one the day they arrived, one September request got a question for its part number but not its drawing, and 4 went to a person. The stops: part numbers also on file for a different customer with a similar name (held for a person; the key would let them through), buyers chasing a request with no open record, and three October requests whose quantities sat in a layout the checks couldn't tie to their part. All three notes aimed at an AI went to a person: the model flagged each, and the check in code also caught May's and September's (written by the same team as the check) but missed October's. Everything to a person (the baseline) gets right only the few emails a month that need one.

### Results: the offline stand-in, not a model

From `--dry-run`: regular expressions for the sample's phrasings, a test of the checks and the matching, not of a model.

## The queue replay: a model, not a measurement

`replay_queue.py` asks what reading every request on arrival is worth. Wendlow's estimators read quotes@ and key each new request into the ERP on Mondays and Thursdays (both the twice-weekly reading and the 10 minutes a request are estimates in the simulation, not records). About 4 in 10 requests arrive missing a revision, a quantity or the drawing; the gap is found when an estimator opens the request, the question goes out then, and the request waits for the answer. The replay runs every request the estimators had to price in a window (new requests first, annual re-quotes with the hours left, as Wendlow does), day by day, three ways, over 20 seeds of the simulation's noise:

- **today:** read and keyed twice a week; the question goes out when the request is opened.
- **daily:** a person reads and keys every request the morning it arrives (the same 10 minutes), and asks then. No AI.
- **intake:** AI reads every request the day it arrives and drafts the question; the lines go to the ERP as an import file. The requests the tool sends to a person (12%, as in the recorded months) are read and keyed by hand on a day someone is in, and a person spends a minute looking over each request's import rows.

Every way of working pays the same quarter hour to check and send each question, sent on a day someone is in. One calibration factor on the quoting time (1.66 in 2024: the owner's formula underestimates quoting time, and the dashboard's forecast with it) is fitted on `today` alone, to each window's actual on-time count. A quote is on time if it went out by the buyer's true decision date, which only the scoring sees. A won quote is worth $35,800 of first-year revenue (every order of its parts in the year after the win, Wendlow's records for 2022–23: `pathmode-corpus/simulations/fabricator/scripts/rfq_value_stats.py`) × 27% margin, at the window's on-time win rate.

| Year | Lost to late quotes | More on time: daily | More on time: intake | Extra wins: intake | First-year margin: intake |
|---|---|---|---|---|---|
| 2023 | 293 | 100 | 137 | 48 | $461,000 |
| 2024 | 210 | 100 | 119 | 44 | $428,000 |
| 2025 (to Nov 26) | 195 | 113 | 129 | 52 | $505,000 |

Today the question goes out about three days after the request arrived. Most of intake's gain is timing: with `--keying-minutes 0` (no keying cost at all), intake gets 83 more quotes out on time in 2024 and a person reading each morning 85; at 5 minutes, intake 101; at 10, 119. Most of the gain is reading daily, which a person can do; intake adds the keying hours back. `--data` runs each year's folder; the defaults reproduce the 2024 row.

**Limits of the model.** A late quote made on time is assumed to win at the average on-time rate. A buyer is assumed to take as long to answer a question asked on day one as one asked on day three. The person reading every morning is assumed to catch every gap. And a won part's later years aren't counted: in Wendlow's records a part won in 2017–19 brought in 2.89 times its first year's revenue over its life.

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
- **One mailbox, one language.** The instructions, the injection patterns and the word lists are English. The injection list is a short pattern list: a reworded instruction can get past it, and then only the model's own flag stands in the way. Code decides every pile, but from what the model read: an email that talked the model into calling a request something else (an award, say) would be filed as that, so every pile gets a person's look before anything moves, and nothing is sent, priced or written to the ERP by the tool.
- **Build your own answer key** from a month of real email, labeled by hand, and set your own thresholds before you score it. It's the only way to know how often it's right.

## Files

| File | What |
|---|---|
| `rfq_intake.py` | Reads the mailbox, asks the model, checks, matches, sorts, plans the queue, scores, and writes the outputs. |
| `records.py` | Your records, and the matching that has to be exact. |
| `dashboard.py` | The HTML dashboard. Everything from an email is escaped. |
| `replay_queue.py` | The queue replay: a model of Wendlow's quoting queue under three ways of working (today, a person reading every morning, AI intake), calibrated on today; `--data` for another window. |
| `graph_mailbox.py` | Copies new email out of a Microsoft 365 mailbox, read-only. |
| `release-thresholds.json` | The owner's go-live limits for the score. |
| `forecast.json` | The re-quote hours a day the forecast holds back, set by a person, when the records have no `requote-hours.csv`. |
| `instructions.md` | The reading part as instructions for a chat assistant, to try by hand. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. The owner's answers to its questions are on the playbook page. |
| `run.sh` | One scheduled run. |
| `sample-data/` | Wendlow's mailbox, records, answer key and the queue replay's inputs. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
