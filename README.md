# Bud and Doris Farms: Books

Plain-text bookkeeping for Bud and Doris Farms (WA sole proprietorship, Schedule F),
kept with [Beancount](https://beancount.github.io/) and [Fava](https://beancount.github.io/fava/).

## Setup (Linux)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bean-check main.beancount            # silent = books balance
fava main.beancount                  # http://localhost:5000
python scripts/schedule_f.py main.beancount 2026
```

## Opening the books (Linux)

From anywhere:

```bash
~/Documents/budanddorisfarms/bud-and-doris-books/books.sh
```

It pulls the latest entries from GitHub, sets up the Python tools on first run,
checks that the books balance, and opens Fava in your browser. Ctrl+C stops it.

## Adding entries

Send Claude a receipt photo or a description ("$42 of drip line at the co-op,
farm card"). Claude proposes the entry, waits for your OK, then writes, checks,
commits and pushes. The workflow is in [CLAUDE.md](CLAUDE.md).

## To do

- [ ] Rename bank/card accounts in `ledger/accounts.beancount` to the real ones
- [ ] Fill in 2026-01-01 opening balances
- [ ] Record 2026 receipts
- [ ] (Later) import GnuCash history
