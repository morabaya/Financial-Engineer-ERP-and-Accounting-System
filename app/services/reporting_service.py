from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.financials import Account, JournalEntry, JournalEntryLine, AccountType
from app.models.vouchers import Voucher
from app.models.invoices import Invoice
import datetime

class ReportingService:
    def __init__(self, db: Session):
        self.db = db

    def get_general_journal(self, start_date, end_date):
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
        results = self.db.query(
            Account.id, 
            Account.name_ar, 
            func.sum(JournalEntryLine.debit).label("total_debit"), 
            func.sum(JournalEntryLine.credit).label("total_credit")
        ).join(JournalEntryLine, Account.id == JournalEntryLine.account_id)\
         .group_by(Account.id).all()
        
        return [{"account": r[1], "debit": r[2] or 0, "credit": r[3] or 0, "net": (r[2] or 0) - (r[3] or 0)} for r in results]

    def get_income_statement(self, start_date, end_date):
        """قائمة الدخل: (الإيرادات - المصاريف)"""
        revenue = self.db.query(func.sum(JournalEntryLine.credit - JournalEntryLine.debit))\
            .join(Account).join(JournalEntry).filter(
                Account.type == AccountType.REVENUE,
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date
            ).scalar() or 0
            
        expenses = self.db.query(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))\
            .join(Account).join(JournalEntry).filter(
                Account.type == AccountType.EXPENSE,
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date
            ).scalar() or 0
            
        return {
            "total_revenue": revenue,
            "total_expenses": expenses,
            "net_profit": revenue - expenses
        }

    def get_balance_sheet(self):
        """الميزانية العمومية: (الأصول = الخصوم + حقوق الملكية)"""
        assets = self.db.query(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))\
            .join(Account).filter(Account.type == AccountType.ASSET).scalar() or 0
        liabilities = self.db.query(func.sum(JournalEntryLine.credit - JournalEntryLine.debit))\
            .join(Account).filter(Account.type == AccountType.LIABILITY).scalar() or 0
        equity = self.db.query(func.sum(JournalEntryLine.credit - JournalEntryLine.debit))\
            .join(Account).filter(Account.type == AccountType.EQUITY).scalar() or 0
            
        return {
            "total_assets": assets,
            "total_liabilities": liabilities,
            "total_equity": equity,
            "is_balanced": abs(assets - (liabilities + equity)) < 0.01
        }

    def get_comparative_report(self, account_type, year, months):
        """التقرير المقارن شهر بشهر"""
        report = {}
        for month in months:
            start = datetime.datetime(year, month, 1)
            if month == 12:
                end = datetime.datetime(year + 1, 1, 1)
            else:
                end = datetime.datetime(year, month + 1, 1)
                
            val = self.db.query(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))\
                .join(Account).join(JournalEntry).filter(
                    Account.type == account_type,
                    JournalEntry.date >= start,
                    JournalEntry.date < end
                ).scalar() or 0
            report[f"Month {month}"] = val
        return report
