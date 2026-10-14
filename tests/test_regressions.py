import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Account
from app.services.seed_service import seed_database
from app.services.invoice_service import InvoiceService


class InvoiceAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        seed_database(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_failed_posting_does_not_persist_invoice_or_stock_change(self):
        item = self.db.query(__import__("app.models", fromlist=["Item"]).Item).filter_by(sku="PRD-001").one()
        old_stock = item.current_stock
        # Force account resolution to fail after invoice calculations and stock updates.
        sales_account = self.db.query(Account).filter_by(code="411").one()
        self.db.delete(sales_account)
        self.db.commit()

        with self.assertRaises(ValueError):
            InvoiceService(self.db).create_invoice(
                inv_type="Sales", contact_id=None,
                items_data=[{"item_id": item.id, "quantity": 1, "unit_price": 1200}],
                payment_method="Cash"
            )
        self.db.rollback()
        self.assertEqual(self.db.query(__import__("app.models", fromlist=["Invoice"]).Invoice).count(), 0)
        self.assertEqual(self.db.query(__import__("app.models", fromlist=["Item"]).Item).filter_by(id=item.id).one().current_stock, old_stock)


    def test_successful_sale_posts_balanced_entries_and_commits(self):
        from app.models import Invoice, Item, JournalEntryLine
        item = self.db.query(Item).filter_by(sku="PRD-001").one()
        old_stock = item.current_stock
        invoice_id = InvoiceService(self.db).create_invoice(
            inv_type="Sales", contact_id=None,
            items_data=[{"item_id": item.id, "quantity": 1, "unit_price": 1200}],
            payment_method="Cash"
        )
        self.assertIsNotNone(self.db.query(Invoice).filter_by(id=invoice_id).one())
        self.assertEqual(self.db.query(Item).filter_by(id=item.id).one().current_stock, old_stock - 1)
        for entry in self.db.query(__import__("app.models", fromlist=["JournalEntry"]).JournalEntry).all():
            self.assertAlmostEqual(sum(line.debit for line in entry.lines), sum(line.credit for line in entry.lines), places=2)

    def test_dashboard_initial_tab_loads_dashboard_markup_not_json(self):
        with open("static/js/main.js", encoding="utf-8") as source:
            js = source.read()
        self.assertIn("openTab('dashboard', 'لوحة التحكم', '/dashboard_view')", js)
        self.assertNotIn("openTab('dashboard', 'لوحة التحكم', '/api/dashboard/stats')", js)

    def test_session_secret_is_not_hardcoded(self):
        with open("main.py", encoding="utf-8") as source:
            app_source = source.read()
        self.assertNotIn("financial_engineer_secret_key_prod_2026", app_source)
        self.assertIn('os.environ.get("FLASK_SECRET_KEY")', app_source)

if __name__ == "__main__":
    unittest.main()
