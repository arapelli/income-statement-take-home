from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "company": "Northwind Coffee Roasters",
    }


def test_api_income_statement_default():
    response = client.get("/income-statement")
    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Northwind Coffee Roasters"
    assert data["currency"] == "USD"
    assert data["period"]["start"] == "2026-01-01"
    assert data["period"]["end"] == "2026-03-31"
    assert data["sections"]["revenue"]["subtotal"] == "37850.50"
    assert data["sections"]["cost_of_goods_sold"]["subtotal"] == "14272.75"
    assert data["sections"]["gross_profit"] == "23577.75"
    assert data["sections"]["operating_expenses"]["subtotal"] == "68100.07"
    assert data["sections"]["operating_income"] == "-44522.32"
    assert data["sections"]["other_income"]["subtotal"] == "42.18"
    assert data["sections"]["net_income"] == "-44480.14"


def test_api_income_statement_explicit_dates():
    response = client.get(
        "/income-statement",
        params={"start": "2026-01-01", "end": "2026-01-31"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"]["start"] == "2026-01-01"
    assert data["period"]["end"] == "2026-01-31"
    # Jan revenue: 12450.75 (JE-002) + 1000.00 (JE-005) = 13450.75
    assert data["sections"]["revenue"]["subtotal"] == "13450.75"
    # Jan COGS: 4980.30 (JE-003)
    assert data["sections"]["cost_of_goods_sold"]["subtotal"] == "4980.30"
    # Gross profit: 13450.75 - 4980.30 = 8470.45
    assert data["sections"]["gross_profit"] == "8470.45"


def test_api_single_date_start_only():
    response = client.get(
        "/income-statement",
        params={"start": "2026-01-05"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"]["start"] == "2026-01-05"
    assert data["period"]["end"] == "2026-01-05"
    # On 2026-01-05: JE-002 (Product rev 12450.75) and JE-003 (COGS 4980.30)
    assert data["sections"]["revenue"]["subtotal"] == "12450.75"
    assert data["sections"]["cost_of_goods_sold"]["subtotal"] == "4980.30"
    assert data["sections"]["gross_profit"] == "7470.45"


def test_api_single_date_end_only():
    response = client.get(
        "/income-statement",
        params={"end": "2026-01-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"]["start"] == "2026-01-01"
    assert data["period"]["end"] == "2026-01-01"
    # On 2026-01-01: JE-007 (Rent 9000.00)
    assert data["sections"]["operating_expenses"]["subtotal"] == "9000.00"
    assert data["sections"]["net_income"] == "-9000.00"


def test_api_invalid_date_format():
    response = client.get(
        "/income-statement",
        params={"start": "01-01-2026", "end": "2026-03-31"},
    )
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_api_invalid_calendar_date():
    response = client.get(
        "/income-statement",
        params={"start": "2026-02-31", "end": "2026-03-31"},
    )
    assert response.status_code == 400
    assert "Invalid date format or calendar date" in response.json()["detail"]


def test_api_leap_year_rejection():
    # 2026 is not a leap year, Feb 29 does not exist
    response = client.get(
        "/income-statement",
        params={"start": "2026-02-29", "end": "2026-03-31"},
    )
    assert response.status_code == 400
    assert "Invalid date format or calendar date" in response.json()["detail"]


def test_api_start_after_end():
    response = client.get(
        "/income-statement",
        params={"start": "2026-03-31", "end": "2026-01-01"},
    )
    assert response.status_code == 400
    assert "cannot be after end date" in response.json()["detail"]


def test_api_include_zeros():
    # Single day with only Rent 9000.00
    res_no_zeros = client.get(
        "/income-statement",
        params={"start": "2026-01-01", "end": "2026-01-01", "include_zeros": False},
    )
    assert len(res_no_zeros.json()["sections"]["revenue"]["accounts"]) == 0

    res_with_zeros = client.get(
        "/income-statement",
        params={"start": "2026-01-01", "end": "2026-01-01", "include_zeros": True},
    )
    # Should show revenue accounts with 0.00
    rev_accounts = res_with_zeros.json()["sections"]["revenue"]["accounts"]
    assert len(rev_accounts) > 0
    assert all(acc["amount"] == "0.00" for acc in rev_accounts)


def test_api_all_activity_full_ledger():
    response = client.get(
        "/income-statement",
        params={"start": "2025-12-15", "end": "2026-04-01"},
    )
    assert response.status_code == 200
    data = response.json()
    # All activity includes JE-001 (Dec 2025, 5000) and JE-024 (Apr 2026, 9100)
    # Total product revenue = 35650.75 + 5000 + 9100 = 49750.75
    prod_rev = [
        acc for acc in data["sections"]["revenue"]["accounts"] if acc["number"] == "4000"
    ][0]
    assert prod_rev["amount"] == "49750.75"


def test_frontend_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "Northwind Coffee Roasters" in html
    assert "Income Statement" in html
    assert "$37,850.50" in html
    assert "$14,272.75" in html
    assert "$23,577.75" in html
    assert "$68,100.07" in html
    assert "($44,522.32)" in html
    assert "$42.18" in html
    assert "($44,480.14)" in html


def test_frontend_with_error():
    response = client.get("/?start=2026-03-31&end=2026-01-01")
    assert response.status_code == 200
    html = response.text
    assert "Start date (2026-03-31) cannot be after end date (2026-01-01)" in html
