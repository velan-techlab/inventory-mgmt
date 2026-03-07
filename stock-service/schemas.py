from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class StockCreate(BaseModel):
    stock_id: str = Field(..., description="Unique stock identifier")
    item_name: str = Field(..., description="Name of the stock item")
    current_qty: int = Field(..., ge=0, description="Quantity of the item")
    created_by: Optional[str] = Field(default="system", description="User who created the record")


class StockUpdate(BaseModel):
    item_name: Optional[str] = Field(None, description="Name of the stock item")
    current_qty: Optional[int] = Field(None, ge=0, description="Quantity of the item")
    updated_by: Optional[str] = Field(default="system", description="User who updated the record")


class StockResponse(BaseModel):
    stock_id: str
    item_name: str
    current_qty: int
    created_date: datetime
    updated_date: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    stock_id: str
    item_name: str
    current_qty: int

    class Config:
        from_attributes = True


class PaginatedStockResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[StockListResponse]


class StockAdjust(BaseModel):
    qty: int = Field(..., gt=0, description="Quantity to add or reduce")
    updated_by: Optional[str] = Field(default="system", description="User performing the adjustment")


class StockBulkAdjustItem(BaseModel):
    stock_id: str = Field(..., description="Unique stock identifier")
    qty: int = Field(..., gt=0, description="Quantity to add or reduce")


class StockBulkAdjust(BaseModel):
    items: List[StockBulkAdjustItem] = Field(..., min_length=1, description="List of stock adjustments")
    updated_by: Optional[str] = Field(default="system", description="User performing the adjustment")


class StockBulkAdjustResult(BaseModel):
    success: List[StockListResponse]
    failed: List[dict]
