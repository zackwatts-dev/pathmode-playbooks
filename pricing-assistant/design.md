# Design: a price on every equipment quote, for Hartwell Supply

## The problem

We're an HVAC/R distributor with twelve branches across Ohio, Indiana, Kentucky, Michigan and western Pennsylvania, about 150 people and $145 million a year. Contractors email, phone or EDI us for equipment prices: a condenser and coil for a replacement, three rooftop units for a school. Our 36 account managers quote about 55,000 times a year, and we win about four quotes in ten.

Every customer has an agreed discount off list. On a quote, the account manager can give a little more, and each one does it their own way. Some give a point or two on nearly everything. Some almost never do. Nobody knows whether it works. We see the quotes we won. We don't see whether the extra point won them, or whether we'd have won anyway.

The answer is in our own quote history: who won at what price, by customer, and who didn't. Some customers buy from us whatever we charge, and the extra point just costs margin. Others shop every job, and a point would have won it. Reading that out of 500,000 quotes by hand isn't possible, so every account manager guesses.

## What it does

**For each new quote request:**
1. **Reads the request** (AI). An AI model (Claude, through Anthropic's API) reads the email or the note an inside rep typed from a call. It lists each item asked for, with:
   - the words that ask for it, quoted exactly;
   - the quantity;
   - the item: a part number when one is given, or for equipment the maker, type, tonnage, efficiency (SEER2) and refrigerant as written;
   - any competitor price, deadline or job name mentioned, quoted.
2. **Checks the reading** (code). Each item is accepted only when:
   - its quote is found word for word in the request;
   - its part number exists, or exactly one catalog product matches every equipment detail written;
   - its quantity is in the quote.

   An item with no match, or more than one, becomes a question for the customer ("410A or 454B?"), drafted by code. Text addressed to an AI is reported and does nothing.
3. **Works out the agreed price** (code): list price, the customer's agreed discount, and any markdown in effect that day, line by line.
4. **Suggests the extra discount** (code and statistics). A win model, trained each night on the last five years of our own quotes, gives the chance of winning at each extra discount from 0% to 5%, from:
   - the customer's trade, their size and their past wins;
   - the size of the quote and how much of it is marked down.

   It suggests the discount with the most expected margin (the chance of winning times the margin). It never goes below cost plus 5%, and anything above 3% needs the sales manager.
5. **Drafts the quote** (code: every price and total) **and a note for the account manager** (AI): one or two sentences in plain words on why this price ("this contractor buys from us at our agreed price about half the time; another point rarely changes that"). The note can only use facts code gives it, and every number in it must be one of them.

**When the customer replies:**
6. **Reads the reply** (AI): accepted, too high, a competitor's price (the amount and the words), not now, the job is off, or something else.
7. **Decides what's allowed** (code). If a competitor's price is named, code works out the extra discount that matches it. If that's within the account manager's authority and still earns more expected margin than holding, the draft matches. Otherwise it holds, or offers the sales manager the choice. The AI drafts the reply with code's numbers.

The account manager decides and sends. The tool changes nothing in the ERP or CRM and sends nothing.

## Inputs

Exports from the ERP and CRM, as CSV:
- **customers:** id, name, branch, trade (residential, mixed, commercial), agreed discount, account manager;
- **products:** part number, description, maker, type, tonnage, SEER2, refrigerant, list price, cost, discontinued date;
- **markdowns:** part number, month, markdown in effect;
- **sales by customer and year,** for size;
- **quotes and quote lines:** date, customer, account manager, status (won, lost, expired), the loss reason when one was entered, list and quoted price by line;
- **requests:** each new request's text, customer and date; **replies:** each reply's text and the quote it answers.

**The answer key** (sample only):
- for each request, every item truly asked for (part number and quantity), and which requests need a question;
- for each reply, its kind and any competitor amount;
- for every quote in the year, the competitor's price, the customer's true sensitivity to price, and whether the contractor's own job went ahead. That's what the simulation knows and a real company never would.

## What "correct" means

- **Reading:** an item is right when its part number and quantity match the key. We measure items found, wrong items (a product that wasn't asked for), and questions asked that weren't needed.
- **Replies:** the kind and the competitor amount match the key.
- **Money:** for every quote in the year, the expected margin at the suggested discount against the expected margin at the discount the account manager actually gave, both worked out with the simulation's true chances of winning. The difference, in dollars and as points of margin on won quotes, is the value. The page has to say this uses the simulation's own win curve. At a real company it would be proven with a split trial: half the quotes priced the old way, half the new.
- **Mistakes aren't equal.** The worst is a wrong item: the customer gets a price for the wrong unit and either buys it or stops trusting the quote. Next is a match the margin doesn't support. A question that wasn't needed costs a day.
- Every rule has a test that runs without calling the AI.

## Security and privacy

- **Read-only:** it reads exports and writes drafts. It changes nothing in the ERP or CRM and can't send anything.
- **The AI sees one request or reply at a time,** with the customer's name, and nothing from our costs, margins, other customers or the win model. It has no tools.
- **Requests and replies are data, not instructions.** Text that tells the AI to do something ("approve 15%") is reported to the sales manager, and can never change a price or an authority.
- **Everything shown is escaped.** Credentials come from the environment.
- **Software:** Python, with pinned numpy and scikit-learn.

## How it runs

- **Every 10 minutes** during the working day, on a server we control, for new requests and replies. A draft is ready within a quarter of an hour.
- **The win model retrains each night** on the quotes closed by then.
- **At most 400 AI reads a day;** anything over that goes to the account manager as usual.
- **Nothing is silently dropped:** a request with no customer match, or one that can't be read, is named at the top of the account manager's list.
- **Every run adds a line to a log:** when, which model, requests read, items, questions, discounts suggested.
- **Account managers mark each suggestion used or not,** and why.
- **After any change,** including a new model version, re-run the answer key before going live.
