import datetime
from sqlalchemy.orm import Session
from app.models.financials import JournalEntry, JournalEntryLine, Base
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Adding Loan model to a new file app/models/loans.py
# (Normally we'd import Base from financials)

class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False) # Annual rate e.g. 0.05 for 5%
    term_months = Column(Integer, nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    loan_type = Column(String(50)) # 'Fixed', 'Reducing'
    status = Column(String(20), default='Active') # 'Active', 'Paid'

class LoanPaymentSchedule(Base):
    __tablename__ = 'loan_payment_schedules'
    id = Column(Integer, primary_key=True)
    loan_id = Column(Integer, ForeignKey('loans.id'))
    payment_number = Column(Integer)
    due_date = Column(DateTime)
    principal_amount = Column(Float)
    interest_amount = Column(Float)
    total_payment = Column(Float)
    is_paid = Column(Integer, default=0) # 0: Unpaid, 1: Paid
