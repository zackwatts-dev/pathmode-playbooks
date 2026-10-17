# Inbox triage and draft replies

Sorts each email in a shared inbox, says who should handle it and how urgent it is, and drafts a reply.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/inbox-triage/**

## What it does

- Sorts every email into a category and urgency, and suggests who should handle it.
- Writes a one-line summary and, where a reply is needed, a draft reply as an .eml file.
- Always flags requests to change payment details, and emails with instructions aimed at an AI. Those checks are code, not the model.

## What it doesn't do

- Send, forward, delete, archive or mark anything as read. IMAP access is read-only and uses PEEK.
- Make promises: the instructions tell the model not to commit to times, prices or credits, and you read every draft.

**Rung 3: it reads your mail. It never sends; a person reads every draft and sends it from their own mail program.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 inbox-triage/inbox_triage.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **A folder of .eml files:** `--eml-dir path/`. Most mail programs can save or drag messages out as .eml.
- **A mailbox export:** `--mbox inbox.mbox` (for example from Google Takeout).
- **Gmail, read-only:** `--imap imap.gmail.com --user you@example.com --limit 25`, with an app password in `IMAP_PASSWORD`. Microsoft 365 turned off password sign-in for IMAP in 2022, so for Outlook, export .eml files instead.
- Fill in `instructions.md` (your categories, routing, voice) and pass it with `--instructions my-instructions.md`.

It writes `out/triage.csv`, `out/summary.md` (with "check these first"), and `out/drafts/*.eml`. Nothing is sent anywhere except the text sent to the model.

## Note

If you build on this with the Gmail API: the narrowest permission that can create drafts (`gmail.compose`) can also send. "Drafts only" has to be enforced by your code, as it is here.

## Files

| File | What |
|---|---|
| `inbox_triage.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
