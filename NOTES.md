# Accounting Notes & Technical Decisions

## 1. Net Income for Q1 2026 (2026-01-01 to 2026-03-31)

**Net Income:** `-$44,480.14` (Net loss of **$44,480.14**, displayed in accounting format as **`($44,480.14)`**).

### Financial Statement Breakdown

```
Revenue
  4000 Product Revenue                               $35,650.75
  4100 Subscription Revenue                            $3,000.00
  4900 Sales Returns & Discounts                       ($800.25)
Total Revenue                                        $37,850.50

Cost of Goods Sold
  5000 Cost of Goods Sold                            $14,272.75
Total Cost of Goods Sold                             $14,272.75

Gross Profit                                         $23,577.75

Operating Expenses
  6000 Salaries                                      $55,500.00
  6100 Rent                                           $9,000.00
  6200 Software                                       $1,099.97
  6300 Marketing (legacy)                             $2,500.10
Total Operating Expenses                             $68,100.07

Operating Income                                    ($44,522.32)

Other Income
  7000 Interest Income                                   $42.18
Total Other Income                                       $42.18

Net Income                                          ($44,480.14)
```

---

## 2. Key Decisions & Assumptions About the Data

1. **Lifecycle Status Filtering (`posted` vs `draft` / `void`):**
   - Only journal entries with `status: "posted"` are included in financial statements.
   - `draft` entries (e.g., `JE-019`, Q1 bonus accrual of $5,000 pending approval) are omitted because they have not been approved into the books.
   - `void` entries (e.g., `JE-009`, duplicate product sale of $8,200; `JE-025`, returned check of $3,200) are cancelled entries kept for audit trails but carry zero balance effect.

2. **Inactive Accounts (`is_active: false`):**
   - Account `6300 Marketing (legacy)` has `is_active: false`. As defined in the accounting primer, inactive denotes an account closed to *new* postings today. Past posted activity (`JE-008` for $2,500.10) is historical fact and must appear on the income statement for that period.

3. **Contra-Revenue (`4900 Sales Returns & Discounts`):**
   - Contra-revenue carries a debit-normal balance, offsetting gross revenue.
   - On the statement, it is shown under Revenue as `($800.25)`. The Revenue section subtotal ($37,850.50) sums gross revenue and contra-revenue directly, matching GAAP Net Revenue.

4. **Expense Account Credits (Vendor Refunds):**
   - In `JE-020`, Software (6200) received a credit of $100.00 for vendor overbilling. For debit-normal expense accounts, credits reduce the net expense from $1,199.97 to $1,099.97.

5. **Date Filtering Boundaries:**
   - Filtering is inclusive: `start <= entry.date <= end`. E.g., `JE-007` on `2026-01-01` (Rent $9,000) and `JE-023` on `2026-03-31` (Interest $42.18) are included in Q1. Out-of-period entries `JE-001` (2025-12-15) and `JE-024` (2026-04-01) are excluded.

6. **Exact Decimals & Money:**
   - Python's standard library `decimal.Decimal` is used throughout the accounting engine. All JSON amounts and UI displays avoid binary floating-point arithmetic (IEEE-754) to eliminate rounding drift.

---

## 3. How We Verified the Numbers

1. **Ledger Integrity:** Wrote an automated verification script confirming that total debits equal total credits for every journal entry in `ledger.json`.
2. **Independent Manual Reconciliation:** Traced and summed every journal entry by hand and T-accounts for Q1 2026, cross-referencing account subtype classifications.
3. **Automated Test Suite (17 pytest tests):**
   - Full Q1 2026 net income and section subtotal tests.
   - Inactive account inclusion and vendor credit reduction tests.
   - Draft and void exclusion regression tests.
   - Date range boundary inclusivity and invalid date validation tests.

---

## 4. Where AI Helped vs Where It Was Untrusted / Wrong

- **Where AI helped:** Boilerplate speed: rapidly generating the FastAPI application shell, Pydantic schemas, HTML table layout, and test scaffolds.
- **Where AI was wrong / untrusted:**
  - When doing informal mental arithmetic, LLMs frequently make simple addition mistakes in cents (e.g., adding `.97 + .10` and writing `.97`, losing 10 cents and reporting Net Income as `-$44,480.04` instead of `-$44,480.14`). Exact Python `Decimal` computations caught this immediately.
  - LLMs often hallucinate how contra-revenue should be displayed (either placing it into operating expenses or adding it to revenue). Human verification ensured it is correctly presented as a contra line reducing revenue.

---

## 5. What to Do Next With More Time

1. **Comparative Statements:** Add side-by-side columns (e.g., Q1 2026 vs prior quarter or prior year) with dollar and percentage variance analysis.
2. **Drill-down to General Ledger:** Clicking an account line reveals a slide-out drawer listing every underlying journal entry and memo for full audit traceability.
3. **Export Package:** Export to CSV, XLSX, and PDF for executive and audit presentations.
4. **Balance Sheet & Cash Flow:** Implement the remaining financial statements from the same general ledger data.
