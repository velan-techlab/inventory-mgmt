import logging
import requests as http_requests

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Purchase, PurchaseDetail
from schemas import (
    PurchaseCreate, PurchaseUpdate, PurchaseApprove, PurchaseResponse,
    PurchaseListResponse, PaginatedPurchaseResponse,
)

STOCK_SERVICE_URL = "http://localhost:8000"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseResponse, status_code=201)
def create_purchase(payload: PurchaseCreate, db: Session = Depends(get_db)):
    logger.info("Creating purchase with id '%s'", payload.purchase_id)
    try:
        existing = db.query(Purchase).filter(Purchase.purchase_id == payload.purchase_id).first()
        if existing:
            logger.debug("Purchase with id '%s' already exists", payload.purchase_id)
            raise HTTPException(status_code=400, detail=f"Purchase with id '{payload.purchase_id}' already exists")

        now = datetime.utcnow()
        created_by = payload.created_by or "system"

        purchase = Purchase(
            purchase_id=payload.purchase_id,
            vendor_name=payload.vendor_name,
            purchase_datetime=payload.purchase_datetime,
            created_by=created_by,
            updated_by=created_by,
            created_date=now,
            updated_date=now,
        )
        db.add(purchase)

        for item in payload.items:
            detail = PurchaseDetail(
                item_id=item.item_id,
                purchase_id=payload.purchase_id,
                item_name=item.item_name,
                purchase_item_qty=item.purchase_item_qty,
                created_by=created_by,
                updated_by=created_by,
                created_date=now,
                updated_date=now,
            )
            db.add(detail)

        db.commit()
        db.refresh(purchase)
        logger.info("Purchase '%s' created successfully with %d items", purchase.purchase_id, len(purchase.items))
        return purchase
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while creating purchase '%s'", payload.purchase_id)
        raise


@router.put("/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(purchase_id: str, payload: PurchaseUpdate, db: Session = Depends(get_db)):
    logger.info("Updating purchase '%s'", purchase_id)
    try:
        purchase = db.query(Purchase).filter(Purchase.purchase_id == purchase_id).first()
        if not purchase:
            logger.debug("Purchase '%s' not found for update", purchase_id)
            raise HTTPException(status_code=404, detail=f"Purchase with id '{purchase_id}' not found")

        if payload.vendor_name is not None:
            purchase.vendor_name = payload.vendor_name
        if payload.purchase_datetime is not None:
            purchase.purchase_datetime = payload.purchase_datetime

        updated_by = payload.updated_by or "system"
        now = datetime.utcnow()
        purchase.updated_by = updated_by
        purchase.updated_date = now

        if payload.items is not None:
            db.query(PurchaseDetail).filter(PurchaseDetail.purchase_id == purchase_id).delete()
            for item in payload.items:
                detail = PurchaseDetail(
                    item_id=item.item_id,
                    purchase_id=purchase_id,
                    item_name=item.item_name,
                    purchase_item_qty=item.purchase_item_qty,
                    created_by=updated_by,
                    updated_by=updated_by,
                    created_date=now,
                    updated_date=now,
                )
                db.add(detail)

        db.commit()
        db.refresh(purchase)
        logger.info("Purchase '%s' updated successfully", purchase_id)
        return purchase
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while updating purchase '%s'", purchase_id)
        raise


@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(purchase_id: str, db: Session = Depends(get_db)):
    logger.info("Deleting purchase '%s'", purchase_id)
    try:
        purchase = db.query(Purchase).filter(Purchase.purchase_id == purchase_id).first()
        if not purchase:
            logger.debug("Purchase '%s' not found for deletion", purchase_id)
            raise HTTPException(status_code=404, detail=f"Purchase with id '{purchase_id}' not found")

        db.delete(purchase)
        db.commit()
        logger.info("Purchase '%s' and its details deleted successfully", purchase_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while deleting purchase '%s'", purchase_id)
        raise


@router.get("/", response_model=PaginatedPurchaseResponse)
def list_purchases(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    logger.debug("Listing purchases - page=%d, page_size=%d", page, page_size)
    try:
        total = db.query(Purchase).count()
        offset = (page - 1) * page_size
        purchases = db.query(Purchase).offset(offset).limit(page_size).all()
        logger.info("Returning %d/%d purchases (page %d)", len(purchases), total, page)
        return PaginatedPurchaseResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[PurchaseListResponse.model_validate(p) for p in purchases],
        )
    except Exception:
        logger.exception("Unexpected error while listing purchases")
        raise


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(purchase_id: str, db: Session = Depends(get_db)):
    logger.debug("Fetching purchase '%s'", purchase_id)
    try:
        purchase = db.query(Purchase).filter(Purchase.purchase_id == purchase_id).first()
        if not purchase:
            logger.error("Purchase '%s' not found", purchase_id)
            raise HTTPException(status_code=404, detail=f"Purchase with id '{purchase_id}' not found")
        logger.info("Purchase '%s' retrieved successfully", purchase_id)
        return purchase
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while fetching purchase '%s'", purchase_id)
        raise


@router.post("/{purchase_id}/approve", response_model=PurchaseResponse)
def approve_purchase(purchase_id: str, payload: PurchaseApprove, db: Session = Depends(get_db)):
    logger.info("Approving purchase '%s'", purchase_id)
    try:
        purchase = db.query(Purchase).filter(Purchase.purchase_id == purchase_id).first()
        if not purchase:
            logger.error("Purchase '%s' not found for approval", purchase_id)
            raise HTTPException(status_code=404, detail=f"Purchase with id '{purchase_id}' not found")

        if purchase.is_approved:
            logger.debug("Purchase '%s' is already approved", purchase_id)
            raise HTTPException(status_code=400, detail=f"Purchase '{purchase_id}' is already approved")

        approved_by = payload.approved_by or "system"
        now = datetime.utcnow()

        for item in purchase.items:
            stock_payload = {
                "qty": item.purchase_item_qty,
                "updated_by": approved_by,
            }
            try:
                resp = http_requests.patch(
                    f"{STOCK_SERVICE_URL}/stocks/{item.item_id}/add",
                    json=stock_payload,
                    timeout=5,
                )
                resp.raise_for_status()
                logger.info(
                    "Stock updated for item '%s' (+%d) via stock service",
                    item.item_id, item.purchase_item_qty,
                )
            except http_requests.RequestException as exc:
                logger.error(
                    "Failed to update stock for item '%s': %s", item.item_id, exc
                )
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to update stock for item '{item.item_id}': {exc}",
                )

        purchase.is_approved = True
        purchase.approved_date = now
        purchase.approved_by = approved_by
        purchase.updated_by = approved_by
        purchase.updated_date = now

        db.commit()
        db.refresh(purchase)
        logger.info("Purchase '%s' approved successfully by '%s'", purchase_id, approved_by)
        return purchase
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while approving purchase '%s'", purchase_id)
        raise
