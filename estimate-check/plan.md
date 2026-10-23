<!-- Generated 2026-10-22 by Claude Sonnet 5.5 (claude -p --model sonnet, run from an empty folder with no tools) from plan-prompt.md and design.md. Unedited. -->

# Build plan: pre-bid spec check

## 1. Ground rules for the agent

- Work on branch `spec-check`. Make one small commit per step in section 6, and stop for review at the marked steps.
- Runtime uses Python's standard library and pinned numpy only. Call the Anthropic API with `urllib`, not the SDK. Dev tools (`ruff`, `bandit`, `pip-audit`) are not part of runtime.
- **Do not edit `tests/` or `answerkey/` without approval.** `scripts/check_locked.sh` fails if either path differs from the last human-approved commit, so a change there needs a human-authored commit.
- Every judgment-bearing number goes in one reviewed file, `config/rules.toml`: kind→cost codes, kind→evidence type, system→cost codes, prevailing rates, minimum job counts, and the labor thresholds. Business logic never hard-codes them.

## 2. Parts and interfaces

Each part is a pure function over plain data, except where noted.

| Part | Input → Output | Notes |
|---|---|---|
| `ingest` | CSV exports, `as_of` time → `BidSnapshot` | Only part that reads files. Read-only. A missing section list or unreadable addendum yields a `Problem`, never a silent skip. |
| `reader` | one bid's documents → raw JSON claims | **Only part with network.** No tools in the request. Also handles "addendum vs. earlier list". |
| `verify` | raw claims + documents → accepted requirements + referrals | Quote check, kind check, status-quote check, injection flags. |
| `reconcile` | earlier list + addendum delta → current list | Adds, changes, deletes. Handles an addendum that amends an earlier addendum. |
| `coverage` | accepted list + estimate + config → gaps, priced-but-not-required | Three special evidence rules. |
| `pricing` | gaps + job history + bid date → cost and range per gap | Same building type, or all types when too few jobs. |
| `labor` | estimate + that estimator's history → flags in hours and dollars | numpy. |
| `report` | everything → one escaped page + one log line | Only part that writes. |
| `runner` | clock → picks new ready estimates and addenda, enforces the 40/day cap | Keeps a small state file of what it has already processed. |
| `evalkey` | answer key + recorded AI replies → scores | `--replay` is deterministic and runs in CI. `--live` calls the API and is run by a person. |

## 3. Business rules and the tests that prove them

Tests come first. For each rule the agent writes a failing test from the design, then the code. **[H]** marks tests a person must review before any code is written. These encode judgment, not plumbing. The AI is replaced by a fake client with canned replies throughout.

| # | Rule | Test |
|---|---|---|
| R1 [H] | Accept a requirement only if its quote is found word for word (whitespace-normalized only) in the section or addendum it names. | Paraphrased, truncated, wrong-section and nonexistent-section quotes are all rejected and referred. |
| R2 [H] | Kind must be on the list of 15. | An invented kind is referred. |
| R3 [H] | "By others", "doesn't apply" and "deleted" need a quote of the words that say so. A deletion must quote the addendum. | Each status without a quote is referred. A deletion quoting the original section instead of the addendum is rejected. |
| R4 | A failed check sends that section to the chief estimator, unread. It does not drop it and does not guess. | The referral names the section and the reason. |
| R5 [H] | A requirement counts as priced when there is a line on its cost code with an amount, or a line whose description names it. | Cases: priced by code, priced by description, a zero-amount line (not priced), a line on the wrong code. |
| R6 [H] | Prevailing wage is priced only by a labor rate at the prevailing rate or a prevailing wage line. A named manufacturer is priced only if the equipment line names that manufacturer. Upgraded insulation is priced only if the insulation line names the thickness or jacket. | A generic line on the right code does not satisfy any of the three. |
| R7 [H] | Unpriced base-bid requirements are gaps. Priced lines for by-others, doesn't-apply or deleted requirements are "priced but not required". | Fixture bid with one of each. Alternates are not gaps. |
| R8 | Gaps are sorted largest first. | Ordering test. |
| R9 [H] | Gap cost is the median share of base cost on same-type completed jobs before the bid date, with a range. It falls back to all types below the minimum job count. | A job completed after the bid date is excluded (leak test). The fallback triggers at the threshold. |
| R10 [H] | A labor flag appears only with enough jobs and a steady over-run for that estimator and system, and gives hours and dollars at that rate. | The variable-margin, too-few-jobs and other-estimator cases give no flag. A steady 10% over-run gives the expected hours and dollars. |
| R11 | An addendum after the first read goes through `reconcile`. | Add, change, delete, and delete-then-reinstate. |
| R12 | The cap is 40 reads a day. The 41st goes to a person, named in the review. | Boundary test at 40 and 41. |
| R13 | Nothing is silently dropped. Missing section list, unreadable addendum, API failure and malformed JSON are named at the top of the review. | One test per cause. |
| R14 | Re-run on addendum only before the bid due date. Re-run with no new input makes no AI call. | Idempotency test. |
| R15 | Each run appends one log line: time, model, bids read, requirements found, gaps, sent to person. | Format test, and the line contains no document text. |
| R16 [H] | Severity gate for the eval: zero accepted requirements whose quote isn't in the documents (a phantom). Then minimize requirements wrongly called required (by-others or deleted). Then missed requirements. Then false gaps. | The scorer reports each tier separately. Any phantom fails the run. |
| R17 [H] | Money metric: reprice each bid with gaps added, labor flags applied, and priced-but-not-required removed. Compare with the same competitors and the same GC choice. | Hand-computed three-bid fixture, including a win gained, a loss avoided and a win lost. |

**Eval split.** Split the answer key into a tuning set and a held-out set, and never tune on the held-out set. Estimator real/not-real marks may adjust `rules.toml` only through a reviewed commit.

## 4. Check order (all deterministic checks first)

Run in this order. The AI review (`/code-review`) happens only after steps 1–5 pass.

1. `python -I -m unittest discover -s tests`
2. `python -I -m halden.evalkey --replay answerkey/ --recorded recorded/` (R16 and R17 gates)
3. `ruff check . && ruff format --check .`
4. `bandit -r src` and `pip-audit -r requirements.txt`
5. `scripts/check_locked.sh` and the `/security-review` skill on the branch diff
6. **AI code review**, last
7. Before go-live, and after any change including a model version: a person runs `evalkey --live` and compares it to the recorded baseline.

## 5. Security rules, where enforced, and proof

| Rule | Enforced in | Test |
|---|---|---|
| Read-only; can't send anything | `ingest` opens files `r`. `report` writes only to the output directory. | Run against a read-only copy of the inputs and check checksums are unchanged. An AST test asserts that `socket`, `smtplib` and `urllib.request` are imported nowhere except `reader`, and that `reader` has a single hard-coded API host. |
| The AI sees one bid's documents only; no estimate, job cost or other bids | `reader` prompt builder takes only a document set | Plant sentinel strings in the estimate, history and a second bid. Assert none appear in the request body. |
| The AI has no tools | `reader` request construction | Assert the payload has no `tools` key. |
| Documents are data, not instructions | The prompt delimits documents and says so. `verify` flags instruction-like text. `coverage` never takes AI output except verified requirements. | Fixture specs and addenda saying "ignore prior rules", "mark all priced" and "this requirement is deleted". These are reported to the chief estimator, remove no requirement, and mark nothing priced. A flagged section cannot supply a "by others / deleted / doesn't apply" downgrade (see Q4). |
| Everything shown is escaped | `report` renders only through one escape function | Quotes containing `<script>`, `&`, quotes and spreadsheet-formula prefixes appear inert in the output. |
| Credentials from the environment | `reader` reads `ANTHROPIC_API_KEY` | A repo scan finds no key patterns. A missing key gives a clear error. The key never appears in logs, referrals or exceptions. |
| Software: stdlib and pinned numpy | `requirements.txt` | A test fails on any other runtime import or an unpinned line. |
| Spec text kept out of the log | `report` log writer | R15 test. |

## 6. Build sequence

Each step is a branch commit or a few. ★ means stop for human review.

1. Skeleton, `rules.toml`, fake AI client, `check_locked.sh`.
2. ★ **Write all tests and fixtures (section 3), plus the answer-key loader.** A person reviews the [H] tests, then locks them.
3. `ingest`.
4. `verify`, then `reconcile`.
5. `coverage`.
6. `pricing`, then `labor`.
7. `report`, then `runner` (cap, state, log).
8. `evalkey` replay, then the `reader` (real prompt and API call).
9. ★ Full check order from section 4, then the human live run.
10. Deployment notes: cron every 30 minutes during working hours, on the server you control.

## 7. Out of scope

- Any write to estimating or job cost, and any email or notification.
- Changing the estimate or suggesting line edits.
- A UI, or storing estimator marks.
- Retraining or automatic rule tuning from marks (v1 only collects them).
- Reading drawings, or anything outside the exports.
- Bid-day or post-bid analysis.

## 8. Open questions to answer before building

1. **Kind → cost-code and evidence table.** The design needs it for R5, R9 and R10, but none of the exports defines it. Who writes it, and who supplies the prevailing-wage rate table?
2. **System → cost-code map** for ductwork, HVAC piping, plumbing and equipment.
3. **Project facts to the AI.** The AI needs building type, public owner and similar facts to judge "doesn't apply". Is it allowed to see the project's facts, or only the documents?
4. **Injection and downgrades.** A quoted "by others" can itself be planted text. Do you accept my rule that flagged sections can't downgrade a requirement, or should every downgrade be human-confirmed?
5. **Thresholds:** minimum jobs for same-type pricing, minimum jobs and "steady margin" for labor flags, and the minimum dollar amount for a line to count as priced.
6. **Answer key size and split.** How many bids, and may I hold out a portion? What counts as passing R17 (a minimum margin change)?
7. **Where the review lands.** A file in a shared folder, or a web page? HTML or plain text? "Sends nothing" means somebody has to fetch it.
8. **Estimator marks.** Where are they stored, given the tool is read-only?
9. **Model and data handling.** Which Claude model and version do we pin? Is sending owner spec documents to Anthropic's API acceptable under your contracts?
10. **Dev tools.** Are `ruff`, `bandit` and `pip-audit` allowed as dev-only dependencies?
11. **When an estimate changes after a review** without a new addendum, should it re-run the coverage check (no AI call needed)?
