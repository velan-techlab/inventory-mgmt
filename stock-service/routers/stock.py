import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database import get_db
from models import Stock
from schemas import StockCreate, StockUpdate, StockResponse, PaginatedStockResponse, StockListResponse, StockAdjust, StockBulkAdjust, StockBulkAdjustResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.post("/", response_model=StockResponse, status_code=201)
def create_stock(payload: StockCreate, db: Session = Depends(get_db)):
    logger.info("Creating stock with id '%s'", payload.stock_id)
    try:
        existing = db.query(Stock).filter(Stock.stock_id == payload.stock_id).first()
        if existing:
            logger.debug("Stock with id '%s' already exists", payload.stock_id)
            raise HTTPException(status_code=400, detail=f"Stock with id '{payload.stock_id}' already exists")

        stock = Stock(
            stock_id=payload.stock_id,
            item_name=payload.item_name,
            current_qty=payload.current_qty,
            created_by=payload.created_by or "system",
            updated_by=payload.created_by or "system",
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow(),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
        logger.info("Stock '%s' created successfully", stock.stock_id)
        return stock
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while creating stock '%s'", payload.stock_id)
        raise


@router.put("/{stock_id}", response_model=StockResponse)
def update_stock(stock_id: str, payload: StockUpdate, db: Session = Depends(get_db)):
    logger.info("Updating stock '%s'", stock_id)
    try:
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            logger.debug("Stock '%s' not found for update", stock_id)
            raise HTTPException(status_code=404, detail=f"Stock with id '{stock_id}' not found")

        if payload.item_name is not None:
            stock.item_name = payload.item_name
        if payload.current_qty is not None:
            stock.current_qty = payload.current_qty

        stock.updated_by = payload.updated_by or "system"
        stock.updated_date = datetime.utcnow()

        db.commit()
        db.refresh(stock)
        logger.info("Stock '%s' updated successfully", stock_id)
        return stock
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while updating stock '%s'", stock_id)
        raise


@router.delete("/{stock_id}", status_code=204)
def delete_stock(stock_id: str, db: Session = Depends(get_db)):
    logger.info("Deleting stock '%s'", stock_id)
    try:
        stock = db.query(Stock).filter(
            (Stock.stock_id == stock_id) | (Stock.item_name == stock_id)
        ).first()
        if not stock:
            logger.debug("Stock '%s' not found for deletion", stock_id)
            raise HTTPException(status_code=404, detail=f"Stock '{stock_id}' not found")

        db.delete(stock)
        db.commit()
        logger.info("Stock '%s' deleted successfully", stock_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while deleting stock '%s'", stock_id)
        raise


@router.get("/", response_model=PaginatedStockResponse)
def list_stocks(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    logger.debug("Listing stocks - page=%d, page_size=%d", page, page_size)
    try:
        total = db.query(Stock).count()
        offset = (page - 1) * page_size
        items = db.query(Stock).offset(offset).limit(page_size).all()
        logger.info("Returning %d/%d stocks (page %d)", len(items), total, page)
        return PaginatedStockResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[StockListResponse.model_validate(item) for item in items],
        )
    except Exception:
        logger.exception("Unexpected error while listing stocks")
        raise


@router.patch("/{stock_id}/add", response_model=StockResponse)
def add_stock(stock_id: str, payload: StockAdjust, db: Session = Depends(get_db)):
    logger.info("Adding %d qty to stock '%s'", payload.qty, stock_id)
    try:
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            logger.error("Stock '%s' not found for add", stock_id)
            raise HTTPException(status_code=404, detail=f"Stock with id '{stock_id}' not found")

        stock.current_qty += payload.qty
        stock.updated_by = payload.updated_by or "system"
        stock.updated_date = datetime.utcnow()

        db.commit()
        db.refresh(stock)
        logger.info("Stock '%s' qty increased by %d, new qty=%d", stock_id, payload.qty, stock.current_qty)
        return stock
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while adding stock qty for '%s'", stock_id)
        raise


@router.patch("/{stock_id}/reduce", response_model=StockResponse)
def reduce_stock(stock_id: str, payload: StockAdjust, db: Session = Depends(get_db)):
    logger.info("Reducing %d qty from stock '%s'", payload.qty, stock_id)
    try:
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            logger.error("Stock '%s' not found for reduce", stock_id)
            raise HTTPException(status_code=404, detail=f"Stock with id '{stock_id}' not found")

        if stock.current_qty < payload.qty:
            logger.error("Insufficient qty for stock '%s': have %d, requested %d", stock_id, stock.current_qty, payload.qty)
            raise HTTPException(status_code=400, detail=f"Insufficient quantity: current={stock.current_qty}, requested={payload.qty}")

        stock.current_qty -= payload.qty
        stock.updated_by = payload.updated_by or "system"
        stock.updated_date = datetime.utcnow()

        db.commit()
        db.refresh(stock)
        logger.info("Stock '%s' qty reduced by %d, new qty=%d", stock_id, payload.qty, stock.current_qty)
        return stock
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while reducing stock qty for '%s'", stock_id)
        raise


@router.patch("/bulk/add", response_model=StockBulkAdjustResult)
def bulk_add_stock(payload: StockBulkAdjust, db: Session = Depends(get_db)):
    logger.info("Bulk add request for %d stocks", len(payload.items))
    success, failed = [], []
    for item in payload.items:
        try:
            stock = db.query(Stock).filter(Stock.stock_id == item.stock_id).first()
            if not stock:
                logger.error("Bulk add: stock '%s' not found", item.stock_id)
                failed.append({"stock_id": item.stock_id, "reason": "not found"})
                continue
            stock.current_qty += item.qty
            stock.updated_by = payload.updated_by or "system"
            stock.updated_date = datetime.utcnow()
            db.commit()
            db.refresh(stock)
            logger.debug("Bulk add: stock '%s' qty increased by %d, new qty=%d", item.stock_id, item.qty, stock.current_qty)
            success.append(StockListResponse.model_validate(stock))
        except Exception:
            db.rollback()
            logger.exception("Bulk add: unexpected error for stock '%s'", item.stock_id)
            failed.append({"stock_id": item.stock_id, "reason": "unexpected error"})
    logger.info("Bulk add complete: %d succeeded, %d failed", len(success), len(failed))
    return StockBulkAdjustResult(success=success, failed=failed)


@router.patch("/bulk/reduce", response_model=StockBulkAdjustResult)
def bulk_reduce_stock(payload: StockBulkAdjust, db: Session = Depends(get_db)):
    logger.info("Bulk reduce request for %d stocks", len(payload.items))
    success, failed = [], []
    for item in payload.items:
        try:
            stock = db.query(Stock).filter(Stock.stock_id == item.stock_id).first()
            if not stock:
                logger.error("Bulk reduce: stock '%s' not found", item.stock_id)
                failed.append({"stock_id": item.stock_id, "reason": "not found"})
                continue
            if stock.current_qty < item.qty:
                logger.error("Bulk reduce: insufficient qty for stock '%s': have %d, requested %d", item.stock_id, stock.current_qty, item.qty)
                failed.append({"stock_id": item.stock_id, "reason": f"insufficient quantity: current={stock.current_qty}, requested={item.qty}"})
                continue
            stock.current_qty -= item.qty
            stock.updated_by = payload.updated_by or "system"
            stock.updated_date = datetime.utcnow()
            db.commit()
            db.refresh(stock)
            logger.debug("Bulk reduce: stock '%s' qty reduced by %d, new qty=%d", item.stock_id, item.qty, stock.current_qty)
            success.append(StockListResponse.model_validate(stock))
        except Exception:
            db.rollback()
            logger.exception("Bulk reduce: unexpected error for stock '%s'", item.stock_id)
            failed.append({"stock_id": item.stock_id, "reason": "unexpected error"})
    logger.info("Bulk reduce complete: %d succeeded, %d failed", len(success), len(failed))
    return StockBulkAdjustResult(success=success, failed=failed)


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: str, db: Session = Depends(get_db)):
    logger.debug("Fetching stock '%s'", stock_id)
    try:
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            logger.error("Stock '%s' not found", stock_id)
            raise HTTPException(status_code=404, detail=f"Stock with id '{stock_id}' not found")
        logger.info("Stock '%s' retrieved successfully", stock_id)
        return stock
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while fetching stock '%s'", stock_id)
        raise
