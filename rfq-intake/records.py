"""Wendlow's own records, exported nightly from the ERP, and the matching that has to be right.

The model reads the email; this code decides which customer, part and open request it means. Every match is
exact or it isn't a match: when two customers could fit, a person decides, never a guess.

    customers.csv        customer_id, name, tier (key, regular or occasional), domain
    contacts.csv         customer_id, name, email (buyers we've had RFQs from; most new buyers aren't here)
    customer-parts.csv   customer_id, part_number, revision, description, family, material, created_on
    open-rfqs.csv        rfq_id, customer_id, buyer, received_on, stated_due, part_numbers, quantities,
                         requested_dates (lists separated by ";")
    estimator-hours.csv  date, hours, and optionally seniority (junior or senior; blank means junior): the
                         estimators' quoting hours per working day. A person keeps it current.
    requote-hours.csv    optional: date, hours (estimator hours spent on the ERP's annual re-quotes each day). With
                         it, the forecast reserves the last four weeks' average; without it, forecast.json's figure.

A malformed row stops the load with the file and row number: a record that can't be read is never skipped quietly.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

TIERS = ("key", "regular", "occasional")
SENIORITY = ("junior", "senior")
# The families the quoting-time formula charges 1.5x for (the owner's answer to the plan's question 3).
WELD_FAMILIES = ("structural weldment", "machined weldment", "assembly")

COLUMNS = {
    "customers.csv": ("customer_id", "name", "tier", "domain"),
    "contacts.csv": ("customer_id", "name", "email"),
    "customer-parts.csv": ("customer_id", "part_number", "revision", "description", "family"),
    "open-rfqs.csv": ("rfq_id", "customer_id", "received_on", "stated_due", "part_numbers", "quantities"),
    "estimator-hours.csv": ("date", "hours"),
    "requote-hours.csv": ("date", "hours"),
}


def squash(text: str) -> str:
    """Letters and digits only, lower case: "ECK-70811" and "eck 70811" are the same part number."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def name_key(name: str) -> str:
    """A company name for an exact match: case, spacing and a final full stop don't count, everything else does.
    Wendlow's records have customers whose names differ only by a comma ("Amstutz Automation, Inc." and
    "Amstutz Automation Inc."), so a looser match would pick between them."""
    text = str(name).replace("’", "'").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip().rstrip(".").strip().lower()


def loose_key(name: str) -> str:
    """The name without its legal suffix or punctuation: only for spotting look-alike records, never to match."""
    return squash(re.sub(r"\b(inc|llc|co|corp|company|ltd)\b\.?", "", str(name).lower()))


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    tier: str
    domain: str

    @property
    def key_account(self) -> bool:
        return self.tier == "key"


@dataclass(frozen=True)
class Part:
    customer: str
    number: str
    revision: str
    family: str
    description: str = ""


@dataclass
class OpenRFQ:
    """A request still open from before this run, from the ERP: its parts and when it came in."""

    id: str
    customer: str
    buyer: str
    received: date
    stated_due: date | None
    parts: list[str]
    quantities: list[int]


@dataclass
class Records:
    customers: dict[str, Customer]
    by_domain: dict[str, list[Customer]]
    contacts: dict[str, list[tuple[str, str]]]  # email -> [(customer id, name)]
    parts: dict[tuple[str, str], list[Part]]  # (customer id, squashed part number) -> every revision on file
    part_owners: dict[str, set[str]]  # squashed part number -> the customers it's on file for
    open_rfqs: list[OpenRFQ]
    hours: dict[date, float]
    seniority: dict[date, str]  # the estimators' seniority each day: junior unless the hours file says senior
    families: dict[str, str]  # a part description -> its family, where every part with it is in one family
    requote_hours: dict[date, float] | None = None  # hours spent on re-quotes each day, when the ERP exports it
    look_alikes: dict[str, list[Customer]] = field(default_factory=dict)  # customer id -> near-identical records

    @classmethod
    def load(cls, folder: Path) -> Records:
        customers: dict[str, Customer] = {}
        for n, r in _rows(folder, "customers.csv"):
            if r["tier"] not in TIERS:
                raise ValueError(f"customers.csv row {n}: tier {r['tier']!r} isn't one of {', '.join(TIERS)}")
            if not r["customer_id"] or not r["name"]:
                raise ValueError(f"customers.csv row {n}: no customer_id or name")
            if r["customer_id"] in customers:
                raise ValueError(f"customers.csv row {n}: customer_id {r['customer_id']} appears twice")
            customers[r["customer_id"]] = Customer(r["customer_id"], r["name"], r["tier"], r["domain"].lower())
        by_domain: dict[str, list[Customer]] = defaultdict(list)
        for c in customers.values():
            if c.domain:
                by_domain[c.domain].append(c)
        contacts: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for n, r in _rows(folder, "contacts.csv"):
            if r["customer_id"] not in customers:
                raise ValueError(f"contacts.csv row {n}: customer {r['customer_id']!r} isn't in customers.csv")
            contacts[r["email"].lower()].append((r["customer_id"], r["name"]))
        parts: dict[tuple[str, str], list[Part]] = defaultdict(list)
        by_desc: dict[str, set[str]] = defaultdict(set)
        owners: dict[str, set[str]] = defaultdict(set)
        for n, r in _rows(folder, "customer-parts.csv"):
            if r["customer_id"] not in customers or not r["part_number"]:
                raise ValueError(f"customer-parts.csv row {n}: unknown customer, or no part number")
            p = Part(r["customer_id"], r["part_number"], r["revision"], r["family"].lower(), r["description"].lower())
            by_desc[p.description].add(p.family)
            parts[(p.customer, squash(p.number))].append(p)
            owners[squash(p.number)].add(p.customer)
        open_rfqs = []
        for n, r in _rows(folder, "open-rfqs.csv"):
            nums = [x for x in r["part_numbers"].split(";") if x]
            qtys = r["quantities"].split(";")
            if r["customer_id"] not in customers or not nums or len(qtys) != len(nums):
                raise ValueError(f"open-rfqs.csv row {n}: unknown customer, or parts and quantities don't line up")
            try:
                received = date.fromisoformat(r["received_on"])
                due = date.fromisoformat(r["stated_due"]) if r["stated_due"] else None
                quantities = [int(q) for q in qtys]
            except ValueError as e:
                raise ValueError(f"open-rfqs.csv row {n}: {e}") from e
            open_rfqs.append(
                OpenRFQ(r["rfq_id"], r["customer_id"], r.get("buyer", ""), received, due, nums, quantities)
            )
        hours: dict[date, float] = {}
        seniority: dict[date, str] = {}
        for n, r in _rows(folder, "estimator-hours.csv"):
            try:
                d, h = date.fromisoformat(r["date"]), float(r["hours"])
            except ValueError as e:
                raise ValueError(f"estimator-hours.csv row {n}: {e}") from e
            if h < 0 or d in hours:
                raise ValueError(f"estimator-hours.csv row {n}: negative hours, or the date appears twice")
            level = (r.get("seniority") or "junior").lower()
            if level not in SENIORITY:
                raise ValueError(f"estimator-hours.csv row {n}: seniority {level!r} isn't junior or senior")
            hours[d], seniority[d] = h, level
        families = {d: next(iter(f)) for d, f in by_desc.items() if d and len(f) == 1}
        look: dict[str, list[Customer]] = {}
        for cs in by_domain.values():
            for c in cs:
                alike = [o for o in cs if o.id != c.id and loose_key(o.name) == loose_key(c.name)]
                if alike:
                    look[c.id] = alike
        requotes = None
        if (folder / "requote-hours.csv").exists():
            requotes = {}
            for n, r in _rows(folder, "requote-hours.csv"):
                try:
                    requotes[date.fromisoformat(r["date"])] = float(r["hours"])
                except ValueError as e:
                    raise ValueError(f"requote-hours.csv row {n}: {e}") from e
        return cls(
            customers,
            dict(by_domain),
            dict(contacts),
            dict(parts),
            dict(owners),
            open_rfqs,
            hours,
            seniority,
            families,
            requotes,
            look,
        )

    # --- matching ----------------------------------------------------------------------------------------------

    def customer_for(
        self, sender: str, named: str, text: str = "", sender_name: str = ""
    ) -> tuple[Customer | None, list[str], list[str]]:
        """The customer an email is from, with the problems that send it to a person, and notes for the record.

        The sender's domain gives the candidates. One candidate is the customer, unless the email names a different
        customer or the sender is on file for one. Several candidates (a domain shared by sister companies) need the
        email to name one of them exactly (a buyer on file is shown as a hint, but doesn't decide). Contacts are only
        a bonus: most buyers are new. Anything else goes to a person. It never guesses."""
        problems: list[str] = []
        notes: list[str] = []
        address = sender.lower().strip()
        domain = address.rsplit("@", 1)[-1] if "@" in address else ""
        cands = self.by_domain.get(domain, [])
        # A buyer on file only counts when the name on file is the sender's: two people can share an address
        # format at one company (Riley and Reese Fenske, both rfenske@).
        on_file = {
            cid
            for cid, who in self.contacts.get(address, [])
            if not sender_name or name_key(who) == name_key(sender_name)
        }
        named_hits = [c for c in self.customers.values() if named.strip() and name_key(c.name) == name_key(named)]
        if not cands:
            if named_hits:
                problems.append(
                    f"the email names {named_hits[0].name}, but the sender's domain ({domain}) isn't theirs"
                )
            else:
                problems.append(f"a sender we can't place: no customer has the domain {domain or '(none)'}")
            return None, problems, notes
        in_domain = [c for c in named_hits if c in cands]
        if named_hits and not in_domain:
            problems.append(f"the sender's domain is {_names(cands)}'s, but the email names {named_hits[0].name}")
            return None, problems, notes
        if in_domain:
            chosen = in_domain[0]
        elif len(cands) == 1:
            chosen = cands[0]
            if named.strip():
                notes.append(f'the email says "{named[:60]}", which isn\'t how our records spell {chosen.name}')
        else:
            # On a shared domain the email has to name the company. A buyer on file is a hint for the person, not a
            # match: one address can sit under sister companies, and the answer key stops these too.
            mine = [c for c in cands if c.id in on_file]
            hint = f"; the buyer is on file for {mine[0].name}" if len(mine) == 1 else ""
            problems.append(
                f"the domain {domain} is shared by {len(cands)} customers ({_names(cands)}), and the email "
                f"doesn't say which{hint}"
            )
            return None, problems, notes
        others = sorted(self.customers[cid].name for cid in on_file if cid != chosen.id)
        if others:
            problems.append(f"the sender's address is on file for {others[0]}, but the email is from {chosen.name}")
            return None, problems, notes
        low = name_key(text)
        rivals = [c for c in cands if c.id != chosen.id and low and _whole(name_key(c.name), low)]
        if rivals:
            problems.append(f"the email names both {chosen.name} and {rivals[0].name}")
            return None, problems, notes
        if chosen.id in self.look_alikes:
            look = "; ".join(c.name for c in self.look_alikes[chosen.id])
            notes.append(f"look-alike records share this domain ({look}): spot-check that it's {chosen.name}")
        return chosen, problems, notes

    def part_status(
        self, customer: Customer, number: str, revision: str, description: str = ""
    ) -> tuple[str, str, str]:
        """(status, family, problem). Status is "repeat" (on file for this customer at this revision), "repeat, new
        revision" (on file at another), or "new". A repeat's family is the record's; a new part's comes from its
        description, when every part on file with that description is in one family. The problem is set when the
        part number is on file only for another customer, or on file as something else than the email describes
        (a number reused for a new part, or a typo)."""
        key, desc = squash(number), description.strip().lower()
        mine = self.parts.get((customer.id, key), [])
        if mine:
            revs = sorted({p.revision for p in mine})
            family = mine[-1].family
            if desc and mine[-1].description and squash(desc) != squash(mine[-1].description):
                return (
                    "repeat",
                    family,
                    (f"{number} is on file as a {mine[-1].description}, but the email says {desc}: a reused number?"),
                )
            if squash(revision) in {squash(r) for r in revs}:
                return "repeat", family, ""
            return f"repeat, new revision (we have rev {', '.join(revs)})", family, ""
        owners = self.part_owners.get(key, set()) - {customer.id}
        if owners:
            return "new", "", f"part {number} is on file for another customer ({self.customers[min(owners)].name})"
        return "new", self.families.get(desc, ""), ""


def _whole(needle: str, haystack: str) -> bool:
    """True if a name appears in the text as whole words ("hollis builders inc" isn't in "hollis builders inc2")."""
    return bool(re.search(rf"(?<![\w]){re.escape(needle)}(?![\w])", haystack))


def _names(cs: list[Customer]) -> str:
    return "; ".join(c.name for c in cs)


def _rows(folder: Path, name: str):
    path = folder / name
    if not path.exists():
        raise ValueError(f"{name} is missing from {folder}")
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = [(h or "").strip() for h in (reader.fieldnames or [])]
        missing = [c for c in COLUMNS[name] if c not in header]
        if missing:
            raise ValueError(f"{name} is missing columns: {', '.join(missing)}")
        for n, row in enumerate(reader, 2):
            yield n, {(k or "").strip(): (v or "").strip() for k, v in row.items() if k}
