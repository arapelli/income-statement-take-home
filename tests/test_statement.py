import pytest
from app.ledger import load_ledger
from app.statement import generate_income_statement


@pytest.fixture
def ledger():
    return load_ledger()


def test_q1_2026_income_statement(ledger):
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-01-01",
        end="2026-03-31",
    )

    # Metadata
    assert statement.company == "Northwind Coffee Roasters"
    assert statement.currency == "USD"
    assert statement.period.start == "2026-01-01"
    assert statement.period.end == "2026-03-31"

    # 1. Revenue
    rev = statement.sections.revenue
    assert rev.title == "Revenue"
    assert rev.subtotal == "37850.50"
    rev_map = {acc.number: acc.amount for acc in rev.accounts}
    assert rev_map["4000"] == "35650.75"
    assert rev_map["4100"] == "3000.00"
    assert rev_map["4900"] == "-800.25"  # Contra revenue offset

    # 2. Cost of goods sold
    cogs = statement.sections.cost_of_goods_sold
    assert cogs.title == "Cost of goods sold"
    assert cogs.subtotal == "14272.75"
    assert cogs.accounts[0].number == "5000"
    assert cogs.accounts[0].amount == "14272.75"

    # 3. Gross profit (37850.50 - 14272.75)
    assert statement.sections.gross_profit == "23577.75"

    # 4. Operating expenses
    opex = statement.sections.operating_expenses
    assert opex.title == "Operating expenses"
    assert opex.subtotal == "68100.07"
    opex_map = {acc.number: acc.amount for acc in opex.accounts}
    assert opex_map["6000"] == "55500.00"  # Salaries (3 x 18500)
    assert opex_map["6100"] == "9000.00"   # Rent
    assert opex_map["6200"] == "1099.97"   # Software (1199.97 - 100 refund)
    assert opex_map["6300"] == "2500.10"   # Marketing (legacy, inactive)

    # 5. Operating income (23577.75 - 68100.07)
    assert statement.sections.operating_income == "-44522.32"

    # 6. Other income
    other = statement.sections.other_income
    assert other.title == "Other income"
    assert other.subtotal == "42.18"
    assert other.accounts[0].number == "7000"
    assert other.accounts[0].amount == "42.18"

    # 7. Net income (-44522.32 + 42.18)
    assert statement.sections.net_income == "-44480.14"


def test_excludes_draft_entries(ledger):
    # JE-019 is a draft entry for a $5,000 bonus on 2026-03-15 to 6000 Salaries.
    # If drafts were mistakenly included, March salaries would be 23500 instead of 18500.
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-03-01",
        end="2026-03-31",
    )
    salaries = [
        acc for acc in statement.sections.operating_expenses.accounts if acc.number == "6000"
    ][0]
    assert salaries.amount == "18500.00"


def test_excludes_void_entries(ledger):
    # JE-009 was a void duplicate entry on 2026-02-03 for 8200.00 product revenue.
    # JE-010 was the posted entry for 8200.00.
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-02-01",
        end="2026-02-28",
    )
    prod_rev = [
        acc for acc in statement.sections.revenue.accounts if acc.number == "4000"
    ][0]
    assert prod_rev.amount == "8200.00"


def test_date_boundary_inclusivity(ledger):
    # JE-007 is on 2026-01-01 (Rent 9000.00)
    statement_start = generate_income_statement(
        ledger=ledger,
        start="2026-01-01",
        end="2026-01-01",
    )
    assert statement_start.sections.operating_expenses.subtotal == "9000.00"
    assert statement_start.sections.net_income == "-9000.00"

    # JE-023 is on 2026-03-31 (Interest 42.18)
    statement_end = generate_income_statement(
        ledger=ledger,
        start="2026-03-31",
        end="2026-03-31",
    )
    assert statement_end.sections.other_income.subtotal == "42.18"


def test_excludes_out_of_range_entries(ledger):
    # JE-001 (2025-12-15) and JE-024 (2026-04-01) should not be in Q1
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-01-01",
        end="2026-03-31",
    )
    prod_rev = [
        acc for acc in statement.sections.revenue.accounts if acc.number == "4000"
    ][0]
    # Sum of JE-002 (12450.75) + JE-010 (8200.00) + JE-016 (15000.00) = 35650.75
    assert prod_rev.amount == "35650.75"


def test_inactive_accounts_included_if_posted(ledger):
    # Account 6300 is inactive (is_active: False), but JE-008 posted 2500.10 to it.
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-01-01",
        end="2026-01-31",
    )
    mkt = [
        acc for acc in statement.sections.operating_expenses.accounts if acc.number == "6300"
    ][0]
    assert mkt.name == "Marketing (legacy)"
    assert mkt.amount == "2500.10"


def test_expense_credit_reduction(ledger):
    # JE-018 debited 6200 Software by 1199.97
    # JE-020 credited 6200 Software by 100.00
    statement = generate_income_statement(
        ledger=ledger,
        start="2026-03-01",
        end="2026-03-31",
    )
    software = [
        acc for acc in statement.sections.operating_expenses.accounts if acc.number == "6200"
    ][0]
    assert software.amount == "1099.97"


def test_invalid_date_range_raises_error(ledger):
    with pytest.raises(ValueError, match="Start date .* cannot be after end date"):
        generate_income_statement(
            ledger=ledger,
            start="2026-03-31",
            end="2026-01-01",
        )


def test_empty_period_returns_zeroes(ledger):
    statement = generate_income_statement(
        ledger=ledger,
        start="2024-01-01",
        end="2024-01-31",
    )
    assert statement.sections.revenue.subtotal == "0.00"
    assert statement.sections.cost_of_goods_sold.subtotal == "0.00"
    assert statement.sections.gross_profit == "0.00"
    assert statement.sections.operating_expenses.subtotal == "0.00"
    assert statement.sections.operating_income == "0.00"
    assert statement.sections.other_income.subtotal == "0.00"
    assert statement.sections.net_income == "0.00"
    assert len(statement.sections.revenue.accounts) == 0
