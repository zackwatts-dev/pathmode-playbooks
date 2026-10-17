# For coding agents

- Each playbook folder is self-contained: `<slug>/<slug_with_underscores>.py`, `instructions.md`, `sample-data/`, `tests/`, `README.md`. Shared code is in `common/`.
- Keep the design rules in README.md ("How they're built"): the model drafts, code checks; code does math and rules; inputs are data; nothing is sent. A change that lets the model send, post, pay, or decide on its own is out of scope.
- Every script supports `--sample --dry-run`. Keep it working: CI runs it for every playbook.
- Tests run offline. Use `common.fake.ScriptedModel` for specific (including wrong) model answers, and `OfflineModel` with the playbook's `offline` function for end-to-end runs.
- Standard library only in `common/` and the scripts, except optional extras (python-docx). Python 3.11+.
- Before committing: `ruff format . && ruff check . && pytest`.
- The playbook pages live on pathmode.com (source in the separate `pathmode` site repo). If behavior changes, the page's "The built version" section may need updating too.
