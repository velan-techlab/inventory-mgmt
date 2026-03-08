from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any


class PurchaseDetailCreate(BaseModel):
    item_id: str = Field(..., description="Unique item identifier")
    item_name: str = Field(..., description="Name of the item")
    purchase_item_qty: int = Field(..., gt=0, description="Quantity purchased")


class PurchaseDetailResponse(BaseModel):
    item_id: str
    item_name: str
    purchase_item_qty: int
    created_date: datetime
    updated_date: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


class PurchaseCreate(BaseModel):
    purchase_id: str = Field(..., description="Unique purchase identifier")
    vendor_name: str = Field(..., description="Name of the vendor")
    purchase_datetime: datetime = Field(..., description="Date and time of the purchase")
    created_by: Optional[str] = Field(default="system", description="User who created the record")
    items: List[PurchaseDetailCreate] = Field(..., min_length=1, description="List of purchased items")


class PurchaseUpdate(BaseModel):
    vendor_name: Optional[str] = Field(None, description="Name of the vendor")
    purchase_datetime: Optional[datetime] = Field(None, description="Date and time of the purchase")
    updated_by: Optional[str] = Field(default="system", description="User who updated the record")
    items: Optional[List[PurchaseDetailCreate]] = Field(None, description="Updated list of items")


class PurchaseApprove(BaseModel):
    approved_by: Optional[str] = Field(default="system", description="User approving the purchase")


class PurchaseResponse(BaseModel):
    purchase_id: str
    vendor_name: str
    purchase_datetime: datetime
    is_approved: bool
    approved_date: Optional[datetime]
    approved_by: Optional[str]
    created_date: datetime
    updated_date: datetime
    created_by: str
    updated_by: str
    items: List[PurchaseDetailResponse]

    class Config:
        from_attributes = True


class PurchaseListResponse(BaseModel):
    purchase_id: str
    vendor_name: str
    purchase_datetime: datetime

    class Config:
        from_attributes = True


class PaginatedPurchaseResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PurchaseListResponse]
