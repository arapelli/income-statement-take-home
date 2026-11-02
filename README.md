# Northwind Coffee Roasters — Income Statement Application

A full-stack accounting application that generates exact **Income Statements (Profit & Loss)** from a double-entry general ledger for any date range.

---

## Language & Tool Versions

- **Language:** Python 3.9+ (tested on macOS with Python 3.9.6 and Python 3.12)
- **Backend Framework:** FastAPI (`0.128.8`), Uvicorn (`0.39.0`)
- **Data Validation & Typing:** Pydantic v2 (`2.13.5`), standard library `decimal.Decimal`
- **Frontend / Templating:** Jinja2 (`3.1.6`), HTML5 / CSS3 / Vanilla JS (Tabular Numeral Typography)
- **Testing:** Pytest (`8.4.2`), HTTPX (`0.28.1`)

---

## Quickstart: How to Run on Mac

### 1. Setup Virtual Environment & Install Dependencies

From the project root:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Backend & Frontend

The application is built as a unified FastAPI service serving both the REST API and the accountant-friendly web frontend:

```bash
# Start server with Uvicorn (accessible at http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

*Alternatively, run directly:*
```bash
python3 -m app.main
```

- **Frontend Web UI:** Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Backend JSON API:** [http://localhost:8000/income-statement?start=2026-01-01&end=2026-03-31](http://localhost:8000/income-statement?start=2026-01-01&end=2026-03-31)
- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run the Tests

To run the automated accounting and API test suite:

```bash
pytest
```

---

## API Specification

### `GET /income-statement`

Generates an income statement for a specified date range.

#### Query Parameters:
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `start` | `string` (`YYYY-MM-DD`) | `2026-01-01` | Accounting start date (inclusive) |
| `end` | `string` (`YYYY-MM-DD`) | `2026-03-31` | Accounting end date (inclusive) |
| `include_zeros` | `boolean` | `false` | Include accounts with zero activity in period |

#### Example Response:

```json
{
  "company": "Northwind Coffee Roasters",
  "currency": "USD",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "sections": {
    "revenue": {
      "title": "Revenue",
      "accounts": [
        { "number": "4000", "name": "Product Revenue", "amount": "35650.75" },
        { "number": "4100", "name": "Subscription Revenue", "amount": "3000.00" },
        { "number": "4900", "name": "Sales Returns & Discounts", "amount": "-800.25" }
      ],
      "subtotal": "37850.50"
    },
    "cost_of_goods_sold": {
      "title": "Cost of goods sold",
      "accounts": [
        { "number": "5000", "name": "Cost of Goods Sold", "amount": "14272.75" }
      ],
      "subtotal": "14272.75"
    },
    "gross_profit": "23577.75",
    "operating_expenses": {
      "title": "Operating expenses",
      "accounts": [
        { "number": "6000", "name": "Salaries", "amount": "55500.00" },
        { "number": "6100", "name": "Rent", "amount": "9000.00" },
        { "number": "6200", "name": "Software", "amount": "1099.97" },
        { "number": "6300", "name": "Marketing (legacy)", "amount": "2500.10" }
      ],
      "subtotal": "68100.07"
    },
    "operating_income": "-44522.32",
    "other_income": {
      "title": "Other income",
      "accounts": [
        { "number": "7000", "name": "Interest Income", "amount": "42.18" }
      ],
      "subtotal": "42.18"
    },
    "net_income": "-44480.14"
  }
}
```

---

## Project Structure

```
├── ledger.json               # General ledger data source
├── requirements.txt          # Python dependencies
├── NOTES.md                  # Q1 Net income, design decisions & verification
├── app/
│   ├── __init__.py
│   ├── models.py             # Pydantic data schemas
│   ├── ledger.py             # Ledger loader and account maps
│   ├── statement.py          # Exact Decimal accounting calculation engine
│   ├── main.py               # FastAPI application (endpoints & formatting filters)
│   └── templates/
│       └── statement.html    # Accountant-readable financial statement UI
└── tests/
    ├── __init__.py
    ├── test_statement.py     # Pure accounting tests (Q1 totals, voids, drafts, credits)
    └── test_api.py           # FastAPI integration tests
```

---

## Accounting & Correctness Highlights

1. **Exact Decimals:** Uses Python `decimal.Decimal` throughout. Zero binary floating-point rounding errors.
2. **Double-Entry Status Filtering:** Only `posted` entries affect statements; `draft` (JE-019) and `void` (JE-009, JE-025) are excluded.
3. **Normal Balances:** 
   - Revenue is credit-normal (`credit - debit`).
   - Contra-revenue (`4900 Sales Returns & Discounts`) reduces revenue.
   - Expenses are debit-normal (`debit - credit`). Vendor refunds (`JE-020`) reduce expense balances.
4. **Inactive Accounts:** Historical posted activity on inactive accounts (`6300 Marketing (legacy)`) is properly reported.
5. **Auditor-Grade UI:** Negative numbers in accounting parentheses `($800.25)`, monospace tabular numerals, and double-underline on Net Income.

See [NOTES.md](NOTES.md) for full accounting rationale and Q1 reconciliation.
