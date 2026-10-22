# Design: holding suppliers to their agreements at Hartwell Supply Co.

## The problem

We buy about $116 million a year from about 45 suppliers. Our twelve largest suppliers account for about $87 million. Each has an agreement that pays us money back:
- volume rebates on tiers;
- growth and product-line incentives;
- co-op marketing funds;
- prepaid freight over a minimum order;
- the right to return slow stock.

Every supplier writes its program differently: a long agreement with exhibits, a one-page program sheet, a clause buried in the terms of sale, an amendment letter, a rep's email.

In March each supplier sends a statement of what it says it owes us, and we accept it, because nobody has the time to re-work twelve programs against a year of invoices. Nobody tracks the co-op deadlines or the return allowance either. Money we've earned goes unclaimed, and nobody knows how much.

## What it does

For the program year just ended:
1. **Read each supplier's documents** (AI). An AI model (OpenAI's API) reads every agreement, amendment, program sheet and email for a supplier, one supplier at a time. It returns each term in a fixed structure:
   - kind (volume tiers, growth, product line, co-op, freight prepaid, stock rotation, eligible locations);
   - the numbers (tiers, rates, thresholds, allowances, deadlines);
   - what purchases it covers, and the dates it applies;
   - **the exact words it came from**, with the document and page.

   It also says when a later document changes an earlier one, and flags anything promised informally or unclear.
2. **Check the reading** (code).
   - Every quoted passage must appear, word for word, in the document it names.
   - Every number in a term must appear in its quoted passage.
   - Tiers must rise, and rates must be between 0 and 10%.
   - A term that fails any check, or that the AI marked as informal or unclear, goes to a person with the passage. It isn't used.
3. **Work out what each supplier owes** (code, no AI), from our own records:
   - eligible purchases from the supplier's invoices (no duplicates), net of returns, by branch and product;
   - the rebate under the terms as amended;
   - co-op accrued against claims filed and eligible marketing spend;
   - freight billed and paid on orders over the prepaid minimum;
   - return allowance against returns made and the stock that hasn't sold.
4. **Compare** with each supplier's statement and with what we've claimed (code). Every difference becomes a line with the amount, the term, the passage, and the records behind the number.
5. **Draft the claims** (AI). For each supplier with money due, the AI writes a short, polite claim letter from the evidence code computed. Code checks every number in the letter appears in that evidence. A letter that fails is replaced by a plain one code writes.
6. **A one-page HTML dashboard:**
   - money due by supplier and by kind;
   - the claims, largest first, each with its letter and evidence;
   - deadlines (co-op claim dates, return windows);
   - the terms waiting for a person.

It's decision support. A person in purchasing reviews every claim and sends it. The tool never contacts a supplier or changes a record.

## Inputs

**From our ERP, accounting and warehouse systems:**
- `suppliers.csv`, `purchase-orders.csv` (with branch and value);
- `supplier-bills.csv` (with freight and what we paid), `supplier-bill-lines.csv`, `products.csv`;
- `supplier-credits.csv` (returns), `rebate-receipts.csv`;
- `co-op-claims.csv`, `marketing-spend.csv`;
- `stock-on-hand-2025-12-31.csv` (with each item's last sale and last receipt).

**The documents:** `agreements/<supplier>/` holds the agreements, amendments, program sheets and emails (PDF and .eml), and each supplier's 2025 rebate statement.

**The answer key:**
- `terms-key.csv`: every term as written;
- `entitlements-key.csv`: per supplier and term, what was earned, what was paid or claimed, and the cause of each gap.

## What "correct" means

- The answer key defines it, and every run is scored against it. That covers the terms read and the money found.
- **Mistakes aren't equal:**
  - **A claim we shouldn't make** (a wrong tier, an informal promise treated as a contract term) is the worst. It costs credibility with a supplier we depend on.
  - **Money missed** is the next worst.
  - **A term sent to a person** counts as neither.
- No term is used unless its passage is found in the document.
- Every rule above has a test. Tests run without calling the AI, so they're free and repeatable.

## Security

- **Access:** read-only, to the exported files and documents. It can't change a record, a payment or a supplier's account, and it can't send anything.
- **Credentials:** from the environment or a secret store, never in the code.
- **The AI:**
  - while reading terms, it gets one supplier's documents and nothing else;
  - while writing a letter, it gets the computed evidence for one supplier and nothing else;
  - it has no tools and no access to files or email.
- **Documents are data, not instructions.** Text inside a document that tells the AI to do something is ignored. The passage checks catch any term it invents.
- **Everything shown is escaped** on the dashboard.
- **Software:** Python's standard library, plus `pdftotext` (poppler) to read the PDFs.

## How it runs

- **Once a year after the statements arrive,** and again whenever a new agreement or amendment comes in. It runs on a server we control.
- **At most 30 documents and 15 letters to the AI per run.**
- **Nothing is silently dropped.** A supplier with no documents, a document that can't be read, or a statement with no matching terms goes to a person.
- **Every run adds a line to a log:** when, which model, how many terms read, how many checked, and the money found by kind.
- **Who sees it:** purchasing, the controller and the CFO.
- **After any change,** including a new model version, re-run the answer key before going live.
