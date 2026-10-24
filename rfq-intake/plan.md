<!-- Written by Claude Sonnet 5.5 from plan-prompt.md and design.md on 2026-10-23, unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: Wendlow quote desk

Module names, commands and numeric defaults below are my proposals. They are marked as assumptions where the design doesn't say.

## 1. Ground rules for the agent

- Python standard library only, run on a version you name (see Q8). Tests use `unittest`.
- Work on branch `quote-desk-v1`, in small commits. Each module gets two commits: tests first (red), then implementation (green).
- **The agent may not edit `tests/`, `fixtures/` or `answer-key.csv` without approval.** `tests/LOCK.sha256` holds their hashes. `tools/check_lock.py` fails the gate if they differ, and only a person updates the lock. If a test looks wrong, the agent stops and asks.
- The Claude API is the only network call, and it lives in one module. Every test uses a fake client, so no test calls the AI.

## 2. Parts and interfaces

Each part is a pure function over plain dataclasses, except `ingest`, `extract` and `run`, which touch files or the network.

| Part | In → Out | Rules it owns |
|---|---|---|
| `ingest` | `.eml` → `Message(id, sender, subject, body, attachments[name, text])` or `Unreadable(reason)` | Extracts text from xlsx and csv (zip and XML) and from PDFs. Rejects oversize files, zip bombs and XML with a DOCTYPE. No readable text → needs a person. |
| `records` | CSVs → typed tables | Fails loudly on a missing column. |
| `extract` | `Message` → `Extraction` or `Unusable` | Sends the email text and attachment text only, with no tools. Asks for kind, customer, and per-line part, revision, quantity, delivery date and due date. Each value comes with its exact quote and its source (email or attachment name). |
| `verify` | `Extraction`, `Message` → `Verified` or a list of failures | Each quote appears verbatim in its named source, and each value appears in its quote. Detects instructions aimed at an AI. |
| `match` | `Verified`, `records` → customer, part (known or new), open request | Exact matches only. Zero or several candidates → ask a person, never guess. |
| `triage` | all of the above → pile, reason, drafted question | Ready / needs info / needs a person / not a request, with routing. The question asks only for what is missing. |
| `history` | part, records → brief, fast-track flag | Same revision, quoted within 3 years, with job history → fast-track. |
| `odds` | customer, records → rate, low-odds flag | Win rate on new-part quotes over 3 years, shrunk toward the shop rate. |
| `queue` | ready requests, estimator hours → order, expected finish, at-risk | Order: due date, then key account, then oldest. A missing due date means 6 working days. At-risk is only a flag. |
| `report` | results → `dashboard.html` | Order: needs-a-person, at-risk, ready queue, then 5 random ready requests. The random pick is seedable. |
| `erp_export` | results → `erp_import.csv` | Fixed columns, one row per line. |
| `run` | everything → outputs, log line | Cap of 200 emails to the AI per run. Overflow is listed and picked up next run. Nothing is dropped silently. |
| `tools/score` | run output, `answer-key.csv` → weighted error report | Reports the three error types separately. |

## 3. Business rules to pin down in tests

- **Fail closed.** Any failed check, ambiguity or unusable AI answer goes to a person, and the reason is shown.
- **Error cost.** Let-through-wrong costs most, then wrong destination, then stopped needlessly. `score` reports the three counts and a weighted total.
- **Nothing priced or declined by the tool.** Piles and flags have no "decline" state. The only prices in the output are historical ones in the brief.
- **Odds** (assumed): `(wins + k·shop_rate) / (n + k)`, with k and the "far below" cutoff set in config (Q4).
- **At-risk** (assumed): simulate the queue in order against this week's hours and flag anything finishing after its due date.

## 4. Tests first

Order of work:
1. Fixtures. Build a small `.eml` set by hand, one per rule below plus some from the answer key.
2. Unit tests per part.
3. An end-to-end test using the fake AI.
4. `score` run against the full answer key.

**A person must review before the agent builds on them:**
- `answer-key.csv` and the fixture set. Check that the labels are right and that every rule has a fixture.
- All `verify`, `match` and `triage` tests. These are the let-through-wrong guards.
- The security tests in section 5.
- The `score` weights and the acceptance thresholds.
- The expected values for `queue`, `odds` and `history`. The agent can't be trusted to compute these independently.

## 5. Security: rule, enforcement, proof

| Rule | Enforced in | Test |
|---|---|---|
| Read-only to the mailbox | `ingest` only reads `mailbox/`. There is no M365, IMAP or SMTP code. | AST scan bans `smtplib`, `imaplib`, `http.client` outside `extract`, and file writes to the input dirs. End-to-end run on a read-only copy of `mailbox/` and `records/`; hashes unchanged afterward. |
| Credentials never in code | `config.py` reads `ANTHROPIC_API_KEY` from the environment. If it's missing, the run stops. | Regex scan of the repo for key patterns. Fake key never appears in the log or output. |
| AI sees the email only | `extract` builds the payload from `Message` alone. | Fake client captures the request. Seeded record names and part numbers are absent, and there is no `tools` field. |
| AI answer counts only after code checks | Type system: `triage` accepts only `Verified`. | Fabricated quote, value not in quote, wrong source name, and malformed JSON all → needs a person. |
| Email is untrusted | `verify` flags injection phrases. `report` escapes all email-derived text. | A fake AI that "obeys" an injected email still ends up in needs-a-person. A `<script>` payload in subject, sender, filename, part number and quote appears escaped in the HTML. |
| CSV injection (added by me) | `erp_export` neutralizes cells starting with `= + - @`. | A part number `=cmd|...` is written safely. |
| Hostile attachments (added by me) | `ingest` limits size, ratio and entity use. | Zip-bomb and DOCTYPE fixtures → needs a person, no crash. |
| Stdlib only | Import allowlist via `sys.stdlib_module_names`. | The test fails on any other import. |
| Never sends, moves, writes to the ERP, prices or declines | No such code. The only writes are to the output dir and the log. | Import ban plus a filesystem-write check on the end-to-end run. The pile enum has no decline. |
| Output folder restricted | `run` creates it with mode `0750`. | Mode assertion. Group ownership is a deploy step (Q9). |
| Log has counts, no email content | `run` writes one line: time, model, emails, per-pile counts. | The log contains no sender, subject or body from fixtures. |
| 200 per run, nothing dropped | `run` | 250 fixtures → 200 sent, 50 listed and handled next run, 0 lost. |

## 6. Deterministic gate, before any AI review

Run this in order. All steps must pass before a commit is proposed for review:

```
python tools/check_lock.py                          # tests/answer key unchanged
python -m compileall -q src tools                   # syntax
python -m unittest discover -s tests -v             # all tests, fake AI
python tools/score.py --key answer-key.csv --fake-ai fixtures/ai_answers/   # replay scoring
```

Add a linter if Q8 allows one. Without one, the import-allowlist test and `compileall -W error` are the lint.

Then run `/security-review` on the branch, followed by a person's review. A real-model run of the answer key happens once at the end, outside the gate. It is required again after any change, including a model version bump.

**Acceptance:** zero let-through-wrong on the answer key, stopped-needlessly at or below a threshold you set (Q6), and all tests green.

## 7. Build order (each step is a test commit and an implementation commit)

1. Scaffold, config, lock and gate scripts.
2. `records`, `ingest`.
3. `verify` (the core safety check).
4. `extract` with a fake client, then `match`.
5. `triage`.
6. `history`, `odds`.
7. `queue`.
8. `report`, `erp_export`.
9. `run`: cap, log, state across runs.
10. `score`, then the full answer-key run with the real model.

## 8. Out of scope

- Sending email, including the drafted questions.
- Writing to the ERP.
- Pricing, declining, and any M365 integration. The copy step is separate.
- The mailbox copy's retention.
- The 15-minute scheduler and server setup, beyond a runnable `python -m quotedesk.run`.
- The estimator-queue replay's data pipeline, beyond what `score` needs.
- Learning or tuning from outcomes.

## 9. Open questions to answer before building

1. **PDFs.** The standard library can't reliably read PDFs. Options: (a) a minimal text-layer reader, with everything else going to a person; (b) allow one external tool such as `pdftotext` as a separate step; (c) pass the PDF to Claude, which breaks the "quote appears in the attachment" check. I recommend (b). How many answer-key emails depend on PDFs?
2. **Answer key.** What are its columns? Does it include expected extractions or only the final pile? Can I hold out about 20% unseen until the end, to catch overfitting?
3. **Email kind.** I assumed the AI classifies and code verifies it (a chaser must match an open request). Correct?
4. **Numbers.**
   - Shrinkage strength and the "far below" cutoff for bid odds.
   - Which tier values count as key accounts.
   - The holiday calendar for working days.
   - How quoting time is calculated, and where "weldment" comes from.
   - The format of the estimator-hours file.
5. **ERP file.** What are the exact columns? Does "waiting on its answer" mean needs-info only?
6. **Thresholds.** What stopped-needlessly rate is acceptable? What does the replay need to show to count as success?
7. **Data to Anthropic.** Is sending customer emails and attachment text to the API approved? Which model ID? What happens if the API is down: retry, or leave the email for the next run?
8. **Tooling.** Which Python version? Are dev-only tools (ruff, bandit) allowed, given "no third-party packages" is meant for runtime?
9. **Mailbox access.** The tool never touches M365, so who confirms the copy step uses a read-only app permission? Who sets the output folder's group?
10. **State.** How should it remember which emails it has handled across 15-minute runs? I'd use a small JSON file in the output dir. Is that fine? Also, what should happen when the same email is re-sent or edited?
11. **Drafted questions.** Is a fixed template acceptable, or should the AI write them? An AI-written draft would need its own check that it asks only for the missing fields.
