from app.models.financials import JournalEntry, JournalEntryLine
from app.models.banking import Check, CheckStatus
from app.services.accounting_engine import create_accounting_entry
from sqlalchemy.orm import Session

class BankingService:
    def __init__(self, db: Session):
        self.db = db

    def receive_check(self, check_no, amount, currency, due_date, contact_id, bank_acc_id, rate=1.0):
        # Create Check record
        check = Check(
            check_number=check_no,
            amount=amount,
            currency=currency,
            due_date=due_date,
            status=CheckStatus.UNDER_COLLECTION,
            type='Incoming',
            contact_id=contact_id,
            account_id=bank_acc_id,
            exchange_rate=rate
        )
        self.db.add(check)
        self.db.flush()

        # Accounting: Debit "Checks under collection", Credit "Customer"
        lines = [
            {'account_id': 1115, 'debit': amount * rate, 'credit': 0}, # Checks under collection account
            {'account_id': 112, 'debit': 0, 'credit': amount * rate}    # Customer account
        ]
        create_accounting_entry(self.db, f"Received Check {check_no}", check_no, lines, currency, rate)
        self.db.commit()
        return check.id

    def clear_check(self, check_id, actual_rate=None):
        check = self.db.query(Check).filter(Check.id == check_id).first()
        if not check: return None
        
        rate = actual_rate if actual_rate else check.exchange_rate
        
        # Update status
        check.status = CheckStatus.PAID
        
        # Accounting: Debit "Bank", Credit "Checks under collection"
        lines = [
            {'account_id': 1113, 'debit': check.amount * rate, 'credit': 0}, # Bank account
            {'account_id': 1115, 'debit': 0, 'credit': check.amount * check.exchange_rate} # Original value
        ]
        
        # Handle Exchange Difference
        diff = (check.amount * rate) - (check.amount * check.exchange_rate)
        if abs(diff) > 0.01:
            if diff > 0: # Gain
                lines[-1]['credit'] += diff # Adjust the credit line to balance
                # Or separate it:
                # lines.append({'account_id': 42, 'debit': 0, 'credit': diff}) # Currency Gain
            else: # Loss
                lines.append({'account_id': 53, 'debit': abs(diff), 'credit': 0}) # Currency Loss
                # Correcting previous line to balance
                lines[-1]['credit'] -= abs(diff) # this logic needs careful adjustment for double entry
        
        # Simplified fix for double entry:
        final_lines = [
            {'account_id': 1113, 'debit': check.amount * rate, 'credit': 0},
            {'account_id': 1115, 'debit': 0, 'credit': check.amount * check.exchange_rate},
        ]
        balance_diff = (check.amount * rate) - (check.amount * check.exchange_rate)
        if balance_diff > 0:
            final_lines.append({'account_id': 42, 'debit': 0, 'credit': balance_diff}) # Gain
        elif balance_diff < 0:
            final_lines.append({'account_id': 53, 'debit': abs(balance_diff), 'credit': 0}) # Loss

        create_accounting_entry(self.db, f"Cleared Check {check.check_number}", check.check_number, final_lines)
        self.db.commit()
        return True
