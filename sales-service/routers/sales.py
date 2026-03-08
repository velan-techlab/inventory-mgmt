import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Sales, SalesDetail
from schemas import (
    SalesCreate, SalesUpdate, SalesApprove, SalesResponse,
    SalesListResponse, PaginatedSalesResponse,
)

STOCK_SERVICE_URL = os.getenv("STOCK_SERVICE_URL", "http://localhost:8000")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/", response_model=SalesResponse, status_code=201)
def create_sale(payload: SalesCreate, db: Session = Depends(get_db)):
    logger.info("Creating sale with id '%s'", payload.sale_id)
    try:
        existing = db.query(Sales).filter(Sales.sale_id == payload.sale_id).first()
        if existing:
            logger.debug("Sale with id '%s' already exists", payload.sale_id)
            raise HTTPException(status_code=400, detail=f"Sale with id '{payload.sale_id}' already exists")

        now = datetime.utcnow()
        created_by = payload.created_by or "system"

        sale = Sales(
            sale_id=payload.sale_id,
            customer_name=payload.customer_name,
            sale_datetime=payload.sale_datetime,
            created_by=created_by,
            updated_by=created_by,
            created_date=now,
            updated_date=now,
        )
        db.add(sale)

        for item in payload.items:
            detail = SalesDetail(
                item_id=item.item_id,
                sale_id=payload.sale_id,
                item_name=item.item_name,
                sales_item_qty=item.sales_item_qty,
                created_by=created_by,
                updated_by=created_by,
                created_date=now,
                updated_date=now,
            )
            db.add(detail)

        db.commit()
        db.refresh(sale)
        logger.info("Sale '%s' created successfully with %d items", sale.sale_id, len(sale.items))
        return sale
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while creating sale '%s'", payload.sale_id)
        raise


@router.put("/{sale_id}", response_model=SalesResponse)
def update_sale(sale_id: str, payload: SalesUpdate, db: Session = Depends(get_db)):
    logger.info("Updating sale '%s'", sale_id)
    try:
        sale = db.query(Sales).filter(Sales.sale_id == sale_id).first()
        if not sale:
            logger.debug("Sale '%s' not found for update", sale_id)
            raise HTTPException(status_code=404, detail=f"Sale with id '{sale_id}' not found")

        if payload.customer_name is not None:
            sale.customer_name = payload.customer_name
        if payload.sale_datetime is not None:
            sale.sale_datetime = payload.sale_datetime

        updated_by = payload.updated_by or "system"
        now = datetime.utcnow()
        sale.updated_by = updated_by
        sale.updated_date = now

        if payload.items is not None:
            db.query(SalesDetail).filter(SalesDetail.sale_id == sale_id).delete()
            for item in payload.items:
                detail = SalesDetail(
                    item_id=item.item_id,
                    sale_id=sale_id,
                    item_name=item.item_name,
                    sales_item_qty=item.sales_item_qty,
                    created_by=updated_by,
                    updated_by=updated_by,
                    created_date=now,
                    updated_date=now,
                )
                db.add(detail)

        db.commit()
        db.refresh(sale)
        logger.info("Sale '%s' updated successfully", sale_id)
        return sale
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while updating sale '%s'", sale_id)
        raise


@router.delete("/{sale_id}", status_code=204)
def delete_sale(sale_id: str, db: Session = Depends(get_db)):
    logger.info("Deleting sale '%s'", sale_id)
    try:
        sale = db.query(Sales).filter(Sales.sale_id == sale_id).first()
        if not sale:
            logger.debug("Sale '%s' not found for deletion", sale_id)
            raise HTTPException(status_code=404, detail=f"Sale with id '{sale_id}' not found")

        db.delete(sale)
        db.commit()
        logger.info("Sale '%s' and its details deleted successfully", sale_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while deleting sale '%s'", sale_id)
        raise


@router.get("/", response_model=PaginatedSalesResponse)
def list_sales(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    logger.debug("Listing sales - page=%d, page_size=%d", page, page_size)
    try:
        total = db.query(Sales).count()
        offset = (page - 1) * page_size
        sales = db.query(Sales).offset(offset).limit(page_size).all()
        logger.info("Returning %d/%d sales (page %d)", len(sales), total, page)
        return PaginatedSalesResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[SalesListResponse.model_validate(s) for s in sales],
        )
    except Exception:
        logger.exception("Unexpected error while listing sales")
        raise


@router.get("/{sale_id}", response_model=SalesResponse)
def get_sale(sale_id: str, db: Session = Depends(get_db)):
    logger.debug("Fetching sale '%s'", sale_id)
    try:
        sale = db.query(Sales).filter(Sales.sale_id == sale_id).first()
        if not sale:
            logger.error("Sale '%s' not found", sale_id)
            raise HTTPException(status_code=404, detail=f"Sale with id '{sale_id}' not found")
        logger.info("Sale '%s' retrieved successfully", sale_id)
        return sale
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while fetching sale '%s'", sale_id)
        raise


@router.post("/{sale_id}/approve", response_model=SalesResponse)
def approve_sale(sale_id: str, payload: SalesApprove, db: Session = Depends(get_db)):
    logger.info("Approving sale '%s'", sale_id)
    try:
        sale = db.query(Sales).filter(Sales.sale_id == sale_id).first()
        if not sale:
            logger.error("Sale '%s' not found for approval", sale_id)
            raise HTTPException(status_code=404, detail=f"Sale with id '{sale_id}' not found")

        if sale.status == "approved":
            logger.debug("Sale '%s' is already approved", sale_id)
            raise HTTPException(status_code=400, detail=f"Sale '{sale_id}' is already approved")

        approved_by = payload.approved_by or "system"
        bulk_items = [
            {"stock_id": item.item_id, "qty": item.sales_item_qty}
            for item in sale.items
        ]
        bulk_payload = {"items": bulk_items, "updated_by": approved_by}

        logger.debug("Calling stock service bulk reduce for sale '%s' with %d items", sale_id, len(bulk_items))
        try:
            response = httpx.patch(
                f"{STOCK_SERVICE_URL}/stocks/bulk/reduce",
                json=bulk_payload,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Stock service returned error for sale '%s': %s", sale_id, exc.response.text)
            raise HTTPException(status_code=502, detail=f"Stock service error: {exc.response.text}")
        except httpx.RequestError as exc:
            logger.error("Could not reach stock service for sale '%s': %s", sale_id, exc)
            raise HTTPException(status_code=502, detail="Stock service is unavailable")

        result = response.json()
        if result.get("failed"):
            failed_ids = [f["stock_id"] for f in result["failed"]]
            logger.error("Stock reduce failed for items %s in sale '%s'", failed_ids, sale_id)
            raise HTTPException(
                status_code=400,
                detail=f"Stock reduction failed for items: {failed_ids}",
            )

        now = datetime.utcnow()
        sale.status = "approved"
        sale.approved_date = now
        sale.approved_by = approved_by
        sale.updated_by = approved_by
        sale.updated_date = now

        db.commit()
        db.refresh(sale)
        logger.info("Sale '%s' approved successfully by '%s'", sale_id, approved_by)
        return sale
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while approving sale '%s'", sale_id)
        raise
