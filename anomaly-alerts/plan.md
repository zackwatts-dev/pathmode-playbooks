<!-- Generated 2026-10-24 by Claude Sonnet 5.5 (claude -p --model sonnet, run from an empty folder with no tools) from plan-prompt.md and design.md, after the AI checkers were added to the design. Unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: morning anomaly briefs

This is a proposal for review. No repo exists yet, so the commands and package names below are my suggestions.

## 1. Ground rules for the agent

- Work on branch `build/anomaly-briefs`. Make one small commit per step in §3, each with its tests green. Don't squash.
- **Protected paths:** `tests/`, `answer_key/`, `tests/golden/`. The agent may not edit or delete these, or loosen a threshold in them, without written approval from a person. `scripts/check_protected.sh` fails the build if a diff touches them without an approval file that a person committed.
- If a test seems wrong, the agent stops and asks. It never edits the test to match the code.
- Python only. Pin numpy and scikit-learn in a lock file. Use `ruff`, `mypy`, `bandit`, `pip-audit` and `pytest`.
- Thresholds live in one `config.toml`, not in code. No numbers are invented. Open questions Q1 and Q2 supply them.

## 2. Parts and interfaces

Each part is a pure function or a small class. Only `reader` and `ai_checks` touch the network, through an injected client, so every other part runs with no AI.

| # | Part | Interface | Rule it owns |
|---|---|---|---|
| 1 | `ingest` | `load(dir, run_date) -> (Tables, list[ExportIssue])` | Missing or late exports are returned as issues, never dropped. Input is opened read-only. |
| 2 | `picture` | `build(Tables, as_of) -> Picture` | 28-day register, closer cash, invoice lines vs. price list, punches vs. schedule. Monday only: actual vs. theoretical usage. Uses only records known as of `as_of`. |
| 3 | `rules` | `Picture -> list[Flag]` | Invoice over list, punch edited to add hours, whole-check manager comp (party package excepted). |
| 4 | `baselines` | `Picture -> list[Flag]` | Employee rate vs. group. Store gap vs. the group's best quarter and vs. its own last 8 weeks. A flag needs a high absolute rate, a material amount and enough occurrences. A one-week jump that reverses is suppressed unless large. |
| 5 | `attribution` | `(store, weeks) -> list[Attribution]` | Regression of weekly bar gap on bartender hours over 12 weeks. |
| 6 | `flagstate` | `select_reads(flags, open_flags, caps) -> (to_read, listed_only)` | Read only new flags or flags whose dollars per week grew by 50% since last read. Cap of 6 per store and 40 per group, ranked by dollars. Every flag is still listed. |
| 7 | `bundle` | `build(flag, Tables) -> Bundle` | One flag only. Its records, plus the store's log entries for those days with names removed, for store-level flags only. Employees appear by id. |
| 8 | `reader` | `read(Bundle) -> ReaderAnswer` | Claude call, no tools. Returns the cited log entry (if any), the explanation, the next step and the cited records. |
| 9 | `code_checks` | `(Bundle, ReaderAnswer) -> list[Failure]` | The quote is found in a given entry. At least one record is cited, and every cited record exists. Every amount is a cited record's amount. No employee-list name appears. Detects log entries addressed to an AI. |
| 10 | `ai_checks` | `log_check(Bundle)` and `language_check(text)` | The log checker never gets the reader's answer. The language checker gets only the explanation and next-step words. |
| 11 | `verdict` | `decide(answer, code_failures, log_check, lang_check) -> Verdict` | Explained only if the reader and log checker name the same entry. Otherwise the flag stays up with both readings. Any failure or unusable checker answer sends the flag to a person, unexplained. An injected log entry goes to the director and never explains. |
| 12 | `briefs` | `render(verdicts, issues) -> {gm[store], director, controller}` | Routing, ordering by money, issues at the top, escaping. |
| 13 | `score` | `score(flags, key) -> Metrics` | Matching and metrics exactly as defined in "What correct means". |
| 14 | `run` | CLI + run log | Wires the parts together. Appends one log line per run. |

## 3. Build order (tests first at every step)

1. Skeleton, lock file, CI script (§6), protected-path check.
2. `score` plus its tests. Everything else is measured against this, so it comes first.
3. `ingest` and `picture`, including as-of tests.
4. `rules`, then `baselines`, then `attribution`.
5. `flagstate`.
6. `bundle`, `code_checks`, `verdict`. These use a fake AI client with canned answers.
7. `reader` and `ai_checks` against the real client behind an env flag. The default test run never calls it.
8. `briefs`.
9. `run`, then a full end-to-end run on the sample data and the answer-key score.

## 4. Tests (written before the code)

**Business-rule tests (no AI):**
- Invoice price over list is flagged. Price at or under list is not.
- A punch edit that adds hours is flagged. An edit that removes hours is not.
- A whole-check manager comp is flagged. A comp under the party package is not.
- Each baseline is tested at the boundary: high rate with too few occurrences gives no flag. High rate with an immaterial amount gives no flag. A high score with a rate not well above typical gives no flag.
- A one-week jump that reverses is suppressed, and a large one is not.
- Attribution on synthetic data with a known culprit ranks that bartender first.
- **As-of:** inject a record dated after the run morning. Flags must be identical with and without it.
- Re-read only on a new flag or a growth of 50% or more. A 49% growth is not re-read.
- Caps: 7 flags in a store means 6 reads and 7 listed. 41 reads group-wide is impossible.
- Late or missing export: named at the top of all three briefs, and the run still completes.

**Answer-key tests:**
- Matching: same store or vendor, same leak kind, same person, within the running window.
- One flag counts for at most one problem.
- A flag coinciding with a benign event that explains it counts for none.
- A log-explained flag is not "found".
- Each metric (§2, `score`) is checked on a small hand-built key with known answers.
- **Acceptance (report, not a gate):** the sample key run produces the metrics. Targets come from Q3.

**Checks tests (fake client):**
- The quote is not in the entry: to a person.
- No record cited, a nonexistent record cited, or an amount not in the cited records: to a person.
- A name from the employee list appears: to a person.
- The reader and checker name different entries: flag stays up with both readings.
- The language checker returns accusation, naming, cause-as-fact or discipline, with words found in the answer: to a person. The same verdict with words not found in the answer: to a person (checker unusable).
- Malformed or empty checker output: to a person.

**A person must review these before the code that satisfies them is written:** the whole `score` suite, the as-of test, the verdict tests, every security test in §5, and the golden briefs.

## 5. Security rules: where enforced and how proved

| Rule from design | Enforced in | Test that proves it |
|---|---|---|
| Read-only. Changes nothing, sends nothing. | `ingest` opens files read-only. `run` writes only under `--out`. No mail or HTTP libraries other than the Anthropic client. | Run on a read-only copy of the exports and compare checksums before and after. Import-graph test fails on `smtplib`, `requests`, `urllib`, `subprocess` outside the allowlist. |
| The AI sees one flag at a time. | `bundle.build` takes a single flag. | Capture the prompt in a fake client. Only that flag's record ids and that store's log entries for those days appear. Planted sentinels from other flags and stores are absent. |
| Names out, employees by id. | `bundle` redaction | Log with every employee name and variant: none survives into the prompt. (Depends on Q4.) |
| Log checker never sees the reader's answer. | `ai_checks.log_check` signature has no answer parameter. | Plant a sentinel in the reader's answer and assert it is absent from the checker's request. |
| Language checker sees only the answer's words. | `ai_checks.language_check(text)` | Assert the request contains only the explanation and next step. |
| No tools on any call. | One wrapper around the client rejects any request with `tools`. | A unit test calls the wrapper with `tools` and expects an error. All real calls go through it. |
| The log is data, not instructions. | Prompts state it. `code_checks` detects instruction-like entries. The verdict forbids explaining from them. | A fake reader that obeys the injected entry still ends up "to a person". The entry is reported in the director brief, and the flag is never explained. |
| Employee flags go to that store's GM and the director only. | `briefs` routing | Controller brief contains no employee id or name. Another store's GM brief contains none of this store's employee flags. |
| Everything shown is escaped. | `briefs` | Names and log quotes containing `<script>`, backticks and pipes render inert in the output. |
| Credentials from the environment. | `run` reads env only. | Missing key gives a clear error. A scan (`gitleaks` or equivalent) finds no secrets. The key never appears in the run log or briefs. |
| Pinned dependencies. | Lock file | CI fails if installed versions differ from the lock. `pip-audit` is clean. |
| Nothing silently dropped. | `flagstate`, `briefs` | See the caps and missing-export tests in §4. |
| Never accuses, contacts or disciplines. | Language check and the verdict. No send code exists. | Language-checker tests in §4, plus the import-graph test above. |

## 6. Commands and review gates

Deterministic checks come first, in this order. Stop at the first failure.

```
scripts/check_protected.sh        # tests/answer key untouched without approval
ruff check . && mypy brief
pytest -q                          # no network, no AI
bandit -r brief && pip-audit -r requirements.lock
gitleaks detect
python -m brief score --key answer_key/ --exports sample/   # prints metrics
```

AI review (`/code-review ultra`, which you trigger) runs last, after all of the above pass. It supplements the checks and doesn't replace them.

Before going live, and after any change including a new model version, re-run the `score` command and compare it with the last accepted metrics.

## 7. Out of scope

- Contacting anyone, writing to any source system, or taking disciplinary action.
- Delivering the briefs. The tool only writes them. How they reach people is yours.
- The manager real/not-real marks tuning thresholds. v1 may define the file format but does not retune (Q8).
- Using the period ledger, budgets or weather, unless Q9 says otherwise.
- Building the nightly exports, the scheduler or server setup, or creating the answer key.

## 8. Open questions to answer before building

1. **Thresholds.** What numbers define "well above typical", "material amount", "enough occurrences", "large" for a reversing jump, and the weeks or ratios for the baselines? Or may the agent propose them from the sample? If so, I recommend a held-out part of the key, so the sample isn't overfit.
2. **Flag identity.** What makes a flag "the same" from day to day (store, kind, subject?), and how is "dollars a week" computed for the 50% growth test?
3. **Go-live bar.** What minimum on problems found, money saved, false alarms per store per week and benign events flagged counts as passing? The design measures these but sets no targets.
4. **Name removal.** How are names taken out of the log: only the employee list, or also nicknames, first names and customers? Does the list include managers?
5. **Answer key and exports.** Do you have the sample files now? I need their schemas, the key format, and the time that defines "known that morning".
6. **Party package.** How is it identified in the data (item, code, approver)?
7. **Open-flag state.** Is it recomputed from 90 days of exports each run, or stored from earlier runs?
8. **Marks.** Is real/not-real capture in v1, or deferred?
9. **Ledger, budgets, weather.** Are they used by any rule, or only listed as inputs?
10. **Output and model.** What format are the briefs (markdown, HTML, PDF) and where do they land? Which pinned model ID, and what are the timeout, retry and monthly cost limits?
11. **Attribution minimums.** What is the minimum data (bartenders, weeks) before the regression is trusted, and how should it show low confidence?
