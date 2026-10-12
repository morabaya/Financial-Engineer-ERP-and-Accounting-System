from app.services.voucher_service import VoucherService
from app.services.invoice_service import InvoiceService
from app.services.reporting_service import ReportingService
from app.services.loan_service import LoanService
from sqlalchemy.orm import Session

class AIFinancialBridge:
    def __init__(self, db: Session):
        self.db = db
        self.vouchers = VoucherService(db)
        self.invoices = InvoiceService(db)
        self.reports = ReportingService(db)
        self.loans = LoanService(db)

    def handle_intent(self, intent, params):
        """
        Handles the intent identified by the LLM and calls the appropriate service.
        Intents examples: 'create_voucher', 'get_report', 'create_loan'
        """
        if intent == "create_voucher":
            return self.vouchers.create_voucher(
                v_type=params.get("type"),
                description=params.get("description"),
                lines_data=params.get("lines"),
                total_amount=params.get("amount"),
                currency=params.get("currency", "ILS"),
                rate=params.get("rate", 1.0)
            )
        
        elif intent == "get_report":
            report_type = params.get("report_type")
            if report_type == "trial_balance":
                return self.reports.get_trial_balance()
            elif report_type == "income_statement":
                return self.reports.get_income_statement(params.get("start"), params.get("end"))
            elif report_type == "comparative":
                return self.reports.get_comparative_report(
                    params.get("account_type"), 
                    params.get("year"), 
                    params.get("months")
                )
        
        elif intent == "create_loan":
            return self.loans.create_loan(
                amount=params.get("amount"),
                rate=params.get("rate"),
                term=params.get("term"),
                loan_type=params.get("type", "Fixed")
            )
        
        return {"error": "Intent not supported or insufficient parameters"}

    def process_natural_language(self, text):
        # In a real implementation, this would call the LLM API (GPT/Claude)
        # to convert the natural language 'text' into (intent, params).
        # For now, we define the structure that the AI will use.
        pass
