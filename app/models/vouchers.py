from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.financials import Base
import datetime

class Voucher(Base):
    __tablename__ = 'vouchers'
    id = Column(Integer, primary_key=True)
    voucher_no = Column(String(50), unique=True, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String(20))
    description = Column(String(255))
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="ILS")
    exchange_rate = Column(Float, default=1.0)
    user_id = Column(Integer)
    lines = relationship("VoucherLine", backref="voucher", cascade="all, delete-orphan")

class VoucherLine(Base):
    __tablename__ = 'voucher_lines'
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey('vouchers.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String(50))
    table_name = Column(String(50))
    record_id = Column(Integer)
    old_value = Column(String(1000))
    new_value = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
