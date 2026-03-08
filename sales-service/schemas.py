from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class SalesDetailCreate(BaseModel):
    item_id: str = Field(..., description="Unique item identifier")
    item_name: str = Field(..., description="Name of the item")
    sales_item_qty: int = Field(..., gt=0, description="Quantity sold")


class SalesDetailResponse(BaseModel):
    item_id: str
    item_name: str
    sales_item_qty: int
    created_date: datetime
    updated_date: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


class SalesCreate(BaseModel):
    sale_id: str = Field(..., description="Unique sale identifier")
    customer_name: str = Field(..., description="Name of the customer")
    sale_datetime: datetime = Field(..., description="Date and time of the sale")
    created_by: Optional[str] = Field(default="system", description="User who created the record")
    items: List[SalesDetailCreate] = Field(..., min_length=1, description="List of items in the sale")


class SalesUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, description="Name of the customer")
    sale_datetime: Optional[datetime] = Field(None, description="Date and time of the sale")
    updated_by: Optional[str] = Field(default="system", description="User who updated the record")
    items: Optional[List[SalesDetailCreate]] = Field(None, description="Updated list of items")


class SalesApprove(BaseModel):
    approved_by: Optional[str] = Field(default="system", description="User who approved the sale")


class SalesResponse(BaseModel):
    sale_id: str
    customer_name: str
    sale_datetime: datetime
    created_date: datetime
    updated_date: datetime
    created_by: str
    updated_by: str
    status: str
    approved_date: Optional[datetime]
    approved_by: Optional[str]
    items: List[SalesDetailResponse]

    class Config:
        from_attributes = True


class SalesListResponse(BaseModel):
    sale_id: str
    customer_name: str
    sale_datetime: datetime

    class Config:
        from_attributes = True


class PaginatedSalesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SalesListResponse]
