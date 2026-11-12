# Bud and Doris Farms: bookkeeping repo

Plain-text books in [Beancount](https://beancount.github.io/) for a Washington State
DBA sole proprietorship that files **Schedule F**. The farm grows apricots (bearing,
with sales), young plum trees (not yet bearing) and a trial haskap planting.

The owner is a data engineer, not an accountant. Explain accounting choices in
plain words, briefly.

## Layout

- `main.beancount`: entry point (options and includes)
- `ledger/accounts.beancount`: chart of accounts. Every Income/Expenses account
  has `schedf:` metadata naming its Schedule F line.
- `ledger/opening-balances.beancount`: balances at 2026-01-01, plus balance assertions
- `ledger/<year>.beancount`: one file per year, transactions in date order
- `receipts/<year>/`: receipt images, named `YYYY-MM-DD-vendor-amount.ext`
- `scripts/schedule_f.py`: year-end rollup by Schedule F line
- `queries/`: saved bean-query queries

## Recording a receipt or expense (the main job)

When the owner sends a receipt photo or describes a purchase or sale:

1. **Read it.** Date, vendor, total, tax, and the line items when they matter for
   classification. If anything is unreadable or ambiguous, ask. Never guess an amount.
2. **Ask how it was paid** if it isn't clear. The owner's payment methods:
   - **CVB business debit card, ending 5662** (preferred) -> `Assets:Bank:CVB-Business-Checking`
   - **CVB personal debit card, Visa ending 9463** (used in 2026 while the business card was
     deactivated) -> `Equity:Owner:Contributions:CVB-Personal-Debit`
   - **Personal credit card, Mastercard ending 8274** (occasional larger buys) ->
     `Equity:Owner:Contributions:Personal-Credit-Card`
   - **Personal cash** -> `Equity:Owner:Contributions:Cash`
   Match the card's last 4 digits on the receipt; ask if they don't match one of these.
   Personal accounts are not tracked in these books. Interest or fees on the
   personal credit card are not farm expenses. If the farm pays the owner back
   for personal-card purchases, debit `Equity:Owner:Draws`.
3. **Classify** using the account descriptions in `ledger/accounts.beancount`.
   Split a receipt across accounts when it mixes categories. If an item is
   personal, leave it out of the farm books and say so.
4. **Show the proposed entry and wait for a yes.** Nothing is written until the
   owner confirms. One short line of reasoning per non-obvious choice.
5. **Write it.** Insert it in date order in `ledger/<year>.beancount` with
   `receipt:` metadata. If the image exists as a file in the session, copy it to
   `receipts/<year>/` under the naming convention. If it's only visible in the
   chat, say the image wasn't saved and record `receipt: "phone"`.
6. **Verify.** Run `bean-check main.beancount`. It must pass.
7. **Commit and push.** Message: `Add <vendor> <date> <amount>`. Batch several
   receipts from one sitting into one commit if the owner prefers.

Use the `!` flag instead of `*` for anything uncertain, and put the question in a
`note:` metadata line. Never invent transactions, amounts or dates.

## Capital items: flag, don't expense

Fruit trees take years to bear, and costs for trees, plantings, irrigation and
equipment are often **capitalized and depreciated**, not deducted right away.
(Rules involved: depreciation, the de minimis safe harbor, and IRC §263A
pre-productive period costs for crops that take more than 2 years to bear.)

- Tree and plant purchases for the orchard go to `Assets:Farm:Orchard:<crop>`
  with the `!` flag, not `Expenses:Farm:Seeds-Plants`.
- Equipment or irrigation over about $2,500 per item goes to
  `Assets:Farm:Equipment` or `Assets:Farm:Irrigation` with the `!` flag.
- Tell the owner to confirm the treatment with a tax preparer. Don't give
  confident tax conclusions on these.

## Washington State notes

- No state income tax. The **B&O tax** may apply to sales, and farmers selling
  their own produce get several exemptions. Record sales with `channel:`
  metadata (`wholesale`, `retail-stand`, `market`, `u-pick`) so this can be
  sorted out later.
- A WA **farmer's sales tax exemption certificate** can exempt qualifying
  purchases. Tag such receipts with `wa_exempt: TRUE`.

## Rules

- Keep `Expenses:Uncategorized` empty by year-end.
- Add a new account only with the owner's OK, with a `schedf:` line and a
  description, in `ledger/accounts.beancount`.
- Don't edit past committed entries silently. Show the diff first.
- Treat all of this data as private.

## Commands

```
pip install -r requirements.txt
bean-check main.beancount
fava main.beancount
python scripts/schedule_f.py main.beancount 2026
bean-query main.beancount "$(cat queries/expenses-by-month.bql)"
```
