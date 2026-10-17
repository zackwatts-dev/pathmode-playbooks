You're helping me plan software that an AI coding agent will build. Turn the design below into a build plan the agent can follow. Use these practices:

- Keep it targeted: the business rules, the interfaces between parts, acceptance criteria written as tests, and the commands to run them. Leave out anything the agent can read from the code.
- Small parts with clear boundaries: reading mail, calling the AI, matching to records, the checks, and the outputs, each separate and testable on its own.
- Tests first, from the answer key and from every rule in the design. Say which tests a person must review, and that the agent may not change tests or the answer key without approval.
- Deterministic checks before any AI review: tests, linting, and a security review of the code.
- Security checked, not assumed: list each security rule from the design, where it will be enforced, and the test that proves it.
- Build on a branch, in small commits a person can review.
- Say what's out of scope.
- End with the open questions I need to answer before building.

Keep it short enough to review in fifteen minutes. Here's the design:
