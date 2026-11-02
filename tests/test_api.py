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


def test_api_start_after_end():
    response = client.get(
        "/income-statement",
        params={"start": "2026-03-31", "end": "2026-01-01"},
    )
    assert response.status_code == 400
    assert "cannot be after end date" in response.json()["detail"]


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
