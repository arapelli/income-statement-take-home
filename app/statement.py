from decimal import Decimal
from typing import Dict, List, Tuple
from app.models import (
    Account,
    IncomeStatementResponse,
    LedgerData,
    Period,
    StatementAccountLine,
    StatementSection,
    StatementSections,
)
from app.ledger import build_account_map


def generate_income_statement(
    ledger: LedgerData,
    start: str,
    end: str,
    include_zeros: bool = False,
) -> IncomeStatementResponse:
    """Computes an income statement for Northwind Coffee Roasters for the date range [start, end] (inclusive).

    Accounting Rules Applied:
    1. Double-Entry Lifecycle:
       Only journal entries with status == 'posted' are included.
       Draft entries (pending approval) and Void entries (cancelled) are excluded.
    2. Income Statement Scope:
       Only revenue and expense accounts belong on an income statement.
       Balance sheet accounts (assets, liabilities, equity) are excluded.
    3. Normal Balances:
       - Revenue is credit-normal: net amount = credits - debits.
         Contra-revenue accounts (returns & discounts) naturally produce negative amounts,
         which offset gross revenues directly.
       - Expenses (COGS, Operating Expenses) are debit-normal: net amount = debits - credits.
         Vendor refunds/credits reduce operating expenses.
    4. Exact Decimal Arithmetic:
       All calculations use Python's built-in Decimal class to prevent floating-point drift.
    5. Section Hierarchy:
       Revenue -> Cost of goods sold -> Gross profit -> Operating expenses ->
       Operating income -> Other income -> Net income.
    """
    if start > end:
        raise ValueError(f"Start date ({start}) cannot be after end date ({end})")

    account_map: Dict[str, Account] = build_account_map(ledger.accounts)

    # Initialize zero balances for all revenue and expense accounts
    balances: Dict[str, Decimal] = {
        acc.number: Decimal("0.00")
        for acc in ledger.accounts
        if acc.type in ("revenue", "expense")
    }

    # Filter posted entries in the date range
    posted_entries = [
        entry
        for entry in ledger.journal_entries
        if entry.status == "posted" and start <= entry.date <= end
    ]

    # Accumulate activity for each account
    for entry in posted_entries:
        for line in entry.lines:
            acc = account_map.get(line.account)
            if not acc:
                raise ValueError(
                    f"Entry {entry.id} references unknown account {line.account}"
                )

            # Skip balance sheet accounts
            if acc.subtype == "balance_sheet":
                continue

            debit = Decimal(line.debit)
            credit = Decimal(line.credit)

            if acc.type == "revenue":
                # Revenue: credit increases, debit decreases
                delta = credit - debit
            elif acc.type == "expense":
                # Expense: debit increases, credit decreases
                delta = debit - credit
            else:
                delta = Decimal("0.00")

            balances[acc.number] = balances.get(acc.number, Decimal("0.00")) + delta

    def _build_section(
        title: str, subtypes: List[str]
    ) -> Tuple[StatementSection, Decimal]:
        matching_accounts = [
            acc for acc in ledger.accounts if acc.subtype in subtypes
        ]
        # Sort accounts by account number ascending
        matching_accounts.sort(key=lambda a: a.number)

        lines: List[StatementAccountLine] = []
        subtotal = Decimal("0.00")

        for acc in matching_accounts:
            bal = balances.get(acc.number, Decimal("0.00"))
            if not include_zeros and bal.is_zero():
                continue

            lines.append(
                StatementAccountLine(
                    number=acc.number,
                    name=acc.name,
                    amount=f"{bal:.2f}",
                )
            )
            subtotal += bal

        return (
            StatementSection(
                title=title,
                accounts=lines,
                subtotal=f"{subtotal:.2f}",
            ),
            subtotal,
        )

    # 1. Revenue
    revenue_section, revenue_subtotal = _build_section(
        "Revenue", ["operating_revenue", "contra_revenue"]
    )

    # 2. Cost of goods sold
    cogs_section, cogs_subtotal = _build_section(
        "Cost of goods sold", ["cogs"]
    )

    # 3. Gross profit
    gross_profit = revenue_subtotal - cogs_subtotal

    # 4. Operating expenses
    opex_section, opex_subtotal = _build_section(
        "Operating expenses", ["operating_expense"]
    )

    # 5. Operating income
    operating_income = gross_profit - opex_subtotal

    # 6. Other income
    other_income_section, other_income_subtotal = _build_section(
        "Other income", ["other_income"]
    )

    # 7. Net income
    net_income = operating_income + other_income_subtotal

    return IncomeStatementResponse(
        company=ledger.company,
        currency=ledger.currency,
        period=Period(start=start, end=end),
        sections=StatementSections(
            revenue=revenue_section,
            cost_of_goods_sold=cogs_section,
            gross_profit=f"{gross_profit:.2f}",
            operating_expenses=opex_section,
            operating_income=f"{operating_income:.2f}",
            other_income=other_income_section,
            net_income=f"{net_income:.2f}",
        ),
    )
