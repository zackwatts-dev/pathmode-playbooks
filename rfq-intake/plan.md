<!-- Written by Claude Sonnet 5.5 from plan-prompt.md and design.md on 2026-10-20, unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: quote request intake (Wendlow Fabrication & Machine)

Python 3, standard library only. The pipeline reads `.eml` files and CSVs and writes one HTML file and a log.

## 1. Ground rules for the agent

- **Branch:** work on `intake-v1`. Never commit to `main`.
- **Commits:** one small commit per step in section 6. Each commit must pass all the gates in section 5.
- **Tests and answer key are frozen.** The agent may not edit `tests/`, `fixtures/`, `answer-key.csv` or `tests.manifest.sha256` without approval. `tools/check_frozen.py` compares their hashes to the manifest, and a mismatch fails the gate. If a test seems wrong, the agent stops and asks.
- **Order of work:**
  1. Write tests from the rules below.
  2. A person reviews them.
  3. The manifest is then created.
  4. The agent writes code until the tests pass.
- **No AI in tests.** The model sits behind an `Extractor` interface. Tests use a fake, and the scorer replays recorded model answers.

## 2. Parts and interfaces

Each part is its own module and takes plain data in and out, so it can be tested alone. Only `extract_ai` touches the network.

| Module | In → Out | Notes |
|---|---|---|
| `eml_reader` | `.eml` path → `Email(id, sender, subject, received, body_text, attachments[], readable)` | No readable text means `readable=False`. Never writes to `mailbox/`. |
| `records` | CSV dir → typed records (customers with tier, buyers, parts, open requests) | A malformed row is a load error, never skipped silently. |
| `extract_ai` | `Email` → `Extraction(kind, customer, lines[], due_date, each value with its quote)` or `Unusable(reason)` | Sends the email and a fixed prompt only. No records, no tools. Uses `urllib` and a fixed host. |
| `verify` | `Email`, `Extraction` → list of failures | Every quote is a substring of the email. Every value is in its quote. |
| `match` | verified `Extraction`, records → `Matches` | Exact only. Returns `none`, `one` or `many`, and `many` is never resolved. |
| `injection` | `Email` → bool | Deterministic pattern scan for text aimed at an AI. |
| `piles` | all of the above → `(pile, reasons, draft_question?, route?)` | Precedence is in section 3. |
| `schedule` | ready items, estimator hours, today → order, expected finish, at-risk flag | Pure functions with the clock passed in. |
| `dashboard` | results → one HTML string | Everything from an email goes through `html.escape(quote=True)`. |
| `run` | orchestrates | Applies the 200-email limit, keeps state, writes the log, purges after 90 days. |

## 3. Business rules to turn into tests

**Pile precedence:** needs a person, then not a request, then needs info, then ready. When in doubt, stop.

**Needs a person**, with the reason shown, if any of these hold:
- A quote is not in the email, or a value is not in its quote.
- The sender matches no customer or buyer, or matches more than one.
- Injection text is found.
- An attachment is unreadable.
- The AI answer is unusable.
- The email has no readable text.
- A chaser or revision matches more than one open request, or none.

**Needs info:** a quantity or revision is missing. Include a drafted question. The draft is text only and is never sent.

**Not a request**, routed by kind:
- A chaser goes to whoever holds the request.
- A revision is attached to its request.
- An award or "no thanks" goes to sales.
- A pitch goes nowhere.

**Ready:** customer matched, and every line has part number, revision and quantity. A new part (one we haven't made before) is still ready, but it is labelled new.

**Order:**
1. Due date, soonest first.
2. Key accounts.
3. Oldest received.

A request with no due date gets received date plus 6 working days. The sort must be stable and deterministic.

**At risk:** walk the ordered queue, consume estimator hours by estimated quoting time, and compute each request's finish. If finish is after due, flag it at risk. Nothing is ever declined by code.

**Run rules:**
- Send at most 200 emails to the AI per run. The rest are listed for a person and picked up next run.
- Never drop an email silently. The numbers in all piles plus the over-limit and couldn't-process lists must equal the number of emails.
- Each run appends one log line: time, model, count, count per pile.
- Delete saved email after 90 days.
- Pick 5 ready items at random for spot-check. Take the seed as a parameter, and take all 5 if there are fewer than 5.

**Dashboard order:** counts, needs a person (highlighted, with reasons), at risk, ready queue (due date and expected finish), spot-check.

## 4. Tests first

**Needs human review before any code is written** (the agent must not self-approve these):
- `test_scoring`: the scorer and the cost weights for the three kinds of mistake.
- `test_piles`: one test per rule in section 3.
- `test_verify` and `test_match`: the exact-match and ambiguity cases.
- `test_schedule`: ordering and at-risk worked examples. A person works the expected numbers by hand.
- `test_security_*`: everything in section 7.
- The answer key itself, plus the fixture emails. Make sure injection and ambiguous cases are in there.

**Scoring harness** (`tools/score.py`):
- `--replay` runs the whole pipeline on the answer key using recorded model answers. It is deterministic and runs in the gate.
- `--live` calls the real model. A person runs it, not CI, and it's required after any prompt, code or model-version change.
- Output is a confusion table by pile and counts of the three mistake types.
- Release gate (proposed): zero "let through but wrong" on the key. Other thresholds are set in the questions below.

## 5. Gates, in order

Every commit and the final branch run these. A failure at any step stops the run.

```
python3 -I tools/check_frozen.py                 # tests/key unchanged
python3 -I -m compileall -q src tests tools      # syntax
python3 -I tools/check_lint.py                   # stdlib-only imports, no bare except, no eval/exec/shell=True
python3 -I -m unittest discover -s tests -v      # all rules and security tests
python3 -I tools/score.py --replay --key answer-key.csv
```

Then, only if all of those pass:
1. Run `/security-review` on the branch diff.
2. A person reviews the review findings, the `--replay` table and the commits.
3. A person runs `--live`.

## 6. Commit sequence on `intake-v1`

1. Skeleton, `Email` and `Extraction` types, the gates, frozen manifest. Tests land first and are approved.
2. `eml_reader` and `records`.
3. `verify`.
4. `match`.
5. `injection`.
6. `piles`.
7. `schedule`.
8. `dashboard`.
9. `extract_ai`: prompt, `urllib` client, fake and recorded-replay modes.
10. `run`: limit, state, log, retention.
11. `score.py` live mode, README with run commands and the cron line.

## 7. Security: rule, where enforced, proof

| Rule | Enforced in | Proving test |
|---|---|---|
| Read-only, never sends, moves or deletes email | The code has no mail client and only opens `mailbox/` for reading. Mailbox permissions are enforced outside the repo (see Q9). | The `mailbox/` hash is identical before and after a run. The lint tool fails on `smtplib`, `imaplib` or `os.remove` on mailbox paths. |
| Credentials from environment, never in code | `extract_ai` reads `OPENAI_API_KEY` only. | A missing key gives a clear error with no call made. A repo scan for key patterns finds none. A canary key value never appears in the log or HTML. |
| The AI gets the email and nothing else, no tools | `extract_ai` payload builder | A canary customer name and part number from `records/` is absent from the outgoing request body. The request has no `tools` field. |
| AI output counts only after code checks it | `verify`, then `piles` | A fake AI returns a quote not in the email, or a value not in its quote. The result is "needs a person". |
| Email is untrusted, instructions ignored | The prompt, plus `injection` and `piles` | Injection fixtures land in "needs a person" with a reason. A fake AI that obeys the injection still cannot change a pile. |
| Everything from email escaped on the dashboard | `dashboard` | `<script>`, `"onerror=` and `&` in subject, sender, part number and quote come out escaped. A parse check finds no unescaped tags from input. |
| Standard library only | `check_lint` | Every import is checked against `sys.stdlib_module_names`. A planted third-party import fails the gate. |
| Never prices, declines or sends | `schedule`, `dashboard` | No price field exists. The at-risk output is a flag only. The only network host used is `api.openai.com`. |
| Over 200 emails, nothing silently dropped | `run` | With 250 fixtures, 200 go to the fake AI and 50 are listed. Pile totals sum to 250. |
| 90-day retention | `run` | With a fake clock, only files older than 90 days are deleted. |
| Only estimating and sales see the output | Output directory mode `0750`, file mode `0640`, group set by deployment | The test checks the modes. Group membership is an ops check (Q9). |
| No email content in the log | `run` | The log line has only the fields listed in section 3. |

## 8. Out of scope

- The step that copies mail from quotes@ into `mailbox/`, and the Microsoft 365 permissions.
- The ERP export.
- Sending, moving or deleting email. The drafted questions are text only.
- Pricing, declining, and any automatic decision about quoting.
- Reading drawing contents (see Q4).
- Hosting, the scheduler setup, and a web server for the dashboard.
- Learning or tuning from outcomes.

## 9. Open questions to answer before building

1. **Answer key:** What are its columns, and how many rows are there? Does it hold the expected pile, the expected extracted values, the expected route, and the due dates? Does it have injection, ambiguous-sender and unreadable-attachment examples? If not, someone has to add them.
2. **Mistake weights and pass mark:** Do you accept "zero let-through-wrong on the key" as the go-live gate? What numbers do you want for "stopped needlessly" and "wrong place"? Without a pass mark, "re-run the answer key" has no decision attached.
3. **Quoting time:** What is the formula for likely quoting time (hours per line, weldment multiplier)? Is it one pooled estimator capacity, or per-estimator? What is the format of the hours file?
4. **Attachments:** Does the AI see only the email text? Standard-library Python can't extract text from PDFs or drawings. What counts as an attachment "it can't read": any non-text attachment, or only a corrupt one? Is a request with only a drawing and a thin body "needs info"?
5. **"Ready" fields:** Is a requested delivery date required for ready, or only part, revision and quantity? Is a new part ready, or should it go to a person?
6. **Working days:** Which holidays apply to the 6-working-day default? What is today's time zone?
7. **Lint and security tooling:** Standard library has no linter. May dev-only tools (ruff, bandit) be used outside the runtime, or must everything be stdlib? The plan assumes a custom checker plus `/security-review`.
8. **OpenAI:** Which model ID, and is sending customer emails and drawings to OpenAI approved? Check the data-handling terms, and decide what to do about a failed or rate-limited call (retry, or "couldn't process").
9. **Deployment checks that tests can't prove:** Who confirms the mailbox credential is truly read-only and who is in the group that sees the output? I suggest a manual checklist signed off before go-live.
10. **State:** Where do "already processed" emails and the over-limit queue live: a JSON file or `sqlite3`? If an email is revised after processing, is it reprocessed?
11. **Retention:** Does the 90 days apply to `mailbox/`, to recorded model answers and to old dashboards, or to all of them?
12. **Injection detection:** Is a deterministic pattern list acceptable, with the model's own flag as an extra signal? Should any match always go to a person, even when the email is otherwise a clean request?
