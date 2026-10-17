# Quotes from call notes

Turns your notes from a sales call into a draft quote, using only your price list. The model picks items and quantities; code does the math.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/quotes-from-notes/**

## What it does

- Has the model choose line items by code from your price list, with a quantity and the words in your notes each came from.
- Looks up every price and does every calculation in code, including tax if you set a rate.
- Leaves off items that aren't on your price list, and flags items that aren't in your notes.
- Writes a draft quote (Markdown, and Word if python-docx is installed) and a "before you send this" checklist.

## What it doesn't do

- Set, change or discount a price.
- Send the quote.

**Rung 2: it works with your notes and your price list.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 quotes-from-notes/quotes_from_notes.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Notes:** `--notes call.md`: typed, dictated or a transcript.
- **Price list:** `--prices price-list.csv` with columns Code, Description, Unit, Unit price.
- **Tax:** `--tax-rate 0.056` for 5.6%. Check the rate for each job yourself.

It writes `out/quote.md`, `out/quote.docx` and `out/check.md`. Nothing is sent anywhere except the text sent to the model.

## Note

For Word output: `pip install python-docx`.

## Files

| File | What |
|---|---|
| `quotes_from_notes.py` | The script. Read it: the rules and checks are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
