# PathMode playbooks

Working code for the free [PathMode playbooks](https://pathmode.com/playbooks/): worked examples of AI on problems most businesses have. Each playbook works out whether the problem is worth solving, then solves it end to end at Summit Mechanical, a simulated commercial HVAC contractor: the design, the plan an AI wrote from it, the code a coding agent built, an answer key to score it, and a dashboard. This repository is that code, with Summit's sample data.

| Playbook | What the code does | Risk |
|---|---|---|
| [Customer RFQ intake](rfq-intake/) | Sorts a quotes mailbox: each request's part numbers, revisions, quantities and dates read with the words they came from and checked, matched to your customers, parts and open requests, and anything doubtful sent to a person; then the ready queue in due-date order, with the requests that would miss their due date flagged at risk. At Wendlow Fabrication & Machine, a simulated job shop. Includes a Microsoft 365 mailbox reader. | Level 3 |
| [Anomaly alerts](anomaly-alerts/) | Rules, baselines and a machine-learning model find money leaking between systems and the habits behind it; an AI explains the top flags within an alert budget; code checks every explanation. | Level 2 |
| [Pricing assistant](pricing-assistant/) | Prices repair jobs from your price book and written sales guidance, citing which clause applies; a second mode negotiates replacement quotes, with code holding the floor the AI never sees. | Level 3 |
| [Customer segments](customer-segments/) | Machine learning groups customers by how they behave and tests each prediction against a one-line rule; an AI names the segments and explains the results, with every number checked. | Level 2 |
| [Account summary](account-summary/) | A one-page briefing on a customer or a branch from several systems: scope checked in code before anything is gathered, every number calculated from written definitions, every number and quote in the AI's words checked. | Level 2 |
| [Inherited records](inherited-records/) | Turns an acquired company's job tickets into records you can merge: an AI copies out each ticket, and code checks every value, groups and matches the locations, merges the equipment (settling mistyped serials, retiring replaced units) and finds the agreements and open quotes. | Level 2 |
| [Request routing](request-routing/) | Routes internal requests by a policy written in plain words: the AI uses judgment, and code holds the lines (safety always first, approval limits, nobody approves their own request, pay stays private). | Level 3 |
| [Estimate check](estimate-check/) | Before a bid goes out, an AI reads the whole specification and its addenda for every requirement that costs money, quoting its words and whose work it is; code checks every quote, checks the estimate prices each one, prices what's missing from past jobs, and compares each estimator's labor with their history. At Halden Mechanical, a simulated mechanical subcontractor. | Level 2 |

Risk levels: 1 chat only; 2 works with files you give it; 3 reads your email or systems, read-only; 4 takes actions. None of these goes past drafting. A person decides.

## How they're built

The same few rules run through all of them.

- **AI reads and explains; code decides.** The model reads messy input or explains a finding, quoting its evidence. Code checks that the evidence is really there, that the numbers come from the records, and that the answer fits. Anything that fails goes to a person, never silently through.
- **The right tool for each job.** Rules for what you know, statistics and classic machine learning for detecting and predicting, a language model for reading and writing.
- **Inputs are data, not instructions.** Emails, notes and messages are marked as data, and the checks that matter run in code, where cleverly worded input can't argue with them.
- **Every run is scored.** Each playbook has an answer key from the simulation, and a recorded model run you can replay for free.
- **Nothing is sent.** Every script reads files (or, for a mailbox, a read-only connection) and writes its results to `out/`.

## Try one

You need Python 3.11 or later. Most playbooks use only the standard library; those that use machine learning have a `requirements.txt`, pinned by version and hash (`pip install --require-hashes -r <folder>/requirements.txt`).

```sh
git clone https://github.com/zackwatts-dev/pathmode-playbooks
cd pathmode-playbooks
python3 rfq-intake/rfq_intake.py --sample --replay rfq-intake/sample-data/recorded-run.json
```

`--replay` repeats a recorded run with a real model's answers, and `--dry-run` uses an offline stand-in, so you can see the whole pipeline for free. To use a real model, set one of:

```sh
export ANTHROPIC_API_KEY=...                  # default provider; model claude-sonnet-5-5
export PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=...
```

and run without `--dry-run`. `PLAYBOOK_MODEL` overrides the model for either provider. Use an API account whose terms say your data isn't used for training.

## Tests

```sh
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest && .venv/bin/ruff check .
```

The tests run offline, with scripted model answers, including deliberately wrong ones, to check that each guard catches them.

## Layout

| Path | What |
|---|---|
| `common/` | The model client (Anthropic or OpenAI, standard library only), the offline stand-ins, the evidence and number checks, and the dashboards' shared look. |
| `plan-prompt.md` | The planning prompt every playbook's `plan.md` was written from. |
| `<playbook>/` | The script, `design.md`, the AI-written `plan.md`, sample data with an answer key and a recorded run, tests, `run.sh` and a README. |
| `tools/build_downloads.py` | Builds each playbook's downloads for pathmode.com. |
| `tools/record.py` | Records a real model's answers on a playbook's sample, for `--replay` (costs API calls). |

The sample data is fictional: Summit Mechanical, a made-up commercial HVAC contractor in Arizona, from a simulation of the whole business that the PathMode course uses throughout. The RFQ intake's is Wendlow Fabrication & Machine, a made-up job shop in Dayton; the anomaly alerts' is Ironbark Tavern & Grill, a made-up restaurant group in Kansas City; the estimate check's is Halden Mechanical, a made-up mechanical subcontractor in Columbus. Each comes from its own simulation.

## License

Code: [MIT](LICENSE). Text, instructions and sample data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with credit to PathMode. Use them, change them, build on them.

By Zack Watts, [PathMode](https://pathmode.com).
