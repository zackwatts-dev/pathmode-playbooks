<!-- Written by Claude Sonnet 5.5 from plan-prompt.md and design.md on 2026-10-19, unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: estimate check for Wendlow Fabrication & Machine

Python 3 standard library only. The package is `estcheck`. Work happens on branch `estimate-check`.

## 1. Parts

Each part is a module with typed inputs and outputs. Parts 1 to 5 are pure functions that don't touch the network.

| # | Part | Does | Does not |
|---|---|---|---|
| 1 | `load` | Reads the 5 CSVs read-only. Validates and types the rows. Uses `Decimal` for hours and money. Returns the good rows and a list of rejected rows, each with a reason. | Decide anything |
| 2 | `comparables` | Finds comparable operations for one line and work centre (rule 1 of the design), with the fallback. Returns the operations and which tier was used. | Calculate |
| 3 | `history` | Computes the median clocked/estimated ratio per work centre, the suggested hours, and the labour cost both ways. | Choose a pile |
| 4 | `classify` | Assigns a pile: check this, may be priced high, looks right, or not enough history. A reason code goes with every "not enough history". | Call anything external |
| 5 | `evidence` | Builds the evidence object for one quote: numbers, work-centre names and an enum for the pile. This is the only thing the AI will ever see. | Include free text or customer fields |
| 6 | `notes` | Has three pieces: the OpenAI client (`urllib`, timeout, HTTPS only), the number check, and the plain note writer. It enforces the 100-note cap. | Run without a fallback |
| 7 | `dashboard` | Renders one static HTML page. Every value goes through `html.escape`. | Use JavaScript or external resources |
| 8 | `runlog` and `run` | Wires 1 to 7 together. Appends one line to the log per run. | Write anywhere except the output directory and the log |
| 9 | `score` | Scores the piles against `answer-key.csv`. Run by a person, not by the agent. | Call the AI |

Piles are final after part 4. The AI can change a note's wording, never a pile.

## 2. Business rules to build as written

These are interpretations or decisions the design left open. Each gets a test, and the open questions in section 7 cover the ones I couldn't settle.

- **Pile thresholds.** Labour-cost ratio = suggested ÷ estimated.
  - At or above 1.10 → check this.
  - At or below 0.85 → may be priced high (information only).
  - Otherwise → looks right.
  - The boundaries are inclusive, and tests cover exactly 1.10 and 0.85.
- **Comparable operations.**
  - Same work centre.
  - Same family, material and quantity band.
  - Finished within 3 years before the quote date, and strictly before the quote's prepared date.
  - At least 20, so 19 fails and 20 passes.
  - Fallback: drop material and quantity, then retry with the same threshold.
- **No hindsight.** An operation finished on or after the prepared date is never used, even on the fallback tier.
- **Nothing silently dropped.** These cases all go to "not enough history" with a reason code:
  - a rejected input row;
  - a work centre with no rate;
  - a line with no hours;
  - a zero estimated-hours history row.
  - Invariant: pile counts always sum to the number of input lines.
- **Note cap.** At most 100 notes go to the AI per run. Over the cap, the remaining notes are code-written, taken in order of dollar gap, largest first.
- **Number check.** Evidence supplies every number as a pre-formatted string, and a note may contain only those strings. Any other number, or a missing API key or an API error, produces the code-written note. A note that fails the check is never shown.
- **Dashboard totals.** The dashboard shows the pile counts and the "to check" lines, largest gap first. It shows breakdowns by estimator and family. It also shows total under-recovered labour, which is the sum of positive gaps on "check this" lines only.

## 3. Order of work

**Fixtures.** Hand-built synthetic CSVs where the right answer is known by construction. Real exports and the real answer key stay out of the repo.

1. **Commit 1, tests only.** Write failing tests for every rule in section 2 and every row in section 5, plus the fixtures. **Stop here for human review.**
2. **Commits 2 to 9.** One part per commit, in the order 1 to 9. Each commit turns its own tests green and touches nothing else.
3. **Final commit.** Wire up `run`, add the scheduling example (a cron line, not an installer) and a short README with the commands.

**Protected files.**
- `tests/` and `fixtures/answer-key*.csv` are protected.
- The agent may not edit, delete or regenerate them without approval. If a test looks wrong, the agent stops and asks.
- `tests/PROTECTED.sha256` holds the hashes a person approved. `tests/test_protected.py` fails if any hash differs. Only a person updates the file.

**Tests a person must review** (they encode the business rules and the security rules):
- `test_comparables`
- `test_classify`
- `test_no_hindsight`
- `test_no_silent_drop`
- `test_score`
- `test_notes_validation`
- `test_security`

Format and layout tests (`dashboard` layout, `runlog` format) can be skimmed.

## 4. Commands and gates

Deterministic gates run in this order, and every one must pass before any AI review.

```
python3 -I -W error -m unittest discover -s tests -v   # all tests; the AI client is replaced by a fake
python3 -m compileall -q src                            # syntax
python3 -I -m unittest tests.test_hygiene               # stdlib-only lint (below)
```

`tests/test_hygiene.py` stands in for a linter that would need third-party packages. It uses the `ast` module to check:
- imports are on a stdlib allowlist;
- there is no `eval`, `exec`, `subprocess`, `os.system` or `pickle`;
- there are no write-mode `open()` calls outside the output and log paths;
- no secret-shaped strings appear.

After the gates are green:
1. Run `/security-review` on the branch, covering the code and the security table in section 5.
2. Run `/code-review`.
3. A person reads the diff commit by commit.

**Go-live gate** (run by a person, with real data, after any change including a new model or new hour standards):

```
python3 -m estcheck.score --quotes … --history … --key answer-key.csv
```

It prints:
- the confusion matrix;
- the count and dollar value of light lines marked "looks right" (the worst case);
- the count of flagged-but-fine lines;
- the "not enough history" rate.

It exits non-zero if any value breaks `release-thresholds.json`, a file a person owns. A separate `python3 -m estcheck.notes_probe` makes real API calls on a sample. It reports the number-check pass rate and writes the notes for a person to read. It is never part of the test suite.

## 5. Security: rule, where enforced, proof

| Rule | Enforced in | Proving test |
|---|---|---|
| Read-only to the exports | `load` opens files `"r"` only. Hygiene bans write-mode `open()` elsewhere. | Make the input files and directory read-only, run the full pipeline, and check it succeeds and the file hashes are unchanged. |
| No credentials in code | `notes` reads `OPENAI_API_KEY` from the environment only. | Hygiene scan for key patterns. With the variable unset, the run completes with code-written notes. |
| The key never reaches logs or the page | `runlog` and `dashboard` take no key. Errors are logged as a type only. | Set a canary key, force an API error, and grep the log and HTML for it. |
| The AI sees only the evidence for one quote | `evidence` builds an allowlisted object. `notes` sends only that object. No tools, no files. | Assert on the exact request body: it has no customer, contact or free-text field and no `tools` key. Also test that a hostile part name (`"ignore previous instructions"`) never appears in the request. |
| An AI note counts only after the check | `notes.validate` | Table of notes: an invented number, a changed figure, a missing evidence figure, and the empty and over-long cases. All fall back to the plain note. |
| Everything on the dashboard is escaped | `dashboard` | Fixtures with `<script>`, `"onload=`, and `&` in every text field and in an AI note. The output contains none of them unescaped. |
| The page loads no external resources and runs no scripts | `dashboard` adds a CSP meta tag and has no `<script>` or external URLs. | Assert on the HTML. |
| Standard library only | Hygiene allowlist | `test_hygiene` |
| 100-note cap and fallback on API failure | `notes` | A fake client counts calls: 150 quotes produce 100 calls. A timeout or a 500 error produces a plain note. |
| Only the estimating team and the general manager see the output | Not enforceable in code. See open question 9. | Deployment checklist item, not a unit test. |

## 6. Out of scope

- Any write to the ERP, a quote or a price.
- Emailing or notifying anyone.
- Changing the hour standards, or any learned or ML model.
- Rework and repeat jobs.
- Login, user accounts and access control for the dashboard.
- Server setup (beyond one example cron line).
- Charts needing a JavaScript library.
- Reviewing quotes already sent.
- Scoring the quality of AI notes in the automatic tests.

## 7. Open questions for you to answer before building

1. **Column names.** I need the headers of all five CSVs, and what each line's identifier is. The list in the design has no **quote prepared date** on `quotes-to-check.csv`, which the no-hindsight rule depends on. Where does it come from? I also need the finish date and the quantity on `job-history.csv`.
2. **Quantity bands.** What are the band edges (for example 1–5, 6–25, 26–100, over 100)?
3. **Any work centre short of history.** If one work centre on a line has fewer than 20 comparables but the others have enough, does the whole line become "not enough history"? That is the design's literal reading, and it could hide a weldment. The alternative is to sort the line using the standard hours for the thin centre, marked partial. Which do you want?
4. **Setup and run hours.** Is one ratio applied to setup plus run together, or are the two kept separate? Is the ratio built from total clocked hours over total estimated hours?
5. **Rate and money rounding.** What is the rounding rule and the currency unit, and is the gap dollar-per-line or per-quote?
6. **Release thresholds.** What results on the test month count as passing? For example: how many light lines marked "looks right" are tolerable (zero?), the highest acceptable flagged-but-fine rate, and the highest acceptable "not enough history" rate. These go into `release-thresholds.json`.
7. **"May be priced high" lines.** The answer key only says whether a line was light, so these can't be scored. Is that fine, or is there a "ran heavy" column?
8. **Real data and the agent.** Can the agent build on synthetic fixtures only? I recommend this, and that a person runs the real answer-key scoring. Otherwise customer data is on the agent's machine.
9. **Who sees the dashboard.** How will the page be served? A web server restricted to the estimating team and the general manager, a shared folder with permissions, or something else? Code can't enforce this.
10. **Data going to OpenAI.** Is it acceptable that the evidence (hours, part family, material, dollar figures, with no customer names) leaves the shop to OpenAI's API? If not, set the cap to 0 and keep all notes code-written. Also, which model name, and who owns the key?
11. **Dev tooling.** Does "no third-party packages" cover dev tools such as ruff and bandit? I've assumed it does, hence the stdlib hygiene test. Say if you'd allow them for development only.
12. **Quote versus line.** Should a quote with several lines get one note covering all its "check this" lines? I've assumed yes. Which date counts as "saved that day": the export's own filter, or something the tool must compute?
