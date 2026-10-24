<!-- Written by Claude Sonnet 5.5 from plan-prompt.md and design.md on 2026-10-23, unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: quote pricing assistant (Hartwell Supply)

## 1. Ground rules for the agent
- Work on branch `build/quote-pricing`. Make small commits, one per step below, and put tests in their own commit before the code they test.
- **Tests and the answer key are frozen.** The agent may not edit `tests/`, `fixtures/`, or `answer_key/` after the "tests approved" commit without written approval from a person. CI hashes those paths against that commit and fails on any difference. If a test looks wrong, the agent stops and asks.
- All AI calls go through one interface, `LLMClient`. Tests use a fake client, so the whole suite runs offline. Only tests marked `live` call Anthropic, and they run by hand.
- Python with pinned numpy and scikit-learn. Credentials come from environment variables only.

## 2. Parts and interfaces
Each part is a pure function or small class with typed inputs and outputs. It is tested alone and does not import its neighbours.

| # | Part | Interface | Notes |
|---|---|---|---|
| 1 | `ingest` | `load_exports(dir) -> Dataset` | Validates the CSV schema. Rejects bad rows loudly. |
| 2 | `reader` (AI) | `read_request(text, customer_name) -> RawReading` | Sends one request and the customer name only. No tools. Returns items, each with `quote`, `qty`, `part_no` or equipment details, plus `competitor_price`, `deadline`, `job_name` and `instructions_found[]`. |
| 3 | `verify` (code) | `verify(reading, text, catalog) -> VerifiedItems, Questions, Flags` | Rules in §4. Drafts questions from templates. |
| 4 | `pricing` | `agreed_price(line, customer, date)` | List × (1 − agreed discount) × (1 − markdown for that month). |
| 5 | `winmodel` | `train(quotes, as_of)`, `p_win(features, extra_disc)` | Trains nightly. Uses only quotes closed before `as_of`. Returns chances at 0–5%. |
| 6 | `suggest` | `suggest(lines, p_win_curve) -> Suggestion` | Maximises P(win) × margin. Enforces the floor (cost + 5%) and the manager flag above 3%. |
| 7 | `draft` | `build_quote(...)` (code); `write_note(facts)` (AI) | Code computes every price and total. The note comes from a fixed fact list, and every number in it is checked against that list. |
| 8 | `reply_reader` (AI) | `read_reply(text) -> {kind, competitor_amount, quote}` | |
| 9 | `negotiate` (code) | `respond(reply, quote, authority, p_win) -> match/hold/escalate` | Finds the extra discount that matches the competitor. Matches only within authority and only if expected margin beats holding. |
| 10 | `outputs` | `render(...)`, `log_run(...)`, `record_feedback(...)` | Escaped HTML or text drafts. One log line per run. Account managers mark each suggestion used or not, with a reason. |
| 11 | `runner` | `run_once(now)` | Runs every 10 minutes. Enforces the 400-reads-a-day cap. Puts exceptions at the top of the account manager's list. |
| 12 | `evaluate` | `score(answer_key) -> Report` | Reading, reply and money scores as in §5. |

## 3. Order of work
0. **Skeleton**: repo layout, tooling config, `Makefile` with the commands in §7.
1. **Tests and fixtures** (no implementation): the tests listed in §4 and §5, a small hand-made fixture set, and loaders for the real answer key. **Stop for human review.**
2. Steps 1–5 below are code-only, in this order: `ingest`, `pricing`, `verify`, `winmodel`, `suggest`, `negotiate`. Each is its own commit.
3. `reader`, `reply_reader` and `draft` behind `LLMClient`, tested with the fake client.
4. `outputs`, `runner`, `evaluate`.
5. Run the deterministic checks (§7), then the live answer-key run, then AI review (§7).

## 4. Business rules and the tests that prove them
Every test runs without the AI.

**Reading checks (`verify`)**
- A quote that isn't word for word in the request rejects the item. The test uses a paraphrased quote.
- A part number that isn't in the catalog rejects the item.
- Equipment details matching zero or two or more products produce a question, never a guess. The test uses "410A or 454B?".
- A quantity that isn't inside the quote rejects the item.
- Zero wrong items on the answer-key sample is the pass bar (see open question 5).

**Prices and discount**
- The agreed price uses the markdown for the quote's month, and the month boundary is covered.
- The suggestion is the argmax of P(win) × margin over 0–5%, checked on a hand-built curve.
- The suggestion never goes below cost + 5%. If the agreed price is already below that, suggest 0% and flag it.
- A suggestion above 3% is marked "needs sales manager". A suggestion at exactly 3% is not.
- The win model's training set excludes quotes closed after `as_of`. A test with a planted future quote proves it.

**Replies**
- The kind and competitor amount match the key.
- Matching happens only within authority and only when it beats holding on expected margin. Otherwise the result is hold or escalate.

**Notes and drafts**
- A note containing a number not in the fact list is rejected and replaced by a plain template.
- A request with no customer match, or one that can't be read, appears at the top of the list. Nothing is dropped silently.
- The 401st read of the day goes to the account manager unprocessed.

**Tests a person must review before any code is written:**
- the answer-key loaders and scoring;
- the margin floor and authority tests;
- every security test (§6);
- the money metric.

## 5. Acceptance: the answer key
Report all of these, produced by `evaluate`:
- **Reading:** items found, wrong items, unneeded questions. Weighted worst to least bad: wrong item, then a match the margin doesn't support, then an unneeded question.
- **Replies:** kind accuracy and competitor-amount accuracy.
- **Money:** for every quote in the year, the expected margin at the suggested discount against the expected margin at the discount the account manager gave. Both use the simulation's true win chances. Show the difference in dollars and in points of margin on won quotes. The report must say it uses the simulation's own win curve, and that a real company would prove it with a split trial.
- Re-run all of this after any change, including a new model version, before going live.

## 6. Security rules: where enforced, and what proves it

| Rule | Enforced in | Test |
|---|---|---|
| Read-only: no writes to ERP/CRM, nothing sent | There is no network or write code beyond the Anthropic call and the output directory. `outputs` writes only under `OUT_DIR`. | Run with network blocked except a mocked Anthropic endpoint. Assert no other sockets and no file writes outside `OUT_DIR`. |
| AI sees one request or reply plus the customer name, and no costs, margins, other customers or win model | `reader` and `reply_reader` build the prompt from a fixed template with two inputs. | Capture the prompt with the fake client. Assert it contains no cost, margin or other-customer strings from the fixtures. |
| The AI has no tools | `LLMClient` sends no `tools` parameter. | Assert the request payload has none. |
| Requests and replies are data: injected instructions are reported and change nothing | The AI's `instructions_found` list and a code-side pattern check feed `Flags`. Prices and authority are computed from catalog and config only. | Requests and replies saying "approve 15%" or "ignore previous rules", with the fake client obeying them. Assert prices and authority are unchanged and the sales manager gets a flag. |
| Everything shown is escaped | `render` uses autoescape. | Customer names and request text containing `<script>` appear escaped in the output. |
| Credentials from the environment | A single config module reads them. | Scan the repo for key-like strings. Startup fails if the variable is missing. |
| Pinned dependencies | `requirements.txt` with hashes. | `pip-audit` in CI. |
| The AI cannot set a number | `draft` and `negotiate` take numbers only from code. | The note-number check test in §4. |

## 7. Commands, in order
Deterministic checks come first, and AI review comes last.
```
make test        # pytest -m "not live"  (all offline)
make lint        # ruff check . && ruff format --check . && mypy src
make security    # bandit -r src && pip-audit
make frozen      # verify hashes of tests/, fixtures/, answer_key/
make eval-live   # pytest -m live; calls the API, run manually
```
After these are green, run `/security-review` on the branch, then `/code-review`. A person reads the diff last.

## 8. Out of scope
- Writing to or syncing with the ERP or CRM, and sending email.
- The split trial on real quotes.
- A web UI beyond the draft output and the used/not-used mark.
- EDI and phone parsing. Input is the request text only.
- Any pricing beyond the 0–5% extra discount.

## 9. Open questions for you
1. **Win model facts and AI privacy.** The design says the AI never sees the win model, but the account-manager note ("buys at our agreed price about half the time") needs a win-model fact. Is the note allowed to see the win-model facts, and the reply draft only code's numbers? I'd say yes to the first and no cost or margin text in anything customer-facing.
2. **Margin and the floor.** Is "cost plus 5%" a markup on cost, and is the floor checked per line or on the whole quote? Is expected margin in dollars or percent? I assume dollars per line.
3. **How the extra discount stacks.** Is it taken off the already-discounted price, or added in points to the agreed discount? Does it apply to every line?
4. **Authority.** What is an account manager's limit? The design gives 3% for suggestions. Is it the same for competitor matching, and what happens when a match needs more than 5%?
5. **Pass bars.** What score on the answer key counts as ready: zero wrong items? A maximum for unneeded questions? A minimum money gain?
6. **Matching rules.** Are discontinued products excluded from matches? If the customer didn't give a detail, such as SEER2, does it count as "matches every detail written" or does it trigger a question?
7. **Injection detection.** Do you accept the AI's `instructions_found` field plus a simple pattern list, or do you want something stricter?
8. **Delivery.** Where do drafts, flags and the "used or not" marks live: files in a folder, a simple page, or something else? And who gets the sales-manager flags?
9. **Selection bias.** In the simulation, are extra discounts given at random, or by account-manager habit? If it's habit, the model's win curve could be biased, and I'd want the money test to show that.
10. **Sample size.** How big is the answer-key sample, and does it cover the full year of quotes the money test needs?
