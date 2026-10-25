<!-- Generated 2026-10-24 by Claude Sonnet 5.5 (claude -p --model sonnet, run from an empty folder with no tools) from plan-prompt.md and design.md, after the AI checker was added to the design. Unedited. The review of it is on the playbook page, Step 3. -->

# Build plan: supplier agreement compliance tool (Hartwell Supply Co.)

## 1. Ground rules for the agent

- Work on branch `build/supplier-rebates`. Make one small commit per step below, with tests in the same commit or the one before it. Don't push or merge.
- **Tests first.** Write each module's tests, see them fail, then implement.
- **Frozen files:** `tests/`, `terms-key.csv` and `entitlements-key.csv` are read-only for the agent. If a test or key row looks wrong, stop and file it under "Needs human decision" in `NOTES.md`. Don't edit it. Enforce this with a CI check that fails if those paths change without a `human-approved` commit trailer.
- Use the standard library, `pdftotext` and the Anthropic SDK for the AI. Ask before adding anything else.
- Default tests never call the network. All AI calls go through one `LLMClient` interface. Tests use a fake that replays recorded fixtures.

## 2. Parts and interfaces

Each part is a pure function over plain dataclasses, serialized as JSON between steps. Nothing but `llm_client` may touch the network.

| # | Module | In → Out | Notes |
|---|---|---|---|
| 1 | `ingest` | `agreements/<supplier>/` → `Document{supplier, doc_id, pages[text]}` list, or `Unreadable{path, reason}` | Runs `pdftotext` and parses `.eml`. Missing supplier folder, unreadable file or no statement is a `Referral`. |
| 2 | `reader` | one supplier's docs → `Term[]` | Fields: `kind`, `numbers`, `covers`, `dates`, `quote`, `doc_id`, `page`, `amends`, `informal_flag`, `unclear_flag`. Gets one supplier's documents only. |
| 3 | `checker` | `(kind, one document)` → `CheckedTerm`. For the statement: `(statement, lines)` → line-to-term mapping | Never receives the reader's output. Includes the tier-rate basis (from first dollar vs within band) and a binding-for-program-year flag. |
| 4 | `validate` | `Term` + `CheckedTerm` + docs → `Accepted` or `Referral{reasons, both readings, passage}` | Pure code. Field-by-field comparison and the exact checks in section 3. |
| 5 | `calc` | accepted terms + CSVs → `Entitlement[]` per supplier and term | No AI. Eligible purchases (deduplicated, net of returns, by branch and product), rebate under amended terms, co-op, freight, returns. |
| 6 | `reconcile` | entitlements + statement + receipts/claims → `Gap[]` | Each gap carries amount, term, passage and source rows. |
| 7 | `letters` | gaps → letter text | Code writes every claim line. The AI gets only supplier name and kinds, and returns an opening and closing. A fallback template replaces any that contains a digit, a threat or a concession. |
| 8 | `dashboard` | gaps, referrals, deadlines → one HTML file | Escapes all output. |
| 9 | `runlog`, `cli` | orchestration, caps, append-only log line | Caps: 30 documents and 15 letters per run, plus one checker call per term and statement. |

`Referral` is the only way out of the pipeline other than `Accepted`. Nothing is dropped silently.

## 3. Business rules to encode as tests

Each rule gets a test with a tiny hand-built fixture.

**Term acceptance (`validate`)**
- R1. A quote must appear word for word in the cited document. (Decide whitespace and hyphenation handling; see Q4.)
- R2. Every number in a term appears in its quote. Every tier row sits on one line of the document.
- R3. Tier thresholds rise. Rates are between 0 and 10%.
- R4. An amendment must say "from" the old value "to" the new one.
- R5. The reader and the checker must agree on every field. A disagreement, an unclear flag, an informal flag or an expired or next-year program becomes a `Referral` with both readings and the reason.
- R6. Statement lines must sum to the credited amount (`rebate-receipts.csv`). Otherwise the statement is referred.

**Calculation (`calc`, `reconcile`)**
- R7. Duplicate invoices are counted once. Returns reduce eligible purchases. Eligibility follows the term's covered purchases, dates and locations.
- R8. Tier rate is applied per the term's basis, either from the first dollar or only within the band. Amended values supersede old ones from the amendment's effective date.
- R9. Co-op owed is accrued amount minus claims filed, limited to eligible spend. The claim window is open or closed as of the run date.
- R10. Prepaid freight is owed on orders over the minimum, based on freight billed minus freight paid.
- R11. The return allowance is limited to stock on hand at 2025-12-31 that has not sold, per the term's rules.
- R12. Every `Gap` links to its term, passage and source rows.

**Letters and outputs**
- R13. Every amount in a letter comes from code. An AI opening or closing with a digit, threat or concession is replaced by the template.
- R14. A person reviews every claim. The tool has no send path.
- R15. Any supplier with no documents, any unreadable document or any statement with no matching terms appears as a referral.
- R16. Each run appends a log line: time, model, terms read, terms checked and money found by kind.

## 4. Acceptance tests

**Tests a person must review before any code is written** (the agent can't change them):
- the R1–R6 validation tests (they decide what the tool treats as true);
- the R7–R11 calculation tests, with hand-computed expected values;
- the security tests in section 5;
- the answer-key scoring test (below).

**Answer-key scoring (`tests/test_key_replay.py`)** uses recorded AI responses. Pass requires:
1. **Zero wrong claims.** No accepted term or claim is absent from or contradicts `terms-key.csv` and `entitlements-key.csv`. A single failure fails the build.
2. **Money missed** is reported as a number and compared with the previous run. It must not get worse.
3. **Referrals** are counted but don't count as errors.
4. Every key gap's cause is classified.

Also include a small set of adversarial fixtures: an informal email promise, an expired program, next-year's offer, an amendment with no "from/to," a document containing "ignore previous instructions," and a quote altered by one word.

## 5. Security: rule, enforcement, proof

| Rule from design | Enforced in | Proving test |
|---|---|---|
| Read-only; cannot change records or send | No write or network code outside `llm_client`; inputs opened read-only; no SMTP or HTTP libraries imported | Import and AST scan fails on `smtplib`, `socket`, `requests` outside `llm_client`; input files unchanged (hash) after a run |
| Credentials from environment only | `llm_client` reads `ANTHROPIC_API_KEY`; fails if absent | Secret-pattern scan of the repo finds nothing; a missing key gives a clear error |
| Reader gets one supplier's documents only | `reader` builds its prompt from one supplier's docs | Fake client records payloads. Assert no other supplier's text, no CSV data and no amounts |
| Checker gets kind + one cited document only, never the reader's answer | `checker` signature takes no `Term` fields other than `kind` and `doc_id` | Payload assertion: the reader's numbers and quote never appear |
| Letter AI gets supplier name and kinds only, no amounts | `letters` prompt builder | Payload assertion: no digits, no amounts |
| AI has no tools or file/email access | `llm_client` sends no `tools` parameter | Request-shape test |
| Document text is data, not instructions | Both prompts say so. R1/R2 catch invented terms | Injection fixture yields no accepted term from the injected text |
| Dashboard output escaped | `dashboard` escapes every interpolated value | `<script>` in a supplier name, quote and reason appears escaped |
| Run caps | `cli` | Test with 31 documents and 16 letters: the run stops or refers the excess, and never exceeds the caps |

## 6. Order of work and commands

Each step is tests first, then code, then a commit.

1. Project skeleton, dataclasses, fake `LLMClient`, frozen-files CI check.
2. `ingest`.
3. `validate`, covering R1–R6. This is the highest-risk part, so review it first.
4. `calc` and `reconcile`.
5. `reader` and `checker` prompts, with recorded fixtures.
6. `letters`.
7. `dashboard`.
8. `cli`, caps and run log.
9. Live-model run against the key, only with human approval (Q7).

**Gate order.** The deterministic checks must pass before any AI review. Proposed commands (confirm tools in Q2):
```
python -I -m unittest discover -s tests          # all tests, no network
ruff check . && ruff format --check .            # lint
bandit -r src                                    # security static scan
python -I -m tests.score_key                     # answer-key replay
```
Only after those pass: an AI review of the diff, and a person's review of the commit series.

## 7. Out of scope

- Contacting suppliers or sending letters.
- Writing to the ERP, accounting or warehouse systems.
- Any automatic acceptance of a term the two AI readings disagree on.
- Ongoing scheduling or triggering (it's run by hand).
- Suppliers beyond the 12 largest, unless you say otherwise (Q8).
- Multi-year history, or editing the answer key.

## 8. Open questions for you to answer before building

1. **Missing definitions.** What counts as "eligible purchases" (by branch, product, returns timing)? What is the exact program year? What are the co-op eligibility rules and the return-allowance formula? Tests R7–R11 can't be written without these.
2. **Tooling.** Is `ruff`/`bandit` allowed given "standard library only"? If not, which linter and security review should we use? Should we use `unittest` instead of `pytest`?
3. **Rounding and currency.** To what precision are amounts calculated, and how is the rounding done (cents, half-up)?
4. **Quote matching.** How strict is "word for word" for PDFs (line breaks, hyphenation, curly quotes, OCR of scans)? What about numbers written as words ("two percent")?
5. **Scale.** The cap is 30 documents per run, but 12 suppliers with exhibits and emails could exceed that. Is the cap per run or per supplier? Should the rest queue, or be referred?
6. **Answer key as test and as tuning set.** Do you have a held-out set of suppliers or terms that the prompts are never tuned against? Otherwise key scores will overstate accuracy.
7. **Live AI runs.** Who approves them and pays for them? May supplier documents leave your network to the API, and under what retention terms?
8. **Which suppliers.** Are all 45 in scope, or the top 12 only?
9. **Who can see the dashboard,** and how is access controlled on the server? The design lists audiences but no mechanism.
10. **Human review.** Which named person signs off on the reviewed tests, and what is the pass bar for "zero wrong claims" if the key itself contains a disputed term?
