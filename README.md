# PathMode playbooks

Working code for the free [PathMode playbooks](https://pathmode.com/playbooks/): worked examples of AI on problems most businesses have. Each playbook works out whether the problem is worth solving, then solves it end to end at Summit Mechanical, a simulated commercial HVAC contractor: the design, the plan an AI wrote from it, the code a coding agent built, an answer key to score it, and a dashboard. This repository is that code, with Summit's sample data.

| Playbook | What the code does | Risk |
|---|---|---|
| [Customer RFQ intake](rfq-intake/) | Turns a quotes mailbox into a clean list: each request matched to your customers, sites and equipment, checked, and anything doubtful sent to a person. Includes a Microsoft 365 mailbox reader. | Level 3 |
| [Anomaly alerts](anomaly-alerts/) | Rules, baselines and a machine-learning model find money leaking between systems and the habits behind it; an AI explains the top flags within an alert budget; code checks every explanation. | Level 2 |

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

The sample data is fictional: Summit Mechanical, a made-up commercial HVAC contractor in Arizona, from a simulation of the whole business that the PathMode course uses throughout.

## License

Code: [MIT](LICENSE). Text, instructions and sample data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with credit to PathMode. Use them, change them, build on them.

By Zack Watts, [PathMode](https://pathmode.com).
