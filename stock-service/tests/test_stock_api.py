"""
Test cases for Stock Service API
Base URL: http://localhost:8000
"""

import pytest
import requests

BASE_URL = "http://localhost:8000"
STOCKS_URL = f"{BASE_URL}/stocks"

STOCK_ID = "STK-TEST-001"
STOCK_ID_2 = "STK-TEST-002"
STOCK_ID_3 = "STK-TEST-003"

SAMPLE_STOCK = {
    "stock_id": STOCK_ID,
    "item_name": "Test Widget",
    "current_qty": 100,
    "created_by": "tester",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_stock(stock_id=STOCK_ID, item_name="Test Widget", qty=100, created_by="tester"):
    payload = {"stock_id": stock_id, "item_name": item_name, "current_qty": qty, "created_by": created_by}
    return requests.post(STOCKS_URL + "/", json=payload)

def delete_stock(stock_id):
    requests.delete(f"{STOCKS_URL}/{stock_id}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    for sid in [STOCK_ID, STOCK_ID_2, STOCK_ID_3]:
        delete_stock(sid)
    yield
    for sid in [STOCK_ID, STOCK_ID_2, STOCK_ID_3]:
        delete_stock(sid)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /stocks/  — Create Stock
# ---------------------------------------------------------------------------

class TestCreateStock:
    def test_create_stock_success(self):
        resp = create_stock()
        assert resp.status_code == 201
        data = resp.json()
        assert data["stock_id"] == STOCK_ID
        assert data["item_name"] == "Test Widget"
        assert data["current_qty"] == 100
        assert data["created_by"] == "tester"

    def test_create_stock_default_created_by(self):
        resp = requests.post(STOCKS_URL + "/", json={
            "stock_id": STOCK_ID, "item_name": "Widget", "current_qty": 10
        })
        assert resp.status_code == 201
        assert resp.json()["created_by"] == "system"

    def test_create_stock_zero_qty_allowed(self):
        resp = requests.post(STOCKS_URL + "/", json={
            "stock_id": STOCK_ID, "item_name": "Widget", "current_qty": 0
        })
        assert resp.status_code == 201
        assert resp.json()["current_qty"] == 0

    def test_create_stock_duplicate_id(self):
        create_stock()
        resp = create_stock()
        assert resp.status_code == 400
        assert STOCK_ID in resp.json()["detail"]

    def test_create_stock_missing_stock_id(self):
        resp = requests.post(STOCKS_URL + "/", json={"item_name": "Widget", "current_qty": 10})
        assert resp.status_code == 422

    def test_create_stock_missing_item_name(self):
        resp = requests.post(STOCKS_URL + "/", json={"stock_id": STOCK_ID, "current_qty": 10})
        assert resp.status_code == 422

    def test_create_stock_missing_current_qty(self):
        resp = requests.post(STOCKS_URL + "/", json={"stock_id": STOCK_ID, "item_name": "Widget"})
        assert resp.status_code == 422

    def test_create_stock_negative_qty_rejected(self):
        resp = requests.post(STOCKS_URL + "/", json={
            "stock_id": STOCK_ID, "item_name": "Widget", "current_qty": -1
        })
        assert resp.status_code == 422

    def test_create_stock_response_has_audit_fields(self):
        resp = create_stock()
        assert resp.status_code == 201
        data = resp.json()
        for field in ["created_date", "updated_date", "created_by", "updated_by"]:
            assert field in data


# ---------------------------------------------------------------------------
# GET /stocks/{stock_id}  — Get Stock
# ---------------------------------------------------------------------------

class TestGetStock:
    def test_get_existing_stock(self):
        create_stock()
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stock_id"] == STOCK_ID
        assert data["item_name"] == "Test Widget"
        assert data["current_qty"] == 100

    def test_get_nonexistent_stock(self):
        resp = requests.get(f"{STOCKS_URL}/NONEXISTENT-999")
        assert resp.status_code == 404

    def test_get_stock_has_all_fields(self):
        create_stock()
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        data = resp.json()
        for field in ["stock_id", "item_name", "current_qty", "created_date", "updated_date", "created_by", "updated_by"]:
            assert field in data


# ---------------------------------------------------------------------------
# PUT /stocks/{stock_id}  — Update Stock
# ---------------------------------------------------------------------------

class TestUpdateStock:
    def setup_method(self):
        create_stock()

    def test_update_item_name(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"item_name": "Updated Widget", "updated_by": "editor"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_name"] == "Updated Widget"
        assert data["updated_by"] == "editor"

    def test_update_current_qty(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"current_qty": 50})
        assert resp.status_code == 200
        assert resp.json()["current_qty"] == 50

    def test_update_qty_to_zero(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"current_qty": 0})
        assert resp.status_code == 200
        assert resp.json()["current_qty"] == 0

    def test_update_negative_qty_rejected(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"current_qty": -5})
        assert resp.status_code == 422

    def test_update_partial_fields_only(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"item_name": "Partial Update"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_name"] == "Partial Update"
        assert data["current_qty"] == 100  # unchanged

    def test_update_nonexistent_stock(self):
        resp = requests.put(f"{STOCKS_URL}/NONEXISTENT-999", json={"item_name": "Ghost"})
        assert resp.status_code == 404

    def test_update_sets_updated_by_default(self):
        resp = requests.put(f"{STOCKS_URL}/{STOCK_ID}", json={"item_name": "X"})
        assert resp.status_code == 200
        assert resp.json()["updated_by"] == "system"


# ---------------------------------------------------------------------------
# DELETE /stocks/{stock_id}  — Delete Stock
# ---------------------------------------------------------------------------

class TestDeleteStock:
    def test_delete_existing_stock(self):
        create_stock()
        resp = requests.delete(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.status_code == 204

    def test_delete_removes_stock(self):
        create_stock()
        requests.delete(f"{STOCKS_URL}/{STOCK_ID}")
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.status_code == 404

    def test_delete_nonexistent_stock(self):
        resp = requests.delete(f"{STOCKS_URL}/NONEXISTENT-999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /stocks/  — List Stocks
# ---------------------------------------------------------------------------

class TestListStocks:
    def test_list_returns_paginated_response(self):
        resp = requests.get(STOCKS_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["total", "page", "page_size", "items"]:
            assert field in data

    def test_list_default_pagination(self):
        resp = requests.get(STOCKS_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_includes_created_stock(self):
        create_stock()
        resp = requests.get(STOCKS_URL + "/")
        ids = [s["stock_id"] for s in resp.json()["items"]]
        assert STOCK_ID in ids

    def test_list_custom_page_size(self):
        resp = requests.get(STOCKS_URL + "/", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 5

    def test_list_page_size_exceeds_max(self):
        resp = requests.get(STOCKS_URL + "/", params={"page_size": 101})
        assert resp.status_code == 422

    def test_list_page_zero_rejected(self):
        resp = requests.get(STOCKS_URL + "/", params={"page": 0})
        assert resp.status_code == 422

    def test_list_items_contain_required_fields(self):
        create_stock()
        resp = requests.get(STOCKS_URL + "/")
        for item in resp.json()["items"]:
            for field in ["stock_id", "item_name", "current_qty"]:
                assert field in item


# ---------------------------------------------------------------------------
# PATCH /stocks/{stock_id}/add  — Add Stock
# ---------------------------------------------------------------------------

class TestAddStock:
    def setup_method(self):
        create_stock(qty=50)

    def test_add_stock_increases_qty(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": 20, "updated_by": "tester"})
        assert resp.status_code == 200
        assert resp.json()["current_qty"] == 70

    def test_add_stock_default_updated_by(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": 10})
        assert resp.status_code == 200
        assert resp.json()["updated_by"] == "system"

    def test_add_stock_zero_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": 0})
        assert resp.status_code == 422

    def test_add_stock_negative_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": -5})
        assert resp.status_code == 422

    def test_add_stock_nonexistent_stock(self):
        resp = requests.patch(f"{STOCKS_URL}/NONEXISTENT-999/add", json={"qty": 10})
        assert resp.status_code == 404

    def test_add_stock_multiple_times(self):
        requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": 10})
        requests.patch(f"{STOCKS_URL}/{STOCK_ID}/add", json={"qty": 15})
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.json()["current_qty"] == 75


# ---------------------------------------------------------------------------
# PATCH /stocks/{stock_id}/reduce  — Reduce Stock
# ---------------------------------------------------------------------------

class TestReduceStock:
    def setup_method(self):
        create_stock(qty=100)

    def test_reduce_stock_decreases_qty(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": 30, "updated_by": "tester"})
        assert resp.status_code == 200
        assert resp.json()["current_qty"] == 70

    def test_reduce_stock_default_updated_by(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": 10})
        assert resp.status_code == 200
        assert resp.json()["updated_by"] == "system"

    def test_reduce_stock_zero_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": 0})
        assert resp.status_code == 422

    def test_reduce_stock_negative_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": -5})
        assert resp.status_code == 422

    def test_reduce_stock_insufficient_qty(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": 200})
        assert resp.status_code == 400

    def test_reduce_stock_exact_qty(self):
        resp = requests.patch(f"{STOCKS_URL}/{STOCK_ID}/reduce", json={"qty": 100})
        assert resp.status_code == 200
        assert resp.json()["current_qty"] == 0

    def test_reduce_stock_nonexistent_stock(self):
        resp = requests.patch(f"{STOCKS_URL}/NONEXISTENT-999/reduce", json={"qty": 10})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /stocks/bulk/add  — Bulk Add Stock
# ---------------------------------------------------------------------------

class TestBulkAddStock:
    def setup_method(self):
        create_stock(STOCK_ID, qty=50)
        create_stock(STOCK_ID_2, item_name="Widget B", qty=30)

    def test_bulk_add_all_success(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/add", json={
            "items": [
                {"stock_id": STOCK_ID, "qty": 10},
                {"stock_id": STOCK_ID_2, "qty": 20},
            ],
            "updated_by": "tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 2
        assert len(data["failed"]) == 0

    def test_bulk_add_partial_failure(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/add", json={
            "items": [
                {"stock_id": STOCK_ID, "qty": 10},
                {"stock_id": "NONEXISTENT-999", "qty": 5},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 1
        assert len(data["failed"]) == 1

    def test_bulk_add_empty_items_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/add", json={"items": []})
        assert resp.status_code == 422

    def test_bulk_add_zero_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/add", json={
            "items": [{"stock_id": STOCK_ID, "qty": 0}]
        })
        assert resp.status_code == 422

    def test_bulk_add_result_has_success_failed_keys(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/add", json={
            "items": [{"stock_id": STOCK_ID, "qty": 5}]
        })
        assert resp.status_code == 200
        assert "success" in resp.json()
        assert "failed" in resp.json()

    def test_bulk_add_updates_qty_correctly(self):
        requests.patch(f"{STOCKS_URL}/bulk/add", json={
            "items": [{"stock_id": STOCK_ID, "qty": 25}]
        })
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.json()["current_qty"] == 75


# ---------------------------------------------------------------------------
# PATCH /stocks/bulk/reduce  — Bulk Reduce Stock
# ---------------------------------------------------------------------------

class TestBulkReduceStock:
    def setup_method(self):
        create_stock(STOCK_ID, qty=100)
        create_stock(STOCK_ID_2, item_name="Widget B", qty=80)

    def test_bulk_reduce_all_success(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/reduce", json={
            "items": [
                {"stock_id": STOCK_ID, "qty": 10},
                {"stock_id": STOCK_ID_2, "qty": 20},
            ],
            "updated_by": "tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 2
        assert len(data["failed"]) == 0

    def test_bulk_reduce_partial_failure_insufficient_qty(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/reduce", json={
            "items": [
                {"stock_id": STOCK_ID, "qty": 10},
                {"stock_id": STOCK_ID_2, "qty": 9999},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 1
        assert len(data["failed"]) == 1

    def test_bulk_reduce_partial_failure_nonexistent(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/reduce", json={
            "items": [
                {"stock_id": STOCK_ID, "qty": 10},
                {"stock_id": "NONEXISTENT-999", "qty": 5},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 1
        assert len(data["failed"]) == 1

    def test_bulk_reduce_empty_items_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/reduce", json={"items": []})
        assert resp.status_code == 422

    def test_bulk_reduce_zero_qty_rejected(self):
        resp = requests.patch(f"{STOCKS_URL}/bulk/reduce", json={
            "items": [{"stock_id": STOCK_ID, "qty": 0}]
        })
        assert resp.status_code == 422

    def test_bulk_reduce_updates_qty_correctly(self):
        requests.patch(f"{STOCKS_URL}/bulk/reduce", json={
            "items": [{"stock_id": STOCK_ID, "qty": 40}]
        })
        resp = requests.get(f"{STOCKS_URL}/{STOCK_ID}")
        assert resp.json()["current_qty"] == 60
