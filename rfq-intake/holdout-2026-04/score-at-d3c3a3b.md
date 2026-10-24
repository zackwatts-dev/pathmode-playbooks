# Against the answer key

162 of 166 emails handled as the answer key says.

| | This run | Everything to a person |
|---|---:|---:|
| Right | 162 | 3 |
| Let through, but wrong | 0 | 0 |
| Sent to the wrong place | 0 | 0 |
| Stopped, but needn't have been | 4 | 163 |

- **Let through, but wrong: the costly kind, nothing stopped it:** 0
- **Sent to the wrong place:** 0
- **Stopped, but needn't have been: costs a person a minute:** 4
  - 0401-1608-quote-needed-bra-43998-rev-a.eml: expected ready to quote, got needs a person (the quote due date: the reader has none, the checker 2026-04-01; the checker says the reading missed: quote due date: the email says the buyer is deciding on Ap)
  - 0409-1005-rfq-attached.eml: expected needs info, got needs a person (LUT-29853's delivery date: the reader has 2027-05-07, the checker 2026-05-07; LUT-65435's delivery date: the reader has 2027-04-30, the checker 2026-04-30; the )
  - 0415-1626-request-for-quote-fis-57277.eml: expected needs info, got needs a person (FIS-57277's delivery date: the reader has 2026-05-28, the checker none; the quote due date: the reader has none, the checker 2026-05-28)
  - 0423-0841-re-quote-needed-sch-44608-rev-a.eml: expected not an rfq, got needs a person (SCH-44608's revision: the reader has none, the checker A; the checker says the reading missed: Revision A for SCH-44608 (given in the subject line))

Requests the key says are missing something: 27 got their question drafted, 2 went to a person instead (counted above as stopped needlessly: no question drafted), 0 were missed.
  - to a person: 0409-1005-rfq-attached.eml
  - to a person: 0415-1626-request-for-quote-fis-57277.eml

Each field read, on every new request the tool read lines for (whatever pile it went to):

| Field | Right | Wrong |
|---|---:|---:|
| customer | 135 | 1 |
| part numbers | 136 | 0 |
| revisions | 136 | 0 |
| quantities | 136 | 0 |
| requested dates | 135 | 1 |
| quote due | 134 | 2 |

Requests with their lines only in an attached RFQ form or parts list: 16 of 16 handled right. Re-quotes sent in by email: 66 of 66 handled right; 61 of them fast-track (the history brief is enough to price from).

Release thresholds (`release-thresholds.json`):

- pass: 0 emails let through wrong (at most 0)
- pass: 2% of the emails the key doesn't stop, stopped (at most 10%)
- pass: 0% of all emails, sent to the wrong place (at most 5%)
- pass: 0% of the requests with lines only in an attachment, not handled right (at most 10%)
- pass: 0% of the re-quotes sent in by email, not handled right (at most 5%)

The forecast flagged 4 requests at risk; of the 0 from this mailbox, 0 were really lost late. Of the 103 it planned to quote in time, 3 were really lost late (the answer key's outcomes, from the simulation: what happened with Wendlow's own order, not the tool's).

