"""Late invoices: decide who gets the automatic reminder and who needs a person, then draft the personal ones.

    python late-invoices/late_invoices.py --sample --dry-run
    python late-invoices/late_invoices.py --aging ar-aging.csv --history payment-history.csv \
        --replies replies/ --as-of 2025-10-31

Rules first. Your accounting software's automatic reminders handle most late invoices. This finds the
ones they shouldn't: customers waiting on you for something, disputes, repeat-late customers, large or
old balances, broken promises and small leftovers. It also flags the records problems that make invoices late: duplicate
customer accounts and invoices with no due date. Every amount and invoice number in a draft comes from
your export, inserted by code; the model writes only the words around them, and any number it adds on its
own is flagged.

The sample is Summit Mechanical's Tucson branch on October 31, 2025, from the Summit simulation.

Writes out/actions.csv, out/summary.md and out/drafts/. Nothing is sent.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.evidence import unsupported_numbers  # noqa: E402
from common.util import BadAnswer, done, model_for, parse_json, parser, read_csv, write_csv, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"
SAMPLE_AS_OF = date(2025, 10, 31)
FIELDS = ["customer", "contact", "email", "overdue", "oldest_days", "invoices", "action", "why", "draft"]

ACTIONS = {
    "none": "Nothing to do: not overdue.",
    "automatic": "Leave it to your accounting software's automatic reminder.",
    "answer": "They're waiting on you. Do what they asked, and pause their reminders until you have.",
    "resolve": "They're questioning the charge. Resolve it first, and pause their reminders until you have.",
    "call": "Call. An email won't fix this one.",
    "small": "A small leftover balance, probably a short payment. Ask why, or write it off.",
    "personal": "Send a personal email (draft below), from a person they know.",
    "wait": "They've promised a date. Wait, and check on that date.",
}
ORDER = ["answer", "resolve", "call", "personal", "wait", "small", "automatic"]


@dataclass
class Invoice:
    number: str
    due: date | None
    amount: float
    balance: float


@dataclass
class Account:
    customer: str
    contact: str
    email: str
    invoices: list[Invoice] = field(default_factory=list)
    days_late_history: list[int] = field(default_factory=list)
    reply: str = ""
    reading: dict | None = None
    action: str = "none"
    why: str = ""
    draft: str = ""
    flags: list[str] = field(default_factory=list)

    def overdue(self, as_of: date) -> list[Invoice]:
        return [i for i in self.invoices if i.balance > 0 and i.due and i.due < as_of]

    def overdue_total(self, as_of: date) -> float:
        return round(sum(i.balance for i in self.overdue(as_of)), 2)

    def oldest_days(self, as_of: date) -> int:
        return max(((as_of - i.due).days for i in self.overdue(as_of)), default=0)

    def average_days_late(self) -> float | None:
        """Average days after the due date over the last year's paid invoices; None if there are too few."""
        return mean(self.days_late_history) if len(self.days_late_history) >= 3 else None


def money(x: float) -> str:
    return f"${x:,.2f}"


def name_key(name: str) -> str:
    """A customer name with case, spacing, punctuation and Inc/LLC/The removed, for spotting duplicates."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(inc|llc|the|co)\b", "", name.lower()))


def load(aging: Path, history: Path | None, replies: Path | None) -> dict[str, Account]:
    accounts: dict[str, Account] = {}
    for row in read_csv(aging):
        a = accounts.setdefault(row["Customer"], Account(row["Customer"], row.get("Contact", ""), row.get("Email", "")))
        due = date.fromisoformat(row["Due date"]) if row.get("Due date") else None
        a.invoices.append(Invoice(row["Invoice"], due, float(row["Amount"]), float(row["Balance"])))
    if history and history.exists():
        for row in read_csv(history):
            if row["Customer"] in accounts and row.get("Paid date"):
                late = (date.fromisoformat(row["Paid date"]) - date.fromisoformat(row["Due date"])).days
                accounts[row["Customer"]].days_late_history.append(max(late, 0))
    if replies and replies.exists():
        for path in sorted(replies.glob("*.txt")) + sorted(replies.glob("*.eml")):
            text = path.read_text(encoding="utf-8", errors="replace")
            low = text.lower()
            for a in accounts.values():
                if (
                    (a.email and a.email.lower() in low)
                    or any(re.search(rf"\b{re.escape(i.number)}\b", text) for i in a.invoices)
                    or a.customer.lower() in low
                ):
                    a.reply = (a.reply + "\n\n" + text).strip()
    return accounts


def flag_records(accounts: dict[str, Account]) -> list[list[str]]:
    """Records problems that make invoices late on their own. Returns groups of names that look like one customer."""
    groups: dict[str, list[str]] = defaultdict(list)
    for name in accounts:
        groups[name_key(name)].append(name)
    dupes = [sorted(g) for g in groups.values() if len(g) > 1]
    for g in dupes:
        for name in g:
            others = ", ".join(o for o in g if o != name)
            accounts[name].flags.append(f"looks like the same customer as {others}: merge the accounts")
    for a in accounts.values():
        undated = [i.number for i in a.invoices if i.balance > 0 and not i.due]
        if undated:
            a.flags.append(f"no due date on {', '.join(undated)}, so no reminder will ever go out: add one")
    return dupes


READ_REPLY = """You read a customer's emails about their invoices and report what they say, as JSON only:
{"kind": "promise | dispute | question | other",
 "need": "what they're waiting for from us, in a few words, or empty",
 "promised_date": "YYYY-MM-DD or empty",
 "dispute_reason": "short, or empty",
 "note": "anything else a person should know, e.g. they say their terms are different"}
A question is a request we have to act on before they can pay: resend an invoice, send line items, a W-9,
a new billing address, or checking whether a payment arrived. A dispute questions the charge itself: they
think it was covered, or charged twice. If there are several emails, report the most serious: dispute, then
question, then promise. Use only what the emails say. If a date has no year, use the year of the email.
Never guess."""


def read_reply(a: Account, model) -> None:
    try:
        r = parse_json(model.complete(READ_REPLY, f"<<<EMAILS\n{a.reply}\nEMAILS>>>"))
    except BadAnswer as e:
        a.flags.append(f"couldn't read the customer's emails: {e}")
        return
    if not isinstance(r, dict):
        return
    if r.get("note"):
        a.flags.append(str(r["note"]))
    kind = r.get("kind")
    if kind == "dispute":
        a.reading = {"kind": "dispute", "about": r.get("dispute_reason") or "they question the charge"}
    elif kind == "question":
        a.reading = {"kind": "question", "need": r.get("need") or "they asked us something"}
    elif kind == "promise" and r.get("promised_date"):
        try:
            a.reading = {"kind": "promise", "date": date.fromisoformat(r["promised_date"])}
        except ValueError:
            a.flags.append(f"the promised date {r['promised_date']!r} isn't a real date: read the email")


def decide(a: Account, as_of: date, late_days: int, large: float, call_after: int, small: float = 100) -> None:
    """The rules. Plain code, so you can read them and change them."""
    if not a.overdue(as_of):
        a.action, a.why = "none", "Nothing overdue."
        return
    total, oldest, avg = a.overdue_total(as_of), a.oldest_days(as_of), a.average_days_late()
    r = a.reading or {}
    if r.get("kind") == "dispute":
        a.action, a.why = "resolve", f"Questioned: {r['about']}."
    elif r.get("kind") == "question":
        a.action, a.why = "answer", f"Waiting on us: {r['need']}."
    elif r.get("kind") == "promise" and r["date"] >= as_of:
        a.action, a.why = "wait", f"Promised payment by {r['date']:%B %-d}."
    elif r.get("kind") == "promise":
        a.action, a.why = "call", f"Promised payment by {r['date']:%B %-d}, and it hasn't arrived."
    elif total < small:
        a.action, a.why = "small", f"Only {money(total)} left, {oldest} days overdue."
    elif oldest > call_after:
        a.action, a.why = "call", f"{oldest} days overdue."
    elif avg is not None and avg > late_days:
        a.action, a.why = "personal", f"Usually late: on average {round(avg)} days after the due date this year."
    elif total >= large:
        a.action, a.why = "personal", f"Large balance: {money(total)} overdue."
    else:
        a.action, a.why = "automatic", "Usually pays close to on time; a reminder should do it."


DRAFT = """You write a short, friendly, personal payment follow-up email from a business to a customer it
wants to keep. Plain words, no threats, no legal language, no exclamation marks. Two short paragraphs at
most. Where the list of unpaid invoices belongs, write the line {{INVOICES}} on its own: the system inserts
the invoice numbers and amounts. Don't write any amounts, invoice numbers or dates yourself. Offer to
help if something is wrong with an invoice. Sign it "{signature}". Answer with the email body only."""


def draft_email(a: Account, as_of: date, model, signature: str) -> None:
    body = model.complete(
        DRAFT.format(signature=signature), f"Customer: {a.customer}\nContact: {a.contact or 'unknown'}\n{a.why}"
    )
    table = (
        "\n".join(f"- Invoice {i.number}, due {i.due:%B %-d}: {money(i.balance)}" for i in a.overdue(as_of))
        + f"\n- Total: {money(a.overdue_total(as_of))}"
    )
    allowed = [i.balance for i in a.invoices] + [float(re.sub(r"\D", "", i.number) or 0) for i in a.invoices]
    invented = unsupported_numbers(body, allowed)
    if invented:
        a.flags.append(f"the draft mentions numbers that aren't in your records ({', '.join(invented)}): fix them")
    if "{{INVOICES}}" not in body:
        body = body.rstrip() + "\n\n{{INVOICES}}"
    a.draft = body.replace("{{INVOICES}}", table)


def bucket(days: int) -> str:
    return "1–30 days" if days <= 30 else "31–60 days" if days <= 60 else "61–90 days" if days <= 90 else "Over 90 days"


def summary_md(accounts: list[Account], dupes: list[list[str]], as_of: date, model_name: str) -> str:
    buckets = dict.fromkeys(["1–30 days", "31–60 days", "61–90 days", "Over 90 days"], 0.0)
    for a in accounts:
        for i in a.overdue(as_of):
            buckets[bucket((as_of - i.due).days)] += i.balance
    total = sum(buckets.values())
    lines = [
        f"# Late invoices as of {as_of:%B %-d, %Y}",
        "",
        f"Model: {model_name}. Nothing was sent.",
        "",
        "## Overdue, by age",
        "",
        "| Age | Amount | Share |",
        "|---|---:|---:|",
    ]
    lines += [f"| {k} | {money(v)} | {v / total:.0%} |" for k, v in buckets.items() if total]
    lines += [f"| **Total** | **{money(total)}** | |", "", "## Who needs what", ""]
    lines += ["| What to do | Customers | Overdue |", "|---|---:|---:|"]
    for action in ORDER:
        group = [a for a in accounts if a.action == action]
        if group:
            amount = sum(a.overdue_total(as_of) for a in group)
            lines.append(f"| {ACTIONS[action].split('.')[0]} | {len(group)} | {money(amount)} |")
    undated = [(a, i) for a in accounts for i in a.invoices if i.balance > 0 and not i.due]
    if dupes or undated:
        lines += ["", "## Fix these records first", ""]
        for g in dupes:
            lines.append(f"- **Same customer, {len(g)} accounts:** {' / '.join(g)}. Merge them.")
        if undated:
            amount = sum(i.balance for _, i in undated)
            lines.append(
                f"- **{len(undated)} invoices with no due date** ({money(amount)}). They don't appear in the "
                "aging above, and no reminder will ever go out for them."
            )
    lines += ["", "## The list", ""]
    for action in ORDER:
        if action == "automatic":
            continue
        group = [a for a in accounts if a.action == action]
        if group:
            lines += [f"### {ACTIONS[action]}", ""]
            for a in group:
                lines.append(f"- **{a.customer}**: {money(a.overdue_total(as_of))} overdue. {a.why}")
                lines += [f"  - Check: {f}" for f in a.flags]
            lines.append("")
    auto = [a for a in accounts if a.action == "automatic"]
    if auto:
        lines += [f"### {ACTIONS['automatic']}", "", f"{len(auto)} customers: see actions.csv.", ""]
    return "\n".join(lines)


def run(
    accounts: dict[str, Account],
    model,
    out: Path,
    as_of: date,
    late_days=20,
    large=5000.0,
    call_after=60,
    signature="Summit Mechanical",
    small=100.0,
) -> tuple[list[Account], list[Path]]:
    dupes = flag_records(accounts)
    result = sorted(accounts.values(), key=lambda a: -a.overdue_total(as_of))
    for a in result:
        if a.reply and a.overdue(as_of):
            read_reply(a, model)
        decide(a, as_of, late_days, large, call_after, small)
        if a.action == "personal":
            draft_email(a, as_of, model, signature)
    written = []
    for n, a in enumerate((a for a in result if a.draft), 1):
        slug = re.sub(r"[^a-z0-9]+", "-", a.customer.lower()).strip("-")
        to = f"{a.contact} <{a.email}>" if a.email else "(add their billing contact)"
        header = f"To: {to}\nSubject: Checking in on open invoices\n\n"
        written.append(write_text(out / "drafts" / f"{n:02d}-{slug}.txt", header + a.draft + "\n"))
    rows = [
        {
            "customer": a.customer,
            "contact": a.contact,
            "email": a.email,
            "overdue": f"{a.overdue_total(as_of):.2f}",
            "oldest_days": a.oldest_days(as_of),
            "invoices": " ".join(i.number for i in a.overdue(as_of)),
            "action": a.action,
            "why": " ".join([a.why, *a.flags]),
            "draft": "yes" if a.draft else "",
        }
        for a in result
        if a.overdue(as_of) or a.flags
    ]
    written[:0] = [
        write_csv(out / "actions.csv", rows, FIELDS),
        write_text(out / "summary.md", summary_md(result, dupes, as_of, model.name)),
    ]
    return result, written


def offline(system: str, user: str) -> str:
    """A crude stand-in for the model, so the pipeline runs for free. It only knows a few phrasings."""
    if system.startswith("You read"):
        text = user.lower()
        reading = {"kind": "other", "need": "", "promised_date": "", "dispute_reason": "", "note": ""}
        if "covered under our agreement" in text:
            reading |= {"kind": "dispute", "dispute_reason": "they think it was covered under their agreement"}
        elif "two trip charges" in text:
            reading |= {"kind": "dispute", "dispute_reason": "they think a trip charge was billed twice"}
        elif "not paying" in text or "won't pay" in text:
            reading |= {"kind": "dispute", "dispute_reason": "they say the work isn't finished"}
        else:
            needs = {
                "w-9": "a W-9",
                "breakdown": "line items for their accounts payable",
                "resend": "the invoice sent again",
                "billing address": "invoices sent to their new billing address",
                "paid?": "a check on whether their payment arrived",
            }
            found = [v for k, v in needs.items() if k in text]
            if found:
                reading |= {"kind": "question", "need": " and ".join(dict.fromkeys(found))}
        return json.dumps(reading)
    contact = re.search(r"Contact: (\S+)", user)
    name = contact.group(1) if contact and contact.group(1) != "unknown" else "there"
    signature = re.search(r'Sign it "([^"]+)"', system)
    return (
        f"Hi {name},\n\nI hope things are going well. I'm checking in on a few invoices that are now past due:\n\n"
        "{{INVOICES}}\n\nIf anything on them looks wrong, tell me and I'll sort it out. Otherwise, could you let me "
        f"know when we can expect payment?\n\nThanks,\n{signature.group(1) if signature else ''}"
    )


def main() -> None:
    p = parser("Sort late invoices into automatic reminders and personal follow-ups. Never sends.", SAMPLE)
    p.add_argument("--aging", type=Path, help="accounts receivable aging export, CSV")
    p.add_argument("--history", type=Path, help="paid invoices with due and paid dates, CSV")
    p.add_argument("--replies", type=Path, help="folder of customer emails (.txt or .eml)")
    p.add_argument("--as-of", type=date.fromisoformat, help="date to measure from (default: today)")
    p.add_argument("--late-days", type=int, default=20, help="average days late that counts as usually late")
    p.add_argument("--large", type=float, default=5000, help="balance that always gets a personal email")
    p.add_argument("--call-after", type=int, default=60, help="days overdue after which you call (default 60)")
    p.add_argument("--small", type=float, default=100, help="balance below which it's a leftover, not a chase")
    p.add_argument("--signature", default="Summit Mechanical")
    args = p.parse_args()
    if args.sample:
        aging, history, replies = SAMPLE / "ar-aging.csv", SAMPLE / "payment-history.csv", SAMPLE / "replies"
        as_of = args.as_of or SAMPLE_AS_OF
    elif args.aging:
        aging, history, replies, as_of = args.aging, args.history, args.replies, args.as_of or date.today()
    else:
        p.error("choose --sample or --aging")
    model = model_for(args, offline)
    result, written = run(
        load(aging, history, replies),
        model,
        args.out,
        as_of,
        args.late_days,
        args.large,
        args.call_after,
        args.signature,
        args.small,
    )
    needs = sum(1 for a in result if a.action in ("answer", "resolve", "call", "personal"))
    auto = sum(1 for a in result if a.action == "automatic")
    done(model, written, f"{needs} customers need a person; {auto} can be left to automatic reminders.")


if __name__ == "__main__":
    main()
