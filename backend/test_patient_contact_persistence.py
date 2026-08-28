"""
Comprehensive Regression & Integration Test Suite for Patient Contact Persistence (Mobile & Email).
Validates complete end-to-end data flow:
Patient Registration -> Backend Models/Schemas -> MySQL Persistence -> Screening Linkage -> WhatsApp & Email Resolvers -> Safety Gates.
"""

import unittest
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import PatientModel, ScreeningModel
from app.whatsapp_service import whatsapp_service
from app.email_service import email_service


class TestPatientContactPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_patient_registration_persists_mobile_and_email(self):
        """1. Patient registered with mobile + email persists both to MySQL."""
        payload = {
            "name": "Regression Test Patient Alpha",
            "age": 48,
            "gender": "female",
            "phone": "+91 98111 22233",
            "email": "alpha.test@ruralcare.org",
            "village": "Rampur",
            "district": "Varanasi",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["id"].startswith("PAT-"))
        self.assertEqual(data["phone"], "+91 98111 22233")
        self.assertEqual(data["mobile"], "+91 98111 22233")
        self.assertEqual(data["email"], "alpha.test@ruralcare.org")

        # Verify in MySQL
        db_patient = self.db.query(PatientModel).filter(PatientModel.id == data["id"]).first()
        self.assertIsNotNone(db_patient)
        self.assertEqual(db_patient.phone, "+91 98111 22233")
        self.assertEqual(db_patient.mobile, "+91 98111 22233")
        self.assertEqual(db_patient.email, "alpha.test@ruralcare.org")

    def test_02_patient_registration_with_only_mobile(self):
        """2. Patient registered with only mobile persists correctly without email."""
        payload = {
            "name": "Regression Test Patient MobileOnly",
            "age": 55,
            "gender": "male",
            "phone": "+91 98222 33344",
            "email": None,
            "village": "Chandauli",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["phone"], "+91 98222 33344")
        self.assertIsNone(data["email"])

    def test_03_patient_registration_with_only_email(self):
        """3. Patient registered with only email persists correctly without mobile."""
        payload = {
            "name": "Regression Test Patient EmailOnly",
            "age": 60,
            "gender": "female",
            "phone": None,
            "email": "email.only@ruralcare.org",
            "village": "Mirzapur",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIsNone(data["phone"])
        self.assertEqual(data["email"], "email.only@ruralcare.org")

    def test_04_field_alias_normalization(self):
        """4. Schema normalizes aliases: mobile, mobile_number, mobileNumber, phone_number, email_address, emailAddress."""
        payload = {
            "name": "Regression Test Aliases",
            "age": 42,
            "gender": "other",
            "mobile": "+91 98333 44455",
            "email_address": "aliases.test@ruralcare.org",
            "village": "Ghazipur",
            "abhaId": "ABHA-1234-5678",
            "diabetesDuration": 6,
            "lastHba1c": 8.1,
            "insulinUse": True,
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["phone"], "+91 98333 44455")
        self.assertEqual(data["mobile"], "+91 98333 44455")
        self.assertEqual(data["email"], "aliases.test@ruralcare.org")
        self.assertEqual(data["abha_id"], "ABHA-1234-5678")
        self.assertEqual(data["diabetes_duration"], 6)
        self.assertEqual(data["last_hba1c"], 8.1)
        self.assertTrue(data["insulin_use"])

    def test_05_list_and_get_patient_endpoints_include_mobile_and_email(self):
        """5. GET /api/patients and GET /api/patients/{id} return both phone, mobile, and email."""
        res_list = self.client.get("/api/patients")
        self.assertEqual(res_list.status_code, 200)
        patients = res_list.json()["patients"]
        self.assertGreater(len(patients), 0)

        # Check first patient detail
        first_id = patients[0]["id"]
        res_detail = self.client.get(f"/api/patients/{first_id}")
        self.assertEqual(res_detail.status_code, 200)
        detail = res_detail.json()
        self.assertIn("phone", detail)
        self.assertIn("mobile", detail)
        self.assertIn("email", detail)

    def test_06_screening_linkage_to_patient_in_db(self):
        """6. Screening record links patient_id to patient in database."""
        # Create patient
        pat_res = self.client.post(
            "/api/patients",
            json={
                "name": "Linked Screening Patient",
                "age": 52,
                "gender": "male",
                "phone": "+91 98444 55566",
                "email": "linked.patient@ruralcare.org",
                "village": "Rampur",
            },
        )
        self.assertEqual(pat_res.status_code, 201)
        patient_id = pat_res.json()["id"]

        # Clean up existing test screening if any
        scr_exist = self.db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-TEST-PERSIST-001").first()
        if scr_exist:
            self.db.delete(scr_exist)
            self.db.commit()

        # Create screening
        scr_res = self.client.post(
            "/api/screenings",
            json={
                "id": "SCR-TEST-PERSIST-001",
                "patient_id": patient_id,
                "patient_name": "Linked Screening Patient",
                "predicted_class": 2,
                "class_name": "Moderate DR",
                "confidence": 0.89,
                "overall_severity": "dr2",
            },
        )
        self.assertEqual(scr_res.status_code, 201)

        # Retrieve screening and verify linkage
        scr_get = self.client.get("/api/screenings/SCR-TEST-PERSIST-001")
        self.assertEqual(scr_get.status_code, 200)
        scr_data = scr_get.json()
        self.assertEqual(scr_data["patient_id"], patient_id)

    def test_07_whatsapp_resolver_gets_patient_mobile(self):
        """7. WhatsApp resolver gets patient mobile from screening.patient_id."""
        resolved = whatsapp_service.resolve_patient_for_screening("SCR-TEST-PERSIST-001", db=self.db)
        self.assertIsNotNone(resolved)
        self.assertEqual(getattr(resolved, "name", None), "Linked Screening Patient")
        self.assertEqual(getattr(resolved, "phone", None), "+91 98444 55566")

    def test_08_email_resolver_gets_patient_email(self):
        """8. Email resolver gets patient email from screening.patient_id."""
        resolved = email_service.resolve_patient_for_screening("SCR-TEST-PERSIST-001", db=self.db)
        self.assertIsNotNone(resolved)
        self.assertEqual(getattr(resolved, "name", None), "Linked Screening Patient")
        self.assertEqual(getattr(resolved, "email", None), "linked.patient@ruralcare.org")

    def test_09_scr_2026_1025_resolves_devendra_mehra_contacts(self):
        """9. SCR-2026-1025 authoritatively resolves Devendra Mehra's registered phone and email."""
        # WhatsApp resolution
        wa_pat = whatsapp_service.resolve_patient_for_screening("SCR-2026-1025", db=self.db)
        self.assertIsNotNone(wa_pat)
        self.assertEqual(getattr(wa_pat, "name", None), "Devendra Mehra")
        self.assertEqual(getattr(wa_pat, "phone", None), "+91 98777 66554")

        # Email resolution
        em_pat = email_service.resolve_patient_for_screening("SCR-2026-1025", db=self.db)
        self.assertIsNotNone(em_pat)
        self.assertEqual(getattr(em_pat, "name", None), "Devendra Mehra")
        self.assertEqual(getattr(em_pat, "email", None), "devendra.mehra@ruralcare.org")

        # WhatsApp status endpoint
        wa_status_res = self.client.get("/api/reports/SCR-2026-1025/whatsapp/status")
        self.assertEqual(wa_status_res.status_code, 200)
        wa_status = wa_status_res.json()
        self.assertEqual(wa_status["patient_name"], "Devendra Mehra")
        self.assertEqual(wa_status["recipient_phone"], "+919877766554")
        self.assertTrue(wa_status["can_send"])

        # Email status endpoint (unconfigured provider)
        em_status_res = self.client.get("/api/reports/SCR-2026-1025/email/status")
        self.assertEqual(em_status_res.status_code, 200)
        em_status = em_status_res.json()
        self.assertEqual(em_status["patient_name"], "Devendra Mehra")
        self.assertEqual(em_status["recipient_email"], "devendra.mehra@ruralcare.org")
        self.assertEqual(em_status["status"], "NOT_CONFIGURED")
        self.assertFalse(em_status["can_send"])
        self.assertEqual(em_status["block_reason"], "Email service is not configured.")

        # Email status endpoint (when SMTP provider is configured)
        from unittest.mock import patch
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.gmail.com", "SMTP_USERNAME": "test@gmail.com", "SMTP_PASSWORD": "password"}):
            em_conf_res = self.client.get("/api/reports/SCR-2026-1025/email/status")
            self.assertEqual(em_conf_res.status_code, 200)
            em_conf_data = em_conf_res.json()
            self.assertTrue(em_conf_data["can_send"])
            self.assertTrue(em_conf_data["is_configured"])
            self.assertEqual(em_conf_data["recipient_email"], "devendra.mehra@ruralcare.org")

    def test_10_health_worker_contacts_never_substituted(self):
        """10. Health worker contacts are NEVER substituted as patient's contact."""
        # Query with health_worker_id provided
        wa_status_res = self.client.get("/api/reports/SCR-2026-1025/whatsapp/status?health_worker_id=HW-ASHA-001")
        self.assertEqual(wa_status_res.status_code, 200)
        wa_status = wa_status_res.json()
        # Must resolve patient's mobile (+919877766554), not health worker mobile (+919876543210)
        self.assertEqual(wa_status["recipient_phone"], "+919877766554")
        self.assertEqual(wa_status["patient_name"], "Devendra Mehra")

    def test_11_missing_contact_safety_gate(self):
        """11. Missing contact correctly blocks delivery and shows safety messages."""
        # Clean up existing test screening if any
        for sid in ["SCR-NO-PHONE-001", "SCR-NO-EMAIL-001"]:
            scr_ex = self.db.query(ScreeningModel).filter(ScreeningModel.id == sid).first()
            if scr_ex:
                self.db.delete(scr_ex)
                self.db.commit()

        # Create patient without phone
        pat_no_phone = self.client.post(
            "/api/patients",
            json={
                "name": "Patient Without Phone",
                "age": 45,
                "gender": "male",
                "phone": None,
                "email": "has.email@ruralcare.org",
                "village": "Rampur",
            },
        ).json()

        # Create patient without email
        pat_no_email = self.client.post(
            "/api/patients",
            json={
                "name": "Patient Without Email",
                "age": 45,
                "gender": "female",
                "phone": "+91 98555 66677",
                "email": None,
                "village": "Rampur",
            },
        ).json()

        # Create screenings
        self.client.post(
            "/api/screenings",
            json={"id": "SCR-NO-PHONE-001", "patient_id": pat_no_phone["id"], "patient_name": "Patient Without Phone"},
        )
        self.client.post(
            "/api/screenings",
            json={"id": "SCR-NO-EMAIL-001", "patient_id": pat_no_email["id"], "patient_name": "Patient Without Email"},
        )

        # Accept review for both so doctor gate passes
        from app.review_service import process_doctor_review
        from app.schemas import DoctorReviewRequest
        process_doctor_review(
            DoctorReviewRequest(screening_id="SCR-NO-PHONE-001", action="ACCEPT", reviewer_id="DOC-SWAMINATHAN", reviewer_name="Dr. Swaminathan"),
            original_ai_result="Moderate",
            original_confidence=0.85,
            role="doctor",
            db=self.db,
        )
        process_doctor_review(
            DoctorReviewRequest(screening_id="SCR-NO-EMAIL-001", action="ACCEPT", reviewer_id="DOC-SWAMINATHAN", reviewer_name="Dr. Swaminathan"),
            original_ai_result="Moderate",
            original_confidence=0.85,
            role="doctor",
            db=self.db,
        )

        # WhatsApp for SCR-NO-PHONE-001 should block sending
        wa_res = self.client.get("/api/reports/SCR-NO-PHONE-001/whatsapp/status")
        self.assertEqual(wa_res.status_code, 200)
        wa_data = wa_res.json()
        self.assertFalse(wa_data["can_send"])
        block_msg = (wa_data.get("block_reason") or wa_data.get("recipient_status") or "").lower()
        self.assertIn("mobile number not available", block_msg)

        # Email for SCR-NO-EMAIL-001 should block sending
        em_res = self.client.get("/api/reports/SCR-NO-EMAIL-001/email/status")
        self.assertEqual(em_res.status_code, 200)
        em_data = em_res.json()
        self.assertFalse(em_data["can_send"])
        block_msg_em = (em_data.get("block_reason") or em_data.get("recipient_status") or "").lower()
        self.assertIn("email address not available", block_msg_em)

    def test_12_existing_patients_without_email_remain_valid(self):
        """12. Existing patients without email remain valid and operable for WhatsApp."""
        wa_res = self.client.get("/api/reports/SCR-NO-EMAIL-001/whatsapp/status")
        self.assertEqual(wa_res.status_code, 200)
        self.assertTrue(wa_res.json()["can_send"])
        self.assertEqual(wa_res.json()["recipient_phone"], "+919855566677")

    def test_13_patient_specific_contact_isolation(self):
        """13. Multiple screenings for different patients resolve their respective unique contacts."""
        # Patient 1: Sanjay Bhati (SCR-2026-0991)
        wa1 = self.client.get("/api/reports/SCR-2026-0991/whatsapp/status").json()
        em1 = self.client.get("/api/reports/SCR-2026-0991/email/status").json()
        self.assertEqual(wa1["patient_name"], "Sanjay Bhati")
        self.assertEqual(em1["patient_name"], "Sanjay Bhati")

        # Patient 2: Sunita Devi (SCR-2026-0992)
        wa2 = self.client.get("/api/reports/SCR-2026-0992/whatsapp/status").json()
        em2 = self.client.get("/api/reports/SCR-2026-0992/email/status").json()
        self.assertEqual(wa2["patient_name"], "Sunita Devi")
        self.assertEqual(em2["patient_name"], "Sunita Devi")

        # Patient 3: Devendra Mehra (SCR-2026-1025)
        wa3 = self.client.get("/api/reports/SCR-2026-1025/whatsapp/status").json()
        em3 = self.client.get("/api/reports/SCR-2026-1025/email/status").json()
        self.assertEqual(wa3["patient_name"], "Devendra Mehra")
        self.assertEqual(wa3["recipient_phone"], "+919877766554")
        self.assertEqual(em3["patient_name"], "Devendra Mehra")
        self.assertEqual(em3["recipient_email"], "devendra.mehra@ruralcare.org")

        # Assert no cross-contamination of contact values
        self.assertNotEqual(wa1["recipient_phone"], wa2["recipient_phone"])
        self.assertNotEqual(wa2["recipient_phone"], wa3["recipient_phone"])
        self.assertNotEqual(em1["recipient_email"], em2["recipient_email"])
        self.assertNotEqual(em2["recipient_email"], em3["recipient_email"])


if __name__ == "__main__":
    unittest.main()
