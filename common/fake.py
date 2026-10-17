"""Offline stand-ins for the model, for tests and for --dry-run.

A playbook gives the stand-in a plain Python function that produces a reasonable answer without any AI
(keyword rules, usually). That keeps the tests free and repeatable, and lets you run the whole pipeline
on the sample data before you set up a key. The answers are deliberately simple: the real model does better.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class OfflineModel:
    respond: Callable[[str, str], str]
    name: str = "offline (dry run, no AI)"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        self.calls.append((system, user))
        return self.respond(system, user)


@dataclass
class ScriptedModel:
    """Returns the given answers in order. For tests that need a specific (often wrong) model answer."""

    answers: list[str]
    name: str = "scripted"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        self.calls.append((system, user))
        if not self.answers:
            raise AssertionError("ScriptedModel ran out of answers")
        return self.answers.pop(0)
