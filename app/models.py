from typing import List, Literal, Optional
from pydantic import BaseModel

AccountType = Literal['asset', 'liability', 'equity', 'revenue', 'expense']
AccountSubtype = Literal[
    'operating_revenue',
    'contra_revenue',
    'cogs',
    'operating_expense',
    'other_income',
    'balance_sheet',
]
JournalEntryStatus = Literal['posted', 'draft', 'void']


class Account(BaseModel):
    number: str
    name: str
    type: AccountType
    subtype: AccountSubtype
    is_active: bool


class JournalLine(BaseModel):
    account: str
    debit: str
    credit: str


class JournalEntry(BaseModel):
    id: str
    date: str
    status: JournalEntryStatus
    memo: str
    lines: List[JournalLine]


class LedgerData(BaseModel):
    company: str
    currency: str
    accounts: List[Account]
    journal_entries: List[JournalEntry]


class StatementAccountLine(BaseModel):
    number: str
    name: str
    amount: str


class StatementSection(BaseModel):
    title: str
    accounts: List[StatementAccountLine]
    subtotal: str


class Period(BaseModel):
    start: str
    end: str


class StatementSections(BaseModel):
    revenue: StatementSection
    cost_of_goods_sold: StatementSection
    gross_profit: str
    operating_expenses: StatementSection
    operating_income: str
    other_income: StatementSection
    net_income: str


class IncomeStatementResponse(BaseModel):
    company: str
    currency: str
    period: Period
    sections: StatementSections
