# Go-live checklist

## Before it runs for real

- [ ] It passed the pass mark on your own email, including the part held back (`pass-mark.md`).
- [ ] It runs on a server you control, on a schedule, with a log line for every run.
- [ ] Mailbox access is read-only and limited to the one mailbox. Checked, not assumed.
- [ ] The AI key and the mailbox credentials are in the server's secret store, nowhere else.
- [ ] The import file maps to your business system's import, tested on a copy.
- [ ] Someone gets an alert if no run appears for an hour, or the needs-a-person pile suddenly doubles.
- [ ] Today's numbers are written down: how long a question takes to go out, requests lost because the quote came too late, quotes won.

## The first two weeks: alongside your people

- [ ] The team works the inbox exactly as before.
- [ ] Each morning someone compares their list with the system's, and logs every difference.
- [ ] Each difference becomes a case in the answer key.
- [ ] Switch over only when the comparisons have stayed clean for [five working days].

## After the switch

- [ ] Daily: five ready requests spot-checked by hand; the running count of changes kept.
- [ ] Every correction an estimator makes before pricing is logged.
- [ ] Monthly: corrections and stops read together. New kinds of email? Buyers leaving out the same thing?
- [ ] Whenever the AI model or the prompt changes: score against the answer key again before it goes back into service.
- [ ] After three to six months: measure the same numbers as before go-live, and decide to keep it, extend it, or stop.
