# Customer replies from your documents

Drafts answers to customer questions from your own documents, with sources, or says "not covered".

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/support-replies/**

## What it does

- Splits your documents into sections and searches them with BM25 (standard library only).
- Sends the model only the best few sections, and requires it to cite them or answer "not covered".
- Checks citations point to sections it was given, and that every number in an answer appears in a cited section.
- Doesn't ask the model at all when nothing in your documents comes close.

## What it doesn't do

- Send replies.
- Know anything your documents don't say. That's the point.

**Rung 2: a person reads every draft and sends it.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 support-replies/support_replies.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Documents:** `--docs folder/` of .md or .txt files. Use `## ` headings to split them into sections.
- **Questions:** `--questions questions.txt`, one per line.
- BM25 matches words, not meanings. If customers say "AC" and your documents say "cooling", add both words to your documents, or move to a search that understands meaning (embeddings) when you outgrow this.

It writes `out/answers.md` and `out/review.csv`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `support_replies.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
