#!/usr/bin/env python3
"""Export the books as JSON files for the phone dashboard.

Usage: python scripts/export_dashboard.py main.beancount 2026 OUT_DIR

Writes OUT_DIR/{schedf,monthly,flagged,owner,summary}.json, each {rows, meta}.
meta carries this script's own text so the numbers can be traced back.
"""
import datetime
import json
import pathlib
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal

from beancount import loader
from beancount.core import data

SCHEDF_NAMES = {
    "1a": "Sales of products you raised", "4a": "Ag program payments",
    "6a": "Crop insurance", "8": "Other income", "10": "Car and truck",
    "11": "Chemicals", "12": "Conservation", "13": "Custom hire",
    "14": "Depreciation", "17": "Fertilizers and lime", "18": "Freight and trucking",
    "19": "Gasoline, fuel and oil", "20": "Insurance", "21b": "Interest",
    "22": "Labor hired", "24a": "Rent: vehicles and equipment", "24b": "Rent: land",
    "25": "Repairs and maintenance", "26": "Seeds and plants", "27": "Storage",
    "28": "Supplies", "29": "Taxes", "30": "Utilities", "32": "Other expenses",
}


def money(d):
    return float(round(d, 2))


def line_key(line):
    digits = "".join(c for c in line if c.isdigit())
    return (int(digits) if digits else 999, line)


def main(path, year, out_dir):
    entries, errors, _ = loader.load_file(path)
    if errors:
        sys.exit("Ledger has errors; run bean-check first.")
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    start, end = datetime.date(year, 1, 1), datetime.date(year + 1, 1, 1)
    opens = {e.account: e for e in entries if isinstance(e, data.Open)}
    txns = [e for e in entries if isinstance(e, data.Transaction) and start <= e.date < end]

    by_acct = defaultdict(Decimal)
    monthly = defaultdict(lambda: {"income": Decimal(0), "expenses": Decimal(0)})
    owner = defaultdict(Decimal)
    flagged = []
    for t in txns:
        if t.flag == "!":
            amt = sum((abs(p.units.number) for p in t.postings if p.units.number > 0), Decimal(0))
            flagged.append({"date": t.date.isoformat(), "payee": t.payee or "",
                            "what": t.narration, "amount": money(amt),
                            "note": str(t.meta.get("note", ""))})
        for p in t.postings:
            n = p.units.number
            m = t.date.strftime("%Y-%m")
            if p.account.startswith("Income:"):
                by_acct[p.account] += -n
                monthly[m]["income"] += -n
            elif p.account.startswith("Expenses:"):
                by_acct[p.account] += n
                monthly[m]["expenses"] += n
            elif p.account.startswith("Equity:Owner:Contributions"):
                owner["Put in from personal money"] += -n
            elif p.account == "Equity:Owner:Draws":
                owner["Taken out for personal use"] += n
            elif p.account.startswith("Liabilities:Loan"):
                owner["Paid on Kubota loan"] += n

    schedf = []
    for acct, amt in by_acct.items():
        line = str(opens[acct].meta.get("schedf", "")) if acct in opens else ""
        schedf.append({
            "line": line, "line_name": SCHEDF_NAMES.get(line, line),
            "category": acct.split(":")[-1].replace("-", " "),
            "account": acct,
            "section": "Income" if acct.startswith("Income:") else "Expense",
            "amount": money(amt)})
    schedf.sort(key=lambda r: (r["section"] != "Income", line_key(r["line"]), r["account"]))

    months = []
    for i in range(1, 13):
        m = f"{year}-{i:02d}"
        months.append({"month": m, "income": money(monthly[m]["income"]),
                       "expenses": money(monthly[m]["expenses"])})

    bank = Decimal(0)
    for e in entries:
        if isinstance(e, data.Transaction) and e.date < end:
            for p in e.postings:
                if p.account == "Assets:Bank:CVB-Business-Checking":
                    bank += p.units.number
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                text=True, cwd=pathlib.Path(path).parent).stdout.strip()
    except OSError:
        commit = ""
    last = max((t.date for t in txns), default=None)
    summary = [{"as_of": datetime.date.today().isoformat(),
                "last_entry": last.isoformat() if last else "",
                "entries": len(txns), "flagged": len(flagged),
                "business_checking": money(bank), "commit": commit}]

    code = pathlib.Path(__file__).read_text()
    meta = [{"label": "export_dashboard.py", "value": code, "type": "code", "lang": "python"},
            {"label": "Input", "value": f"bud-and-doris-books/{pathlib.Path(path).name} @ {commit}"}]
    for name, rows in [("schedf", schedf), ("monthly", months), ("flagged", flagged),
                       ("owner", [{"item": k, "amount": money(v)} for k, v in owner.items()]),
                       ("summary", summary)]:
        (out / f"{name}.json").write_text(json.dumps({"rows": rows, "meta": meta}, indent=1))
        print(f"{name}.json: {len(rows)} rows")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
