# Design: an AI analyst that finds where the money goes, for Summit Mechanical

## The problem

We're a commercial HVAC contractor: about 170 people, three branches, about $55 million billed a year. We know money leaks somewhere. Some finished work probably never gets billed, some jobs need a second visit, some service agreements may lose money, and customers leave without saying why. We can't say which of these are real, how big each one is, or where to start.

The answer is spread across six systems that don't agree with each other: field service (work orders, visits, time, parts, notes), the customer portals (purchase orders, not-to-exceed amounts, increase requests, invoice submissions), accounting (invoices, payments, write-offs, payroll), the service inbox, the warehouse and truck stock, and outside data such as the weather. Nobody here has the time or the SQL to join them, and a consultant would take three months. So the questions stay open for years.

## What it does

An AI analyst studies the whole business from a read-only copy of its records, the way a good outside analyst would, and hands the owner a short list of where the money goes: each finding with its dollars a year, the evidence, how sure it is, what it is *not* evidence of, and the next step. A second AI attacks every finding before anyone sees it. Code checks that every number in the report came from a query the analyst actually ran.

The work runs in stages, each a fresh AI session that sees only what that stage needs:

1. **Orient** (AI). Reads the warehouse documentation and queries the tables. Writes a map of the business's operating cycles (what each table records, its grain, what it can and can't answer) and a list of data concerns: anything that looks wrong, missing or suspicious in the records. It recommends nothing.
2. **Propose** (AI). From the map, writes twelve hypotheses about where money or time is lost. Each is falsifiable, sized roughly with the reasoning shown, says what would support it and what would weaken it, and names the tables and columns it needs. Ranks them twice, separately: by likely dollars, and by whether the data can answer them. Code picks the investigations: the top ones by the two rankings together, up to the run's budget (ten by default).
3. **Investigate** (AI, one session per hypothesis). Before its first query, writes down how it will test the hypothesis, what would support it, what would weaken it, and what it expects. Then queries, following what it finds: concentration, time, segments, denominators. Writes one finding: the conclusion, dollars a year where it can size them, the counts and denominators, its confidence, what it couldn't tell, and the query behind every number.
4. **Challenge** (an AI checker, one fresh session per finding). Gets the finding and the queries it cites, never the investigator's working notes. Assumes the conclusion may be wrong and looks for what would explain the same numbers another way: confounders, aggregation, seasonality, mix, selection, missing data, how the system records things. Runs its own queries to tell them apart. Returns one of: stands, stands with changes (with what changed), or retracted, and the queries behind it.
5. **Revise** (AI, the investigator again, with the challenge). Accepts the challenge or answers it with queries. The revised finding replaces the original. A retracted finding can't come back without new queries that answer the challenge's.
6. **Check** (code). See "The checks" below. A finding that fails is held back from the report and listed, with why.
7. **Report** (code assembles; AI writes the summary). Findings ranked by dollars a year, each with its confidence and its challenge verdict; the hypotheses looked at and found not to hold (a result, not a gap); the data concerns; and what the records can't answer. The AI writes a one-page summary for the owner from the checked findings only, and code checks its numbers the same way.

The analyst never recommends discipline or names an employee as the cause of anything; people appear by id, and a pattern in someone's records is a pattern worth a conversation, never a conclusion.

## The tools the AI has

Every session has the same three tools and nothing else: no shell, no network, no files outside its own folder.

- **query**: runs one SQL statement against a read-only copy of the warehouse (DuckDB, opened read-only). Only `SELECT` and `WITH` are accepted; one statement at a time; results are capped at 200 rows shown (the full count is reported). Every call, its SQL, and its full result are written to the run's ledger by the tool, with an id the AI cites.
- **docs**: reads a file from the warehouse documentation.
- **save**: writes the stage's output file (the map, the hypotheses, the prediction, the finding, the challenge) into the session's own folder, in a fixed JSON shape.

The ledger is written by the tool, not by the AI, so the checks never rely on what the AI says it ran.

## Inputs

- **The warehouse:** a DuckDB file built from the six systems' exports, with its documentation: a short context primer (what the company is and does, in the owner's words, three or four sentences) and a description of every table and column. Nothing else: no findings from earlier analyses, no answer key, no hints about what's wrong.
- **The owner's notes** (optional): known events the data won't explain (we moved the warehouse in March; this customer is billed differently). Empty for the simulation runs.
- **The answer key** (simulation only, never seen by any AI session in the run): every problem the simulation planted, what drives it, where it shows in the records, and its true size per year; and the truth database it came from.

## The checks (code)

- **Every number traces.** Each number in a finding's claims (counts, dollars, rates, ratios) must appear in the result of a query the session ran, at the precision shown (a rounded figure matches the value it rounds). Arithmetic on results counts only if the AI ran it as a query too: the rule "never emit a number you didn't compute" made literal. Exempt: years, dates, and small integers up to 12 used as counts of things named in the text. A finding with an untraced number is held back.
- **Every cited query exists** in that session's ledger, and code re-runs it against the warehouse and gets the same result.
- **The size is a computed value.** A finding's dollars a year must equal a value in one of its cited queries' results.
- **The prediction came first.** In each investigation, the prediction file must be saved before the session's first query.
- **The challenge is respected.** A retracted finding is never reported as a finding; it moves to "looked at, not true", unless its revision cites new queries run after the challenge.
- **No one is accused.** An AI checker reads each finding's and the summary's words (only the words) and says whether they name an employee, accuse anyone, state a cause as fact without evidence, or suggest discipline, quoting them. Any of those, with its words found in the text, holds the finding back for a person.
- **Instructions in the data are reported, never followed.** Free text in the warehouse (notes, emails) is data. A finding or a summary that reports text addressed to an AI as an instruction is fine; one that changes what it does because of it fails review. Every session's prompt says so.

## What "correct" means

- **The answer key defines it.** A finding matches a planted problem when it identifies the same mechanism (what happens, where in the business) with evidence from the records. Fully: mechanism and where it shows. Partly: the right effect with a wrong or missing cause, or one part of a two-part problem. A finding can also be true but not planted, when the truth database confirms it, and it counts as correct, not as a match. A finding the truth contradicts is wrong.
- **Grading** is done finding by finding by an AI grader that gets one finding, the answer key and read access to the truth database, and must cite the truth query behind its grade. Code checks every number in the grade. A person reviews every grade before it's recorded; the scorecard says which grades the person changed and why.
- **What we measure:**
  - planted problems found, fully and partly, and their share of the planted dollars a year;
  - sizing: each found problem's dollars against the truth's;
  - wrong findings: how many reached the report as findings, and how high they ranked;
  - findings held back by the checks, and why;
  - the run's cost: sessions, tokens, and hours.
- **Mistakes aren't equal.** A wrong finding near the top of the report is the worst: the owner acts on it. A missed problem costs money that stays lost. A finding held back by a check costs a person's look.
- Every check has a test that runs without calling the AI.

## Security

- **Read-only.** The warehouse is a copy, opened read-only; the query tool refuses anything but `SELECT`/`WITH`, refuses `ATTACH`, `COPY`, `INSTALL`, `LOAD`, `PRAGMA`, `SET` and file-reading functions (`read_csv`, `read_parquet` and the like), and runs with external access turned off.
- **No other tools.** No shell, no network, no web, no files outside the session's folder. Through the Claude CLI, the allowed tools are exactly the three, and everything else is denied.
- **Each session sees what its stage needs:** the challenger never sees the investigator's notes; the words checker sees only the words; no session sees the answer key, the truth database, or earlier analyses.
- **Data is not instructions.** Notes and emails in the warehouse are free text written by staff and customers; the prompts mark them as data.
- **Employees appear by id.** The report goes to the owner only.
- **Software:** Python 3.11+, DuckDB pinned by hash. Credentials come from the environment.

## How it runs

- **On demand,** not on a schedule: once to start an engagement, then again after a big change in the business. One run takes a few hours.
- **A budget per run:** at most ten investigations, each with one challenge and one revision; a cap on queries per session (150) and on dollars per session. A session that hits its cap saves what it has, marked incomplete.
- **Everything is kept:** every session's transcript, the ledger, the hypotheses not pursued, and the checks' results, so a person can follow any number back to its query.
- **Replay:** a recorded run replays for free: the checks, the report and the scoring re-run from the ledger and the saved outputs.
- **After any change** to a prompt, a check or the model, the method is re-run on the development businesses before it's used again.

## Development and testing

- **Development** on two other simulated businesses, Hartwell Supply Co. (a distributor) and Wendlow Fabrication & Machine (a job shop), whose answer keys and earlier blind runs we have. Prompts and checks are tuned there only.
- **The sample** is Summit Mechanical as it stands, run once with the method frozen. Earlier analyses (by other methods) ran on Summit; none of their outputs is visible to this run.
- **The held-back test** is a new run of Summit with three or four problems planted that no version of the method has seen, chosen and described by someone with no sight of the playbook, built into the simulation with the change recorded, and the method run once, frozen, and scored. Its pass marks are written before it exists.
