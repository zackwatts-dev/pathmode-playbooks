# Application checklists

Checks each job application against your written requirements, with quoted evidence. No scores, no ranking.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/applicant-screening/**

## What it does

- Removes names, contact details, street addresses and education years before anything goes to the model.
- Checks each application on its own against each requirement: met, not met or unclear, with the words that show it.
- Downgrades "met" to "unclear" if the quoted evidence isn't in the application.
- Flags answers that mention personal traits, and applications with instructions aimed at an AI.
- Lists results by file name.

## What it doesn't do

- Score, rank, compare or recommend applicants.
- Reject anyone. A person reads every application and makes every decision.

**Rung 2. Read the legal notes in the playbook before using it, and talk to an employment lawyer, especially if you hire in New York City, Illinois, California or Colorado.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 applicant-screening/applicant_screening.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Requirements:** `--requirements job.md` with `## Must have` and `## Nice to have` lists.
- **Applications:** `--applications folder/` of .txt or .md files. Name them by number, not by the applicant's name.
- Redaction is a regex, and imperfect. Check the redacted text if in doubt.

It writes `out/checklists.md` and `out/checklists.csv`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `applicant_screening.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
