# Customer RFQ intake

Reads incoming quote requests and pulls out the products, quantities, deadlines and missing information. Then it matches each item to your catalog and sorts everything by when the quote is due, so quoting starts from a clean list and no request slips.

The full playbook, with no-code setup on ChatGPT, Claude, Gemini and Copilot, a cost calculator and the risks: **https://pathmode.com/playbooks/rfq-intake/**

## What it does

- Reads quote requests saved as .eml, including CSV and text attachments (an equipment schedule, a parts list).
- Has the model extract the customer, site, quote-due and needed-by dates, and every item with its quantity, quoting the words it came from.
- Matches each item to your catalog in code: by your code, by a part number or name customers use (the Aliases column), or as a possible match by shared words. Each gets marked exact, alias, possible or no match.
- Decides in code what's missing, and writes the questions: vague quantities, unmatched items, no site. It drafts a reply asking for them.
- Flags any item that isn't in the email, and any date that isn't a real date.
- Sorts requests by quote due date, with days left, and sets aside emails that aren't quote requests.

## What it doesn't do

- Price anything, or choose products for the customer. Hand the clean list to your quoting tool, or to the [quotes-from-notes](../quotes-from-notes/) playbook.
- Send the questions. They're drafts.
- Read PDFs. Convert them to text first, or use a no-code assistant, which reads PDFs.

**Rung 2: it reads requests you export. A person checks the list and sends every reply.**

## Try it in five minutes

From the repository folder, with Python 3.11 or later and nothing to install:

```sh
python3 rfq-intake/rfq_intake.py --sample --dry-run
```

`--dry-run` uses a simple offline stand-in instead of an AI model, so it's free and needs no account. Its answers are deliberately crude; the point is to see the whole pipeline and the checks.

Then with a real model: set `ANTHROPIC_API_KEY` (or `PLAYBOOK_PROVIDER=openai`, `OPENAI_API_KEY` and `PLAYBOOK_MODEL`), and run the same command without `--dry-run`. Use an API account or business plan whose terms say your data isn't used for training.

## Use it on your own data

- **Requests:** `--eml-dir folder/` of saved emails. Most mail programs can save or drag messages out as .eml. A filter that labels everything sent to quotes@ makes this a one-click export.
- **Catalog:** `--catalog catalog.csv` with Code, Description, Unit, Aliases. Aliases are the other names for each item, separated by semicolons: manufacturer part numbers, sizes written different ways, what customers actually call it. The better your aliases, the more exact matches you get. Every "no match" the tool reports is a candidate alias.
- `--as-of 2026-07-13` counts days left from a date other than today.

It writes `out/summary.md`, `out/rfq-log.csv` (one row per request), `out/line-items.csv` (one row per item, ready for a quoting spreadsheet), and `out/questions/*.eml`. Nothing is sent anywhere except the text sent to the model.

## Files

| File | What |
|---|---|
| `rfq_intake.py` | The script. Read it: the matching and the missing-information rules are plain code. |
| `instructions.md` | The same job as instructions for a no-code assistant (a Project, Gem or agent). |
| `sample-data/` | Fictional data for Summit Mechanical, a made-up commercial HVAC contractor: five requests and a catalog. |
| `tests/` | Tests that run offline: `pytest` from the repository root. |
