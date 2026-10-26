import unittest
from app.models import Base
from app.services.seed_service import seed_database
import main


class ContactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(main.engine)
        with main.SessionLocal() as db:
            if db.query(main.Account).count() == 0:
                seed_database(db)

    def setUp(self):
        self.client = main.app.test_client()
        # Login as admin
        self.client.post("/login", data={"username": "admin", "password": "test-only-password"})

    def test_contacts_view_accessible(self):
        response = self.client.get("/contacts_view")
        self.assertEqual(response.status_code, 200)
        self.assertIn("إدارة جهات التعامل", response.get_data(as_text=True))

    def test_contacts_crud_and_lifecycle(self):
        # 1. Create a customer
        create_res = self.client.post("/api/contacts", json={
            "name": "شركة الوادي للتجارة",
            "type": "عميل",
            "phone": "0599001122",
            "email": "wadi@example.com",
            "city": "نابلس",
            "tax_number": "912345678",
            "credit_limit": 50000,
            "currency": "ILS",
            "address": "شارع فيصل"
        })
        self.assertEqual(create_res.status_code, 201)
        data = create_res.get_json()
        contact_id = data.get("id")
        self.assertIsNotNone(contact_id)

        # 2. Get list of contacts
        list_res = self.client.get("/api/contacts")
        self.assertEqual(list_res.status_code, 200)
        contacts = list_res.get_json()
        names = [c["name"] for c in contacts]
        self.assertIn("شركة الوادي للتجارة", names)

        # 3. Update contact
        update_res = self.client.put(f"/api/contacts/{contact_id}", json={
            "credit_limit": 60000,
            "phone": "0599334455"
        })
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.get_json().get("contact")
        self.assertEqual(updated["credit_limit"], 60000)
        self.assertEqual(updated["phone"], "0599334455")

        # 4. Toggle status
        toggle_res = self.client.post(f"/api/contacts/{contact_id}/toggle")
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(toggle_res.get_json()["is_active"])

        toggle_res2 = self.client.post(f"/api/contacts/{contact_id}/toggle")
        self.assertEqual(toggle_res2.status_code, 200)
        self.assertTrue(toggle_res2.get_json()["is_active"])

        # 5. Statement
        stmt_res = self.client.get(f"/api/contacts/{contact_id}/statement")
        self.assertEqual(stmt_res.status_code, 200)
        stmt = stmt_res.get_json()
        self.assertEqual(stmt["contact_name"], "شركة الوادي للتجارة")
        self.assertIn("lines", stmt)
        self.assertIn("total_debit", stmt)
        self.assertIn("total_credit", stmt)

        # 6. Export statement
        export_res = self.client.get(f"/api/contacts/{contact_id}/statement/export")
        self.assertEqual(export_res.status_code, 200)
        self.assertIn("text/csv", export_res.headers.get("Content-Type"))
        csv_text = export_res.get_data(as_text=True)
        self.assertIn("شركة الوادي للتجارة", csv_text)
