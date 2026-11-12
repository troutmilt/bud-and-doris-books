#!/usr/bin/env python3
"""Roll up a year of farm income and expenses by Schedule F line.

Usage: python scripts/schedule_f.py main.beancount 2026

Each Income/Expenses account declares its Schedule F line with `schedf:`
metadata on its `open` directive (see ledger/accounts.beancount).
"""
import datetime
import sys
from collections import defaultdict
from decimal import Decimal

from beancount import loader
from beancount.core import data


def line_sort_key(line):
    digits = "".join(c for c in line if c.isdigit())
    return (int(digits) if digits else 999, line)


def main(path, year):
    entries, errors, _ = loader.load_file(path)
    if errors:
        loader.printer.print_errors(errors, file=sys.stderr)
        sys.exit("Fix the ledger errors above first (bean-check main.beancount).")

    start, end = datetime.date(year, 1, 1), datetime.date(year + 1, 1, 1)
    line_of = {
        e.account: e.meta.get("schedf")
        for e in entries
        if isinstance(e, data.Open)
    }

    by_line = defaultdict(lambda: defaultdict(Decimal))
    unmapped = defaultdict(Decimal)
    flagged = 0
    for e in entries:
        if not isinstance(e, data.Transaction) or not (start <= e.date < end):
            continue
        if e.flag == "!":
            flagged += 1
        for p in e.postings:
            if not p.account.startswith(("Income:", "Expenses:")):
                continue
            # Income is negative in Beancount; flip so the report shows positives.
            amt = -p.units.number if p.account.startswith("Income:") else p.units.number
            line = line_of.get(p.account)
            if line:
                by_line[line][p.account] += amt
            else:
                unmapped[p.account] += amt

    income = sum(sum(a.values()) for l, a in by_line.items() if any(k.startswith("Income:") for k in a))
    expenses = sum(sum(a.values()) for l, a in by_line.items() if any(k.startswith("Expenses:") for k in a))

    print(f"Bud and Doris Farms: Schedule F worksheet, tax year {year}\n")
    for line in sorted(by_line, key=line_sort_key):
        accounts = by_line[line]
        print(f"Line {line:>6}  {sum(accounts.values()):>12,.2f}")
        for acct, amt in sorted(accounts.items()):
            print(f"            {amt:>12,.2f}  {acct}")
    print(f"\nGross farm income (Part I):   {income:>12,.2f}")
    print(f"Total expenses (Part II):     {expenses:>12,.2f}")
    print(f"Net farm profit (loss):       {income - expenses:>12,.2f}")

    if unmapped:
        print("\nWARNING: accounts with no schedf: line:")
        for acct, amt in unmapped.items():
            print(f"  {amt:>12,.2f}  {acct}")
    if "REVIEW" in by_line:
        print("\nWARNING: Expenses:Uncategorized is not empty. Classify those before filing.")
    if flagged:
        print(f"\nWARNING: {flagged} transaction(s) flagged '!' for review.")
    print("\nThis is a worksheet for you or your preparer, not a filed return.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]))
