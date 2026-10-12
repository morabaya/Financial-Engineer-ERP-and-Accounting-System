from app.models.loans import Loan, LoanPaymentSchedule
from app.services.accounting_engine import create_accounting_entry
from sqlalchemy.orm import Session
import datetime

class LoanService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_fixed_payment(self, principal, annual_rate, term_months):
        # Monthly interest rate
        monthly_rate = annual_rate / 12 / 100
        # Payment formula: P * (r(1+r)^n) / ((1+r)^n - 1)
        if monthly_rate == 0:
            return principal / term_months
        
        payment = principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
        return payment

    def create_loan(self, amount, rate, term, loan_type="Fixed", user_id=1):
        loan = Loan(loan_amount=amount, interest_rate=rate, term_months=term, loan_type=loan_type)
        self.db.add(loan)
        self.db.flush()

        monthly_payment = self.calculate_fixed_payment(amount, rate, term)
        
        remaining_balance = amount
        for i in range(1, term + 1):
            interest_payment = remaining_balance * (rate / 12 / 100)
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            due_date = loan.start_date + datetime.timedelta(days=30 * i)
            
            schedule = LoanPaymentSchedule(
                loan_id=loan.id,
                payment_number=i,
                due_date=due_date,
                principal_amount=round(principal_payment, 2),
                interest_amount=round(interest_payment, 2),
                total_payment=round(monthly_payment, 2),
                is_paid=0
            )
            self.db.add(schedule)
        
        self.db.commit()
        return loan.id

    def mark_payment_as_paid(self, schedule_id):
        schedule = self.db.query(LoanPaymentSchedule).filter(LoanPaymentSchedule.id == schedule_id).first()
        if not schedule: return False
        
        schedule.is_paid = 1
        
        # Accounting Entry for Loan Payment:
        # Debit Loan Principal, Debit Interest Expense, Credit Bank/Cash
        lines = [
            {'account_id': 221, 'debit': schedule.principal_amount, 'credit': 0}, # Loan Account
            {'account_id': 53, 'debit': schedule.interest_amount, 'credit': 0}, # Interest Expense
            {'account_id': 1113, 'debit': 0, 'credit': schedule.total_payment} # Bank
        ]
        create_accounting_entry(self.db, f"Loan Payment #{schedule.payment_number}", f"LOAN-PAY-{schedule.id}", lines)
        
        self.db.commit()
        return True
