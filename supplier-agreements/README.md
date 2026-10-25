# Supplier agreements

Holds suppliers to what their agreements say they owe you. An AI reader reads every agreement, amendment, program sheet, terms page and email for each supplier, and returns each term with the exact words it came from. An AI checker reads each term again from only the document it cites, without the reader's answer, and code compares the two readings. Code checks every term against its words and works out what each supplier owes from your own purchase records. It compares that with the supplier's statement and with what you've claimed. A person reviews every claim and sends it; nothing here contacts a supplier or changes a record.

The full playbook, worked through at Hartwell Supply Co. (a simulated HVAC/R distributor) with the design, the plan an AI wrote from it, and the answers to its questions: **https://pathmode.com/playbooks/supplier-agreements/**

## What it does

For the program year in `records/program.json`, supplier by supplier, largest purchases first:

1. **Reads the documents** (code). PDFs are read with poppler's `pdftotext`, page by page, with words hyphenated across a line break joined again. Emails (`.eml`) are read with Python's email parser, HTML-only ones as their words. A person reads, instead:
   - a document it can't read, or one with no text (a scan);
   - a supplier with nothing on file;
   - two suppliers whose names make the same folder.
2. **Reads the terms** (AI). One supplier's documents go to the model at a time, as data. It returns each term in a fixed form:
   - volume tiers, growth, a product-line incentive, co-op, freight prepaid, stock rotation, or eligible locations;
   - the numbers, what purchases it covers, and the dates;
   - **the exact words it came from**;
   - whether it's informal or unclear.

   It also reads the supplier's statement, line by line. At most 30 documents go to the model in one run. A supplier over the limit is listed for the next run.
3. **Checks each term** (code, then an AI checker).

   **What code can check exactly.** A term goes on only if:
   - each passage of its words is in the document it names, word for word and in order (up to 30 other words allowed between two of them), ignoring case, punctuation, hyphens and how the PDF laid it out (a table cell interleaved with its neighbours is still found; passages joined by "..." may come from anywhere in the document);
   - every number in it is in those words, and every tier is in the document as its threshold followed closely by its rate;
   - co-op says what share is reimbursed, added locations say when they start counting, and a tier table says whether its rate applies from the first dollar;
   - its tiers rise, and its rates are between 0 and 10%.

   **The AI checker.** Each kind of term in each document goes to the model again, asked a different question: here is one document; what does it say about this kind of term? It gets the term's kind and that one document, never the reader's answer, and returns the term's fields itself, whether it applies to the program year (or is an informal promise, an expired program or next year's offer), and any second reading it sees, with the words that support it. Code compares the two readings on every field the money depends on (tiers, from the first dollar or by band, rates, shares, minimums, allowances, fees, ages, dates, the products and locations covered). A term is used only if they agree. A disagreement, a second reading backed by the document's words, or a term the checker says doesn't apply goes to a person, with both readings and the checker's reason. An unusable answer accepts nothing it was checking.

   The statement is read the same way. Each line must be in the statement (its amount, with every word of the line near it), the lines must add up to what you were actually credited (`rebate-receipts.csv`), and the checker says which term each line pays, from the line's words alone. A document the reading took nothing from goes to a person, and so does a statement amount for a term that wasn't read. Text addressed to an AI or an automated system is reported and does nothing.

   An informal promise (a rep's email that the program doesn't provide for) or an unclear term goes to a person with its words, never into a claim. So does anything that fails a check.
4. **Settles the terms** (code). A later document's term of the same kind replaces an earlier one. An amendment to one tier must name a tier the table has, change it, and leave the tiers rising; it changes only that tier. An amendment that doesn't check out sends that supplier's tier rebate, and its growth rebate, to a person. Added locations count from the date they were added.
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
   - a co-op balance, or a return allowance, whose window has closed by the run date.
7. **Drafts the letters**, one per supplier with money due. Code writes every claim: the amount, how it was worked out, the words it rests on, and whether its window is open. The AI writes only a warm opening and closing, from the supplier's name and the kinds of thing being asked for; it never sees an amount. Its opening and closing may hold no numbers, no threats (withholding payment, moving business, legal action) and no concessions (late, a courtesy, a waiver), or code's plain ones are used. At most 15 a run go to the AI.
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

# Replay a recorded run: what a real model (Claude Sonnet 5.5) read and checked on the sample, free
python3 supplier-agreements/supplier_agreements.py --sample --replay supplier-agreements/sample-data/recorded-run.json

# The held-back year replayed (2020 is the one to trust; see Results)
python3 supplier-agreements/supplier_agreements.py --data supplier-agreements/holdout-2020 \
  --answer-key supplier-agreements/holdout-2020/answer-key/entitlements-key.csv \
  --replay supplier-agreements/holdout-2020/recorded-run.json

# A real model: an API account whose terms say your data isn't used for training
ANTHROPIC_API_KEY=... python3 supplier-agreements/supplier_agreements.py --sample
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

`holdout-2024/` to `holdout-2020/` are earlier program years, with the gaps on other suppliers each time. 2022, 2021 and 2020 are written in other suppliers' words, a new set each year, by an AI that never saw this code (`pathmode-corpus`, `simulations/hartwell/scripts/agreements_text_heldout*.py`). Each `recorded-run.json` says how it was made: the real calls, the answers reused from an earlier recording of exactly the same inputs, and any failed calls.

## Results

The pass mark (`release-thresholds.json`) was set before any held-back year was run, and hasn't changed: no wrong claims, at least 95% of the answer key's money found, at most three items for a person.

| Year | What it is | Wrong claims | Money found | For a person |
|---|---|---|---|---|
| 2020 | **Held back**: generated after the code froze at 6f04443, in a fourth set of suppliers' words, scored once | **0** | **99.9%** ($585,333 of $585,868) | **3** |
| 2025 | The sample | 0 | 100% ($699,214) | 2 |
| 2024, 2023 | Earlier held-back years, development data since the checker was built on them | 0 | 100% | 2 each |
| 2022 | Held back in new words; failed at e9af023 (below), development data since | 0 | 99.7% | 3 |
| 2021 | Held back in new words; failed at 440fa9a (below), development data since | 0 | 100% | 2 |

The rows after the first are replays of the final code on recordings made while it was developed, so they show it still works on what it was built on; only the first is a test it hadn't seen. Each year's items for a person are the right ones: the note addressed to automated systems (reported, and it changed nothing), a rep's emailed promise the program doesn't back, and in 2022 and 2020 a stock-rotation term where the checker caught the reader carrying a terms page's general 20% restocking fee into a rotation term that waives it.

**How the AI checker was built.** It was added to a version that already scored 100% on 2025, 2024 and 2023 by checking the reading with word lists ("first dollar", the words a statement line must use, dates written a few ways). Those lists judged prose, and new wording would break them, so the checker replaced them, developed on those three years (already scored, so development data). Its prompt was changed four times on them, each time recorded in `dev-checker-run-*.json`: a growth term called unclear because the sheet didn't repeat a definition; a one-tier table called unclear because the sheet said "hit a tier" (a second reading now needs the document's words behind it); a territory manager's notice under the program's own section called informal; and statement lines whose kinds were defined too narrowly.

**The held-back years that failed.** Three held-back years were written in new suppliers' words, each after a freeze, each scored once:
- **2022, at e9af023: failed** (57% of the money, 17 for a person). No wrong claims; the AI calls read every term that reached them right. Code's checks that a passage was in the document were tied to the PDF's layout: a statement line wrapped onto two lines, and tier tables written as a sentence put a threshold and its rate on different lines. Those checks were made layout-independent (commit after `score-at-e9af023.md`).
- **2021, at 440fa9a: failed** (59%, 9 for a person). No wrong claims. A change table's cells interleaved in the PDF's text, and a list quoted with "...", so code couldn't find the words in order. Passages are now matched word by word in order, with a few words allowed between, whatever the layout (`score-at-440fa9a.md`).
- **2020, at 6f04443: passed** (`score-at-6f04443.md`).

Each failure is kept in the repository with its recording at the frozen code (`recorded-run-at-*.json`), and each year that failed became development data. That was the third attempt; the rule was to stop after three.

## Before you run this on your own data

- **Check the reading on a supplier you know well first.** Compare `terms.csv` with the agreement yourself. Code proves the words are there, and the checker reads them a second time; neither proves both readings can't be wrong the same way.
- **Your invoices are the base.** If your purchasing system doesn't keep the supplier's invoice number, add a check for duplicates that suits it.
- **Freight credits.** It claims freight billed and paid on prepaid orders. If a supplier credits freight back separately, add those credits to the records first, or it will claim them twice.
- **Locations, product groups and categories must match your agreements' words.** Map them once, and have someone who negotiates the agreements confirm it.
- **Claim windows matter.** Set `as_of` in `records/program.json` to the day you run it. A co-op claim past its window goes to a person.
- **An amount is a claim, not a fact, until the supplier agrees.** Send the evidence with every claim, and keep the conversation friendly; you'll be buying from them next year.

## Running it for real

- Once after the statements arrive, and again when a new agreement or amendment comes in.
- On a server you control, with the key in its secret store.
- The output goes to a folder only purchasing, the controller and the CFO can open.
- After any change, including a new model version, run the sample and the held-back years again, and check `release-thresholds.json`.

## Files

| File | What it is |
|---|---|
| `supplier_agreements.py` | Reads, checks, works out, compares, drafts and scores |
| `agreements_dashboard.py` | The one-page dashboard |
| `design.md`, `plan.md` | The design, and the plan an AI wrote from it (unedited, regenerated when the checker was added) |
| `release-thresholds.json` | What counts as good enough: set before any held-back year was run |
| `tests/` | Every rule above, without calling the AI |
| `sample-data/`, `holdout-2024/` to `holdout-2020/` | Hartwell's documents, records, answer keys, recorded runs and, for the held-back years, each score at its frozen code |
