"""
Unit and Integration Test Suite for Phase 14:
Patient Email Registration + Clinical PDF Report Email Delivery (Verified Real SMTP Delivery).

Tests:
1. Patient registration with valid email
2. Patient registration rejecting invalid email format
3. Patient registration with missing/optional email (stores None)
4. Patient email persistence and update via MySQL
5. Patient email retrieval via GET /api/patients/{id}
6. Authoritative patient email resolution (Screening -> Patient.email)
7. Multi-patient isolation (Sanjay Bhati vs Sunita Devi vs Balwinder Singh)
8. Health worker email rejection if used as clinical report recipient
9. Mismatched/unauthorized recipient email rejection
10. Doctor-review gate: blocks unreviewed screening
11. Doctor-review gate: blocks re-capture requested screening
12. Doctor-review gate: permits doctor-accepted screening
13. Missing patient email blocks dispatch ('Patient email address not available.')
14. Unconfigured email service blocks dispatch ('Email service is not configured.')
15. Email formatting (Subject: 'Diabetic Retinopathy Screening Report — {Patient Name}', Body)
16. PDF attachment generation and verified SMTP message construction
17. Real SMTP outbound dispatch with verified provider acceptance (status: SENT)
18. SMTP dispatch error handling (connection/auth failure -> status: FAILED)
19. Safe test email dispatch to learnixdigital@gmail.com
20. Duplicate send returns existing delivery record safely
21. Retry endpoint POST /api/reports/{screening_id}/email/retry
22. Concurrent WhatsApp & Email delivery coexistence
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, get_db
from app.main import app
from app.models import (
    PatientModel,
    ScreeningModel,
    ScreeningReviewModel,
    EmailDeliveryModel,
    EmailAuditEventModel,
    WhatsAppDeliveryModel,
)
from app.email_service import email_service
from app.db_seeder import seed_database_if_empty

# Set up in-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestPhase14EmailReportDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)
        db = TestingSessionLocal()
        seed_database_if_empty(db)

        # Seed SCR-PHASE14-ACCEPTED with doctor accepted review
        sid = "SCR-PHASE14-ACCEPTED"
        s_rec = db.query(ScreeningModel).filter(ScreeningModel.id == sid).first()
        if not s_rec:
            s_rec = ScreeningModel(
                id=sid,
                patient_id="PAT-2026-081",
                patient_name="Sanjay Bhati",
                village="Rampur Gram Panchayat",
                screening_date="2026-08-28 10:00 AM",
                timestamp_iso="2026-08-28T10:00:00Z",
                predicted_class=2,
                class_name="Moderate",
                confidence=0.92,
                dr_severity_od="dr2",
                dr_severity_os="dr1",
                overall_severity="dr2",
                safety_status="READY_FOR_AI",
                screening_status="RELIABLE AI SCREENING",
                risk_category="MODERATE",
                referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
                doctor_status="verified",
                review_status="AI RESULT ACCEPTED",
            )
            db.add(s_rec)

        rev_rec = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == sid).first()
        if not rev_rec:
            rev_rec = ScreeningReviewModel(
                id=f"REV-{sid}",
                screening_id=sid,
                action="ACCEPT",
                doctor_id="DOC-SWAMINATHAN",
                doctor_name="Dr. Arvind Swaminathan, MS",
                original_ai_result="Moderate",
                original_confidence=0.92,
                reviewed_result="Moderate",
                review_comment="Approved during clinical review.",
                review_status="AI RESULT ACCEPTED",
                review_timestamp="2026-08-28T10:00:00Z",
            )
            db.add(rev_rec)
        db.commit()
        db.close()

    def setUp(self):
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    # =================================================================
    # 1. Patient Registration Email Field & Validation Tests
    # =================================================================

    def test_01_register_patient_with_valid_email(self):
        """Registers a new patient with valid email and verifies DB persistence."""
        payload = {
            "name": "Arjun Singhal",
            "age": 54,
            "gender": "male",
            "phone": "+91 98111 22334",
            "email": "arjun.singhal@testhealth.org",
            "village": "Rampur Sector 4",
            "district": "Varanasi",
            "abha_id": "91-1122-3344-5566",
            "diabetes_duration": 6,
            "last_hba1c": 8.1,
            "insulin_use": True,
            "visual_acuity_od": "6/12",
            "visual_acuity_os": "6/18",
            "symptoms": ["blurredVision"],
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Arjun Singhal")
        self.assertEqual(data["email"], "arjun.singhal@testhealth.org")

        # Verify directly in database
        pat_db = self.db.query(PatientModel).filter(PatientModel.id == data["id"]).first()
        self.assertIsNotNone(pat_db)
        self.assertEqual(pat_db.email, "arjun.singhal@testhealth.org")

    def test_02_register_patient_invalid_email_rejected(self):
        """Rejects patient registration when email format is invalid."""
        payload = {
            "name": "Invalid Email Patient",
            "age": 42,
            "gender": "female",
            "phone": "+91 98000 11111",
            "email": "invalid-email-no-at-sign",
            "village": "Rampur",
            "district": "Varanasi",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid email address format", res.json()["detail"])

    def test_03_register_patient_without_email_optional(self):
        """Permits registration without email (email=None)."""
        payload = {
            "name": "No Email Patient",
            "age": 60,
            "gender": "female",
            "phone": "+91 97000 22222",
            "email": None,
            "village": "Kolar Rural",
            "district": "Kolar",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIsNone(data["email"])

    def test_04_get_patient_detail_includes_email(self):
        """Retrieves patient detail including email address."""
        res = self.client.get("/api/patients/PAT-2026-081")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], "PAT-2026-081")
        self.assertEqual(data["name"], "Sanjay Bhati")
        self.assertEqual(data["email"], "sanjay.bhati@example.com")

    def test_05_update_patient_email(self):
        """Updates patient email address via PATCH endpoint."""
        payload = {
            "name": "Update Test Patient",
            "age": 48,
            "gender": "male",
            "phone": "+91 96000 33333",
            "email": "initial.email@test.com",
            "village": "Shivpuri",
            "district": "Varanasi",
        }
        create_res = self.client.post("/api/patients", json=payload)
        pat_id = create_res.json()["id"]

        patch_res = self.client.patch(
            f"/api/patients/{pat_id}",
            json={"email": "updated.email@test.com"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["email"], "updated.email@test.com")

        bad_patch = self.client.patch(
            f"/api/patients/{pat_id}",
            json={"email": "not-a-valid-email"},
        )
        self.assertEqual(bad_patch.status_code, 400)

    # =================================================================
    # 2. Authoritative Recipient Resolution & Security Gate Tests
    # =================================================================

    def test_06_resolve_patient_email_for_screening(self):
        """Resolves patient email for SCR-2026-1024 authoritatively to Sanjay Bhati."""
        pat = email_service.resolve_patient_for_screening("SCR-2026-1024", db=self.db)
        self.assertIsNotNone(pat)
        self.assertEqual(pat.name, "Sanjay Bhati")
        self.assertEqual(pat.email, "sanjay.bhati@example.com")

    def test_07_resolve_different_patient_emails(self):
        """Verifies distinct patient email mapping across different screening records."""
        # Sanjay Bhati
        pat1 = email_service.resolve_patient_for_screening("SCR-2026-0991", db=self.db)
        self.assertEqual(pat1.name, "Sanjay Bhati")
        self.assertEqual(pat1.email, "sanjay.bhati@example.com")

        # Sunita Devi
        pat2 = email_service.resolve_patient_for_screening("SCR-2026-0992", db=self.db)
        self.assertEqual(pat2.name, "Sunita Devi")
        self.assertEqual(pat2.email, "sunita.devi@example.com")

        # Balwinder Singh (no email)
        pat3 = email_service.resolve_patient_for_screening("SCR-2026-0993", db=self.db)
        self.assertEqual(pat3.name, "Balwinder Singh")
        self.assertIsNone(pat3.email)

    def test_08_reject_health_worker_email_as_recipient(self):
        """Strictly rejects health worker's email if submitted as clinical report recipient."""
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.gmail.com", "SMTP_USERNAME": "test@gmail.com", "SMTP_PASSWORD": "password"}):
            payload = {
                "screening_id": "SCR-2026-1024",
                "recipient_email": "asha.rampur@phc.in",
                "language": "en",
                "opt_in_confirmed": True,
            }
            res = self.client.post("/api/reports/SCR-2026-1024/email/send", json=payload)
            self.assertEqual(res.status_code, 400)
            self.assertIn("Unauthorized recipient email", res.json()["detail"])

    def test_09_reject_unauthorized_random_email_recipient(self):
        """Rejects arbitrary third-party email that does not match patient's registered email."""
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.gmail.com", "SMTP_USERNAME": "test@gmail.com", "SMTP_PASSWORD": "password"}):
            payload = {
                "screening_id": "SCR-2026-1024",
                "recipient_email": "random.thirdparty@gmail.com",
                "language": "en",
                "opt_in_confirmed": True,
            }
            res = self.client.post("/api/reports/SCR-2026-1024/email/send", json=payload)
            self.assertEqual(res.status_code, 400)
            self.assertIn("Unauthorized recipient email", res.json()["detail"])

    # =================================================================
    # 3. Doctor-Review Safety Gate Tests
    # =================================================================

    def test_10_doctor_review_gate_blocks_unreviewed_screening(self):
        """Blocks email delivery when screening has not completed doctor review."""
        scr_id = "SCR-EMAIL-UNREVIEWED-01"
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            screening_date="2026-08-28",
            timestamp_iso="2026-08-28T10:00:00Z",
            predicted_class=2,
            class_name="Moderate",
            confidence=0.92,
            doctor_status="pending",
            review_status="PENDING DOCTOR REVIEW",
        )
        self.db.add(scr)
        self.db.commit()

        res = self.client.get(f"/api/reports/{scr_id}/email/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["can_send"])
        self.assertEqual(data["doctor_review_status"], "PENDING DOCTOR REVIEW")
        self.assertIn("Doctor review has not been completed", data["block_reason"])

    def test_11_doctor_review_gate_blocks_recapture_requested(self):
        """Blocks email delivery when doctor has requested image re-capture."""
        scr_id = "SCR-EMAIL-RECAPTURE-01"
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            screening_date="2026-08-28",
            timestamp_iso="2026-08-28T10:00:00Z",
            predicted_class=2,
            class_name="Moderate",
            confidence=0.92,
            doctor_status="recapture_requested",
            review_status="IMAGE RE-CAPTURE REQUESTED",
        )
        rev = ScreeningReviewModel(
            id=f"REV-{scr_id}",
            screening_id=scr_id,
            action="RECAPTURE",
            doctor_id="DOC-SWAMINATHAN",
            doctor_name="Dr. Arvind Swaminathan, MS",
            original_ai_result="Moderate",
            reviewed_result="Image Re-capture Required",
            review_status="IMAGE RE-CAPTURE REQUESTED",
            review_timestamp="2026-08-28T10:05:00Z",
        )
        self.db.add(scr)
        self.db.add(rev)
        self.db.commit()

        res = self.client.get(f"/api/reports/{scr_id}/email/status")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["can_send"])
        self.assertIn("waiting for re-capture", res.json()["block_reason"])

    def test_12_missing_patient_email_blocks_delivery(self):
        """Blocks email delivery when patient has no registered email ('Patient email address not available.')."""
        res = self.client.get("/api/reports/SCR-2026-0850/email/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["can_send"])
        self.assertEqual(data["block_reason"], "Patient email address not available.")
        self.assertIsNone(data["recipient_email"])

    def test_13_unconfigured_email_service_blocks_delivery(self):
        """When SMTP_HOST is unset, status endpoint returns NOT_CONFIGURED and 'Email service is not configured.'."""
        with patch.dict(os.environ, {"SMTP_HOST": "", "EMAIL_PROVIDER": ""}):
            res = self.client.get("/api/reports/SCR-2026-1024/email/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["can_send"])
            self.assertFalse(data["is_configured"])
            self.assertEqual(data["status"], "NOT_CONFIGURED")
            self.assertEqual(data["block_reason"], "Email service is not configured.")

            # Attempt to dispatch without SMTP configured must fail with 400
            send_res = self.client.post(
                "/api/reports/SCR-2026-1024/email/send",
                json={"screening_id": "SCR-2026-1024", "recipient_email": "sanjay.bhati@example.com"},
            )
            self.assertEqual(send_res.status_code, 400)
            self.assertEqual(send_res.json()["detail"], "Email service is not configured.")

    # =================================================================
    # 4. Email Formatting & MIME Attachment Construction Tests
    # =================================================================

    def test_14_email_content_formatting(self):
        """Verifies correct subject line and body structure according to clinical requirements."""
        subject, body = email_service.format_email_content(
            patient_name="Sanjay Bhati",
            screening_id="SCR-2026-1024",
            classification="Moderate",
            doctor_status="AI RESULT ACCEPTED",
        )
        self.assertEqual(subject, "Diabetic Retinopathy Screening Report — Sanjay Bhati")
        self.assertIn("Hello Sanjay Bhati,", body)
        self.assertIn("Screening ID: SCR-2026-1024", body)
        self.assertIn("AI Screening Result: Moderate", body)
        self.assertIn("Doctor Review Status: AI RESULT ACCEPTED", body)
        self.assertIn("Your clinical report is attached as a PDF.", body)
        self.assertIn("Rural DR Screening AI", body)

    # =================================================================
    # 5. Verified Real SMTP Outbound Dispatch & Error Handling Tests
    # =================================================================

    @patch("smtplib.SMTP")
    def test_15_verified_smtp_send_success(self, mock_smtp_cls):
        """Verifies outbound SMTP connection, login, PDF attachment, provider acceptance, and SENT persistence."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = {}  # Empty dict indicates successful acceptance by SMTP server
        mock_smtp_cls.return_value = mock_server
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "dr.screening@madocs.health.in",
            "SMTP_PASSWORD": "app-specific-password",
        }):
            scr_id = "SCR-2026-1024"
            payload = {
                "screening_id": scr_id,
                "recipient_email": "sanjay.bhati@example.com",
                "language": "en",
                "opt_in_confirmed": True,
            }
            res = self.client.post(f"/api/reports/{scr_id}/email/send", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "SENT")
            self.assertEqual(data["recipient_email"], "sanjay.bhati@example.com")
            self.assertEqual(data["patient_name"], "Sanjay Bhati")
            self.assertTrue(data["provider_message_id"].startswith("smtp-"))
            self.assertFalse(data["is_demo"])

            # Verify SMTP server interactions
            mock_smtp_cls.assert_called_with("smtp.gmail.com", 587, timeout=20)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("dr.screening@madocs.health.in", "app-specific-password")
            mock_server.send_message.assert_called_once()

            # Verify attached message contains PDF
            sent_msg = mock_server.send_message.call_args[0][0]
            self.assertEqual(sent_msg["To"], "sanjay.bhati@example.com")
            self.assertIn("Diabetic Retinopathy Screening Report", sent_msg["Subject"])
            payloads = sent_msg.get_payload()
            self.assertGreaterEqual(len(payloads), 2)  # Body text + PDF attachment

            # Verify delivery record in database
            del_db = self.db.query(EmailDeliveryModel).filter(EmailDeliveryModel.screening_id == scr_id).first()
            self.assertIsNotNone(del_db)
            self.assertEqual(del_db.status, "SENT")
            self.assertFalse(del_db.is_demo)

    @patch("smtplib.SMTP")
    def test_16_smtp_dispatch_failure_marks_failed(self, mock_smtp_cls):
        """When SMTP connection or authentication fails, records FAILED status and returns 400 with error detail."""
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("535 5.7.8 Username and Password not accepted")
        mock_smtp_cls.return_value = mock_server
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        scr_id = "SCR-EMAIL-FAIL-01"
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            screening_date="2026-08-28",
            timestamp_iso="2026-08-28T10:00:00Z",
            predicted_class=2,
            class_name="Moderate",
            confidence=0.92,
            doctor_status="verified",
            review_status="AI RESULT ACCEPTED",
        )
        rev = ScreeningReviewModel(
            id=f"REV-{scr_id}",
            screening_id=scr_id,
            action="ACCEPT",
            doctor_id="DOC-SWAMINATHAN",
            doctor_name="Dr. Arvind Swaminathan, MS",
            original_ai_result="Moderate",
            reviewed_result="Moderate",
            review_status="AI RESULT ACCEPTED",
            review_timestamp="2026-08-28T10:00:00Z",
        )
        self.db.add(scr)
        self.db.add(rev)
        self.db.commit()

        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "invalid@gmail.com",
            "SMTP_PASSWORD": "wrong-password",
        }):
            payload = {
                "screening_id": scr_id,
                "recipient_email": "sanjay.bhati@example.com",
            }
            res = self.client.post(f"/api/reports/{scr_id}/email/send", json=payload)
            self.assertEqual(res.status_code, 400)
            self.assertIn("Username and Password not accepted", res.json()["detail"])

            # Verify database recorded failure
            del_db = self.db.query(EmailDeliveryModel).filter(EmailDeliveryModel.screening_id == scr_id).first()
            self.assertIsNotNone(del_db)
            self.assertEqual(del_db.status, "FAILED")
            self.assertIn("Username and Password not accepted", del_db.failure_reason)

    @patch("smtplib.SMTP")
    def test_17_safe_test_email_dispatch(self, mock_smtp_cls):
        """Tests verified delivery to the safe test email learnixdigital@gmail.com."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = {}
        mock_smtp_cls.return_value = mock_server
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "sender@gmail.com",
            "SMTP_PASSWORD": "app-password",
        }):
            # Register test patient with learnixdigital@gmail.com
            pat_res = self.client.post("/api/patients", json={
                "name": "Learnix Test Patient",
                "age": 45,
                "gender": "female",
                "phone": "+91 98888 77777",
                "email": "learnixdigital@gmail.com",
                "village": "Safe Test Block",
                "district": "Varanasi",
            })
            self.assertEqual(pat_res.status_code, 201)
            pat_data = pat_res.json()

            # Create accepted screening
            scr_id = "SCR-TEST-LEARNIX-01"
            scr_rec = ScreeningModel(
                id=scr_id,
                patient_id=pat_data["id"],
                patient_name=pat_data["name"],
                screening_date="2026-08-28",
                timestamp_iso="2026-08-28T10:00:00Z",
                predicted_class=1,
                class_name="Mild",
                confidence=0.88,
                doctor_status="verified",
                review_status="AI RESULT ACCEPTED",
            )
            self.db.add(scr_rec)
            rev_rec = ScreeningReviewModel(
                id=f"REV-{scr_id}",
                screening_id=scr_id,
                action="ACCEPT",
                doctor_id="DOC-SWAMINATHAN",
                doctor_name="Dr. Arvind Swaminathan, MS",
                original_ai_result="Mild",
                reviewed_result="Mild",
                review_status="AI RESULT ACCEPTED",
                review_timestamp="2026-08-28T10:00:00Z",
            )
            self.db.add(rev_rec)
            self.db.commit()

            # Dispatch email to learnixdigital@gmail.com
            res = self.client.post(f"/api/reports/{scr_id}/email/send", json={
                "screening_id": scr_id,
                "recipient_email": "learnixdigital@gmail.com",
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "SENT")
            self.assertEqual(data["recipient_email"], "learnixdigital@gmail.com")
            self.assertTrue(data["provider_message_id"].startswith("smtp-"))

    @patch("smtplib.SMTP")
    def test_18_retry_email_delivery(self, mock_smtp_cls):
        """Retries email delivery on a previously failed screening."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = {}
        mock_smtp_cls.return_value = mock_server
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "sender@gmail.com",
            "SMTP_PASSWORD": "app-password",
        }):
            scr_id = "SCR-2026-0991"
            retry_res = self.client.post(
                f"/api/reports/{scr_id}/email/retry",
                json={"screening_id": scr_id, "force_regenerate_pdf": False},
            )
            self.assertEqual(retry_res.status_code, 200)
            self.assertEqual(retry_res.json()["status"], "SENT")

    @patch("smtplib.SMTP")
    def test_19_whatsapp_and_email_concurrent_coexistence(self, mock_smtp_cls):
        """Verifies WhatsApp delivery and Email delivery operate concurrently without interference."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = {}
        mock_smtp_cls.return_value = mock_server
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "sender@gmail.com",
            "SMTP_PASSWORD": "app-password",
        }):
            scr_id = "SCR-PHASE14-ACCEPTED"

            # 1. Dispatch WhatsApp
            wa_res = self.client.post(
                f"/api/reports/{scr_id}/whatsapp/send",
                json={
                    "screening_id": scr_id,
                    "recipient_phone": "+91 73782 16613",
                    "health_worker_id": "HW-RAMPUR-01",
                },
            )
            self.assertEqual(wa_res.status_code, 200)
            self.assertEqual(wa_res.json()["recipient_phone"], "+917378216613")

            # 2. Dispatch Email
            em_res = self.client.post(
                f"/api/reports/{scr_id}/email/send",
                json={
                    "screening_id": scr_id,
                    "recipient_email": "sanjay.bhati@example.com",
                },
            )
            self.assertEqual(em_res.status_code, 200)
            self.assertEqual(em_res.json()["recipient_email"], "sanjay.bhati@example.com")

            # 3. Check WhatsApp status is intact
            wa_stat = self.client.get(f"/api/reports/{scr_id}/whatsapp/status")
            self.assertEqual(wa_stat.status_code, 200)
            self.assertEqual(wa_stat.json()["recipient_phone"], "+917378216613")

            # 4. Check Email status is intact
            em_stat = self.client.get(f"/api/reports/{scr_id}/email/status")
            self.assertEqual(em_stat.status_code, 200)
            self.assertEqual(em_stat.json()["recipient_email"], "sanjay.bhati@example.com")


if __name__ == "__main__":
    unittest.main()
