from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.financials import Base
import datetime

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    invoice_no = Column(String(50), unique=True, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String(30)) # 'Sales', 'Purchase', 'Sales_Return', 'Purchase_Return'
    contact_id = Column(Integer) # Linked to Customer/Vendor
    total_before_tax = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_after_tax = Column(Float, default=0.0)
    currency = Column(String(10), default="ILS")
    exchange_rate = Column(Float, default=1.0)
    user_id = Column(Integer)

    items = relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    item_id = Column(Integer) # Linked to Items table
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.16) # Palestinian VAT 16%
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
