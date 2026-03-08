from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class Purchase(Base):
    __tablename__ = "purchase"

    purchase_id = Column(String, primary_key=True, index=True)
    vendor_name = Column(String, nullable=False)
    purchase_datetime = Column(DateTime, nullable=False)
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_date = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String, nullable=False, default="system")
    updated_by = Column(String, nullable=False, default="system")

    items = relationship("PurchaseDetail", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseDetail(Base):
    __tablename__ = "purchasedetails"

    item_id = Column(String, primary_key=True, index=True)
    purchase_id = Column(String, ForeignKey("purchase.purchase_id"), nullable=False)
    item_name = Column(String, nullable=False)
    purchase_item_qty = Column(Integer, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String, nullable=False, default="system")
    updated_by = Column(String, nullable=False, default="system")

    purchase = relationship("Purchase", back_populates="items")
