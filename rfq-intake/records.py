"""Summit's own records, exported from its field-service system, and the matching that has to be right.

The model reads the email; this code decides which customer, site and piece of equipment it means. Every
match is exact or unique, or it isn't a match: when two units could fit, we ask the customer which one
rather than guessing.
"""

from __future__ import annotations

import difflib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from common.evidence import value_in_quote
from common.util import read_csv

FAMILIES = {
    "rtu": ["rooftop", "rtu", "package unit", "packaged unit", "roof top"],
    "split": ["split", "mini split", "condensing unit", "heat pump"],
    "walkin": ["walk-in", "walk in", "walkin"],
    "reachin": ["reach-in", "reach in", "reachin"],
    "chiller": ["chiller"],
    "boiler": ["boiler"],
}

NAMES = {
    "rtu": "rooftop unit",
    "split": "split system",
    "walkin": "walk-in",
    "reachin": "reach-in",
    "chiller": "chiller",
    "boiler": "boiler",
}


def squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def name_key(name: str) -> str:
    return squash(re.sub(r"\b(inc|llc|the|co)\b\.?", "", str(name).lower()))


def unit_family(equipment_type: str) -> str:
    """The family of a unit, from your export's Type column. Exports spell it many ways ("rtu", "Rooftop Unit",
    "Walk-In Cooler"): the same words that sort an email's equipment sort the records, so they can meet."""
    return family_of(equipment_type) or squash(equipment_type)


def family_of(text: str) -> str:
    low = str(text).lower()
    for fam, words in FAMILIES.items():
        if any(w in low for w in words):
            return fam
    return ""


@dataclass
class Unit:
    id: str
    site: str
    family: str
    make: str
    model: str
    serial: str
    installed: str


@dataclass
class Site:
    id: str
    customer: str
    name: str
    address: str
    units: list[Unit] = field(default_factory=list)


@dataclass
class Customer:
    id: str
    name: str
    sites: list[Site] = field(default_factory=list)


@dataclass
class Records:
    customers: dict[str, Customer]
    sites: dict[str, Site]
    units: dict[str, Unit]
    by_email: dict[str, str]
    by_serial: dict[str, Unit]

    @classmethod
    def load(cls, folder: Path) -> Records:
        customers = {
            r["Customer ID"]: Customer(r["Customer ID"], r["Name"]) for r in read_csv(folder / "customers.csv")
        }
        sites = {}
        for r in read_csv(folder / "sites.csv"):
            s = Site(r["Site ID"], r["Customer ID"], r["Site"], r["Address"])
            sites[s.id] = s
            if s.customer in customers:
                customers[s.customer].sites.append(s)
        units, orphans = {}, []
        for r in read_csv(folder / "equipment.csv"):
            u = Unit(
                r["Equipment ID"],
                r["Site ID"],
                unit_family(r["Type"]),
                r["Make"],
                r["Model"],
                r["Serial"],
                r["Installed"],
            )
            if u.site not in sites:
                # Equipment at a site that isn't in sites.csv can't be tied to a customer, so it can't be matched:
                # an email quoting its serial reads as "not in our records" and goes to a person.
                orphans.append(u.id)
                continue
            units[u.id] = u
            sites[u.site].units.append(u)
        if orphans:
            print(
                f"warning: {len(orphans)} equipment row(s) name a site that isn't in sites.csv, skipped "
                f"(e.g. Equipment ID {orphans[0]})",
                file=sys.stderr,
            )
        by_email = {r["Email"].lower(): r["Customer ID"] for r in read_csv(folder / "contacts.csv")}
        by_serial = {squash(u.serial): u for u in units.values() if u.serial}
        return cls(customers, sites, units, by_email, by_serial)

    def customer_for(self, sender_email: str, name: str) -> tuple[Customer | None, str]:
        """The customer, and how we know: 'contact' (the sender is on file) or 'name' (an exact name match)."""
        cid = self.by_email.get(sender_email.lower())
        if cid in self.customers:
            return self.customers[cid], "contact"
        key = name_key(name)
        hits = [c for c in self.customers.values() if key and name_key(c.name) == key]
        return (hits[0], "name") if len(hits) == 1 else (None, "")

    def site_for(self, customer: Customer, name: str, address: str = "") -> Site | None:
        """A site of this customer whose name or street address matches exactly (ignoring case and punctuation)."""
        wanted = {squash(name), squash(address)} - {""}
        hits = [s for s in customer.sites if wanted & {squash(s.name), squash(s.address)}]
        if not hits and name:
            # "Glendale Boutique #101" written with the city after it: still exact on the name part, as whole
            # words, so "#1001" never matches a site called "#100".
            hits = [s for s in customer.sites if squash(s.name) and value_in_quote(s.name, f"{name} {address}")]
        return hits[0] if len(hits) == 1 else None

    def nearest_serial(self, serial: str, site: Site | None) -> str:
        pool = [u.serial for u in (site.units if site else self.units.values())]
        close = difflib.get_close_matches(serial, pool, n=1, cutoff=0.75)
        return close[0] if close else ""
