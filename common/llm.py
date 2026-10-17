"""One small client for a language model, so every playbook talks to it the same way.

Pick the provider with PLAYBOOK_PROVIDER ("anthropic" or "openai"; default anthropic) and set its key:
ANTHROPIC_API_KEY or OPENAI_API_KEY. PLAYBOOK_MODEL overrides the model.

Standard library only (urllib), so there is nothing to install. With --dry-run, playbooks use an offline
stand-in instead (see common/fake.py), so you can see the whole pipeline before you spend anything.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

ANTHROPIC_DEFAULT = "claude-sonnet-5-5"


class Model(Protocol):
    name: str

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str: ...


class ModelError(RuntimeError):
    pass


def _post(url: str, headers: dict[str, str], body: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        raise ModelError(f"{url} returned {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise ModelError(f"Couldn't reach {url}: {e.reason}") from e


@dataclass
class AnthropicModel:
    api_key: str
    name: str = ANTHROPIC_DEFAULT

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        data = _post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {
                "model": self.name,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        return "".join(block.get("text", "") for block in data.get("content", []))


@dataclass
class OpenAIModel:
    api_key: str
    name: str

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        data = _post(
            "https://api.openai.com/v1/chat/completions",
            {"authorization": f"Bearer {self.api_key}"},
            {
                "model": self.name,
                "max_completion_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
        )
        return data["choices"][0]["message"]["content"] or ""


def from_env(env: dict[str, str] | None = None) -> Model:
    """The model named by the environment, or a clear message saying what to set."""
    env = dict(os.environ) if env is None else env
    provider = env.get("PLAYBOOK_PROVIDER", "anthropic").lower()
    model = env.get("PLAYBOOK_MODEL")
    if provider == "anthropic":
        key = env.get("ANTHROPIC_API_KEY")
        if not key:
            raise ModelError("Set ANTHROPIC_API_KEY (or run with --dry-run to try it offline).")
        return AnthropicModel(key, model or ANTHROPIC_DEFAULT)
    if provider == "openai":
        key = env.get("OPENAI_API_KEY")
        if not key:
            raise ModelError("Set OPENAI_API_KEY (or run with --dry-run to try it offline).")
        if not model:
            raise ModelError("Set PLAYBOOK_MODEL to the OpenAI model you want to use.")
        return OpenAIModel(key, model)
    raise ModelError(f"PLAYBOOK_PROVIDER must be 'anthropic' or 'openai', not {provider!r}.")
