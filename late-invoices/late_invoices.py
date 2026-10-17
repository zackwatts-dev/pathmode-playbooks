"""Late invoices: decide who gets the automatic reminder and who needs a person, then draft the personal ones.

    python late-invoices/late_invoices.py --sample --dry-run
    python late-invoices/late_invoices.py --aging ar-aging.csv --history payment-history.csv \
        --replies replies/ --as-of 2026-07-13

Rules first. Your accounting software's automatic reminders handle most late invoices. This finds the
ones they shouldn't: repeat-late customers, large or old balances, broken promises and disputes. Every
amount and invoice number in a draft comes from your export, inserted by code; the model writes only the
words around them, and any number it adds on its own is flagged.

Writes out/actions.csv, out/summary.md and out/drafts/. Nothing is sent.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.evidence import unsupported_numbers  # noqa: E402
from common.util import BadAnswer, done, model_for, parse_json, parser, read_csv, write_csv, write_text  # noqa: E402

HERE = Path(__file__).parent
SAMPLE = HERE / "sample-data"
SAMPLE_AS_OF = date(2026, 7, 13)
FIELDS = ["customer", "contact", "email", "overdue", "oldest_days", "invoices", "action", "why", "draft"]

ACTIONS = {
    "none": "Nothing to do: not overdue.",
    "automatic": "Leave it to your accounting software's automatic reminder.",
    "personal": "Send a personal email (draft below), from a person they know.",
    "wait": "They've promised a date. Wait, and check on that date.",
    "call": "Call. An email won't fix this one.",
    "resolve": "Resolve the dispute first. Don't chase payment until it's settled.",
}


@dataclass
class Invoice:
    number: str
    due: date
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
    promise: dict | None = None
    action: str = "none"
    why: str = ""
    draft: str = ""
    flags: list[str] = field(default_factory=list)

    def overdue(self, as_of: date) -> list[Invoice]:
        return [i for i in self.invoices if i.balance > 0 and i.due < as_of]

    def overdue_total(self, as_of: date) -> float:
        return round(sum(i.balance for i in self.overdue(as_of)), 2)

    def oldest_days(self, as_of: date) -> int:
        return max(((as_of - i.due).days for i in self.overdue(as_of)), default=0)

    def usually_late(self, late_days: int) -> bool:
        late = [d for d in self.days_late_history if d > late_days]
        return len(self.days_late_history) >= 2 and len(late) / len(self.days_late_history) >= 0.5


def money(x: float) -> str:
    return f"${x:,.2f}"


def load(aging: Path, history: Path | None, replies: Path | None) -> dict[str, Account]:
    accounts: dict[str, Account] = {}
    for row in read_csv(aging):
        a = accounts.setdefault(row["Customer"], Account(row["Customer"], row.get("Contact", ""), row.get("Email", "")))
        a.invoices.append(
            Invoice(row["Invoice"], date.fromisoformat(row["Due date"]), float(row["Amount"]), float(row["Balance"]))
        )
    if history and history.exists():
        for row in read_csv(history):
            if row["Customer"] in accounts and row.get("Paid date"):
                late = (date.fromisoformat(row["Paid date"]) - date.fromisoformat(row["Due date"])).days
                accounts[row["Customer"]].days_late_history.append(max(late, 0))
    if replies and replies.exists():
        for path in sorted(replies.glob("*.txt")) + sorted(replies.glob("*.eml")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for a in accounts.values():
                if (a.email and a.email.lower() in text.lower()) or any(i.number in text for i in a.invoices):
                    a.reply = (a.reply + "\n\n" + text).strip()
    return accounts


READ_REPLY = """You read a customer's reply about an unpaid invoice and report what it says, as JSON only:
{"kind": "promise | dispute | question | other",
 "promised_date": "YYYY-MM-DD or empty",
 "promised_amount": number or null,
 "dispute_reason": "short, or empty",
 "note": "anything else a person should know, e.g. they say their terms are different"}
Use only what the reply says. If a date has no year, assume the year of the reply. Never guess."""


def read_reply(a: Account, model) -> None:
    try:
        r = parse_json(model.complete(READ_REPLY, f"<<<REPLY\n{a.reply}\nREPLY>>>"))
    except BadAnswer as e:
        a.flags.append(f"couldn't read the customer's reply: {e}")
        return
    if not isinstance(r, dict):
        return
    if r.get("note"):
        a.flags.append(str(r["note"]))
    if r.get("kind") == "dispute":
        a.promise = {"dispute": r.get("dispute_reason") or "the customer disputes it"}
    elif r.get("kind") == "promise" and r.get("promised_date"):
        try:
            a.promise = {"date": date.fromisoformat(r["promised_date"]), "amount": r.get("promised_amount")}
        except ValueError:
            a.flags.append(f"the promised date {r['promised_date']!r} isn't a real date: read the reply")


def decide(a: Account, as_of: date, late_days: int, large: float, call_after: int) -> None:
    """The rules. Plain code, so you can read them and change them."""
    if not a.overdue(as_of):
        a.action, a.why = "none", "Nothing overdue."
        return
    total, oldest = a.overdue_total(as_of), a.oldest_days(as_of)
    if a.promise and "dispute" in a.promise:
        a.action, a.why = "resolve", f"Disputed: {a.promise['dispute']}"
    elif a.promise and a.promise["date"] >= as_of:
        a.action, a.why = "wait", f"Promised payment by {a.promise['date']:%B %-d}."
    elif a.promise:
        a.action, a.why = "call", f"Promised payment by {a.promise['date']:%B %-d}, and it hasn't arrived."
    elif oldest > call_after:
        a.action, a.why = "call", f"{oldest} days overdue."
    elif a.usually_late(late_days):
        avg = round(mean(a.days_late_history))
        a.action, a.why = "personal", f"Pays late most of the time (on average {avg} days after the due date)."
    elif total >= large:
        a.action, a.why = "personal", f"Large balance: {money(total)} overdue."
    else:
        a.action, a.why = "automatic", "Usually pays on time; a reminder should do it."


DRAFT = """You write a short, friendly, personal payment follow-up email from a small business to a customer it
wants to keep. Plain words, no threats, no legal language, no exclamation marks. Two short paragraphs at
most. Where the list of unpaid invoices belongs, write the line {{INVOICES}} on its own: the system inserts
the invoice numbers and amounts. Don't write any amounts, invoice numbers or dates yourself. Offer to
help if something is wrong with an invoice. Sign it "{signature}". Answer with the email body only."""


def draft_email(a: Account, as_of: date, model, signature: str) -> None:
    body = model.complete(DRAFT.format(signature=signature), f"Customer: {a.customer}\nContact: {a.contact}\n{a.why}")
    table = (
        "\n".join(f"- Invoice {i.number}, due {i.due:%B %-d}: {money(i.balance)}" for i in a.overdue(as_of))
        + f"\n- Total: {money(a.overdue_total(as_of))}"
    )
    allowed = [i.balance for i in a.invoices] + [float(i.number) for i in a.invoices if i.number.isdigit()]
    invented = unsupported_numbers(body, allowed)
    if invented:
        a.flags.append(f"the draft mentions numbers that aren't in your records ({', '.join(invented)}): fix them")
    if "{{INVOICES}}" not in body:
        body = body.rstrip() + "\n\n{{INVOICES}}"
    a.draft = body.replace("{{INVOICES}}", table)


def summary_md(accounts: list[Account], as_of: date, model_name: str) -> str:
    buckets = {"1–30 days": 0.0, "31–60 days": 0.0, "61–90 days": 0.0, "Over 90 days": 0.0}
    for a in accounts:
        for i in a.overdue(as_of):
            d = (as_of - i.due).days
            key = "1–30 days" if d <= 30 else "31–60 days" if d <= 60 else "61–90 days" if d <= 90 else "Over 90 days"
            buckets[key] += i.balance
    lines = [
        f"# Late invoices as of {as_of:%B %-d, %Y}",
        "",
        f"Model: {model_name}. Nothing was sent.",
        "",
        "## Overdue, by age",
        "",
        "| Age | Amount |",
        "|---|---|",
    ]
    lines += [f"| {k} | {money(v)} |" for k, v in buckets.items()]
    lines += [f"| **Total** | **{money(sum(buckets.values()))}** |", "", "## What to do", ""]
    order = ["call", "resolve", "personal", "wait", "automatic"]
    for action in order:
        group = [a for a in accounts if a.action == action]
        if group:
            lines += [f"### {ACTIONS[action]}", ""]
            for a in group:
                lines.append(f"- **{a.customer}**: {money(a.overdue_total(as_of))} overdue. {a.why}")
                lines += [f"  - Check: {f}" for f in a.flags]
            lines.append("")
    return "\n".join(lines)


def run(
    accounts: dict[str, Account],
    model,
    out: Path,
    as_of: date,
    late_days=5,
    large=5000.0,
    call_after=60,
    signature="Summit Mechanical",
) -> tuple[list[Account], list[Path]]:
    result = sorted(accounts.values(), key=lambda a: -a.overdue_total(as_of))
    for a in result:
        if a.reply and a.overdue(as_of):
            read_reply(a, model)
        decide(a, as_of, late_days, large, call_after)
        if a.action == "personal":
            draft_email(a, as_of, model, signature)
    written = []
    for n, a in enumerate((a for a in result if a.draft), 1):
        slug = re.sub(r"[^a-z0-9]+", "-", a.customer.lower()).strip("-")
        header = f"To: {a.contact} <{a.email}>\nSubject: Checking in on open invoices\n\n"
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
    ]
    written[:0] = [
        write_csv(out / "actions.csv", rows, FIELDS),
        write_text(out / "summary.md", summary_md(result, as_of, model.name)),
    ]
    return result, written


def offline(system: str, user: str) -> str:
    if system.startswith("You read"):
        text = user.lower()
        if re.search(r"not paying|won't pay|dispute|until someone fixes", text):
            reason = "says the work isn't finished"
            return json.dumps(
                {"kind": "dispute", "promised_date": "", "promised_amount": None, "dispute_reason": reason, "note": ""}
            )
        months = {
            m: i
            for i, m in enumerate(
                [
                    "january",
                    "february",
                    "march",
                    "april",
                    "may",
                    "june",
                    "july",
                    "august",
                    "september",
                    "october",
                    "november",
                    "december",
                ],
                1,
            )
        }
        found = re.search(r"(" + "|".join(months) + r")\s+(\d{1,2})", text)
        year = re.search(r"date: (\d{4})", text)
        if found:
            d = date(int(year.group(1)) if year else 2026, months[found.group(1)], int(found.group(2)))
            note = "they mention different payment terms: check the contract" if "net " in text else ""
            return json.dumps(
                {
                    "kind": "promise",
                    "promised_date": d.isoformat(),
                    "promised_amount": None,
                    "dispute_reason": "",
                    "note": note,
                }
            )
        return json.dumps(
            {"kind": "other", "promised_date": "", "promised_amount": None, "dispute_reason": "", "note": ""}
        )
    contact = re.search(r"Contact: (\S+)", user)
    name = contact.group(1) if contact else "there"
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
    p.add_argument("--replies", type=Path, help="folder of customer replies (.txt or .eml)")
    p.add_argument("--as-of", type=date.fromisoformat, help="date to measure from (default: today)")
    p.add_argument("--late-days", type=int, default=5, help="days past due that count as late (default 5)")
    p.add_argument("--large", type=float, default=5000, help="balance that always gets a personal email")
    p.add_argument("--call-after", type=int, default=60, help="days overdue after which you call (default 60)")
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
    )
    needs = sum(1 for a in result if a.action in ("call", "resolve", "personal"))
    done(model, written, f"{needs} customers need a person; the rest can be left to automatic reminders.")


if __name__ == "__main__":
    main()
