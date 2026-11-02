from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.ledger import load_ledger
from app.models import IncomeStatementResponse
from app.statement import generate_income_statement

app = FastAPI(
    title="Northwind Coffee Roasters Income Statement API",
    description="Serves exact double-entry income statements for any date range.",
    version="1.0.0",
)

# Load ledger at startup
ledger_data = load_ledger()

# Template configuration
templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def format_currency(amount_str: str, currency_symbol: str = "$") -> str:
    """Formats exact decimal string to accountant representation ($X,XXX.XX or ($X,XXX.XX))."""
    if not amount_str:
        return f"{currency_symbol}0.00"
    amount_str = amount_str.strip()
    is_negative = amount_str.startswith("-")
    unsigned = amount_str[1:] if is_negative else amount_str

    if "." in unsigned:
        int_part, frac_part = unsigned.split(".", 1)
    else:
        int_part, frac_part = unsigned, "00"

    frac_part = frac_part.ljust(2, "0")[:2]
    int_with_commas = f"{int(int_part):,}" if int_part else "0"
    formatted = f"{currency_symbol}{int_with_commas}.{frac_part}"

    if is_negative:
        return f"({formatted})"
    return formatted


# Register filter with Jinja2
templates.env.filters["format_currency"] = format_currency


def validate_date(date_str: str, field_name: str) -> None:
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        # Ensure year is formatted as 4 digits
        if f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}" != date_str:
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format or calendar date for {field_name}: '{date_str}'. Expected YYYY-MM-DD.",
        )


@app.get("/health")
def health():
    return {"status": "ok", "company": ledger_data.company}


@app.get("/income-statement", response_model=IncomeStatementResponse)
def get_income_statement(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), inclusive"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD), inclusive"),
    include_zeros: bool = Query(False, description="Include accounts with 0 balance"),
):
    """Generates an Income Statement (P&L) for the specified date range."""
    start_date = start or "2026-01-01"
    end_date = end or "2026-03-31"

    validate_date(start_date, "start")
    validate_date(end_date, "end")

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"start date ({start_date}) cannot be after end date ({end_date})",
        )

    try:
        return generate_income_statement(
            ledger=ledger_data,
            start=start_date,
            end=end_date,
            include_zeros=include_zeros,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    include_zeros: bool = Query(False),
):
    """Renders the accountant-friendly Income Statement UI."""
    start_date = start or "2026-01-01"
    end_date = end or "2026-03-31"
    error: Optional[str] = None
    statement = None

    try:
        validate_date(start_date, "start")
        validate_date(end_date, "end")
        if start_date > end_date:
            raise ValueError(f"Start date ({start_date}) cannot be after end date ({end_date})")

        statement = generate_income_statement(
            ledger=ledger_data,
            start=start_date,
            end=end_date,
            include_zeros=include_zeros,
        )
    except Exception as e:
        error = getattr(e, "detail", str(e))
        # Fall back to default Q1 2026 so statement is still rendered below the error alert
        statement = generate_income_statement(
            ledger=ledger_data,
            start="2026-01-01",
            end="2026-03-31",
            include_zeros=include_zeros,
        )

    return templates.TemplateResponse(
        request=request,
        name="statement.html",
        context={
            "statement": statement,
            "start": start_date,
            "end": end_date,
            "error": error,
            "format_currency": format_currency,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
