# Expense categories

Applies your bank rules first, has the model suggest accounts for what's left, and sends anything uncertain to your bookkeeper.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/expense-categories/**

## What it does

- Applies your rules ("description contains" → account) before the model sees anything.
- Accepts only accounts on your chart of accounts, each with a confidence score.
- Always sends to review: low confidence, large amounts, transfers to people, meals and owner spending.
- Suggests new rules from the model's confident answers, so its share shrinks each month.

## What it doesn't do

- Post anything to your books. Your bookkeeper reviews and imports.

**Rung 2: it suggests; a person posts.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 expense-categories/expense_categories.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Transactions:** `--transactions bank.csv` with Date, Description, Amount (money out negative). That's QuickBooks' three-column upload format.
- **Chart of accounts:** `--accounts chart.csv` with Account, Type, Use for.
- **Rules:** `--rules rules.csv` with "If description contains", Account.
- Thresholds: `--threshold 0.8` (confidence) and `--large 2500`.

It writes `out/categorized.csv`, `out/review.csv`, `out/suggested-rules.csv` and `out/summary.md`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `expense_categories.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
