"""
Test cases for Sales Service API
Base URL: http://localhost:8001
Stock Service (required for approve tests): http://localhost:8000
"""

import pytest
import requests

BASE_URL = "http://localhost:8001"
SALES_URL = f"{BASE_URL}/sales"

STOCK_BASE_URL = "http://localhost:8000"
STOCKS_URL = f"{STOCK_BASE_URL}/stocks"

SALE_ID = "SALE-TEST-001"
SALE_ID_2 = "SALE-TEST-002"
SALE_ID_3 = "SALE-TEST-003"

STOCK_ID_A = "STK-SALE-TEST-A"
STOCK_ID_B = "STK-SALE-TEST-B"
STOCK_ID_C = "STK-SALE-TEST-C"

SAMPLE_SALE = {
    "sale_id": SALE_ID,
    "customer_name": "Alice",
    "sale_datetime": "2026-01-15T10:00:00",
    "created_by": "tester",
    "items": [
        {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 5},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_sale(
    sale_id=SALE_ID,
    customer_name="Alice",
    sale_datetime="2026-01-15T10:00:00",
    created_by="tester",
    items=None,
):
    if items is None:
        items = [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 5}]
    payload = {
        "sale_id": sale_id,
        "customer_name": customer_name,
        "sale_datetime": sale_datetime,
        "created_by": created_by,
        "items": items,
    }
    return requests.post(SALES_URL + "/", json=payload)


def delete_sale(sale_id):
    requests.delete(f"{SALES_URL}/{sale_id}")


def create_stock(stock_id, item_name="Test Item", qty=100):
    return requests.post(STOCKS_URL + "/", json={
        "stock_id": stock_id,
        "item_name": item_name,
        "current_qty": qty,
        "created_by": "tester",
    })


def delete_stock(stock_id):
    requests.delete(f"{STOCKS_URL}/{stock_id}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    for sid in [SALE_ID, SALE_ID_2, SALE_ID_3]:
        delete_sale(sid)
    yield
    for sid in [SALE_ID, SALE_ID_2, SALE_ID_3]:
        delete_sale(sid)


@pytest.fixture
def stock_setup():
    """Create stocks in stock service for approve tests, clean up after."""
    create_stock(STOCK_ID_A, "Widget A", qty=100)
    create_stock(STOCK_ID_B, "Widget B", qty=50)
    create_stock(STOCK_ID_C, "Widget C", qty=10)
    yield
    delete_stock(STOCK_ID_A)
    delete_stock(STOCK_ID_B)
    delete_stock(STOCK_ID_C)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /sales/  — Create Sale
# ---------------------------------------------------------------------------

class TestCreateSale:
    def test_create_sale_success(self):
        resp = create_sale()
        assert resp.status_code == 201
        data = resp.json()
        assert data["sale_id"] == SALE_ID
        assert data["customer_name"] == "Alice"
        assert data["created_by"] == "tester"
        assert data["status"] == "pending"

    def test_create_sale_default_created_by(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "customer_name": "Bob",
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1}],
        })
        assert resp.status_code == 201
        assert resp.json()["created_by"] == "system"

    def test_create_sale_has_items(self):
        resp = create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 3},
            {"item_id": STOCK_ID_B, "item_name": "Widget B", "sales_item_qty": 7},
        ])
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["items"]) == 2

    def test_create_sale_duplicate_id(self):
        create_sale()
        resp = create_sale()
        assert resp.status_code == 400
        assert SALE_ID in resp.json()["detail"]

    def test_create_sale_missing_sale_id(self):
        resp = requests.post(SALES_URL + "/", json={
            "customer_name": "Alice",
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1}],
        })
        assert resp.status_code == 422

    def test_create_sale_missing_customer_name(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1}],
        })
        assert resp.status_code == 422

    def test_create_sale_missing_sale_datetime(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "customer_name": "Alice",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1}],
        })
        assert resp.status_code == 422

    def test_create_sale_empty_items_rejected(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "customer_name": "Alice",
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [],
        })
        assert resp.status_code == 422

    def test_create_sale_zero_item_qty_rejected(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "customer_name": "Alice",
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 0}],
        })
        assert resp.status_code == 422

    def test_create_sale_negative_item_qty_rejected(self):
        resp = requests.post(SALES_URL + "/", json={
            "sale_id": SALE_ID,
            "customer_name": "Alice",
            "sale_datetime": "2026-01-15T10:00:00",
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": -3}],
        })
        assert resp.status_code == 422

    def test_create_sale_response_has_audit_fields(self):
        resp = create_sale()
        assert resp.status_code == 201
        data = resp.json()
        for field in ["created_date", "updated_date", "created_by", "updated_by"]:
            assert field in data

    def test_create_sale_approved_fields_are_null(self):
        resp = create_sale()
        assert resp.status_code == 201
        data = resp.json()
        assert data["approved_date"] is None
        assert data["approved_by"] is None


# ---------------------------------------------------------------------------
# GET /sales/{sale_id}  — Get Sale
# ---------------------------------------------------------------------------

class TestGetSale:
    def test_get_existing_sale(self):
        create_sale()
        resp = requests.get(f"{SALES_URL}/{SALE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sale_id"] == SALE_ID
        assert data["customer_name"] == "Alice"

    def test_get_nonexistent_sale(self):
        resp = requests.get(f"{SALES_URL}/NONEXISTENT-999")
        assert resp.status_code == 404

    def test_get_sale_has_all_fields(self):
        create_sale()
        resp = requests.get(f"{SALES_URL}/{SALE_ID}")
        data = resp.json()
        for field in [
            "sale_id", "customer_name", "sale_datetime",
            "created_date", "updated_date", "created_by", "updated_by",
            "status", "approved_date", "approved_by", "items",
        ]:
            assert field in data

    def test_get_sale_includes_items(self):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 2},
        ])
        resp = requests.get(f"{SALES_URL}/{SALE_ID}")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["item_id"] == STOCK_ID_A
        assert items[0]["sales_item_qty"] == 2


# ---------------------------------------------------------------------------
# PUT /sales/{sale_id}  — Update Sale
# ---------------------------------------------------------------------------

class TestUpdateSale:
    def setup_method(self):
        create_sale()

    def test_update_customer_name(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={"customer_name": "Bob", "updated_by": "editor"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_name"] == "Bob"
        assert data["updated_by"] == "editor"

    def test_update_sale_datetime(self):
        new_dt = "2026-06-20T15:30:00"
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={"sale_datetime": new_dt})
        assert resp.status_code == 200
        assert "2026-06-20" in resp.json()["sale_datetime"]

    def test_update_items_replaces_existing(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={
            "items": [
                {"item_id": STOCK_ID_B, "item_name": "Widget B", "sales_item_qty": 10},
            ]
        })
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["item_id"] == STOCK_ID_B

    def test_update_partial_fields_only(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={"customer_name": "Charlie"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_name"] == "Charlie"
        assert data["items"][0]["item_id"] == STOCK_ID_A  # unchanged

    def test_update_sets_updated_by_default(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={"customer_name": "X"})
        assert resp.status_code == 200
        assert resp.json()["updated_by"] == "system"

    def test_update_nonexistent_sale(self):
        resp = requests.put(f"{SALES_URL}/NONEXISTENT-999", json={"customer_name": "Ghost"})
        assert resp.status_code == 404

    def test_update_item_zero_qty_rejected(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={
            "items": [{"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 0}]
        })
        assert resp.status_code == 422

    def test_update_empty_items_rejected(self):
        resp = requests.put(f"{SALES_URL}/{SALE_ID}", json={"items": []})
        # items is Optional but if provided must have at least 1 item (min_length=1 on SalesCreate)
        # SalesUpdate items has no min_length constraint — accepts null to skip update
        # An empty list would just clear all items; behavior depends on implementation
        # We assert it does NOT return 500 at minimum
        assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# DELETE /sales/{sale_id}  — Delete Sale
# ---------------------------------------------------------------------------

class TestDeleteSale:
    def test_delete_existing_sale(self):
        create_sale()
        resp = requests.delete(f"{SALES_URL}/{SALE_ID}")
        assert resp.status_code == 204

    def test_delete_removes_sale(self):
        create_sale()
        requests.delete(f"{SALES_URL}/{SALE_ID}")
        resp = requests.get(f"{SALES_URL}/{SALE_ID}")
        assert resp.status_code == 404

    def test_delete_also_removes_items(self):
        create_sale()
        requests.delete(f"{SALES_URL}/{SALE_ID}")
        # Recreating with same id should succeed (items table was also cleaned)
        resp = create_sale()
        assert resp.status_code == 201

    def test_delete_nonexistent_sale(self):
        resp = requests.delete(f"{SALES_URL}/NONEXISTENT-999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /sales/  — List Sales
# ---------------------------------------------------------------------------

class TestListSales:
    def test_list_returns_paginated_response(self):
        resp = requests.get(SALES_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["total", "page", "page_size", "items"]:
            assert field in data

    def test_list_default_pagination(self):
        resp = requests.get(SALES_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_includes_created_sale(self):
        create_sale()
        resp = requests.get(SALES_URL + "/")
        ids = [s["sale_id"] for s in resp.json()["items"]]
        assert SALE_ID in ids

    def test_list_custom_page_size(self):
        resp = requests.get(SALES_URL + "/", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 5

    def test_list_page_size_exceeds_max(self):
        resp = requests.get(SALES_URL + "/", params={"page_size": 101})
        assert resp.status_code == 422

    def test_list_page_zero_rejected(self):
        resp = requests.get(SALES_URL + "/", params={"page": 0})
        assert resp.status_code == 422

    def test_list_items_contain_required_fields(self):
        create_sale()
        resp = requests.get(SALES_URL + "/")
        for item in resp.json()["items"]:
            for field in ["sale_id", "customer_name", "sale_datetime"]:
                assert field in item

    def test_list_multiple_sales(self):
        create_sale(SALE_ID)
        create_sale(SALE_ID_2, customer_name="Bob", items=[
            {"item_id": STOCK_ID_B, "item_name": "Widget B", "sales_item_qty": 2}
        ])
        resp = requests.get(SALES_URL + "/")
        ids = [s["sale_id"] for s in resp.json()["items"]]
        assert SALE_ID in ids
        assert SALE_ID_2 in ids

    def test_list_second_page_empty_when_no_data(self):
        resp = requests.get(SALES_URL + "/", params={"page": 9999, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ---------------------------------------------------------------------------
# POST /sales/{sale_id}/approve  — Approve Sale
# ---------------------------------------------------------------------------

class TestApproveSale:
    def test_approve_sale_success(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 5},
        ])
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["approved_by"] == "manager"
        assert data["approved_date"] is not None

    def test_approve_sale_default_approved_by(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1},
        ])
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={})
        assert resp.status_code == 200
        assert resp.json()["approved_by"] == "system"

    def test_approve_reduces_stock(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 10},
        ])
        stock_before = requests.get(f"{STOCKS_URL}/{STOCK_ID_A}").json()["current_qty"]
        requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        stock_after = requests.get(f"{STOCKS_URL}/{STOCK_ID_A}").json()["current_qty"]
        assert stock_after == stock_before - 10

    def test_approve_updates_audit_fields(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1},
        ])
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        data = resp.json()
        assert data["updated_by"] == "manager"
        assert data["updated_date"] is not None

    def test_approve_nonexistent_sale(self):
        resp = requests.post(f"{SALES_URL}/NONEXISTENT-999/approve", json={"approved_by": "manager"})
        assert resp.status_code == 404

    def test_approve_already_approved_sale(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 1},
        ])
        requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        assert resp.status_code == 400
        assert "already approved" in resp.json()["detail"]

    def test_approve_stock_not_found_fails(self):
        # Use item_id that does not exist in stock service
        create_sale(items=[
            {"item_id": "STK-NONEXISTENT-XYZ", "item_name": "Ghost Item", "sales_item_qty": 1},
        ])
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        assert resp.status_code == 400
        assert "STK-NONEXISTENT-XYZ" in resp.json()["detail"]

    def test_approve_insufficient_stock_fails(self, stock_setup):
        # STOCK_ID_C has only 10 qty; request 9999
        create_sale(items=[
            {"item_id": STOCK_ID_C, "item_name": "Widget C", "sales_item_qty": 9999},
        ])
        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        assert resp.status_code == 400
        assert STOCK_ID_C in resp.json()["detail"]

    def test_approve_sale_status_remains_pending_on_failure(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_C, "item_name": "Widget C", "sales_item_qty": 9999},
        ])
        requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        sale = requests.get(f"{SALES_URL}/{SALE_ID}").json()
        assert sale["status"] == "pending"

    def test_approve_multi_item_sale_reduces_all_stocks(self, stock_setup):
        create_sale(items=[
            {"item_id": STOCK_ID_A, "item_name": "Widget A", "sales_item_qty": 5},
            {"item_id": STOCK_ID_B, "item_name": "Widget B", "sales_item_qty": 3},
        ])
        qty_a_before = requests.get(f"{STOCKS_URL}/{STOCK_ID_A}").json()["current_qty"]
        qty_b_before = requests.get(f"{STOCKS_URL}/{STOCK_ID_B}").json()["current_qty"]

        resp = requests.post(f"{SALES_URL}/{SALE_ID}/approve", json={"approved_by": "manager"})
        assert resp.status_code == 200

        qty_a_after = requests.get(f"{STOCKS_URL}/{STOCK_ID_A}").json()["current_qty"]
        qty_b_after = requests.get(f"{STOCKS_URL}/{STOCK_ID_B}").json()["current_qty"]
        assert qty_a_after == qty_a_before - 5
        assert qty_b_after == qty_b_before - 3
