# Estimate check

Before a quote goes out, compares each line's labor with what the first runs of similar parts actually took, and flags the lines history says are light. Code finds the comparable work, does the arithmetic and sorts every line; an AI only writes a short note to the estimator, and code checks every number in it.

The full playbook, worked through at Wendlow Fabrication & Machine (a simulated Dayton job shop) with the design, the plan an AI wrote from it, and the owner's answers to its questions: **https://pathmode.com/playbooks/estimate-check/**

## What it does

It's used only on the families in `scope.json` (a person owns it): at Wendlow, the welded work (structural weldments, machined weldments and assemblies). A line in any other family is **not checked**: no history is looked up, no note is written, and the estimator prices it as today. `--scope all` checks every family.

For every quote line in scope:

1. **Finds comparable finished work** (code). For each work center on the line: operations at the same work center, on parts of the same family and material, in the same quantity band (1–4, 5–19, 20–99, 100 and over), finished in the three years before the quote was prepared and **strictly before that day**, and only **first runs** (`run_number` 1): these are new parts, and repeat jobs run faster as the floor learns. It needs at least 20. If there are fewer, it drops the material and quantity conditions (keeping first runs, the work center, the family and the dates) and tries again.
2. **Works out what history says** (code): for each work center, the median of each comparable operation's clocked over estimated hours, on setup plus run together. A work center with fewer than 20 comparables keeps its estimated hours and is marked "too few first runs", unless it matters (below). Then the line's labor both ways at the shop rates.
3. **Sorts the line** (code), on history's labor over the estimate's:
   - **check this:** 1.10 or more (at least 10% over);
   - **may be priced high:** 0.85 or less (at least 15% under). For information; it doesn't hold the quote;
   - **looks right:** in between;
   - **not enough history:** a person checks it. When *no* work center on the line has 20 comparables; when a thin work center matters (it's the family's main work center, the one with the most estimated labor across its first runs, or it carries 25% or more of the line's labor); when the line has no hours for a work center that at least half of its family's first-run jobs used (a weld step left off a weldment would otherwise make the line look right); or when the line can't be read: a bad row, the same line twice, the same hours row twice, no hours, an hours row that can't be read, or a work center with no shop rate. Every one says why, and the piles, with "not checked", always add up to the lines that came in. A row that can't be read goes to a person whatever its family.
4. **Writes a note per quote** with a line to check (AI). The model sees only the evidence for that quote: numbers already written out as text, work center codes, and the family and material from a fixed list. Lines are named L1, L2 and so on; no part number, customer, description, estimator or other free text, so nothing typed into a part record can reach it. The dashboard and `notes.md` say which part each name stands for. Every number in the note must be one of the evidence's own, written the same way; every percentage must keep the evidence's "over" or "under"; a year must be one of the evidence's months; no numbers in words; nothing reassuring ("looks fine", "no need to change"); and the note must give each line's dollar gap. A note that fails, a model error, a missing key, or anything over the limit of 100 notes a run gets a plain note code writes instead.
5. **A one-page dashboard**: the count in each pile, "not checked" included; the lines to check, largest dollar gap first, with their notes and the history behind them; lines sorted "looks right" or "may be priced high" with a thin work center, and why; the same by estimator and by part family; history's estimate of the labor the flagged lines would under-recover; and, with an answer key, the score, what the flagged lines truly under-recovered, and a flag-everything baseline.

It also writes `lines.csv` (every line, its pile and why; a cell that starts with `=`, `+`, `-` or `@` gets a leading `'` so a spreadsheet won't run it), `notes.md`, `rejected.csv` (every input row it couldn't use, and why), `summary.md`, `score.md`, and appends a line to `runs.csv`: when, which model, how many lines, how many in each pile.

## What it doesn't do

Change a quote, a price or the ERP, or send anything. It reads exported files and writes to `out/`. The estimator decides.

**Risk: works with files you give it. Level 2.**

## Try it

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
# The offline stand-in: no AI. It writes a plain note from the evidence.
python3 estimate-check/estimate_check.py --sample --dry-run

# Replay a recorded run: the notes a real model (Claude Sonnet 5.5) wrote on the sample, free
python3 estimate-check/estimate_check.py --sample --replay estimate-check/sample-data/recorded-run.json

# A real model: an API account whose terms say your data isn't used for training
export ANTHROPIC_API_KEY=...        # or PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=...
python3 estimate-check/estimate_check.py --sample
```

Then open `out/dashboard.html`. With `--sample`, `out/score.md` scores the run against the answer key. If a replay has no recorded note for a quote (because the evidence or the sample changed), that quote gets a code-written note and the run says "N quotes had no recorded answer". Without a key and without `--dry-run`, it still runs, and code writes every note.

`--data <folder> --answer-key <file>` scores a folder of your own (or a later month) the same way. `--scope all` ignores `scope.json`. `--gate` exits with an error if the score breaks `release-thresholds.json` (the owner's go-live limits). To record a new run with a real model (it costs API calls): `python3 tools/record.py estimate-check`.

## The sample: Wendlow's April and May 2024 quotes

Wendlow Fabrication & Machine is a fictional job shop, from a simulation of the whole business (`pathmode-corpus/simulations/fabricator/scripts/playbook_estimate.py`):
- **`quotes-to-check.csv`:** 327 new-part quote lines on 157 quotes, prepared in April and May 2024.
- **`quote-hours.csv`:** each line's setup and run hours by work center, from the hour standards.
- **`job-history.csv`:** 81,036 finished operations from April 2021 to March 2024, with estimated and clocked hours and which run of the part each job was. 5,825 are first runs.
- **`shop-rates.csv`:** the hourly rate for each work center.
- **`answer-key.csv`:** whether each line was really light (its work truly took 10% or more labor than estimated), from the simulation's truth, which the shop only learns after the job.

### Results: the offline stand-in, not the recorded run

These are from `--dry-run`. The piles and the score come from code alone, so a real model's run sorts the lines the same way; only the notes differ. Each run is also compared with the simplest rule there is: flag every line in scope.

Two things to know before reading them. **The answer key is kinder than a real one:** "light" comes from the simulation's expected first-run hours for each line, with no shop-floor noise, so it's the truth a perfect clocking system would give. A key built from real clocked hours will be noisier, and the check will score lower against it. **The welding overrun was planted:** the simulation makes welding on first runs of these families take about 25% longer than the standard. The check found it, but the holdout below tests whether what it found holds over time, not whether it can discover something new.

**1. First run, April–May 2024, every family** (`--sample --scope all`, before there was a scope):

- **327 lines:** 73 check this, 0 may be priced high, 239 looks right, 15 not enough history (14 missing an expected work center, 1 with a thin main work center).
- **Against the answer key** (75 really light): **34** caught ($30,861 truly under-recovered); **40** missed ($7,164); **39** false flags ($27,466 flagged); **15** to a person (1 of them light).
- History's estimate of the labor the flagged lines would under-recover: $47,395. What they truly under-recovered, from the answer key: $25,826 (history overstates it, because some flagged lines ran over by less than 10%, or under).
- **Release thresholds:** fails two of three. 53% of light lines missed (at most 20%), 53% of flags fine (at most 50%), 5% to a person (passes, at most 10%).
- **Flag everything:** 75 caught, 0 missed, 77% of flags fine. The check is far more precise than that, but it misses half the light lines.

What that means: the check finds the shop's *systematic* light spots. All 25 light weldments are flagged, and 9 of the 11 light assemblies. It can't see a line that's light for its own reasons in a family history says is estimated about right: 38 of the misses are cut-and-formed and sheet-metal parts, and they're small (about $180 each).

**The decision.** The check failed the release thresholds, so the owner limited it to the welded families (structural weldment, machined weldment, assembly), in `scope.json`. That was written down after this run and before any holdout data was made.

**2. The same quotes with the scope** (`--sample`, the default):

- **327 lines:** 73 check this, 0 may be priced high, 2 looks right, 0 not enough history, 252 not checked.
- **In scope** (75 lines, 36 really light): **34** caught ($30,861); **2** missed ($943); **39** false flags ($27,466 flagged); **0** to a person. Truly under-recovered on the flagged lines: $25,826.
- **Out of scope:** 252 lines not checked, 39 of them light. They're priced as they are today, and they don't count in the rates.
- **Release thresholds, in scope:** 6% missed (passes); 0% to a person (passes); **53% of flags fine (fails, at most 50%)**.
- **Flag everything in scope:** 36 caught, 0 missed, 52% of flags fine. **The check does no better than flagging every welded line.** This is the April–May data the scope was chosen from, so it flatters the scope.

**3. Holdout, June–July 2024, with the scope.** These quotes were held back until the decision and the unchanged thresholds were written down, with history ending 31 May 2024. Generate them with `simulations/fabricator/scripts/playbook_estimate.py OUT --as-of 2024-06-01 --to 2024-07-31` in the corpus, then score with `--data OUT --answer-key OUT/answer-key.csv`.

- **380 lines:** 93 check this, 0 may be priced high, 3 looks right, 0 not enough history, 284 not checked.
- **In scope** (96 lines, 50 really light): **49** caught ($34,539 truly under-recovered); **1** missed ($380); **44** false flags ($30,026 flagged); **0** to a person. Truly under-recovered on the flagged lines: $32,613, against history's estimate of $52,210.
- **Out of scope:** 284 not checked, 34 of them light.
- **Release thresholds:** all three pass. 2% missed (at most 20%), **47% of flags fine (at most 50%, a narrow pass)**, 0% to a person.
- **Flag everything in scope:** 50 caught, 0 missed, 48% of flags fine. Again, about the same as the check.
- For comparison, every family (`--scope all`): 93 / 0 / 280 / 7 / 0; 49 caught, 35 missed, 44 false flags, 7 to a person; fails on misses (42%).

**What that says.** In scope, it flags 93 of 96 lines: nearly every welded quote is light, because the shop's welding standard is. Flagging every welded line would do as well. The check's value here isn't picking lines out; it's the evidence, per work center and with the history behind it, for fixing the welding standard (no AI needed), and a safety net afterward. Once the standard is fixed, run the answer key again: the flags should fall, and the thresholds and the baseline will tell you whether it still earns its keep.

## Before you run this on your own data

- **The columns are Wendlow's.** `quotes-to-check.csv` needs `quote_id, quote_line_id, prepared_on, estimator, part_number, family, material, quantity` (part number, customer and description are shown on the dashboard, never sent to the AI); `quote-hours.csv` needs `quote_line_id, work_centre, setup_hours, run_hours_each`; `job-history.csv` needs `job_id, completed_on, family, material, quantity, run_number, work_centre, est_hours, clocked_hours`; `shop-rates.csv` needs `work_centre, rate_per_hour`. A missing column stops the run.
- **Dates must be `YYYY-MM-DD`; hours and quantities plain numbers.** Rates may have a `$` and commas. Anything else (`4/1/2024`, `N/A`, a negative) isn't guessed: a quote or hours row like that sends its line to a person, and a history or rate row is listed in `rejected.csv` and not used. History rows with zero estimated hours are skipped (there's no ratio to take), and listed too.
- **`run_number` matters.** Without it, or if your system counts repeat jobs as first runs, history mixes in jobs the floor has learned, and light quotes look fine. If you can't get it, the check is weaker than it looks.
- **The scope is Wendlow's.** `scope.json` lists the families to check; the names must be in `FAMILIES`, or the run stops. Choose yours from your own answer-key run, write the choice down before you score a later month, and score that month with the scope.
- **The quantity bands, the 20-comparable minimum, the three-year window and the thresholds** are constants at the top of `estimate_check.py`. Change them only with a new answer-key run.
- **Families and materials the AI is told** come from fixed lists (`FAMILIES`, `MATERIALS`); anything else is sent as "other" (the line is still sorted with its own family). Put your own families in.
- **Work center codes must be plain** (letters, digits, `-` or `_`). A work center with hours but no rate, or two different rates, sends its lines to a person.
- **The note check is strict.** "$1,240" passes; "1,240 dollars", "$1.2k", "two lines", "by 2024", "28% under" for "28% over", and any number the evidence doesn't have (even "2 lines") fail, and so does reassurance ("looks fine", "no need to change"). Code writes the note instead. The reassurance list is a small phrase list: a reworded reassurance can get through, which is why the note can never change a pile.
- **Expected work centers come from history.** A center on at least half of a family's first-run jobs in the window is expected on its lines, so the history needs a `job_id` that ties a job's operations together. A family that genuinely skips a step on some parts (no paint on some weldments) will send those lines to a person.
- **One quote line, one estimate.** The median ratio treats setup and run together; it can't tell a slow setup from a slow run.
- **Build your own answer key** before you trust it: for a month of quotes already finished, mark the lines whose clocked labor came in 10% or more over. Re-run it after any change, including a new model or new hour standards.
- **Who can see the output** is up to where you write it. Point `--out` at a folder only the estimating team and the general manager can open.

## Running it for real

`run.sh` runs it once over the day's export. Schedule it each evening, for example with cron:

```
30 18 * * 1-5 /srv/pathmode-playbooks/estimate-check/run.sh >> /srv/estimating/cron.log 2>&1
```

## Files

| File | What |
|---|---|
| `estimate_check.py` | Load, comparables, history, piles, evidence, notes and the number check, scoring, the run log. |
| `estimate_dashboard.py` | The dashboard. |
| `release-thresholds.json` | The owner's go-live limits for the score. |
| `scope.json` | The families the check is used on (the owner's decision after the first run). |
| `instructions.md` | A chat-assistant version, to try the note by hand. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited (written before the first-runs change). |
| `sample-data/` | Wendlow's quotes, hours, history, rates, answer key and recorded run. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
