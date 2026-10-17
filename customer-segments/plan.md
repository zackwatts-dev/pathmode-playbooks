<!-- Written by Claude Sonnet 5.5 from ../plan-prompt.md and design.md on 2026-10-17, unedited. The review of it is on the playbook page, Step 3. The prompt then still said "reading mail, matching to records", left over from RFQ intake; the plan noticed, and the prompt has since been made generic. -->

# Build plan: Summit customer segments

Commands assume Python with pytest, ruff and bandit. Confirm that in the open questions.

## 1. Ground rules for the agent

- Work on branch `segments-v1`. Make one commit per step in §6, each with its tests passing.
- **Tests and the answer key are read-only to the agent.** It may add tests but must not edit or delete existing ones, or the answer key, without a person's approval. If a test seems wrong, stop and ask.
- Only the evaluation module and its tests may read the answer key. The pipeline code must not be able to import or open it (see leakage test L3).
- Run checks in this order: tests, then lint, then the security scan, then the AI review. A failure at any step stops the process.

## 2. Parts and their boundaries

Each part is a separate module with typed inputs and outputs, and each can be tested without the others.

| Part | In → Out | Rules |
|---|---|---|
| `ingest` | the 7 export files + cutoff date → validated tables | Rejects missing columns, bad types and dangling IDs. Drops any row dated after the cutoff and counts the drops in the log. |
| `features` | tables + cutoff → one row per customer | Features as listed in the design. Window is the 24 months before the cutoff. Uses nothing dated after the cutoff. |
| `segments` | feature matrix → segment label, 2D coordinates | Scale features, then k-means. Choose k by silhouette score over a fixed range. Fixed random seed. |
| `predict` | features + outcome labels → verdict per question | 70/30 split with a fixed seed. Logistic regression and a one-line rule are compared on the 30% test set only. Verdict is `model`, `rule` or `not_predictable`. |
| `matching` | AI output → checked output | Extracts every number in the AI text and checks it against the data it was given. Rejects the text if any number is unsupported. |
| `explain` | segment averages, or one customer's numbers → text | Calls the AI. Input is built from an allow-list of fields. Output goes through `matching` before it is kept. |
| `outputs` | all results → dashboard files + log line | Dashboard has the four panels from the design. Writes one log line per run. |

The design says "matching to records". I read that as `matching` (checking AI numbers against the data). The design contains no mail, so I read "reading mail" as `ingest`. Please confirm both.

## 3. Business rules to pin down

These are the points the agent must not decide for itself.

1. **Cutoff and outcomes.** Features use data up to the cutoff only. The "paid late" and "left" outcomes come from the following 12 months. Outcome labels are never available to `features`.
2. **Test set.** The 30% is held out before any fitting. Scaling and imputation are fitted on the 70% only.
3. **Verdict rule.** The model wins only if it beats the rule on the test set by a margin and metric set in §8, with a stated uncertainty check. If neither beats a trivial baseline, the verdict is `not_predictable`.
4. **Re-testing.** Every run re-splits, re-fits and re-tests. If a prediction that previously passed no longer beats the rule, the dashboard shows that on the panel.
5. **AI text.** The AI may use only the numbers it is given. Any number that fails the check means the text is discarded and the dashboard shows the figures without commentary.
6. **Log line.** Each run writes one line with: date, cutoff, row counts, chosen k, verdicts, and the number of AI texts rejected. It contains no customer data.

## 4. Tests first (written before any implementation)

**Segments**
- S1. On the simulated data, segments match the hidden behavior groups. The threshold (for example adjusted Rand index) is set in §8.
- S2. Same input and seed give identical labels.
- S3. k is the silhouette maximum over the range (checked on a small fixture with a known best k).

**Predictions**
- P1. On data where the outcome is random, the verdict is `not_predictable`.
- P2. On data where the outcome follows a simple threshold, the verdict is `rule`.
- P3. On data with a combined signal, the verdict is `model`.
- P4. No customer is in both the 70% and the 30%.
- P5. Scaler and model are fitted on the 70% only.
- P6. A previously passing prediction that now fails shows the warning on the dashboard.

**Leakage**
- L1. Add records dated after the cutoff. The feature output must not change.
- L2. No feature column can be derived from the outcome it predicts. Test this by shuffling outcome labels and checking the features are unchanged.
- L3. Pipeline modules cannot read the answer-key path.

**AI and checks**
- A1. Text with a number not in the input is rejected.
- A2. Text with only supplied numbers (including rounded forms) passes.
- A3. The AI input contains only allow-listed fields.

**Other**
- F1. Each feature has a hand-computed expected value on a small fixture.
- I1. Each ingest rejection case fails with a clear error.
- O1. The log line has the expected fields and no customer data.

**A person must review before the agent starts building:** S1 and its threshold, P1–P3, L1–L3, A1–A3, F1. These define "correct". The rest are mechanical.

## 5. Security rules, where enforced, how proven

| Rule from the design | Enforced in | Proven by |
|---|---|---|
| Customer data stays on Summit's server | The only outbound call is in `explain`. Network access is blocked everywhere else. | Test that fails if any other module opens a socket. Run the pipeline with network disabled. |
| AI sees only segment averages, or one customer's numbers at a time | Allow-list in `explain` that builds the request | A3, plus a test that sends one customer and checks the payload contains exactly the allowed fields |
| No contacts or addresses reach the AI | The same allow-list. Contact and address columns are dropped in `features` and never passed on. | Test with a fixture containing names, emails and addresses. Search the request payload for them. |
| The late-payment list is billing-only | Access check in `outputs`. The list is written to a separate file or page that requires the billing role. | Test that a non-billing user is denied (403) and that the main dashboard contains no list |
| Pinned packages with hashes | `requirements.txt` generated with hashes. Install with `--require-hashes`. | CI step that fails on an unpinned or unhashed entry. `pip-audit` for known vulnerabilities. |
| The AI cannot be fooled into leaking via its output | Output passes `matching`. Output is escaped when rendered. | Test with text containing HTML or script. It must be rendered inert. |

## 6. Order of work (one commit each)

1. Project skeleton, pinned requirements, lint config, empty test folders.
2. Tests from §4 (a person reviews these before step 3).
3. `ingest`
4. `features`
5. `segments`
6. `predict`
7. `matching`
8. `explain` with the allow-list. Use a stub AI in tests.
9. `outputs`, the access check and the log line.
10. End-to-end run on the simulated data.

## 7. Checks before merge

```
pytest -q                          # all tests, including the answer-key ones
ruff check . && ruff format --check .
bandit -r src/
pip-audit -r requirements.txt --require-hashes
```

After these pass, run the security-review skill on the diff. Only then run the AI code review. A person reviews the final diff and the end-to-end output.

## 8. Out of scope

- Live or real-time updates, or integration with Summit's system (read-only exports only).
- Acting on the results: no emails, reminders or changes to customer terms.
- Models other than k-means and logistic regression.
- Hyperparameter tuning beyond the chosen k.
- Training on real customer data (this build uses the simulation).
- Multi-user accounts beyond a billing/non-billing split.

## 9. Open questions to answer before building

1. **Mail.** Is there any email input, or does "reading mail" just mean reading the exports?
2. **Dates.** What are the cutoff date and the outcome window? The answer key says "2025", so I assume a cutoff at the end of 2024.
3. **Definitions.** What counts as "left"? For example, no job in 12 months. What is "late" for a payment (more than 20 days past due)? What counts as a "slow" job or a "repeat visit"?
4. **The one-line rule.** Which rule for each question? For example, "paid late last year, so will pay late next year".
5. **Beating the rule.** Which metric (AUC, precision at top 50?), what margin, and how much uncertainty is acceptable? With about 360 test customers, small gaps will be noise.
6. **Segment pass mark.** What agreement with the hidden groups counts as passing (S1)?
7. **The AI.** Which model, and is it hosted? If hosted, "stays on Summit's server" holds only for the raw data, and the averages leave the building. Is that acceptable?
8. **Billing-only.** How do users log in and get a role today? Without that, I can only build a stub check.
9. **Dashboard.** Static files or a small web app, and what must it run on?
10. **Tooling.** Is Python with pytest, ruff, bandit and pip-audit fine, and which Python version?
11. **Failure behavior.** If a run fails partway, should the dashboard keep the previous quarter's results or show an error?
