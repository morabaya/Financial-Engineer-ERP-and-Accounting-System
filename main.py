import datetime
import os
import secrets
import io
import csv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import check_password_hash
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Import all models to ensure complete metadata registration
from app.models import (
    Base, Account, AccountType, Currency, Contact, 
    Voucher, Invoice, Item, Check, Loan, User
)
from app.models.contacts import ContactType

from app.services.seed_service import seed_database
from app.services.voucher_service import VoucherService
from app.services.invoice_service import InvoiceService
from app.services.reporting_service import ReportingService
from app.services.inventory_service import InventoryService
from app.services.banking_service import BankingService
from app.services.loan_service import LoanService
from app.services.ai_bridge import AIFinancialBridge
from app.services.user_service import UserService

app = Flask(__name__)
# A stable production secret must be supplied through the environment. The random
# fallback is only for local development and invalidates sessions on restart.
_secret_key = os.environ.get("FLASK_SECRET_KEY")
if os.environ.get("FLASK_ENV", "development").lower() == "production" and not _secret_key:
    raise RuntimeError("FLASK_SECRET_KEY must be configured in production")
app.secret_key = _secret_key or secrets.token_urlsafe(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV", "development").lower() == "production"

_database_url = os.environ.get('DATABASE_URL', 'sqlite:///accounting_system.db')
engine = create_engine(_database_url, connect_args={'check_same_thread': False} if _database_url.startswith('sqlite') else {})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
with SessionLocal() as db_session:
    seed_database(db_session)

# Do not expose money-moving actions without a second explicit confirmation.
@app.before_request
def create_session():
    request.db = SessionLocal()
    if request.endpoint in {"login", "static"}:
        return None
    if not session.get("user_id"):
        if request.path.startswith("/api/"):
            return jsonify({"error": "يلزم تسجيل الدخول"}), 401
        return redirect(url_for("login", next=request.path))
    user = request.db.query(User).filter(User.id == session["user_id"], User.is_active == 1).first()
    if not user:
        session.clear()
        if request.path.startswith("/api/"):
            return jsonify({"error": "جلسة غير صالحة؛ سجل الدخول مجدداً"}), 401
        return redirect(url_for("login"))
    request.current_user = user
    role_names = {role.name for role in user.roles}
    policies = {
        "reseed_database": {"POST": {"Admin"}},
        "manage_vouchers": {"GET": {"Admin", "Accountant"}, "POST": {"Admin", "Accountant"}},
        "manage_invoices": {"GET": {"Admin", "Accountant"}, "POST": {"Admin", "Accountant", "Cashier"}},
        "manage_checks": {"GET": {"Admin", "Accountant"}, "POST": {"Admin", "Accountant"}},
        "check_action": {"POST": {"Admin", "Accountant"}},
        "manage_inventory": {"GET": {"Admin", "Accountant", "Cashier"}, "POST": {"Admin", "Accountant"}},
        "inventory_count": {"POST": {"Admin", "Accountant"}},
        "manage_loans": {"GET": {"Admin", "Accountant"}, "POST": {"Admin", "Accountant"}},
        "loan_preview": {"POST": {"Admin", "Accountant"}},
        "pay_loan_installment": {"POST": {"Admin", "Accountant"}},
        "dashboard_stats": {"GET": {"Admin", "Accountant"}},
        "get_report": {"GET": {"Admin", "Accountant"}},
        "ai_process": {"POST": {"Admin", "Accountant"}},
        "manage_contacts": {"GET": {"Admin", "Accountant", "Cashier"}, "POST": {"Admin", "Accountant"}},
        "update_contact": {"GET": {"Admin", "Accountant", "Cashier"}, "PUT": {"Admin", "Accountant"}},
        "toggle_contact_status": {"POST": {"Admin", "Accountant"}},
        "contact_statement": {"GET": {"Admin", "Accountant"}},
        "export_contact_statement": {"GET": {"Admin", "Accountant"}},
        "get_accounts": {"GET": {"Admin", "Accountant"}},
        "get_currencies": {"GET": {"Admin", "Accountant"}},
    }
    allowed_roles = policies.get(request.endpoint, {}).get(request.method)
    if allowed_roles and role_names.isdisjoint(allowed_roles):
        if request.path.startswith("/api/"):
            return jsonify({"error": "لا تملك صلاحية لتنفيذ هذا الإجراء"}), 403
        return "غير مصرح لك بهذا الإجراء", 403

@app.after_request
def close_session(response):
    if hasattr(request, 'db'):
        request.db.close()
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    user = request.db.query(User).filter(User.username == username, User.is_active == 1).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template('login.html', error="اسم المستخدم أو كلمة المرور غير صحيحة"), 401
    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
    target = request.args.get('next', '/dashboard')
    if not target.startswith('/') or target.startswith('//'):
        target = '/dashboard'
    return redirect(target)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
#              PAGE ROUTES
# ==========================================

@app.route('/')
@app.route('/dashboard')
def index():
    return render_template('base.html')

@app.route('/pos')
def pos():
    return render_template('pos.html')

@app.route('/vouchers')
def vouchers():
    return render_template('vouchers.html')

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/loans')
def loans():
    return render_template('loans.html')

@app.route('/dashboard_view')
def dashboard_view():
    return render_template('dashboard_view.html')

@app.route('/accounts_view')
def accounts_view():
    return render_template('accounts_view.html')

@app.route('/checks_view')
def checks_view():
    return render_template('checks_view.html')

@app.route('/contacts_view')
def contacts_view():
    return render_template('contacts_view.html')

@app.route('/settings')
def settings():
    return """
    <div class="container-fluid p-4">
        <h3><i class="fas fa-cog"></i> إعدادات النظام المالي</h3>
        <hr>
        <div class="row g-3">
            <div class="col-md-6">
                <div class="card p-3 shadow-sm">
                    <h5>العملة الأساسية والضرائب</h5>
                    <p class="text-muted">العملة الأساسية: <b>شيكل إسرائيلي (ILS ₪)</b></p>
                    <p class="text-muted">نسبة ضريبة القيمة المضافة الفلسطينية: <b>16%</b></p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card p-3 shadow-sm">
                    <h5>التهيئة وقاعدة البيانات</h5>
                    <button class="btn btn-outline-warning" onclick="fetch('/api/system/seed', {method:'POST'}).then(r=>r.json()).then(d=>alert(d.message))">
                        إعادة تهيئة دليل الحسابات الافتراضي
                    </button>
                </div>
            </div>
        </div>
    </div>
    """

# ==========================================
#          DASHBOARD & STATS APIS
# ==========================================

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """مؤشرات الأداء المالي الرئيسية (KPIs)"""
    db = request.db
    reporting = ReportingService(db)

    # 1. النقدية والبنوك
    cash_accs = db.query(Account).filter(Account.code.in_(["1111", "1112", "1113", "1114"])).all()
    total_cash = 0.0
    for acc in cash_accs:
        gl = reporting.get_general_ledger(acc.id)
        if isinstance(gl, dict) and "closing_balance" in gl:
            total_cash += gl["closing_balance"]

    # 2. رصيد ذمم العملاء (Receivables)
    total_receivables = db.query(func.sum(Contact.current_balance)).filter(Contact.current_balance > 0).scalar() or 0.0

    # 3. إجمالي قيمة المخزون
    items = db.query(Item).all()
    inventory_val = sum(it.current_stock * it.purchase_price for it in items)

    # 4. الشيكات برسم التحصيل
    checks_under_coll = db.query(func.sum(Check.amount)).filter(Check.status == "UNDER_COLLECTION").scalar() or 0.0

    # 5. صافي الأرباح وقائمة الدخل
    income_stmt = reporting.get_income_statement()

    return jsonify({
        "total_cash": round(total_cash, 2),
        "total_receivables": round(total_receivables, 2),
        "inventory_value": round(inventory_val, 2),
        "checks_under_collection": round(checks_under_coll, 2),
        "total_revenue": income_stmt["total_revenue"],
        "net_profit": income_stmt["net_profit"],
        "operating_expenses": income_stmt["operating_expenses"]
    })

# ==========================================
#         CHART OF ACCOUNTS APIS
# ==========================================

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = request.db.query(Account).order_by(Account.code.asc()).all()
    return jsonify([acc.to_dict() for acc in accounts])

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    currencies = request.db.query(Currency).all()
    return jsonify([c.to_dict() for c in currencies])

# ==========================================
#             CONTACTS APIS
# ==========================================

def parse_contact_type(t_str):
    if isinstance(t_str, ContactType):
        return t_str
    s = str(t_str).strip()
    if s in [ContactType.CUSTOMER.value, "CUSTOMER", "customer", "عميل", "زبون"]:
        return ContactType.CUSTOMER
    elif s in [ContactType.SUPPLIER.value, "SUPPLIER", "supplier", "مورد"]:
        return ContactType.SUPPLIER
    elif s in [ContactType.EMPLOYEE.value, "EMPLOYEE", "employee", "موظف"]:
        return ContactType.EMPLOYEE
    return ContactType.CUSTOMER

@app.route('/api/contacts', methods=['GET', 'POST'])
def manage_contacts():
    db = request.db
    if request.method == 'POST':
        data = request.json or {}
        name = data.get('name')
        if not name:
            return jsonify({"error": "اسم جهة التعامل مطلوب"}), 400

        c_type = parse_contact_type(data.get('type', 'عميل'))
        
        # Link default CoA account if not specified
        acc_id = data.get('account_id')
        if not acc_id:
            if c_type == ContactType.CUSTOMER:
                def_acc = db.query(Account).filter(Account.code == "1121").first()
            elif c_type == ContactType.SUPPLIER:
                def_acc = db.query(Account).filter(Account.code == "2111").first()
            else:
                def_acc = db.query(Account).filter(Account.code == "1122").first()
            if def_acc:
                acc_id = def_acc.id

        contact = Contact(
            name=name.strip(),
            type=c_type,
            tax_number=data.get('tax_number', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            city=data.get('city', 'رام الله'),
            currency=data.get('currency', 'ILS'),
            account_id=acc_id,
            credit_limit=float(data.get('credit_limit', 0.0)),
            current_balance=0.0,
            is_active=True
        )
        db.add(contact)
        db.commit()
        return jsonify({"message": "تم إضافة جهة التعامل بنجاح", "id": contact.id, "contact": contact.to_dict()}), 201

    c_type_raw = request.args.get('type')
    query = db.query(Contact)
    if c_type_raw and c_type_raw != 'all':
        query = query.filter(Contact.type == parse_contact_type(c_type_raw))
    contacts = query.order_by(Contact.id.desc()).all()
    return jsonify([c.to_dict() for c in contacts])

@app.route('/api/contacts/<int:contact_id>', methods=['GET', 'PUT'])
def update_contact(contact_id):
    db = request.db
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return jsonify({"error": "جهة التعامل غير موجودة"}), 404

    if request.method == 'GET':
        return jsonify(contact.to_dict())

    data = request.json or {}
    if 'name' in data and data['name'].strip():
        contact.name = data['name'].strip()
    if 'type' in data:
        contact.type = parse_contact_type(data['type'])
    if 'tax_number' in data:
        contact.tax_number = data['tax_number']
    if 'phone' in data:
        contact.phone = data['phone']
    if 'email' in data:
        contact.email = data['email']
    if 'address' in data:
        contact.address = data['address']
    if 'city' in data:
        contact.city = data['city']
    if 'currency' in data:
        contact.currency = data['currency']
    if 'credit_limit' in data:
        contact.credit_limit = float(data.get('credit_limit', 0.0))
    if 'is_active' in data:
        contact.is_active = bool(data['is_active'])

    db.commit()
    return jsonify({"message": "تم تحديث بيانات جهة التعامل بنجاح", "contact": contact.to_dict()})

@app.route('/api/contacts/<int:contact_id>/toggle', methods=['POST'])
def toggle_contact_status(contact_id):
    db = request.db
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return jsonify({"error": "جهة التعامل غير موجودة"}), 404

    contact.is_active = not contact.is_active
    db.commit()
    status_str = "تفعيل" if contact.is_active else "إيقاف"
    return jsonify({"message": f"تم {status_str} جهة التعامل بنجاح", "is_active": contact.is_active})

@app.route('/api/contacts/<int:contact_id>/statement', methods=['GET'])
def contact_statement(contact_id):
    reporting = ReportingService(request.db)
    stmt = reporting.get_contact_statement(contact_id)
    if "error" in stmt:
        return jsonify(stmt), 404
    return jsonify(stmt)

@app.route('/api/contacts/<int:contact_id>/statement/export', methods=['GET'])
def export_contact_statement(contact_id):
    reporting = ReportingService(request.db)
    stmt = reporting.get_contact_statement(contact_id)
    if "error" in stmt:
        return jsonify(stmt), 404

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["كشف حساب جهة تعامل", stmt.get("contact_name", "")])
    writer.writerow(["النوع", stmt.get("contact_type", ""), "الرقم الضريبي", stmt.get("tax_number", "")])
    writer.writerow(["الهاتف", stmt.get("phone", ""), "الرصيد الحالي", stmt.get("current_balance", 0.0)])
    writer.writerow([])
    writer.writerow(["التاريخ", "رقم القيد", "البيان", "مدين", "دائن", "الرصيد التراكمي"])
    
    for line in stmt.get("lines", []):
        writer.writerow([
            line.get("date", ""),
            line.get("entry_no", ""),
            line.get("desc", ""),
            line.get("debit", 0.0),
            line.get("credit", 0.0),
            line.get("balance", 0.0)
        ])
    
    writer.writerow([])
    writer.writerow(["المجموع", "", "", stmt.get("total_debit", 0.0), stmt.get("total_credit", 0.0), stmt.get("net_balance", 0.0)])

    csv_data = output.getvalue()
    bom_data = '\ufeff' + csv_data
    return Response(
        bom_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=statement_{contact_id}.csv"}
    )

# ==========================================
#             VOUCHERS APIS
# ==========================================

@app.route('/api/vouchers', methods=['GET', 'POST'])
def manage_vouchers():
    service = VoucherService(request.db)
    if request.method == 'POST':
        data = request.json or {}
        try:
            v_id = service.create_voucher(
                v_type=data.get('type', 'Receipt'),
                description=data.get('description', ''),
                lines_data=data.get('lines', []),
                total_amount=float(data.get('total_amount', 0.0)),
                currency=data.get('currency', 'ILS'),
                rate=float(data.get('exchange_rate', 1.0)),
                contact_id=data.get('contact_id')
            )
            voucher = service.get_voucher_by_id(v_id)
            return jsonify({"message": "تم إصدار وترحيل السند بنجاح", "voucher": voucher.to_dict()}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    v_type = request.args.get('type')
    vouchers_list = service.get_all_vouchers(v_type=v_type)
    return jsonify([v.to_dict() for v in vouchers_list])

# ==========================================
#             INVOICES & POS APIS
# ==========================================

@app.route('/api/invoices', methods=['GET', 'POST'])
def manage_invoices():
    service = InvoiceService(request.db)
    if request.method == 'POST':
        data = request.json or {}
        try:
            inv_id = service.create_invoice(
                inv_type=data.get('type', 'Sales'),
                contact_id=data.get('contact_id'),
                items_data=data.get('items', []),
                payment_method=data.get('payment_method', 'Cash'),
                currency=data.get('currency', 'ILS'),
                rate=float(data.get('exchange_rate', 1.0)),
                notes=data.get('notes')
            )
            inv = service.get_invoice_by_id(inv_id)
            return jsonify({"message": "تم إصدار الفاتورة وترحيل القيود وتحديث المخزون بنجاح", "invoice": inv.to_dict()}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    inv_type = request.args.get('type')
    invoices_list = service.get_all_invoices(inv_type=inv_type)
    return jsonify([inv.to_dict() for inv in invoices_list])

# ==========================================
#            INVENTORY APIS
# ==========================================

@app.route('/api/inventory/items', methods=['GET', 'POST'])
def manage_inventory():
    service = InventoryService(request.db)
    if request.method == 'POST':
        data = request.json or {}
        try:
            item_id = service.create_item(
                sku=data.get('sku'),
                name_ar=data.get('name_ar'),
                name_en=data.get('name_en'),
                category=data.get('category', 'عام'),
                unit=data.get('unit', 'قطعة'),
                purchase_price=float(data.get('purchase_price', 0.0)),
                sale_price=float(data.get('sale_price', 0.0)),
                initial_stock=float(data.get('initial_stock', 0.0)),
                min_stock=float(data.get('min_stock_level', 5.0))
            )
            return jsonify({"message": "تم إضافة الصنف بنجاح", "id": item_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    items = service.get_all_items()
    return jsonify([it.to_dict() for it in items])

@app.route('/api/inventory/count', methods=['POST'])
def inventory_count():
    service = InventoryService(request.db)
    data = request.json or {}
    try:
        diff = service.perform_inventory_count(
            item_id=int(data.get('item_id')),
            warehouse_id=int(data.get('warehouse_id', 1)),
            actual_qty=float(data.get('actual_qty', 0.0))
        )
        return jsonify({"message": f"تمت تسوية الجرد المخزني. الفارق المسجل: {diff} وحدة", "difference": diff})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ==========================================
#          BANKING & CHECKS APIS
# ==========================================

@app.route('/api/banking/checks', methods=['GET', 'POST'])
def manage_checks():
    service = BankingService(request.db)
    if request.method == 'POST':
        data = request.json or {}
        try:
            c_type = data.get('type', 'Incoming')
            due_date = datetime.datetime.strptime(data.get('due_date'), "%Y-%m-%d")
            if c_type == 'Incoming':
                check_id = service.receive_check(
                    check_no=data.get('check_number'),
                    drawer_name=data.get('drawer_name', 'زبون'),
                    amount=float(data.get('amount', 0.0)),
                    currency=data.get('currency', 'ILS'),
                    due_date=due_date,
                    contact_id=data.get('contact_id'),
                    bank_name=data.get('bank_name', 'بنك فلسطين'),
                    rate=float(data.get('exchange_rate', 1.0))
                )
            else:
                check_id = service.issue_check(
                    check_no=data.get('check_number'),
                    beneficiary_name=data.get('beneficiary_name', 'مورد'),
                    amount=float(data.get('amount', 0.0)),
                    currency=data.get('currency', 'ILS'),
                    due_date=due_date,
                    vendor_id=data.get('contact_id'),
                    rate=float(data.get('exchange_rate', 1.0))
                )
            return jsonify({"message": "تم تسجيل الشيك وترحيل قيده بنجاح", "id": check_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    status = request.args.get('status')
    c_type = request.args.get('type')
    checks = service.get_all_checks(status=status, check_type=c_type)
    return jsonify([c.to_dict() for c in checks])

@app.route('/api/banking/checks/<int:check_id>/action', methods=['POST'])
def check_action(check_id):
    service = BankingService(request.db)
    data = request.json or {}
    action = data.get('action') # 'clear', 'return', 'endorse'
    try:
        if action == 'clear':
            service.clear_check(check_id, actual_rate=data.get('actual_rate'))
            return jsonify({"message": "تم تحصيل/صرف الشيك بالبنك بنجاح"})
        elif action == 'return':
            service.return_check(check_id, reason=data.get('reason', 'رصيد غير كافٍ'))
            return jsonify({"message": "تم إثبات ارتجاع الشيك وإعادة الذمة بنجاح"})
        elif action == 'endorse':
            vendor_id = int(data.get('vendor_id'))
            service.endorse_check(check_id, vendor_id=vendor_id)
            return jsonify({"message": "تم تجيير الشيك بنجاح لصالح المورد"})
        else:
            return jsonify({"error": "إجراء غير معروف"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ==========================================
#               LOANS APIS
# ==========================================

@app.route('/api/loans', methods=['GET', 'POST'])
def manage_loans():
    service = LoanService(request.db)
    if request.method == 'POST':
        data = request.json or {}
        try:
            loan_id = service.create_loan(
                amount=float(data.get('loan_amount')),
                rate=float(data.get('interest_rate')),
                term=int(data.get('term_months')),
                loan_type=data.get('loan_type', 'Fixed'),
                borrower_name=data.get('borrower_name', 'الشركة')
            )
            return jsonify({"message": "تم إنشاء القرض واعتماد جدول السداد وترحيل قيد الاستلام بنجاح", "id": loan_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    loans_list = service.get_all_loans()
    return jsonify([l.to_dict() for l in loans_list])

@app.route('/api/loans/preview', methods=['POST'])
def loan_preview():
    service = LoanService(request.db)
    data = request.json or {}
    try:
        sched = service.calculate_schedule_preview(
            amount=data.get('loan_amount', 0),
            rate=data.get('interest_rate', 0),
            term=data.get('term_months', 1),
            loan_type=data.get('loan_type', 'Fixed')
        )
        return jsonify({"schedule": sched})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/loans/schedule/<int:schedule_id>/pay', methods=['POST'])
def pay_loan_installment(schedule_id):
    service = LoanService(request.db)
    try:
        success = service.mark_payment_as_paid(schedule_id)
        if success:
            return jsonify({"message": "تم سداد قسط القرض وترحيل قيد السداد والفوائد بنجاح"})
        return jsonify({"error": "تعذر سداد القسط أو تم سداده مسبقاً"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ==========================================
#             REPORTS APIS
# ==========================================

@app.route('/api/reports/<rep_type>')
def get_report(rep_type):
    reporting = ReportingService(request.db)
    if rep_type == 'trial_balance':
        return jsonify(reporting.get_trial_balance())
    elif rep_type == 'income_statement':
        return jsonify(reporting.get_income_statement())
    elif rep_type == 'balance_sheet':
        return jsonify(reporting.get_balance_sheet())
    elif rep_type == 'comparative':
        return jsonify(reporting.get_comparative_monthly_report())
    elif rep_type == 'journal':
        return jsonify(reporting.get_general_journal())
    elif rep_type == 'ledger':
        acc = request.args.get('account', '1111')
        return jsonify(reporting.get_general_ledger(acc))
    return jsonify({"error": "التقرير غير موجود"}), 404

# ==========================================
#            AI ASSISTANT API
# ==========================================

@app.route('/api/ai/process', methods=['POST'])
def ai_process():
    data = request.json or {}
    user_query = str(data.get('query', '')).strip()
    bridge = AIFinancialBridge(request.db)
    pending = session.get('pending_ai_action')
    normalized = user_query.lower()
    if pending:
        if normalized in {'أكد', 'تأكيد', 'نعم', 'نفذ', 'نفّذ', 'confirm', 'yes'}:
            session.pop('pending_ai_action', None)
            return jsonify(bridge.process_natural_language(pending))
        if normalized in {'إلغاء', 'الغاء', 'لا', 'cancel', 'no'}:
            session.pop('pending_ai_action', None)
            return jsonify({"reply": "تم إلغاء العملية؛ لم يُنشأ أي سند."})
        session.pop('pending_ai_action', None)

    is_money_action = any(term in normalized for term in ('سند صرف', 'سند قبض', 'payment voucher', 'receipt voucher'))
    if is_money_action:
        import re
        amount_match = re.search(r'(?<![\w])\d+(?:\.\d{1,2})?', normalized)
        if not amount_match:
            return jsonify({"reply": "اذكر قيمة السند صراحةً حتى أعرض مسودة للمراجعة.", "requires_confirmation": False})
        session['pending_ai_action'] = user_query
        return jsonify({
            "reply": f"مسودة عملية مالية بقيمة {amount_match.group(0)} ₪. لن يتم الترحيل قبل تأكيدك. أرسل «تأكيد» للتنفيذ أو «إلغاء» للإلغاء.",
            "requires_confirmation": True
        })

    return jsonify(bridge.process_natural_language(user_query))

# ==========================================
#          SYSTEM ADMINISTRATION
# ==========================================

@app.route('/api/system/seed', methods=['POST'])
def reseed_database():
    seed_database(request.db)
    return jsonify({"message": "تم تهيئة دليل الحسابات والبيانات التأسيسية بنجاح"})

if __name__ == "__main__":
    is_production = os.environ.get("FLASK_ENV", "development").lower() == "production"
    app.run(debug=not is_production, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
