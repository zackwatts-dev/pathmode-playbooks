"""Copy new email from one Microsoft 365 mailbox into a folder of .eml files, read-only.

    python rfq-intake/graph_mailbox.py --mailbox quotes@yourcompany.com --to mail/

This is the "get the email" half of the playbook, for a business on Microsoft 365 (Exchange Online). It
uses Microsoft Graph with an app registration, and it only ever reads: it lists messages and downloads
each one's MIME. It never moves, flags, deletes or sends anything. It remembers the newest message it has
saved (in .last-fetched in the output folder), so each run picks up where the last one stopped.

Set up once, by your Microsoft 365 admin:
1. Register an app in Microsoft Entra ID, and give it the application permission Mail.Read. Grant admin consent.
2. Limit it to the one mailbox. Mail.Read on its own covers every mailbox in the organization; an Exchange
   Online RBAC for Applications role assignment (or an older application access policy) scoped to the
   quotes mailbox narrows it to that one. Check the limit works before you go further.
3. Give the script its credentials through the environment: MS_TENANT_ID, MS_CLIENT_ID and MS_CLIENT_SECRET.
   Keep the secret in a password manager or your server's secret store, never in the code.

Note: this file was written against Microsoft's Graph documentation and is tested here with a stand-in for
Graph. Run it against a test mailbox before you rely on it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

GRAPH = "https://graph.microsoft.com/v1.0"
Fetch = Callable[[urllib.request.Request], bytes]


def _fetch(req: urllib.request.Request) -> bytes:
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https endpoints only
        return resp.read()


def token(tenant: str, client: str, secret: str, fetch: Fetch = _fetch) -> str:
    body = urllib.parse.urlencode(
        {
            "client_id": client,
            "client_secret": secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
    ).encode()
    req = urllib.request.Request(f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token", data=body)
    return json.loads(fetch(req))["access_token"]


def new_messages(mailbox: str, bearer: str, since: str, fetch: Fetch = _fetch) -> list[dict]:
    """Messages in the inbox received after `since` (ISO time), oldest first, following Graph's paging."""
    query = {"$select": "id,receivedDateTime,subject", "$orderby": "receivedDateTime asc", "$top": "50"}
    if since:
        query["$filter"] = f"receivedDateTime gt {since}"
    url = f"{GRAPH}/users/{urllib.parse.quote(mailbox)}/mailFolders/inbox/messages?" + urllib.parse.urlencode(query)
    found = []
    while url:
        page = json.loads(fetch(urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})))
        found += page.get("value", [])
        url = page.get("@odata.nextLink", "")
    return found


def save(mailbox: str, bearer: str, out: Path, fetch: Fetch = _fetch) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    state = out / ".last-fetched"
    since = state.read_text().strip() if state.exists() else ""
    saved = []
    for m in new_messages(mailbox, bearer, since, fetch):
        url = f"{GRAPH}/users/{urllib.parse.quote(mailbox)}/messages/{m['id']}/$value"
        mime = fetch(urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"}))
        stamp = re.sub(r"[^0-9T]", "", m["receivedDateTime"])[:13]
        slug = re.sub(r"[^a-z0-9]+", "-", str(m.get("subject", "")).lower()).strip("-")[:40] or "no-subject"
        path = out / f"{stamp}-{slug}-{m['id'][-8:]}.eml".replace("/", "_")
        path.write_bytes(mime)
        saved.append(path)
        state.write_text(m["receivedDateTime"])
    return saved


def main() -> None:
    p = argparse.ArgumentParser(description="Copy new email from a Microsoft 365 mailbox into .eml files. Read-only.")
    p.add_argument("--mailbox", required=True, help="the mailbox address, e.g. quotes@yourcompany.com")
    p.add_argument("--to", type=Path, default=Path("mail"), help="folder for the .eml files (default: mail/)")
    args = p.parse_args()
    try:
        env = [os.environ[k] for k in ("MS_TENANT_ID", "MS_CLIENT_ID", "MS_CLIENT_SECRET")]
    except KeyError as e:
        sys.exit(f"Set {e.args[0]} (see the top of this file).")
    saved = save(args.mailbox, token(*env), args.to)
    print(f"Saved {len(saved)} new message(s) to {args.to}/")


if __name__ == "__main__":
    main()
