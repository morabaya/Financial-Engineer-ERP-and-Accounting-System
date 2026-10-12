from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import enum

Base = declarative_base()

class AccountType(enum.Enum):
    ASSET = "أصول"
    LIABILITY = "خصوم"
    EQUITY = "حقوق ملكية"
    REVENUE = "إيرادات"
    EXPENSE = "مصاريف"

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100))
    type = Column(Enum(AccountType), nullable=False)
    parent_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    level = Column(Integer, default=1)
    children = relationship("Account", backref="parent", remote_side=[id])

class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String(255))
    reference_no = Column(String(50))
    currency = Column(String(10), default="ILS")
    exchange_rate = Column(Float, default=1.0)
    lines = relationship("JournalEntryLine", backref="entry", cascade="all, delete-orphan")

class JournalEntryLine(Base):
    __tablename__ = 'journal_entry_lines'
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    account = relationship("Account")
