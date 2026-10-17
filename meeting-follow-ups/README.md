# Meeting follow-ups

Turns a meeting transcript into decisions, tasks with owners and dates, and a follow-up email. It flags any task nobody owns.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/meeting-follow-ups/**

## What it does

- Reads .vtt (Teams, Zoom), .txt ("Name: words") or .docx transcripts.
- Requires a quote from the transcript for every decision and task, and checks it's there.
- Checks every owner was a speaker, every date is real and after the meeting, and every task has an owner and a date.
- Writes a tasks CSV (Title, Assigned to, Due date, Notes) to import into your task tool.

## What it doesn't do

- Send the follow-up email or create tasks anywhere.
- Fill in a missing owner or date: it flags them.

**Rung 2: it works with a transcript you give it.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 meeting-follow-ups/meeting_follow_ups.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Transcript:** `--transcript meeting.vtt --date 2026-07-13`. Download it from Teams (Recap → Transcript → Download), Zoom (Recordings & Transcripts) or Meet (the transcript Doc, saved as .docx or .txt).
- Tell people the meeting is being transcribed. Some states require everyone's consent.

It writes `out/minutes.md`, `out/tasks.csv` and `out/follow-up.txt`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `meeting_follow_ups.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
