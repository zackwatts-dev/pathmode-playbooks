# Build plan: quote intake for Wendlow

Python 3, standard library only. All commands run from the repo root. Module and command names are proposals; the agent should follow them unless the code already says otherwise.

## 1. Ground rules for the agent

- Work on branch `quote-intake-v1`, in small commits (one module or one rule group each, with its tests). Never commit to main.
- **Tests come first.** Write a module's tests, see them fail, then write the code.
- **The agent may not edit, delete, skip, or loosen any test or `answer-key.csv` without written approval.** If a test seems wrong, stop and ask. This applies to tests marked ★ below and to all others.
- ★ marks tests a person must review before the code they cover is written. Review them in one sitting, at step 2 of the build order.
- Run the checks in this order and stop at the first failure:
  1. `python3 -m unittest discover -s tests -v`
  2. `python3 -m compileall -q src && python3 -W error -m quoteintake.lint` (stdlib-only lint: unused names, bare `except`, `eval`/`exec`/`shell=True`, imports outside the standard library)
  3. The security review in section 5.
  4. Only then, an AI code review.
- No test may call the AI. Downstream code is tested with hand-written reader and checker outputs in `tests/fixtures/`.

## 2. Parts and interfaces

Each part is a pure function or a small class on plain dataclasses. Parts 1 to 8 do no network calls except part 2. A part never reaches into another's internals.

| # | Part | In → Out |
|---|---|---|
| 1 | `intake` | `.eml` path → `Message` (id, sender, date, subject, body text, attachments with extracted text or `unreadable`) |
| 2 | `ai` | `Message` → `ReaderResult`, then `Message + ReaderResult` → `CheckerResult`. One `AIClient` interface; the real one uses `urllib` to the Anthropic API, the fake one is for tests. Sends the email text and nothing else, with no tools. |
| 3 | `compare` | `ReaderResult + CheckerResult` → `agree` or a list of reasons |
| 4 | `match` | `ReaderResult + records` → `Matches` (customer, per-part status, open request, drawing present, date checks, quote-phrase check, injection hit) |
| 5 | `classify` | `Message + all results` → one pile with reasons |
| 6 | `enrich` | requests + records → history brief, fast-track flag, bid odds, low-odds flag |
| 7 | `schedule` | ready requests + hours file → order, expected finish, at-risk flag |
| 8 | `outputs` | everything → `dashboard.html`, `erp-import.csv`, one run-log line |
| 9 | `run` | orchestration: the 200-email cap, "couldn't process" handling, write outputs |

## 3. Business rules (each one gets a test)

**Reading and checking**
- R1. Email kind is one of: new request, chaser, revision, award or no-thanks, other.
- R2. For a request, each part has part number, revision, quantity, requested delivery date. The quote due date is optional. Every value carries its exact source words.
- R3. Every source phrase must appear in the email or its attachment text word for word, or the email goes to a person.
- R4. The checker returns per part and value: what the email says, and clear or ambiguous. It also returns anything left out and any line aimed at an AI.
- R5. If reader and checker disagree, or the checker flags ambiguity or an omission, the email goes to a person with the reason.

**Matching (exact matches only; more than one candidate means ask a person)**
- R6. The sender maps to exactly one customer, or the email goes to a person.
- R7. Each part is classified as made before at this revision, known at another revision, or new. A part on file as something else goes to a person.
- R8. A chaser or revision maps to exactly one open request, or goes to a person.
- R9. Every new part has a drawing attached.
- R10. Dates are not before the email's date and not more than a year after it.

**Piles**
- R11. Pile order of precedence: needs a person, then not a request, then needs info, then ready. Needs a person covers: unplaceable sender, part on file as something else, instructions aimed at an AI, unreadable attachment, unusable AI answer, no readable text, and all disagreements.
- R12. Needs info means a quantity, revision or drawing is missing. It comes with a drafted question asking only for what is missing.
- R13. Not a request is routed to a destination: chaser to the request holder, revision to its request, award to sales, pitch to nowhere.

**Enrichment**
- R14. A repeat part is one made or quoted before. Its history brief holds the last quote (date, quantity, unit price, won or lost), the revision then against now, and estimated against actual hours on recent jobs.
- R15. Fast-track needs all of: same revision, quoted in the last 3 years, job history present.
- R16. Bid odds are the customer's new-part win share over 3 years, pulled toward the shop's rate when there are few quotes. Low odds means far below the shop's rate. It is display only and never changes order or declines.

**Order and risk**
- R17. Ready queue order is: stated due date soonest first, then key accounts, then oldest first. With no due date, use received date plus 6 working days.
- R18. Expected finish comes from each request's estimated quoting time (more lines and weldments mean longer) against the estimators' hours this week. A request that would miss its due date is flagged at risk and nothing else happens.

**Outputs**
- R19. The dashboard has, in order: pile counts, needs-a-person list with reasons, at-risk list, ready queue, and 5 random ready requests for spot-checking.
- R20. The ERP file has one row per line for ready and waiting-on-answer requests, in a fixed column layout.
- R21. Run limit is 200 emails to the AI per run. The excess is listed and picked up next run. Nothing is silently dropped. Each run appends one log line: time, model, email count, count per pile.

## 4. Acceptance tests

**Tests first, in this order:**

1. ★ **Answer-key scorer** (`tests/test_score.py`). Loads `answer-key.csv` and a results file, and counts three error types: let through but wrong (worst), stopped needlessly, sent to the wrong place. It is tested on small hand-made result sets, including a weights check that "let through but wrong" always outranks the others.
2. ★ **Rule tests R1 to R21**, one or more per rule, from the fixtures. Include these edge cases:
   - ambiguous date `4.3.2025`
   - quantity that could belong to two parts
   - a quote phrase that is paraphrased, not exact
   - two customers that could match one sender
   - a drawing missing for one of three parts
   - a due date in the past and one 13 months out
   - the cap at 201 emails
3. ★ **Security tests** (section 5).
4. Output tests: dashboard sections in order, 5 spot-checks drawn from ready only (fixed seed in tests), ERP column layout matches the agreed file.
5. Plain tests for `intake` (eml parsing, spreadsheet text, unreadable attachment) and `schedule` (working-day arithmetic).

**Answer-key run (live AI, costs money, a person starts it):** `python3 -m quoteintake.run --mailbox <dir> --records <dir> --hours <file> --out <dir> && python3 -m quoteintake.score answer-key.csv <out>/results.csv`. The gate for going live is in open question 4. Re-run it after any change, including a new model version.

## 5. Security: rule, where enforced, proof

| Rule | Enforced in | Test that proves it |
|---|---|---|
| Read-only mailbox; can't send, move or delete | Tool only reads `mailbox/` files; no mail protocol code exists | Lint bans `smtplib`, `imaplib`, `poplib`, and Graph/MSAL imports; hash the mailbox dir before and after a run: unchanged |
| Never writes to the ERP | `outputs` writes only to `--out` and the log | Run with `records/` read-only and check that only `--out` and the log file changed |
| Credentials from environment or secret store | `ai.client` | Lint scan for key-shaped strings; missing key gives a clear error; key value never appears in outputs or log (plant a sentinel key) |
| AI gets the email and nothing else, no tools | `ai.client` request builder | Plant a sentinel customer name in `records/`; with the fake client, assert the sent payload never contains it and has no `tools` field |
| AI answer counts only after checker agrees and code matches it | `compare`, `match`, `classify` | Reader-only valid answer with checker missing or disagreeing never reaches ready |
| Email is untrusted; instruction aimed at an AI goes to a person | Three detectors: reader, checker, code (`match`) | Three tests, each with only one detector firing, each ending in needs a person |
| Email text is escaped on the dashboard and in the import file | `outputs` | Fixtures with `<script>`, `"><img onerror=…>`, and cells starting `=`, `+`, `-`, `@`; assert escaped HTML and neutralised CSV cells |
| Standard library only | Lint | Every import is in `sys.stdlib_module_names` or is a local module |
| Never sends, changes mail, writes to the ERP, prices, or declines | `classify`, `outputs` | No "declined" pile exists; no price field in either output; at-risk and low-odds do not change a request's pile |
| Output readable only by estimating and sales | `run` creates the dir `0750` and files `0640`; the group itself is set by the server | Mode test on created files; the group itself is an ops task |
| AI calls go only to the Anthropic API | `ai.client` | Test that the URL is allow-listed and that any other host is refused |
| Log holds counts only | `run` | Log line contains no sender, subject or body text |
| Hostile attachments (proposed addition) | `intake` | Size and decompression caps on spreadsheets and PDFs; an oversized or malformed file becomes `unreadable`, which goes to a person |

The security review (step 3 of the checks) is a person-or-agent read of `ai/`, `intake/` and `outputs/` against this table, with findings listed before any AI code review runs.

## 6. Build order (one commit group each)

1. Skeleton, dataclasses, lint tool, import check, fixtures folder.
2. **Stop: a person reviews all ★ tests.**
3. `intake`.
4. `match` (R3, R6 to R10, code injection check).
5. `compare` and `classify` (R5, R11 to R13).
6. `enrich` (R14 to R16).
7. `schedule` (R17, R18).
8. `ai` (fake client first, then the real one with the security tests).
9. `outputs` (R19, R20).
10. `run` (R21, cap, logging, permissions).
11. Security review, then AI code review, then a person starts the answer-key run.

## 7. Out of scope

- Sending email, moving or deleting mail, or reading the live M365 mailbox (the copy step does that).
- Writing to the ERP, the nightly ERP export, and maintaining the hours file.
- Pricing, declining, and any action on at-risk or low-odds flags.
- Scheduling and server setup (the 15-minute timer), and the folder's group permissions.
- OCR of scanned documents.
- The queue-replay evaluation (judging order, at-risk, fast-track and odds together). Build it after v1 if you want it.

## 8. Open questions before building

1. **State between runs.** The tool runs every 15 minutes. How does it know which emails are new, and is the dashboard rebuilt from all open requests or only that run's emails? I'd suggest a small state file of processed email IDs and results, which means a rule for when old items drop off.
2. **File layouts.** I need the `answer-key.csv` columns and labels, the CSV schemas in `records/`, the hours-file format, and the ERP import column layout. Without real samples the agent will invent them.
3. **Missing numbers.** What are the values for:
   - how far "pulled toward the shop's rate" goes (a minimum quote count would do);
   - "far below" for low odds;
   - quoting-time per line and per weldment;
   - who counts as a key account (is it a tier value?);
   - working-day holidays.
4. **Go-live bar.** Is it zero "let through but wrong" on the answer key, or a rate? And what limits apply to the other two error types? I suggest zero for the worst error.
5. **The 200 cap.** Is it 200 emails (up to 400 calls)? Does a non-request email get only the reader call, or both?
6. **Lint and PDFs.** Standard library only rules out ruff and bandit, so the plan uses a homemade lint. Is that acceptable, or may dev-only tools be installed? Also, stdlib PDF text extraction handles only simple text PDFs; scanned or complex PDFs will go to a person. Is that fine for the roughly 20% of requests with a buyer form?
7. **Injection patterns.** The code-side detector is a pattern list and will miss clever phrasing. Is that acceptable given the other two detectors, or do you want a stricter rule such as sending any email with attachments containing imperative phrases to a person?
8. **CSV neutralising.** Part numbers can legitimately start with `-` or `+`. Should the import file prefix a quote character to such cells, or reject the row to a person?
9. **Waiting-on-answer.** Does the import file include "needs info" requests before the buyer replies, and what happens to their rows when the answer arrives (new rows, or updates)?
