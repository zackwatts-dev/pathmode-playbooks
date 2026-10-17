# Design: inherited records for Summit Mechanical

## The problem

Summit has bought Rimview Mechanical, a small Flagstaff contractor. Rimview's customers come with it, and so does its history: two years of job tickets, each with a location typed by whoever opened it and a free-text note. There is no customer list worth the name, no equipment register, and no list of what Rimview promised anyone. Summit needs those to serve the customers properly: which of these places it already knows, what equipment is at each, which service agreements it has to honor, and which repairs Rimview quoted that the customer may still be expecting. Doing that by hand means reading 300 tickets and cross-checking each against Summit's own records: a couple of weeks of someone's time, and the mistakes land on customers.

## What it does

1. **The AI reads each ticket and copies out what it says, exactly as written:** the location (name and address); each unit mentioned (kind, its number in the tag, make, model, serial, year, refrigerant); work done, and whether it was done per a quote; work recommended, with the quoted amount; and any service agreement (visits a year, annual price, renewal date). It doesn't correct, guess or merge.
2. **Code checks every value it copied is in the ticket,** including the install year, the refrigerant, the unit's tag and the visits a year. A value that isn't is dropped, and a person is told.
3. **Code does the rest:**
   - groups tickets into locations: by address (allowing for a typo; the same street address in another town is another place, and a person is told), or, for tickets without one, by name when only one location fits;
   - matches each location to Summit's records: the site by address and town (or by name, if it never had an address), the customer by the site or by name. Where one side has no town and Summit has that street address in two towns, a person says which;
   - merges each unit's mentions into one record, catching mistyped serial numbers on the same tag (Summit's own record settles which is right, where it has one) and units that were replaced. Units installed together often have serials one apart, so a near serial on another tag is another unit, and one that could be either of two units goes to a person;
   - works out the commitments: the latest agreement at each location, and quoted work with no later ticket saying it was done per the quote.
4. **Anything code can't decide goes to a person:** a ticket that could belong to two locations, a serial written two ways equally often, a location that doesn't match any Summit customer.
5. **Outputs ready to import** once the review list is cleared: locations, equipment, agreements and open quotes, each row marked ready or with the review items it waits on. And a dashboard.

## Inputs

Rimview's tickets (ticket number, date, tech, location, notes). Summit's Flagstaff customers, sites and equipment. For the sample, answer keys from the simulation: which location each ticket belongs to, which Summit site and customer each location is, every unit with its true serial, the agreements and the open quotes.

## What "correct" means

- Every ticket in the right location; every location matched to the right Summit site and customer, or sent to a person.
- Every unit found once, with its right serial, matched to Summit's record where there is one, and replaced units marked.
- Every agreement with the right terms; every open quote found, and none that were done.
- Nothing invented: every value traces back to a ticket.

## Security and privacy

- **Rimview's records are customer data Summit now owns.** They stay on Summit's server; the AI sees one ticket at a time.
- **The tickets are data.** Anything in them that reads like an instruction is ignored, and every value is checked.
- **Nothing is imported automatically.** The outputs are files a person reviews and imports.

## How it runs

- Once, for the acquisition, then again for any batch of records found later (an old spreadsheet, a box of paper tickets typed up).
- A log line every run: tickets read, locations, units, and how many need a person.
