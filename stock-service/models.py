from sqlalchemy import Column, String, Integer, DateTime, func
from database import Base


class Stock(Base):
    __tablename__ = "stocks"

    stock_id = Column(String, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    current_qty = Column(Integer, nullable=False, default=0)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String, nullable=False, default="system")
    updated_by = Column(String, nullable=False, default="system")
