from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.financials import Base
import datetime

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100))
    category_id = Column(Integer)
    unit_id = Column(Integer)
    purchase_price = Column(Float, default=0.0)
    sale_price = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.16)
    current_stock = Column(Float, default=0.0)
    min_stock_level = Column(Float, default=0.0)

class Warehouse(Base):
    __tablename__ = 'warehouses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))

class StockMovement(Base):
    __tablename__ = 'stock_movements'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    quantity = Column(Float, nullable=False) # Positive for In, Negative for Out
    movement_type = Column(String(50)) # 'Purchase', 'Sale', 'Adjustment', 'Transfer'
    reference_no = Column(String(50))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer)
