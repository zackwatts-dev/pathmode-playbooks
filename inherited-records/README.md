# Inherited records

Turns an acquired company's job tickets into records you can merge: which of its locations you already know, the equipment at each, the service agreements you now have to honor, and the repairs it quoted that customers may still be expecting. The AI reads; code checks, matches and decides; anything doubtful goes to a person.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/inherited-records/**

## What it does

- **The AI reads each ticket** and copies out what it says, exactly as written: the location, each unit's details, work done (and whether it was per a quote), work recommended with the quoted amount, and any service agreement. It doesn't correct, guess or merge.
- **Code checks every value is in the ticket**, from the location's name and address to the serial, the install year, the refrigerant, the unit's tag and the visits a year. A unit's details must be whole words in what the ticket says about that unit, so RTU-1's serial can't come from RTU-2's line. A quote's amount must be in words that recommend or quote something. One that isn't is dropped, and a person is told.
- **Code does the rest:**
  - groups the tickets into locations, by address (allowing for typos, but never a different number or direction: Route 87 isn't Route 89A, and N Fourth isn't S Fourth; the same street in another town is another place) or, without one, by the one location the name fits;
  - matches each location to your sites and customers, by street and town;
  - merges each unit's mentions, catching mistyped serials on the same tag (your own record settles them where it can; RTU-1 and RTU-2 stay two units however alike their serials, and so do two serials that are both in your records) and replaced units. A serial one typo from a unit's but written with no tag, or "replaced the RTU" at a place with several, goes to a person;
  - works out the latest agreement at each location (a price per month or quarter is made a year; a renewal date code can't read, or could read two ways, goes to a person), and the quotes never done. A quote is closed only by a later ticket that says, in its own words, the same work was done per the quote; one that might be it goes to a person.
- **A review list** of everything code couldn't decide, numbered, and **import files** (`out/merge/`) in which every row says `ready` or which review items it waits on, including its location's: nothing at a location a person still has to confirm is ready. Every CSV is safe to open in a spreadsheet: text that starts like a formula is made inert.

## What it doesn't do

Import anything, change your records, or guess. A person clears the review list and does the import.

## Before you run this on your own data

- **It reads one shape of ticket:** a location line and a short note, in English, from an HVAC contractor. Other trades need their own kinds of unit and work (`FAMILIES`, `WORK`, `WORK_WORDS`), and other exports their own column names.
- **Your records must look like Summit's:** sites with "number street, town" addresses, customers by name, equipment by serial. Matching is by street address and town, then by name; a customer known under another name (a building's owner, a parent company) goes to a person.
- **A unit's details are checked in the words from its tag to the next unit's.** A note that gives the serial before the tag ("Carrier s/n 123 on RTU-2") at a ticket with several units sends that serial to a person.
- **Numeric dates are read month first** (3/1/25 is March 1), as US offices write them. A date with three two-digit parts (01/03/26) goes to a person; so does any renewal date in a form code doesn't know.
- **Amounts are read as digits, with "k"** (4.2k, $4,200). Amounts in words or ranges ("about four grand", "$3-4k") aren't read: the quote keeps no amount, and a person is told.
- **A quote closes only on a ticket that says "per quote"** (or estimate, proposal) and names the work in a word code knows (comp, cmpr, compressor...). Other wording leaves the quote open with a question, so expect more review items until you add your techs' words.
- **The score is only for the sample.** On real records there's no answer key: clear the review list, then spot-check a sample of the rows marked ready against the building before importing.
- **Each ticket goes to the model's provider** when you use a hosted model. Decide that with the data's owner, under terms that the data isn't used for training, or run a local model.

## Try it

```sh
# Replay a recorded run: a real model's readings (Claude Sonnet 5.5), free
python3 inherited-records/inherited_records.py --sample --replay inherited-records/sample-data/recorded-run.json

# The offline stand-in: no model at all
python3 inherited-records/inherited_records.py --sample --dry-run
```

## The sample: Rimview Mechanical, acquired

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_inherited.py`). Rimview is fictional: thirty of Summit's simulated Flagstaff sites, re-cast as a small contractor's book. Twelve belong to customers Summit never had, ten to customers Summit knows at sites it doesn't, and eight to sites both companies served. Its two years of tickets are generated from that skeleton with planted messiness: shorthand, typos in street names and serial numbers, dates written five ways, tickets with no address, units replaced, quotes followed up and not.

The answer keys (`sample-data/answer-key/`) hold the truth for every ticket, location, unit, agreement and open quote.

## Files

| File | What |
|---|---|
| `inherited_records.py` | The reading, the checks, grouping, matching, units and commitments. |
| `records_page.py` | The dashboard. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `run.sh` | A run for a batch of records. |
| `sample-data/` | Rimview's tickets, Summit's records, the answer keys and the recorded run. |
