from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base


class Sales(Base):
    __tablename__ = "sales"

    sale_id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    sale_datetime = Column(DateTime, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String, nullable=False, default="system")
    updated_by = Column(String, nullable=False, default="system")
    status = Column(String, nullable=False, default="pending")
    approved_date = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)

    items = relationship("SalesDetail", back_populates="sale", cascade="all, delete-orphan")


class SalesDetail(Base):
    __tablename__ = "salesdetails"

    item_id = Column(String, primary_key=True)
    sale_id = Column(String, ForeignKey("sales.sale_id"), primary_key=True)
    item_name = Column(String, nullable=False)
    sales_item_qty = Column(Integer, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String, nullable=False, default="system")
    updated_by = Column(String, nullable=False, default="system")

    sale = relationship("Sales", back_populates="items")
