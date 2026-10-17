# Inherited records

Turns an acquired company's job tickets into records you can merge: which of its locations you already know, the equipment at each, the service agreements you now have to honor, and the repairs it quoted that customers may still be expecting. The AI reads; code checks, matches and decides; anything doubtful goes to a person.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/inherited-records/**

## What it does

- **The AI reads each ticket** and copies out what it says, exactly as written: the location, each unit's details, work done (and whether it was per a quote), work recommended with the quoted amount, and any service agreement. It doesn't correct, guess or merge.
- **Code checks every value is in the ticket**, from the serial to the install year, the refrigerant, the unit's tag and the visits a year. One that isn't is dropped, and a person is told.
- **Code does the rest:**
  - groups the tickets into locations, by address (allowing for typos; the same street in another town is another place) or, without one, by the one location the name fits;
  - matches each location to your sites and customers, by street and town;
  - merges each unit's mentions, catching mistyped serials on the same tag (your own record settles them where it can; RTU-1 and RTU-2 stay two units however alike their serials) and replaced units;
  - works out the latest agreement at each location, and the quotes never done.
- **A review list** of everything code couldn't decide, numbered, and **import files** (`out/merge/`) in which every row says `ready` or which review items it waits on. Every CSV is safe to open in a spreadsheet: text that starts like a formula is made inert.

## What it doesn't do

Import anything, change your records, or guess. A person clears the review list and does the import.

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
