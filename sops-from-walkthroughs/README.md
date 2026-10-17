# Procedures from walkthroughs

Turns a transcript of someone explaining how they do a job into a written procedure.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/sops-from-walkthroughs/**

## What it does

- Writes steps, exceptions ("If ..., then ..."), a done-when checklist, open questions and "only one person knows this".
- Requires a quote from the transcript for every step and exception, and marks anything not found as "not in the walkthrough".
- Adds an owner, a written date and a review-by date.

## What it doesn't do

- Replace the test: someone else following the procedure once, while the expert watches.

**Rung 2: it works with a transcript you give it.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 sops-from-walkthroughs/sops_from_walkthroughs.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Transcript:** `--transcript walkthrough.txt --owner "Ann Lee"`. Lines like "Name: words" or plain text both work.

It writes `out/sop.md`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `sops_from_walkthroughs.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
