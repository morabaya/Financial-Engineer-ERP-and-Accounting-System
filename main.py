import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.financials import Base
from app.services.voucher_service import VoucherService
from app.services.invoice_service import InvoiceService
from app.services.reporting_service import ReportingService
from app.services.inventory_service import InventoryService
from app.services.banking_service import BankingService
from app.services.loan_service import LoanService
from app.services.ai_bridge import AIFinancialBridge
from app.services.user_service import UserService

app = Flask(__name__)
app.secret_key = 'financial_engineer_secret_key'

# Database Setup
engine = create_engine('sqlite:///accounting_system.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@app.before_request
def create_session():
    request.db = SessionLocal()

@app.after_request
def close_session(response):
    request.db.close()
    return response

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/ai/process', methods=['POST'])
def ai_process():
    data = request.json
    user_query = data.get('query')
    
    # In a real scenario, we'd call the LLM here to get (intent, params)
    # For the prototype, we simulate the AI bridge
    bridge = AIFinancialBridge(request.db)
    
    # Simulation of AI intent mapping
    if "سند صرف" in user_query:
        res = bridge.handle_intent("create_voucher", {"type": "Payment", "description": "AI Generated", "amount": 100, "lines": [{'account_id': 521, 'debit': 100, 'credit': 0}, {'account_id': 1111, 'debit': 0, 'credit': 100}]})
        return jsonify({"reply": f"تم إنشاء سند صرف بنجاح. رقم السند: {res}"})
    
    elif "ميزان المراجعة" in user_query:
        res = bridge.handle_intent("get_report", {"report_type": "trial_balance"})
        return jsonify({"reply": f"إليك ميزان المراجعة: {res}"})
    
    return jsonify({"reply": "عذراً، لم أفهم الطلب بدقة. يمكنك طلب إنشاء سند، فاتورة، أو تقرير مالي."})

@app.route('/api/reports/<type>')
def get_report(type):
    reporting = ReportingService(request.db)
    if type == 'trial_balance':
        return jsonify(reporting.get_trial_balance())
    return jsonify({"error": "Report not found"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
