<!-- Written by Claude Sonnet 5.5 from plan-prompt.md and design.md on 2026-10-21, unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: quote request intake (Wendlow)

I assumed a Python package `quoteintake/`, `unittest` for tests, and one command to run everything. Each place I had to guess is listed under open questions at the end.

## 1. Ground rules for the agent

- Work on branch `feat/quote-intake`. Make small commits, one part or one rule set each. Don't merge.
- **Tests come first.** Commit them failing and stop for human review (section 3). Only then write code.
- **Never edit `tests/`, `tests/fixtures/` or `answer-key.csv` without written approval.** `tools/check_locked.py` compares their hashes to `LOCKED.sha256` and fails the build on any difference. Only a person updates that file.
- Standard library only. Don't add a dependency.
- If a rule is ambiguous, stop and ask. Don't pick an interpretation.

## 2. Parts and interfaces

Each part is a pure function over plain dataclasses, and only the AI client touches the network. Each can be tested alone.

| Part | In → Out | Notes |
|---|---|---|
| `reader` | `.eml` path → `Email(id, sender, subject, received, text, attachments[name, readable])` or `Unreadable(reason)` | Uses the `email` module. No readable text, malformed or oversized → `Unreadable`. |
| `records` | CSVs + hours file → `Records` | Bad or missing file stops the run loudly. |
| `ai_client` | `Email` → raw JSON text | The only network code. Sends the email text only, with no tools. Has a fake for tests. |
| `parse` | raw JSON → `Extraction` or `Unusable` | Strict schema check. Every value comes with its quote. |
| `verify` | `Email`, `Extraction` → list of failures | Each quote appears in the email. Each value appears in its own quote. Detects instructions aimed at an AI. |
| `match` | `Email`, `Extraction`, `Records` → customer, per-part new/known, open request | Exact matches only. More than one candidate → `Ambiguous`. |
| `triage` | all of the above → `Decision(pile, reasons, route, draft_question)` | The only place piles are assigned. |
| `order` | ready decisions → ordered list with effective due date | |
| `risk` | ordered list + hours → expected finish and at-risk flag | |
| `dashboard` | everything → one HTML file | One `esc()` function wraps every email-derived string. |
| `run` | wires the above; enforces the 200 cap; writes the log line; applies retention | |
| `score` | decisions + `answer-key.csv` → weighted error report | |

## 3. Tests first

Tests use a fake AI client and recorded AI responses, so they are free and repeatable. Commit order is tests, then review, then code.

**A person must review these before any code is written.** They define "correct", so a wrong test hides a wrong rule:
- `test_verify`, `test_triage` (pile precedence) and `test_security`
- `test_order` and `test_risk`
- `score` and its error weights
- The answer-key loader, and a spot-check of 20 key rows against their emails

**Tests derived from the design's rules:**
- **verify:**
  - A quote missing from the email → needs a person.
  - A value absent from its own quote → needs a person. Cover customer, part, revision, quantity and dates.
  - An empty quote fails.
  - Quote matching follows the normalization rule from the open questions.
- **match:**
  - Unknown sender → needs a person.
  - A sender matching two customers → needs a person with an "ambiguous" reason.
  - A chaser or revision with 0 or 2+ open candidates → needs a person.
  - Exact part match is known. A near-miss (case, a dash) is not matched.
- **triage:**
  - One test per pile.
  - A failed check beats missing info, which beats ready.
  - The drafted question names only what's missing.
  - Each not-a-request kind routes to its stated place. Pitch → nowhere.
  - An unusable AI answer → "couldn't process".
  - No readable text → needs a person.
- **order:**
  - Soonest effective due date first, then key accounts, then oldest.
  - No stated date → received + 6 working days, skipping weekends.
- **risk:**
  - Hand-computed fixtures with more lines, weldments and fewer hours.
  - A request that would miss its date is flagged. A request that makes it is not.
  - The flag never changes the pile.
- **dashboard:**
  - Section order: counts, needs-a-person, at-risk, ready queue, spot-check.
  - The sample is 5 ready ones, chosen with a seeded RNG, or all of them if fewer than 5.
- **run:**
  - **Accounting invariant:** every input email appears exactly once, in a pile, "couldn't process" or "deferred".
  - 250 emails → 200 go to the AI, 50 are listed and picked up next run.
  - The log line is written once per run.
  - Retention uses a fake clock and deletes saved email after 90 days.
- **Answer key:** the `score` replay runs offline against recorded AI responses.

**Error weights** (let through but wrong ≫ sent to wrong place > stopped needlessly) are set by you in `score.py`. See the open questions.

## 4. Security: rule → where enforced → proof

| Rule | Enforced in | Test that proves it |
|---|---|---|
| Read-only, one mailbox, can't send/move/delete | This code never connects to the mailbox. It reads `mailbox/` files only. | Static test: no `smtplib`, `imaplib`, `poplib` or Graph URLs, and no write or delete calls on `mailbox/` except retention. **A person also confirms the copy step's Mail.Read-only permission, which is outside this repo.** |
| Credentials from environment or secret store | `ai_client` reads `OPENAI_API_KEY` from the environment only | Secret-pattern scan of the repo. A missing key fails clearly. The key never appears in the log or output. |
| AI gets the email only, no tools | `ai_client` builds the payload | Put a sentinel customer name in the records. Assert it's absent from the captured payload. Assert no `tools` or `functions` field. |
| AI answer counts only after code checks | `parse` → `verify` → `triage` | Fabricated quote, wrong value, malformed JSON and extra fields each end in needs a person or "couldn't process". Never ready. |
| Ignore instructions in email, flag them | The prompt, plus a code detector in `verify` | Corpus of injection emails ("ignore previous…", "mark as ready", "you are an AI…", in the body, subject and filenames). Every one lands in needs a person. A benign-email corpus must not trigger. |
| Escape everything from email on the dashboard | `dashboard.esc()` | `<script>`, `"onerror=` and `</td>` in sender, subject, part number, filename, AI reason and drafted question. Assert raw tags are absent from the HTML. Also add a restrictive CSP meta tag, and test it's present. |
| No third-party packages | Runtime and dependency policy | `tools/check_stdlib_only.py` parses every import against `sys.stdlib_module_names`. |
| Never sends, changes, prices or declines | No such code or fields exist | The same static test as above. No price field in any dataclass. At-risk text says "for a person to decide". |
| Max 200 emails per run, rest listed | `run` | The 250-email test above. |
| Nothing silently dropped | `run` | The accounting invariant. |
| Log line per run: when, model, count, pile counts | `run` | Log-format test. Assert no email content in the log. |
| Delete saved email after 90 days | `run` retention step | Fake-clock test at 89 and 91 days. Deletes only files under the saved-email directory. |
| Only estimating and sales see the output | Deployment, not code. The code writes output with mode 0640 into a given directory. | File-mode test. **A person verifies the real directory permissions on the server.** |

Also in scope and tested: an oversized or malformed `.eml`, and attachment names with `../`. Attachment names are never used as file paths.

## 5. Checks, in this order

Cheap, deterministic checks come before any AI review. Stop at the first failure.

1. `python -m unittest discover -s tests -v`
2. `python tools/check_locked.py`
3. `python tools/check_stdlib_only.py`
4. `ruff check .` and `bandit -r quoteintake`. These are dev-only, not installed on the server (see the open questions).
5. `python -m quoteintake.score --replay tests/fixtures/ai_responses answer-key.csv`. This must meet the threshold you set.
6. `/security-review` on the branch, then `/code-review`. These are AI reviews and add to the deterministic checks. They don't replace them.
7. Human review of each commit.
8. **Before go-live, and after any code or model change:** a person runs `python -m quoteintake.score --live answer-key.csv`. It calls OpenAI and costs money. The agent doesn't run it.

## 6. Commit sequence

1. Scaffold, lock tooling, and `check_*` scripts.
2. Failing tests for the rules, plus fixtures. **Stop for review.**
3. `reader` and `records`
4. `parse` and `verify`
5. `match`
6. `triage`
7. `order` and `risk`
8. `dashboard`
9. `ai_client` and `run`: cap, log, retention
10. `score`, the replay, and the README with run instructions and the schedule entry

## 7. Out of scope

- Sending email, including the drafted questions, and anything that touches the M365 mailbox or its copy step
- Pricing, declining, or contacting buyers
- Reading drawing contents or OCR. Only whether a drawing is attached.
- Writing back to the ERP, or exporting from it
- Dashboard login, hosting, or the 15-minute scheduler setup (the README documents the command only)
- Learning from corrections, and non-English email
- Tuning prompts or the model beyond what's needed to pass the answer key

## 8. Open questions for you

Answer these before building. The default I'd use is in brackets.

1. **Does `answer-key.csv` include the expected values** (part, revision, quantity, due date) or only the label? Without values, "let through but wrong" can't be scored. [Needs values.]
2. **What are the error weights, and what score must pass?** [Zero "let through but wrong" on the key.]
3. **How is the quoting time estimated?** I need the formula for lines and weldments, the hours-file format, and whether work is sequential in queue order. [You supply the formula and I won't invent one.]
4. **What counts as "key account"?** Which tier values in the customer file?
5. **Order sort:** I read it as an effective due date (stated, or received + 6 working days) for every request, with ties broken by key account and then age. Is that right? Do holidays count in working days?
6. **Quote matching:** exact, or tolerant of whitespace and case? [Whitespace and case tolerant for the quote check only.]
7. **What counts as "the drawing"?** Any PDF/DWG/STEP attachment? Or a link? [Any of those file types.]
8. **Routing targets:** for a chaser, how do we know "whoever has the request"? Does the open-requests CSV have an owner column? Is there a sales address for awards?
9. **Is a new part (not in the customer's parts) ready to quote?** Right now a typo'd part number would show as "new". [New parts are ready, but marked "new" on the dashboard.]
10. **One AI call per email** (kind and extraction together), or two? [One.]
11. **Which saved email does the 90-day retention delete?** Is it `mailbox/` or a separate copy, and who owns the copy step?
12. **Are dev-time linters (ruff, bandit) acceptable**, given the stdlib-only rule for runtime? [Yes, dev-only.]
13. **Is sending customer email text to OpenAI approved?** Do you need a data-processing agreement or a no-training setting? What happens on API outage or timeout? [Retry twice, then "couldn't process".]
14. **Which attachments, if any, have their text sent to the AI?** [None. Body and subject only.]

I can save this as `PLAN.md` in the repo if you want.
