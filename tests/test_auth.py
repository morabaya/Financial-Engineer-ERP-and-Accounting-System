import os
import unittest

# Isolate app import and seed data from the repository's local database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["INITIAL_ADMIN_PASSWORD"] = "test-only-password"

import main


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        main.engine.dispose()

    def setUp(self):
        self.client = main.app.test_client()

    def test_pages_redirect_to_login_when_unauthenticated(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_api_rejects_unauthenticated_requests(self):
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 401)

    def test_login_authenticates_seeded_admin(self):
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": "test-only-password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/api/accounts").status_code, 200)

    def test_ai_financial_action_requires_confirmation_before_posting(self):
        from app.models import Voucher
        self.client.post("/login", data={"username": "admin", "password": "test-only-password"})
        with main.SessionLocal() as db:
            before = db.query(Voucher).count()
        response = self.client.post("/api/ai/process", json={"query": "سند صرف 100 إيجار"})
        with main.SessionLocal() as db:
            after = db.query(Voucher).count()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("requires_confirmation"))
        self.assertEqual(before, after)
        confirmed = self.client.post("/api/ai/process", json={"query": "تأكيد"})
        self.assertEqual(confirmed.status_code, 200)
        self.assertIn("تم إنشاء", confirmed.get_json().get("reply", ""))

    def test_cashier_is_denied_financial_reports_and_voucher_writes(self):
        from werkzeug.security import generate_password_hash
        from app.models import User, Role
        db = main.SessionLocal()
        cashier = db.query(User).filter_by(username="test-cashier").first()
        if cashier is None:
            cashier = User(username="test-cashier", password_hash=generate_password_hash("cashier-password"), full_name="Test Cashier", is_active=1)
            cashier.roles.append(db.query(Role).filter_by(name="Cashier").one())
            db.add(cashier)
            db.commit()
        db.close()
        self.client.post("/login", data={"username": "test-cashier", "password": "cashier-password"})
        self.assertEqual(self.client.get("/api/reports/trial_balance").status_code, 403)
        self.assertEqual(self.client.post("/api/vouchers", json={}).status_code, 403)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            "/login", data={"username": "admin", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
