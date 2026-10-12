from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.financials import Account, JournalEntry, JournalEntryLine
from app.models.vouchers import Voucher
from app.models.invoices import Invoice
import datetime

class ReportingService:
    def __init__(self, db: Session):
        self.db = db

    def get_general_journal(self, start_date, end_date):
        """كشف دفتر اليومية: جميع القيود مرتبة زمنياً"""
        entries = self.db.query(JournalEntry).filter(
            JournalEntry.date >= start_date, 
            JournalEntry.date <= end_date
        ).order_by(JournalEntry.date.asc()).all()
        
        report = []
        for entry in entries:
            report.append({
                "date": entry.date,
                "ref": entry.reference_no,
                "desc": entry.description,
                "lines": [
                    {"account": line.account.name_ar, "debit": line.debit, "credit": line.credit}
                    for line in entry.lines
                ]
            })
        return report

    def get_general_ledger(self, account_id, start_date, end_date):
        """كشف دفتر الأستاذ: حركة حساب معين"""
        lines = self.db.query(JournalEntryLine).join(JournalEntry).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntry.date >= start_date,
            JournalEntry.date <= end_date
        ).order_by(JournalEntry.date.asc()).all()
        
        balance = 0
        report = []
        for line in lines:
            balance += (line.debit - line.credit)
            report.append({
                "date": line.entry.date,
                "ref": line.entry.reference_no,
                "desc": line.entry.description,
                "debit": line.debit,
                "credit": line.credit,
                "balance": balance
            })
        return report

    def get_trial_balance(self):
        """ميزان المراجعة: إجمالي المدين والدائن لكل حساب"""
        results = self.db.query(
            Account.id, 
            Account.name_ar, 
            func.sum(JournalEntryLine.debit).label("total_debit"), 
            func.sum(JournalEntryLine.credit).label("total_credit")
        ).join(JournalEntryLine, Account.id == JournalEntryLine.account_id)\
         .group_by(Account.id).all()
        
        return [{"account": r[1], "debit": r[2] or 0, "credit": r[3] or 0, "net": (r[2] or 0) - (r[3] or 0)} for r in results]
