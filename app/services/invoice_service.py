from app.models.financials import JournalEntry, JournalEntryLine
from app.models.invoices import Invoice, InvoiceItem
from app.services.accounting_engine import create_accounting_entry
from sqlalchemy.orm import Session

class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def create_invoice(self, inv_type, contact_id, items_data, currency="ILS", rate=1.0, user_id=1):
        # 1. Generate Invoice Number
        prefix = {'Sales': 'I', 'Purchase': 'H', 'Sales_Return': 'SR', 'Purchase_Return': 'PR'}.get(inv_type, 'INV')
        last_inv = self.db.query(Invoice).filter(Invoice.invoice_no.like(f"{prefix}%")).order_by(Invoice.id.desc()).first()
        inv_no = f"{prefix}-{str(int(last_inv.invoice_no.split('-')[1]) + 1).zfill(4)}" if last_inv else f"{prefix}-0001"

        # 2. Calculate Totals
        total_before_tax = 0
        total_tax = 0
        
        invoice = Invoice(invoice_no=inv_no, type=inv_type, contact_id=contact_id, currency=currency, exchange_rate=rate, user_id=user_id)
        self.db.add(invoice)
        self.db.flush()

        for item in items_data:
            # Logic for Palestinian Tax (16% default)
            line_total = item['quantity'] * item['unit_price'] - item.get('discount', 0)
            tax = line_total * item.get('tax_rate', 0.16)
            
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                item_id=item['item_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                discount=item.get('discount', 0),
                tax_rate=item.get('tax_rate', 0.16),
                tax_amount=tax,
                total=line_total + tax
            )
            self.db.add(inv_item)
            total_before_tax += line_total
            total_tax += tax

        invoice.total_before_tax = total_before_tax
        invoice.tax_amount = total_tax
        invoice.total_after_tax = total_before_tax + total_tax
        self.db.commit()

        # 3. Create Accounting Entry
        # This logic varies by invoice type (Sales vs Purchase)
        # Example for Sales: Debit Customer, Credit Sales, Credit Tax
        lines = []
        if inv_type == 'Sales':
            # Simplified: Account IDs would be fetched from CoA
            lines.append({'account_id': 112, 'debit': invoice.total_after_tax, 'credit': 0}) # Customer
            lines.append({'account_id': 41, 'debit': 0, 'credit': total_before_tax}) # Sales
            lines.append({'account_id': 212, 'debit': 0, 'credit': total_tax}) # Tax Liability
        
        if lines:
            create_accounting_entry(self.db, f"Invoice {inv_no}", inv_no, lines, currency, rate)
        
        self.db.commit()
        return invoice.id
