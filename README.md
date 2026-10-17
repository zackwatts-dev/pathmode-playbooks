# PathMode playbooks

Working code for the free [PathMode playbooks](https://pathmode.com/playbooks/): step-by-step fixes for problems most businesses have. Each playbook on the site covers the problem, a cost calculator, the fix that needs no AI (where there is one), no-code setup on ChatGPT, Claude, Gemini and Copilot, and the risks. This repository is the built version: small, readable Python scripts with sample data and tests.

| Playbook | What the code does | Risk |
|---|---|---|
| [Inbox triage](inbox-triage/) | Sorts a shared inbox, routes each email and drafts replies. Never sends. | Rung 3 |
| [Late invoices](late-invoices/) | Separates customers automatic reminders can handle from those who need a person, and drafts the personal follow-ups. | Rung 2 |
| [Quotes from notes](quotes-from-notes/) | Turns call notes into a draft quote from your price list. Code does the math. | Rung 2 |
| [Meeting follow-ups](meeting-follow-ups/) | Turns a transcript into decisions, owned tasks and a follow-up email. | Rung 2 |
| [Support replies](support-replies/) | Drafts answers from your own documents, with sources, or says "not covered". | Rung 2 |
| [Weekly report](weekly-report/) | Calculates the week's numbers, has the model write the summary, checks every number in it. | Rung 2 |
| [SOPs from walkthroughs](sops-from-walkthroughs/) | Turns a recorded walkthrough into a written procedure. | Rung 2 |
| [Expense categories](expense-categories/) | Rules first, the model for the rest, a review list for your bookkeeper. | Rung 2 |
| [Applicant screening](applicant-screening/) | Checks each application against your must-haves with quoted evidence. No ranking. | Rung 2 |

"Rung" is the risk ladder from the [course](https://pathmode.com/resources/course/): 1 chat, 2 works with your files, 3 connected to your systems, 4 takes actions. None of these goes past drafting. A person decides and sends.

## How they're built

The same few rules run through all nine.

- **The model drafts; code checks.** Every script asks the model to quote its evidence or cite its source, then checks in code that the quote is really there, that the numbers are numbers it was given, and that its answer fits what was asked. Anything that fails is flagged for a person, not hidden.
- **Code does the math and the rules.** Prices, totals, metrics, thresholds and "always ask a person about this" rules are plain Python you can read and change. The model never does arithmetic that matters.
- **Inputs are data, not instructions.** What the model reads (an email, an application, a customer's question) is marked as data, and the checks that matter most run in code, where a cleverly worded input can't argue with them.
- **Nothing is sent.** Every script reads files (or, for the inbox, a read-only connection) and writes its results to `out/`.

## Try one

You need Python 3.11 or later. Nothing to install for the scripts themselves.

```sh
git clone https://github.com/zackwatts-dev/pathmode-playbooks
cd pathmode-playbooks
python3 inbox-triage/inbox_triage.py --sample --dry-run
```

`--dry-run` uses an offline stand-in (simple keyword rules) instead of a model, so you can see the whole pipeline for free. To use a real model, set one of:

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
| `common/` | The model client (Anthropic or OpenAI, standard library only), the offline stand-ins, and the evidence and number checks. |
| `<playbook>/` | The script, `instructions.md` for no-code assistants, sample data, tests and a README. |
| `tools/build_downloads.py` | Builds each playbook's downloads (instructions, cost worksheet, "for your AI" file) for pathmode.com. |

The sample data is fictional: Summit Mechanical, a made-up commercial HVAC contractor in the Phoenix area that the PathMode course uses throughout.

## License

Code: [MIT](LICENSE). Text, instructions and sample data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with credit to PathMode. Use them, change them, build on them.

By Zack Watts, [PathMode](https://pathmode.com).
