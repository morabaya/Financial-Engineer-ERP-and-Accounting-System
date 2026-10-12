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
@app.route('/dashboard')
def index():
    return render_template('base.html')

@app.route('/pos')
def pos():
    # In a real app, we'd render a specific pos.html
    return "<h1>صفحة نقطة البيع (POS)</h1><p>جاري تحميل واجهة المبيعات السريعة...</p>"

@app.route('/vouchers')
def vouchers():
    return "<h1>إدارة السندات</h1><p>قائمة بسندات القبض والصرف والقيد...</p>"

@app.route('/invoices')
def invoices():
    return "<h1>إدارة الفواتير</h1><p>قائمة بفواتير المبيعات والمشتريات...</p>"

@app.route('/inventory')
def inventory():
    return "<h1>إدارة المخازن</h1><p>جرد الأصناف وحركات المستودعات...</p>"

@app.route('/reports')
def reports():
    return "<h1>التقارير المالية</h1><p>ميزان المراجعة وقائمة الدخل والميزانية...</p>"

@app.route('/loans')
def loans():
    return "<h1>إدارة القروض</h1><p>جداول السداد وحاسبة الفوائد...</p>"

@app.route('/settings')
def settings():
    return "<h1>الإعدادات</h1><p>إعدادات النظام والمستخدمين والصلاحيات...</p>"

@app.route('/api/ai/process', methods=['POST'])
def ai_process():
    data = request.json
    user_query = data.get('query')
    bridge = AIFinancialBridge(request.db)
    
    # Simple Simulation of AI logic
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
