"""Build each playbook's downloads for pathmode.com from this repository and the site's playbook pages.

    .venv/bin/python tools/build_downloads.py --site ../pathmode

For every playbook in the site's src/_data/playbooks.json, writes into the site:
- src/_includes/playbooks/<slug>-instructions.md: the instructions the page shows (from <slug>/instructions.md);
- src/assets/downloads/playbooks/<slug>/<slug>-instructions.md: the same, to download;
- .../<slug>-cost-worksheet.xlsx: the page's cost calculator as a spreadsheet with live formulas;
- .../<slug>-for-your-ai.md: the page, the instructions and the code's README in one Markdown file;
- .../<slug>-summit-files.zip: the playbook's Summit sample data, for a worked example ("sample" set in the JSON);
- .../<slug>-build-prompt.md: the description to give an AI coding assistant (from <slug>/build-prompt.md, if any);
- .../<slug>-dashboard.html: the worked example's dashboard, from its recorded run ("dashboard" set in the JSON).

The printable guide (PDF) is made afterwards by the site's scripts/print-playbooks.mjs, from the built page.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
FORMULA = re.compile(r"^[\w\s+\-*/().]+$")


def worksheet(item: dict, path: Path, checked: str) -> None:
    cost = item["cost"]
    wb = Workbook()
    ws = wb.active
    ws.title = "What it costs"
    bold, green = Font(bold=True), PatternFill("solid", fgColor="EEF5E0")
    ws["A1"] = f"{item['title']}: what it costs you"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Replace the example values in column B with your own. The results below update."
    ws["A2"].font = Font(italic=True)
    ws["A4"], ws["B4"] = "Your numbers", "Value"
    ws["A4"].font = ws["B4"].font = bold
    cells = {}
    row = 5
    for i in cost["inputs"]:
        ws.cell(row, 1, i["label"])
        c = ws.cell(row, 2, i["value"])
        c.fill = green
        cells[i["id"]] = f"B{row}"
        row += 1
    row += 1
    ws.cell(row, 1, "Results").font = bold
    row += 1
    for o in cost["outputs"]:
        formula = o["formula"]
        if not FORMULA.match(formula):
            raise ValueError(f"{item['slug']}: bad formula {formula!r}")
        names = set(re.findall(r"[A-Za-z_]\w*", formula))
        if names - cells.keys():
            raise ValueError(f"{item['slug']}: unknown inputs {names - cells.keys()} in {formula!r}")
        excel = re.sub(r"[A-Za-z_]\w*", lambda m: cells[m.group()], formula)
        ws.cell(row, 1, o["label"])
        c = ws.cell(row, 2, f"={excel}")
        c.number_format = '"$"#,##0' if o["format"] == "money" else '#,##0" hours"'
        c.font = bold
        row += 1
    row += 1
    for note in [
        f"From the PathMode playbook: https://pathmode.com/playbooks/{item['slug']}/ (checked {checked}).",
        "Measure the 'with the assistant' numbers yourself, in the playbook's test. Don't take anyone's word for them.",
    ]:
        ws.cell(row, 1, note).alignment = Alignment(wrap_text=True)
        row += 1
    ws.column_dimensions["A"].width = 78
    ws.column_dimensions["B"].width = 16
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def flow_text(site: Path, name: str) -> str:
    """A flow diagram partial's text version (the "As text:" part of its comment), for readers who get text."""
    html = (site / "src/_includes/partials" / f"{name}-flow.njk").read_text()
    text = re.search(r"As text[^:]*:\n(.*?)\n-#\}", html, flags=re.S)
    if not text:
        raise ValueError(f"{name}-flow.njk has no 'As text:' version")
    return text.group(1).strip()


def page_markdown(page: str, item: dict, instructions: str, repo: str, site: Path) -> str:
    """The page source as plain Markdown: Nunjucks includes and variables replaced with their content."""
    body = re.sub(r"^---\n(?:.*?\n)?---\n", "", page, flags=re.S)
    calc = ["| Your numbers | Example |", "|---|---:|"]
    calc += [f"| {i['label']} | {i['value']} |" for i in item["cost"]["inputs"]]
    calc += ["", "| Result | Formula |", "|---|---|"]
    calc += [f"| {o['label']} | `{o['formula']}` |" for o in item["cost"]["outputs"]]
    body = body.replace('{% include "partials/cost-calculator.njk" %}', "\n".join(calc))
    body = re.sub(r'\{% include "playbooks/[\w-]+-instructions\.md" %\}', lambda _: instructions.strip(), body)
    body = re.sub(
        r'\{% include "playbooks/([\w-]+)-build-prompt\.md" %\}',
        lambda m: (ROOT / m.group(1) / "build-prompt.md").read_text().strip(),
        body,
    )
    body = re.sub(r'\{% include "partials/([\w-]+)-flow\.njk" %\}', lambda m: flow_text(site, m.group(1)), body)
    body = body.replace("{{ playbooks.repo }}", repo)
    body = re.sub(r"</?details>|<summary>.*?</summary>", "", body)
    body = body.replace("](/", "](https://pathmode.com/").replace('="/', '="https://pathmode.com/')
    if "{%" in body or "{{" in body:
        raise ValueError(f"{item['slug']}: unreplaced template code in the page")
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def for_your_ai(item: dict, page_md: str, instructions: str, readme: str, checked: str) -> str:
    return "\n".join(
        [
            f"# {item['title']}: a PathMode playbook, for your AI",
            "",
            "This file holds everything in one PathMode playbook: the page, the assistant instructions, and the README",
            "for the working code. Load it into ChatGPT, Claude, Gemini or Copilot and ask it to help you apply the",
            f"playbook to your own business. Page: https://pathmode.com/playbooks/{item['slug']}/. Vendor details "
            f"checked {checked}; menus change, so check them on screen.",
            "",
            f"**The problem:** {item['problem']}",
            "",
            f"**The playbook:** {item['summary']}",
            "",
            "---",
            "",
            page_md,
            "",
            "---",
            "",
            "# The instructions, to paste into an assistant",
            "",
            instructions.strip(),
            "",
            "---",
            "",
            "# The built version: README",
            "",
            readme.strip(),
            "",
            "---",
            "",
            "From PathMode (https://pathmode.com), by Zack Watts. Free to use and share under CC BY 4.0, with credit.",
            "",
        ]
    )


def dashboard(folder: Path, slug: str, path: Path) -> None:
    """The worked example's dashboard, from replaying the recorded model run on the sample data."""
    with tempfile.TemporaryDirectory() as tmp:
        script = folder / f"{slug.replace('-', '_')}.py"
        replay = folder / "sample-data" / "recorded-run.json"
        subprocess.run(
            [sys.executable, str(script), "--sample", "--replay", str(replay), "--out", tmp],
            check=True,
            capture_output=True,
        )
        shutil.copy(Path(tmp) / "dashboard.html", path)


def sample_zip(folder: Path, path: Path) -> None:
    """The sample files in a fixed order with fixed timestamps, so the zip only changes when they do."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                info = zipfile.ZipInfo(str(Path("summit-files") / f.relative_to(folder)), (2025, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--site", type=Path, required=True, help="path to the pathmode site repository")
    args = p.parse_args()
    data = json.loads((args.site / "src/_data/playbooks.json").read_text())
    for item in data["items"]:
        slug = item["slug"]
        folder = ROOT / slug
        instructions = (folder / "instructions.md").read_text()
        readme = (folder / "README.md").read_text()
        page = (args.site / "src/playbooks" / f"{slug}.md").read_text()
        out = args.site / "src/assets/downloads/playbooks" / slug
        out.mkdir(parents=True, exist_ok=True)
        include = args.site / "src/_includes/playbooks" / f"{slug}-instructions.md"
        include.parent.mkdir(parents=True, exist_ok=True)
        include.write_text(instructions)
        (out / f"{slug}-instructions.md").write_text(instructions)
        worksheet(item, out / f"{slug}-cost-worksheet.xlsx", data["checked"])
        md = page_markdown(page, item, instructions, data["repo"], args.site)
        (out / f"{slug}-for-your-ai.md").write_text(for_your_ai(item, md, instructions, readme, data["checked"]))
        made = "instructions, worksheet, for-your-ai"
        prompt = folder / "build-prompt.md"
        if prompt.exists():
            (args.site / "src/_includes/playbooks" / f"{slug}-build-prompt.md").write_text(prompt.read_text())
            (out / f"{slug}-build-prompt.md").write_text(prompt.read_text())
            made += ", build prompt"
        if item.get("dashboard"):
            dashboard(folder, slug, out / f"{slug}-dashboard.html")
            made += ", dashboard"
        if item.get("sample"):
            sample_zip(folder / "sample-data", out / f"{slug}-summit-files.zip")
            made += ", Summit files"
        print(f"{slug}: {made}")


if __name__ == "__main__":
    main()
