# Supplier agreements

Holds suppliers to what their agreements say they owe you. An AI reads every agreement, amendment, program sheet, terms page and email for each supplier, and returns each term with the exact words it came from. Code checks every term against those words and works out what each supplier owes from your own purchase records. It compares that with the supplier's statement and with what you've claimed. A person reviews every claim and sends it; nothing here contacts a supplier or changes a record.

The full playbook, worked through at Hartwell Supply Co. (a simulated HVAC/R distributor) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/supplier-agreements/**

## What it does

For the program year in `records/program.json`, supplier by supplier, largest purchases first:

1. **Reads the documents** (code). PDFs are read with poppler's `pdftotext`, page by page, with words hyphenated across a line break joined again. Emails (`.eml`) are read with Python's email parser. A document it can't read goes to a person, and so does a supplier with nothing on file.
2. **Reads the terms** (AI). One supplier's documents go to the model at a time, as data. It returns each term in a fixed form:
   - volume tiers, growth, a product-line incentive, co-op, freight prepaid, stock rotation, or eligible locations;
   - the numbers, what purchases it covers, and the dates;
   - **the exact words it came from**;
   - whether it's informal or unclear.

   It also reads the supplier's statement, line by line. At most 30 documents go to the model in one run. A supplier over the limit is listed for the next run.
3. **Checks each term** (code). A term is used only if:
   - its words are in the document it names (ignoring case, punctuation and spacing, with "..." between passages no more than 200 characters apart);
   - every number in it is in those words, and every tier row (threshold and rate) is on one line of the document;
   - its tiers rise;
   - its rates are between 0 and 10%.

   An informal promise (a rep's email that the agreement doesn't back) or an unclear term goes to a person with its words, never into a claim. So does anything that fails a check.
4. **Settles the terms** (code). A later document's term of the same kind replaces an earlier one. An amendment that changes one tier changes only that tier. Added locations count from the date they were added.
5. **Works out what's owed** (code, no AI), from the records:
   - eligible purchases from the supplier's own invoices, each counted once (a re-sent copy ending `-R` is a duplicate), net of returns, by product and by location as the terms say;
   - the volume rebate at the tier reached, from the first dollar or by band as the terms say;
   - growth over the prior year;
   - the product-line incentive from its start date;
   - co-op accrued against claims filed and eligible marketing spend;
   - freight billed and paid on orders at or over the prepaid minimum;
   - the stock-rotation allowance against returns made and stock unsold all year within the age limit, less any restocking fee.
6. **Compares** (code) with the statement, which must add up to what you were actually credited (`rebate-receipts.csv`), and with the co-op claims filed. Three cases never become a claim and go to a person instead:
   - a rebate with no statement read;
   - one that depends on a term that went to a person;
   - a co-op balance whose claim window has closed by the run date.
7. **Drafts the letters** (AI), one per supplier with money due, from the evidence code computed: the amounts, the term's words, how each was worked out. Every number in a letter must be one of the evidence's own; a letter that fails, a model error, or one over the limit of 15 a run is replaced by a plain letter code writes.
8. **A one-page dashboard**:
   - money due by supplier and by kind, largest first, each with its words and how it was worked out;
   - the stock that can go back;
   - the deadlines;
   - what's waiting for a person;
   - the letters;
   - with an answer key, the score.

It also writes:
- `claims.csv`, with every amount and the records behind it (a cell that starts like a formula gets a leading `'`);
- `terms.csv`, every term used;
- `to-a-person.csv`;
- `letters.md` and `summary.md`;
- `score.md`, with an answer key;

and it adds a line to `runs.csv`: when, which model, how many terms, and the money found by kind.

## What it doesn't do

- **It doesn't send anything:** no email, no claim, no return request. A person reviews and sends each one.
- **It doesn't change a record,** a payment or a supplier's account.
- **It doesn't read scanned PDFs** (images of text). Those go to a person as unreadable.
- **It doesn't decide informal promises.** A rep's email that the agreement doesn't back is shown to a person, with its words.

## Try it

```sh
# The offline stand-in: no AI. Every agreement goes to a person, which is the safe failure.
python3 supplier-agreements/supplier_agreements.py --sample --dry-run

# Replay a recorded run: what a real model (Claude Sonnet 5.5) read on the sample, free
python3 supplier-agreements/supplier_agreements.py --sample --replay supplier-agreements/sample-data/recorded-run.json

# The held-back year, 2024, replayed
python3 supplier-agreements/supplier_agreements.py --data supplier-agreements/holdout-2024 \
  --answer-key supplier-agreements/holdout-2024/answer-key/entitlements-key.csv \
  --replay supplier-agreements/holdout-2024/recorded-run.json

# A real model: an API account whose terms say your data isn't used for training
ANTHROPIC_API_KEY=... python3 supplier-agreements/supplier_agreements.py --sample
PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=... python3 supplier-agreements/supplier_agreements.py --sample
```

It needs Python 3.11 or later and `pdftotext` (poppler; `apt install poppler-utils` or `brew install poppler`). Nothing else.

## The sample: Hartwell's 2025 program year

Hartwell's twelve largest suppliers (four equipment makers and eight parts and supplies houses) account for about $87 million of its 2025 purchases.

**The documents** are in `sample-data/agreements/<supplier>/`, written the way suppliers write them:
- distributor agreements with exhibits;
- an amendment letter;
- program sheets;
- terms-and-conditions pages with the program in one section;
- a territory manager's email adding two branches;
- a rep's email promising something the program doesn't say;
- each supplier's 2025 rebate statement.

One program sheet carries a note telling "automated rebate systems" to record everything as paid. It changes nothing.

**The records** are in `sample-data/records/`: Hartwell's supplier bills and their lines, purchase orders, products, returns to suppliers, rebate credits received, co-op claims, marketing spend, and stock on hand at the year end.

**The answer key** is in `sample-data/answer-key/`:
- `terms-key.csv`, every term as written;
- `entitlements-key.csv`, what each supplier truly owed under each term, what was paid or claimed, and why they differ.

`holdout-2024/` is a second program year, generated after the checks were settled, with the gaps on other suppliers. The release thresholds (`release-thresholds.json`) were written down before it was run.

## Before you run this on your own data

- **Check the reading on a supplier you know well first.** Compare `terms.csv` with the agreement yourself. The checks prove the words are there; they don't prove the AI chose the right words.
- **Your invoices are the base.** If your purchasing system doesn't keep the supplier's invoice number, add a check for duplicates that suits it.
- **Locations, product groups and categories must match your agreements' words.** Map them once, and have someone who negotiates the agreements confirm it.
- **Claim windows matter.** Set `as_of` in `records/program.json` to the day you run it. A co-op claim past its window goes to a person.
- **An amount is a claim, not a fact, until the supplier agrees.** Send the evidence with every claim, and keep the conversation friendly; you'll be buying from them next year.

## Running it for real

- Once after the statements arrive, and again when a new agreement or amendment comes in.
- On a server you control, with the key in its secret store.
- The output goes to a folder only purchasing, the controller and the CFO can open.
- After any change, including a new model version, run the sample and the held-back year again, and check `release-thresholds.json`.

## Files

| File | What it is |
|---|---|
| `supplier_agreements.py` | Reads, checks, works out, compares, drafts and scores |
| `agreements_dashboard.py` | The one-page dashboard |
| `design.md`, `plan.md` | The design, and the plan an AI wrote from it (unedited) |
| `release-thresholds.json` | What counts as good enough: set before the held-back year was run |
| `tests/` | Every rule above, without calling the AI |
| `sample-data/`, `holdout-2024/` | Hartwell's documents, records, answer keys and recorded runs |
