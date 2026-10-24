# Build plan: Hartwell quote pricing tool

Working directory `/tmp/tmp.WaJnaoDw4v` is not a git repo, so step 0 is `git init`, then work on branch `build/quote-pricing`.

## 1. Parts and interfaces

Each part is a Python module with typed inputs and outputs. Only `reader` and `checker` (and the note and reply-drafting calls) touch the AI, through one `LLMClient` protocol that tests replace with a fake. Everything else is pure code.

| Part | In → Out | Rule |
|---|---|---|
| `ingest` | CSV files → typed records | Validates columns and dates. Unknown customer yields `Unmatched`, never a drop. |
| `reader` | request text, customer name → `Reading` (items with exact quote, qty, part no. or equipment fields; competitor price, deadline, job name, each quoted) | Calls the LLM. |
| `checker` | request text, `Reading` → `Check` (per-item facts and clarity, missed items, competitor price, AI-addressed lines) | A separate LLM call. |
| `compare` | `Reading`, `Check` → `Agree` / `ToPerson(reason)` / `AskCustomer(question)` | Code. |
| `match` | `Reading`, `Check`, catalog → accepted lines, questions | Code. Verbatim-quote check, part-number lookup, exactly-one equipment match, injection flagging. |
| `pricing` | line, customer, date → agreed price | `Decimal`. List, then agreed discount, then that day's markdown. |
| `winmodel` | history, as-of date → P(win) at each extra discount | scikit-learn, pinned. Nightly. |
| `policy` | agreed price, cost, P(win) curve → suggestion | Argmax of P(win) × margin. Floor cost + 5%. Above 3% needs the sales manager. |
| `note` | facts from code → 1–2 sentence note | LLM. Every number in the output must be in the facts, or the note is dropped and a template is used. |
| `replies` | reply text → kind, competitor amount; then `negotiate()` in code | Reader and checker as above. Code decides match, hold or escalate. |
| `outputs` | drafts, AM list, run log, feedback | Escapes everything. Writes files only. |
| `runner` | schedule, 400-read budget | Every 10 minutes. Over budget goes to the AM, flagged. |
| `eval` | answer key → reading, reply and money metrics | One command, one report. |

## 2. Business rules (each gets an ID and a test)

- **R1** Every quoted phrase appears in the request word for word. A part number appears in its own words.
- **R2** An item is accepted only if the part number exists, or exactly one catalog product matches the equipment fields that reader and checker agree on. Zero or several matches become a customer question drafted by code.
- **R3** Any reader/checker disagreement, unclear item or missed item goes to a person with the reason, or to the customer if the request doesn't give the detail.
- **R4** Price = list × (1 − agreed discount), then the markdown in effect on the quote date, per line.
- **R5** The suggested extra discount is the one on the 0–5% grid with the highest P(win) × margin.
- **R6** The price after the extra discount is never below cost × 1.05. The suggestion is capped at the highest discount that satisfies this.
- **R7** Any extra discount above 3% is marked "needs sales manager". Only AM and sales-manager authority change what is offered.
- **R8** A reply with a named competitor price: code computes the matching extra discount. Match only if it is within AM authority **and** expected margin beats holding. Otherwise hold, or offer the sales manager the choice.
- **R9** The win model trains only on quotes closed in the 3 years before the as-of date. None on or after it.
- **R10** Note numbers are a subset of the numbers code provided.
- **R11** Nothing is silently dropped. No customer match or unreadable means top of the AM's list.
- **R12** The run log has one line per run: time, model, requests, items, questions, discounts.
- **R13** The daily cap is 400 AI reads. A request costs two. Overflow is flagged to the AM.

## 3. Security rules: where enforced, what proves it

| Rule | Enforced in | Test |
|---|---|---|
| Read-only, can't send | No SMTP/ERP/CRM client in dependencies. Outputs write only under `drafts/`. | Import-graph test fails if network or mail libs are imported outside `llm_client`. Test that a full run changes no input file hash. |
| AI sees one request, customer name only, no costs, margins, other customers, model | `prompts.build()` takes only text and name | Snapshot test of the prompt. Canary values (cost, other customer name) planted in fixtures must not appear. |
| AI has no tools | `llm_client` never passes `tools` | Test asserts the request payload has no `tools` key. |
| Requests are data, not instructions | `match` flags AI-addressed text from the reader, the checker, or a code regex. Prices come only from `pricing` and `policy`. | Fixture "approve 15%" in request and reply: price, floor and authority are identical to the clean version, and a flag goes to the sales manager. |
| Output escaped | One `render()` function, autoescape on | Fixtures with `<script>` in names and text appear escaped in every output. |
| Credentials from environment | `config.py` reads env only | Test that the missing-key error names the variable. Secret scan (see §5) finds no keys in the repo. |
| Pinned dependencies | `requirements.txt` with exact versions | Test parses it and fails on any unpinned line. `pip-audit` runs. |

## 4. Tests first

Write tests before each part, in this order, from the rules above and the answer key. The first commit holds the tests only, and they fail.

- **Unit tests per rule** R1–R13 with a fake `LLMClient`, so none call the AI.
- **Key-driven tests:** reading (items found, wrong items, unneeded questions), reply kind and amount, and the money metric. These run on recorded AI outputs. A separate `eval --live` calls the real model.
- **Properties:** floor never violated across random inputs. Suggestion never above the cap without the flag. Training rows never dated at or after the as-of date.

**A person must review before the agent builds on them:** R1, R2, R6, R7, R8, R9, all security tests, and the metric definitions and thresholds in `eval`. These are the money, wrong-item and safety rules.

**Locked files:** `tests/` and `answer_key/` are hashed in `LOCKED.sha256`, committed by a person. `scripts/check_locked.sh` fails on any difference. The agent may not edit tests, the key or the hash file without written approval. If a test seems wrong, the agent stops and asks.

## 5. Checks, in order (all deterministic before any AI review)

```
pytest -q                      # unit + key-driven, no AI calls
ruff check . && ruff format --check .
mypy src
bandit -r src                  # security review of the code
pip-audit -r requirements.txt
gitleaks detect                # or detect-secrets; no credentials in repo
scripts/check_locked.sh
python -m hartwell.eval --key answer_key/ --recorded   # metrics report
```

Only after all pass does an AI code review run on the diff (for example `/code-review`). Before go-live, and after any model-version change, run `eval --live` and compare with the last report.

## 6. Build order (small commits, one reviewable step each)

1. Tests-only commit, then human review of the list in §4.
2. `ingest` and fixtures.
3. `pricing` (R4).
4. `policy` (R5–R7) and `winmodel` (R9).
5. `reader`, `checker`, `compare`, `match` with the fake client (R1–R3).
6. `note` (R10), `replies` and `negotiate` (R8).
7. `outputs`, `runner`, log, feedback capture (R11–R13).
8. `eval` and first metrics report.

Each commit passes §5 on its own. The agent stops at the end of steps 1, 4 and 8 for review.

## 7. Out of scope

Writing to ERP/CRM, sending email, and EDI parsing beyond text. A split trial on real quotes. A UI beyond the draft files and AM list. Retraining the reader or checker. Multi-language requests. Tuning the win model beyond the stated inputs.

## 8. Open questions before building

1. **Budget:** 55,000 quotes a year is about 220 requests a working day, which is about 440 reads before any replies. Is 400 a day meant to be this tight, or should it be higher?
2. **Discount grid:** whole points (0,1,…,5) or finer steps?
3. **Level:** is the extra discount chosen per line or for the whole quote? Is "expected margin" in dollars?
4. **Floor:** is cost + 5% measured on the price after the agreed discount and markdown? What if the agreed price already sits below it?
5. **Stacking:** does a markdown replace, or add to, the customer's agreed discount?
6. **Authority:** what is each AM's limit? Is it one number (3%) or per person?
7. **Pass thresholds:** what are the acceptable wrong-item rate (zero?), items-found rate and unneeded-question rate for go-live?
8. **Win model:** which model class (logistic regression?), and how should a customer with little history be handled?
9. **Where the answer key lives** and who owns `LOCKED.sha256`. Who is the reviewer for §4?
10. **Competitor-price replies:** if the named price is below the floor, hold, or offer the sales manager the choice?
11. **Tooling:** are ruff, mypy, bandit, gitleaks and pip-audit acceptable, or does your team have standards?
