from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.financials import Base
import datetime
import enum

class CheckStatus(enum.Enum):
    UNDER_COLLECTION = "تحت التحصيل"
    DUE = "مستحق"
    PAID = "مدفوع"
    RETURNED = "مرتجع"
    ENDORSED = "مجير"

class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)
    check_number = Column(String(50), nullable=False)
    bank_name = Column(String(100))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="ILS")
    exchange_rate = Column(Float, default=1.0)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(CheckStatus), default=CheckStatus.UNDER_COLLECTION)
    type = Column(String(20)) # 'Incoming' (وارد), 'Outgoing' (صادر)
    contact_id = Column(Integer) # Customer/Vendor
    account_id = Column(Integer, ForeignKey('accounts.id')) # Linked Bank/Cash Account
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

class BankReconciliation(Base):
    __tablename__ = 'bank_reconciliations'
    id = Column(Integer, primary_key=True)
    bank_account_id = Column(Integer, ForeignKey('accounts.id'))
    statement_date = Column(DateTime)
    statement_balance = Column(Float)
    book_balance = Column(Float)
    difference = Column(Float)
    user_id = Column(Integer)
