# Build plan: Summit Mechanical AI analyst

This is a plan, not code. Commands are proposed defaults (`pytest`, `ruff`, `bandit`, `pip-audit`) until you confirm the toolchain.

## 1. Parts and boundaries

Each part is a module with typed inputs and outputs (JSON files or pure functions). Only the session runner touches the AI. Everything else runs offline.

| Part | Does | Interface |
|---|---|---|
| `sqlguard` | Decides whether a SQL string is allowed | `str -> ok / reason` |
| `tools` | `query`, `docs` and `save`. `query` runs on read-only DuckDB, caps display at 200 rows, and writes every call and full result to the ledger | tool call -> result + ledger id |
| `ledger` | Append-only record of calls (id, sequence number, SQL, full result) | read/append API |
| `schemas` | Fixed JSON shapes: map, hypotheses, prediction, finding, challenge, revision, summary | validate(file) |
| `runner` | Starts a fresh Claude CLI session with exactly the three tools, per-session folder, query and dollar caps. A session that hits a cap saves its output marked incomplete | stage inputs -> saved output |
| `stages` | Orient, Propose, Select, Investigate, Challenge, Revise. Select is code, not AI | files in, files out |
| `checks/*` | One function per check: numbers trace, queries exist and replay, size is computed, prediction first, challenge respected, instructions in data | `(finding, ledger, warehouse) -> failures[]` |
| `wordscheck` | AI checker given only the words, plus code that confirms each quoted phrase is in the text | text -> flags |
| `report` | Assembles the checked findings and the summary, and checks the summary's numbers | checked findings -> report |
| `score` | AI grader, check of the grade's numbers, human-review record, scorecard | finding + key -> grade |
| `replay` | Re-runs checks, report and scoring from the saved ledger and outputs, with no AI calls | run dir -> report |

## 2. Rules and the tests that prove them

All tests run without the AI. Fixtures are tiny hand-built warehouses and ledgers.

- **Numbers trace:**
  - A number in a result passes.
  - A number rounded from a result passes.
  - An unqueried number fails.
  - Arithmetic passes only if it was run as a query.
  - Years, dates and integers up to 12 are exempt.
  - 13 is not exempt.
- **Cited queries exist and replay:** A missing id fails. A changed result fails. A result that comes back in a different order is handled per the open question below.
- **Size is computed:** The dollar figure equals a cited result value. A near-miss fails.
- **Prediction first:** A prediction saved after query 1 fails. One saved before passes. This is judged by ledger sequence, not file time.
- **Challenge respected:** A retracted finding with no new queries goes to "looked at, not true". New queries after the challenge in ledger order let it through.
- **No accusation:** Fixtures that name an employee, accuse, state a cause as fact, or suggest discipline are held. Neutral text passes. A flag whose quote is not in the text is ignored.
- **Data is not instructions:** A planted "ignore previous instructions" note in a fixture. Reporting it passes. A finding whose behavior changed because of it fails. Every stage prompt carries the data-is-not-instructions line, and a test asserts it.
- **Selection:** The top N from the two rankings combined, with a default of 8 and a budget override.
- **Caps:** Session 151 of 150 queries is refused. The dollar cap saves the output as incomplete.
- **Report:** Ordered by dollars a year. Shows confidence and challenge verdict. Includes "looked at, not true", data concerns and what the records can't answer. Held-back findings are listed with the reason.
- **Scoring:** A full match, a partial match, true-but-not-planted, and contradicted. A grade with an uncited or untraced number fails.
- **Replay:** A recorded run reproduces the same report with no network access.

**Human-reviewed tests:** `sqlguard`, number tracing (exemptions and precision), prediction-first, challenge-respected, the no-accusation fixtures, the scoring fixtures, and the pass marks. A person approves these before any implementation starts.

**Immutability:** The agent may not edit tests, fixtures, answer keys, or pass marks without written approval. Protect them with a CODEOWNERS-style path rule and a CI step that fails if those paths change in an unapproved commit. The agent must not read the Summit answer key or the held-back plan. It builds against the Hartwell and Wendlow keys only.

## 3. Gates, in order

1. `ruff check . && ruff format --check .`
2. `pytest -q`, with coverage required on `checks/` and `sqlguard`
3. `bandit -r src` and `pip-audit`, with DuckDB hash-pinned in requirements
4. A human reads the security matrix results
5. Only then, any AI review (a model code review on the branch, never a substitute for 1–4)

## 4. Security matrix

| Rule | Enforced in | Proving test |
|---|---|---|
| Only `SELECT`/`WITH`, one statement | `sqlguard`, parsed rather than pattern-matched | Inputs with `;`, comments, mixed case, `CREATE`, `INSERT`, `DROP` are refused |
| `ATTACH`, `COPY`, `INSTALL`, `LOAD`, `PRAGMA`, `SET` refused | `sqlguard` | One case per keyword, plus keywords hidden in comments and strings |
| File-reading functions refused (`read_csv`, `read_parquet`, etc.) | `sqlguard` and DuckDB `enable_external_access=false` | Each function is blocked at the guard, and with the guard bypassed the engine still refuses |
| Warehouse is read-only | `tools.query` opens DuckDB with `read_only=True` | A write attempt through the raw connection errors |
| Exactly three tools, all else denied | `runner` CLI flags | A test reads the built CLI args and asserts the allowlist equals the three tools |
| No files outside the session folder | `tools.save` and `tools.docs` path resolution | `../` paths, absolute paths and symlinks are refused |
| Ledger written by the tool | `tools.query` | The AI-facing API has no ledger-write path. The ledger matches actual executions |
| Stage isolation | Stage input builders | The challenger input contains no investigator notes. The words checker input is text only. No input contains the key or truth paths |
| Data is not instructions | Prompts and `checks/instructions` | See section 2 |
| Employees by id only | `wordscheck` plus a code backstop that scans for names from the warehouse employee table | A fixture with a real name is held |
| Credentials from environment only | Config loader | A scan finds no secrets in the repo, and a missing env var gives a clear error |
| Summary and findings carry no accusations | `wordscheck` | See section 2 |

## 5. Branch and commits

`git init` first, since this directory isn't a repo. Work on `build/analyst-v1`. Commit order, each commit reviewable alone and green on the gates:

1. Scaffolding, schemas, tooling config
2. Human-approved tests (red)
3. `sqlguard`, `tools`, `ledger`
4. `runner`
5. Each check, one commit per check
6. `stages` and selection
7. `report`
8. `score` and `replay`
9. Security matrix pass and docs

## 6. Out of scope

- Building the warehouse or simulation (assumed to exist for Hartwell, Wendlow and Summit)
- Scheduling, a UI, or sending the report anywhere
- Prompt tuning (a separate step on the development businesses)
- Running the Summit sample or the held-back test
- Any action on findings, and any discipline or employee conclusions

## 7. Open questions for you

1. **Toolchain:** Are `pytest`, `ruff`, `bandit` and `pip-audit` acceptable? Is there CI, or does the agent run these locally?
2. **CLI feasibility:** Does the Claude CLI let you restrict a session to three custom tools (via an MCP server) with everything else denied? I suggest a short spike before committing to the `runner` design.
3. **Number matching:** What are the precision rules (decimals, percent vs fraction, `$1.2M` vs `1,200,000`)? How does code decide that a small integer is "a count of things named in the text"?
4. **Replay equality:** Queries without `ORDER BY` may return rows in a different order. Compare as sorted sets? What float tolerance?
5. **Ordering of events:** Is "before the first query" and "after the challenge" defined by ledger sequence number? I recommend yes.
6. **Selection formula:** How are the two rankings combined (rank sum, product, something else)? How are ties broken?
7. **Budget numbers:** What is the dollar cap per session, and where do token prices come from?
8. **Models:** Which model runs each stage, and a different one for the words checker and grader?
9. **Words checker:** What happens when it flags something and the quote isn't found? Who clears held-back findings, and how is that recorded?
10. **Summary numbers:** Must they trace to the checked findings' numbers, or to ledger queries directly?
11. **Review UI:** How does a person review and change grades (file edit, CLI prompt)? Where is the change reason stored?
12. **Pass marks:** Who writes them for the held-back test, and when? The agent must not see them.
13. **Development data:** Where are the Hartwell and Wendlow warehouses, docs and keys, and may the build agent have read access to those two only?
14. **Name backstop:** Is scanning against the employee table's names acceptable, given that the report goes to the owner only?
15. **Reviewers:** Who is the named human reviewer for the tests in section 2?
