"""
Test cases for Purchase Service API
Base URL: http://localhost:8001
"""

import pytest
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8001"
PURCHASES_URL = f"{BASE_URL}/purchases"

PURCHASE_ID = "PO-TEST-001"
PURCHASE_ID_2 = "PO-TEST-002"

SAMPLE_PURCHASE = {
    "purchase_id": PURCHASE_ID,
    "vendor_name": "Test Vendor",
    "purchase_datetime": "2026-03-08T10:00:00Z",
    "created_by": "tester",
    "items": [
        {"item_id": "ITEM-001", "item_name": "Widget A", "purchase_item_qty": 10},
        {"item_id": "ITEM-002", "item_name": "Widget B", "purchase_item_qty": 5},
    ],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# @pytest.fixture(autouse=True)
# def cleanup():
#     """Delete test purchases before and after each test."""
#     for pid in [PURCHASE_ID, PURCHASE_ID_2]:
#         requests.delete(f"{PURCHASES_URL}/{pid}")
#     yield
#     for pid in [PURCHASE_ID, PURCHASE_ID_2]:
#         requests.delete(f"{PURCHASES_URL}/{pid}")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /purchases/  — Create Purchase
# ---------------------------------------------------------------------------

class TestCreatePurchase:
    def test_create_purchase_success(self):
        resp = requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        assert resp.status_code == 201
        data = resp.json()
        assert data["purchase_id"] == PURCHASE_ID
        assert data["vendor_name"] == "Test Vendor"
        assert data["created_by"] == "tester"
        assert len(data["items"]) == 2

    def test_create_purchase_default_created_by(self):
        payload = {**SAMPLE_PURCHASE, "purchase_id": PURCHASE_ID_2}
        payload.pop("created_by", None)
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["created_by"] == "system"

    def test_create_purchase_duplicate_id(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        assert resp.status_code == 400
        assert PURCHASE_ID in resp.json()["detail"]

    def test_create_purchase_missing_purchase_id(self):
        payload = {k: v for k, v in SAMPLE_PURCHASE.items() if k != "purchase_id"}
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_missing_vendor_name(self):
        payload = {k: v for k, v in SAMPLE_PURCHASE.items() if k != "vendor_name"}
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_missing_purchase_datetime(self):
        payload = {k: v for k, v in SAMPLE_PURCHASE.items() if k != "purchase_datetime"}
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_empty_items_list(self):
        payload = {**SAMPLE_PURCHASE, "items": []}
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_item_zero_qty(self):
        payload = {
            **SAMPLE_PURCHASE,
            "items": [{"item_id": "ITEM-X", "item_name": "Bad Item", "purchase_item_qty": 0}],
        }
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_item_negative_qty(self):
        payload = {
            **SAMPLE_PURCHASE,
            "items": [{"item_id": "ITEM-X", "item_name": "Bad Item", "purchase_item_qty": -5}],
        }
        resp = requests.post(PURCHASES_URL + "/", json=payload)
        assert resp.status_code == 422

    def test_create_purchase_response_has_audit_fields(self):
        resp = requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        assert resp.status_code == 201
        data = resp.json()
        for field in ["created_date", "updated_date", "created_by", "updated_by"]:
            assert field in data

    def test_create_purchase_items_have_audit_fields(self):
        resp = requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        for field in ["created_date", "updated_date", "created_by", "updated_by"]:
            assert field in item


# ---------------------------------------------------------------------------
# GET /purchases/{purchase_id}  — Get Purchase
# ---------------------------------------------------------------------------

class TestGetPurchase:
    def test_get_existing_purchase(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.get(f"{PURCHASES_URL}/{PURCHASE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["purchase_id"] == PURCHASE_ID
        assert data["vendor_name"] == "Test Vendor"
        assert len(data["items"]) == 2

    def test_get_nonexistent_purchase(self):
        resp = requests.get(f"{PURCHASES_URL}/NONEXISTENT-999")
        assert resp.status_code == 404

    def test_get_purchase_items_detail(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.get(f"{PURCHASES_URL}/{PURCHASE_ID}")
        items = resp.json()["items"]
        item_ids = {i["item_id"] for i in items}
        assert "ITEM-001" in item_ids
        assert "ITEM-002" in item_ids


# ---------------------------------------------------------------------------
# PUT /purchases/{purchase_id}  — Update Purchase
# ---------------------------------------------------------------------------

class TestUpdatePurchase:
    def setup_method(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)

    def test_update_vendor_name(self):
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"vendor_name": "Updated Vendor", "updated_by": "editor"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vendor_name"] == "Updated Vendor"
        assert data["updated_by"] == "editor"

    def test_update_purchase_datetime(self):
        new_dt = "2026-06-01T08:30:00Z"
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"purchase_datetime": new_dt},
        )
        assert resp.status_code == 200
        assert "2026-06-01" in resp.json()["purchase_datetime"]

    def test_update_items_replaces_all(self):
        new_items = [{"item_id": "ITEM-NEW", "item_name": "New Widget", "purchase_item_qty": 20}]
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"items": new_items},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["item_id"] == "ITEM-NEW"

    def test_update_partial_fields_only(self):
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"vendor_name": "Partial Update"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vendor_name"] == "Partial Update"
        assert len(data["items"]) == 2  # items unchanged

    def test_update_nonexistent_purchase(self):
        resp = requests.put(
            f"{PURCHASES_URL}/NONEXISTENT-999",
            json={"vendor_name": "Ghost"},
        )
        assert resp.status_code == 404

    def test_update_sets_updated_by_default(self):
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"vendor_name": "X"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated_by"] == "system"

    def test_update_item_zero_qty_rejected(self):
        resp = requests.put(
            f"{PURCHASES_URL}/{PURCHASE_ID}",
            json={"items": [{"item_id": "X", "item_name": "X", "purchase_item_qty": 0}]},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /purchases/{purchase_id}  — Delete Purchase
# ---------------------------------------------------------------------------

class TestDeletePurchase:
    def test_delete_existing_purchase(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.delete(f"{PURCHASES_URL}/{PURCHASE_ID}")
        assert resp.status_code == 204

    def test_delete_removes_purchase(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        requests.delete(f"{PURCHASES_URL}/{PURCHASE_ID}")
        resp = requests.get(f"{PURCHASES_URL}/{PURCHASE_ID}")
        assert resp.status_code == 404

    def test_delete_nonexistent_purchase(self):
        resp = requests.delete(f"{PURCHASES_URL}/NONEXISTENT-999")
        assert resp.status_code == 404

    def test_delete_cascade_removes_items(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        requests.delete(f"{PURCHASES_URL}/{PURCHASE_ID}")
        # Re-create with same ID to confirm items are gone (not duplicated)
        resp = requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        assert resp.status_code == 201
        assert len(resp.json()["items"]) == 2


# ---------------------------------------------------------------------------
# GET /purchases/  — List Purchases
# ---------------------------------------------------------------------------

class TestListPurchases:
    def test_list_returns_paginated_response(self):
        resp = requests.get(PURCHASES_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["total", "page", "page_size", "items"]:
            assert field in data

    def test_list_default_pagination(self):
        resp = requests.get(PURCHASES_URL + "/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_includes_created_purchase(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.get(PURCHASES_URL + "/")
        ids = [p["purchase_id"] for p in resp.json()["items"]]
        assert PURCHASE_ID in ids

    def test_list_custom_page_size(self):
        resp = requests.get(PURCHASES_URL + "/", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 5

    def test_list_page_size_exceeds_max(self):
        resp = requests.get(PURCHASES_URL + "/", params={"page_size": 101})
        assert resp.status_code == 422

    def test_list_page_zero_rejected(self):
        resp = requests.get(PURCHASES_URL + "/", params={"page": 0})
        assert resp.status_code == 422

    def test_list_items_contain_required_fields(self):
        requests.post(PURCHASES_URL + "/", json=SAMPLE_PURCHASE)
        resp = requests.get(PURCHASES_URL + "/")
        items = resp.json()["items"]
        assert len(items) > 0
        for item in items:
            for field in ["purchase_id", "vendor_name", "purchase_datetime"]:
                assert field in item

    def test_list_second_page_offset(self):
        for i in range(3):
            p = {**SAMPLE_PURCHASE, "purchase_id": f"PO-PAGE-{i:03d}"}
            requests.post(PURCHASES_URL + "/", json=p)

        resp = requests.get(PURCHASES_URL + "/", params={"page": 1, "page_size": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["items"]) <= 2

        # cleanup extra test purchases
        for i in range(3):
            requests.delete(f"{PURCHASES_URL}/PO-PAGE-{i:03d}")
