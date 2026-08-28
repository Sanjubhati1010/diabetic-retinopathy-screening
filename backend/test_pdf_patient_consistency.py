"""
Regression & Patient Data Consistency Test Suite for Generated Clinical PDF Reports.
Validates:
1. Complete, 100% patient data consistency throughout all sections of the generated PDF report.
2. Complete absence of fallback/mock patient data (e.g. Ramesh Kumar Verma, 91-4829-1029-4821, 8.6%).
3. Multi-patient isolation (Patient A report contains strictly Patient A data and zero Patient B data; Patient B report contains strictly Patient B data and zero Patient A data).
4. Safety gate: Broken/missing screening-patient linkage fails safely with 'Patient/report data could not be verified for this screening.'.
5. Cross-patient delivery security gates for Email and WhatsApp.
"""

import unittest
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import PatientModel, ScreeningModel, DoctorModel, HealthWorkerModel, ScreeningReviewModel
from app.pdf_service import pdf_service
from app.whatsapp_service import whatsapp_service
from app.email_service import email_service
from app.review_service import process_doctor_review
from app.schemas import DoctorReviewRequest


class TestPdfPatientConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Ensure active reviewing doctor and health worker exist
        doc = cls.db.query(DoctorModel).filter(DoctorModel.id == "DOC-ARVIND-001").first()
        if not doc:
            doc = DoctorModel(
                id="DOC-ARVIND-001",
                name="Dr. Arvind Swaminathan, MS",
                title="Consultant Ophthalmologist",
                specialization="Retina Specialist",
                hospital="Tele-Ophthalmology Network",
                location="Varanasi",
                languages_json='["Hindi", "English"]',
                working_days_json='["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]',
            )
            cls.db.add(doc)

        hw = cls.db.query(HealthWorkerModel).filter(HealthWorkerModel.id == "HW-RAMPUR-01").first()
        if not hw:
            hw = HealthWorkerModel(
                id="HW-RAMPUR-01",
                name="Pooja Sharma (ASHA Worker)",
                village="Rampur Gram Panchayat",
                phc_center="Primary Health Center Rampur",
                phone="+919876543210",
                whatsapp_opt_in=True,
            )
            cls.db.add(hw)

        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _extract_text_from_pdf(self, filepath: Path) -> str:
        """Extracts complete text from a PDF file using pypdf."""
        reader = PdfReader(str(filepath))
        return " ".join([page.extract_text() for page in reader.pages])

    def _cleanup_records(self, screening_id: str, patient_id: str):
        from app.models import (
            WhatsAppAuditEventModel,
            WhatsAppDeliveryModel,
            EmailAuditEventModel,
            EmailDeliveryModel,
            ReportModel,
            ReviewAuditEventModel,
            ScreeningReviewModel,
        )
        self.db.query(WhatsAppAuditEventModel).filter(WhatsAppAuditEventModel.screening_id == screening_id).delete()
        self.db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id == screening_id).delete()
        self.db.query(EmailAuditEventModel).filter(EmailAuditEventModel.screening_id == screening_id).delete()
        self.db.query(EmailDeliveryModel).filter(EmailDeliveryModel.screening_id == screening_id).delete()
        self.db.query(ReportModel).filter(ReportModel.screening_id == screening_id).delete()
        self.db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.screening_id == screening_id).delete()
        self.db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == screening_id).delete()
        self.db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).delete()
        self.db.query(PatientModel).filter(PatientModel.id == patient_id).delete()
        self.db.commit()

    def test_01_create_patient_a_and_screening_a(self):
        """1. Register distinct Patient A and generate Screening A."""
        self._cleanup_records("SCR-TEST-PDF-A01", "PAT-TEST-PDF-A01")

        pat_a = PatientModel(
            id="PAT-TEST-PDF-A01",
            name="Aarav Sharma",
            age=27,
            gender="male",
            abha_id="ABHA-AARAV-1001",
            phone="+91 98111 22334",
            email="aarav.sharma@ruralcare.org",
            village="Kashi Puram",
            district="Varanasi",
            diabetes_duration=3,
            last_hba1c=5.9,
            insulin_use=False,
            visual_acuity_od="6/6",
            visual_acuity_os="6/9",
            symptoms_json='["Mild blurriness"]',
            registered_date="2026-08-28",
        )
        self.db.add(pat_a)

        scr_a = ScreeningModel(
            id="SCR-TEST-PDF-A01",
            patient_id="PAT-TEST-PDF-A01",
            patient_name="Aarav Sharma",
            village="Kashi Puram",
            screening_date="2026-08-28",
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            predicted_class=1,
            class_name="Mild DR",
            confidence=0.92,
            doctor_status="verified",
            review_status="AI RESULT ACCEPTED",
        )
        self.db.add(scr_a)
        self.db.commit()

        # Complete formal doctor review gate
        process_doctor_review(
            request=DoctorReviewRequest(
                screening_id="SCR-TEST-PDF-A01",
                action="ACCEPT",
                reviewer_name="Dr. Arvind Swaminathan, MS",
                reviewer_id="DOC-ARVIND-001",
                review_comment="Mild non-proliferative diabetic retinopathy verified. Annual follow-up advised.",
            ),
            role="doctor",
            original_ai_result="Mild DR",
            original_confidence=0.92,
            db=self.db,
        )

    def test_02_create_patient_b_and_screening_b(self):
        """2. Register distinct Patient B and generate Screening B."""
        self._cleanup_records("SCR-TEST-PDF-B02", "PAT-TEST-PDF-B02")

        pat_b = PatientModel(
            id="PAT-TEST-PDF-B02",
            name="Sunita Devi",
            age=68,
            gender="female",
            abha_id="ABHA-SUNITA-2002",
            phone="+91 98777 66554",
            email="sunita.devi@ruralcare.org",
            village="Rampur Central",
            district="Varanasi",
            diabetes_duration=14,
            last_hba1c=9.8,
            insulin_use=True,
            visual_acuity_od="6/24",
            visual_acuity_os="6/36",
            symptoms_json='["Floaters", "Night vision loss"]',
            registered_date="2026-08-28",
        )
        self.db.add(pat_b)

        scr_b = ScreeningModel(
            id="SCR-TEST-PDF-B02",
            patient_id="PAT-TEST-PDF-B02",
            patient_name="Sunita Devi",
            village="Rampur Central",
            screening_date="2026-08-28",
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            predicted_class=3,
            class_name="Severe DR",
            confidence=0.96,
            doctor_status="verified",
            review_status="AI RESULT ACCEPTED",
        )
        self.db.add(scr_b)
        self.db.commit()

        # Complete formal doctor review gate
        process_doctor_review(
            request=DoctorReviewRequest(
                screening_id="SCR-TEST-PDF-B02",
                action="ACCEPT",
                reviewer_name="Dr. Arvind Swaminathan, MS",
                reviewer_id="DOC-ARVIND-001",
                review_comment="Severe NPDR with macular threat verified. Urgent retinal specialist referral required.",
            ),
            role="doctor",
            original_ai_result="Severe DR",
            original_confidence=0.96,
            db=self.db,
        )

    def test_03_pdf_a_contains_only_patient_a_data(self):
        """3. PDF for Screening A contains ONLY Patient A data throughout all sections and NO Patient B or fallback data."""
        res = self.client.post("/api/reports/SCR-TEST-PDF-A01/pdf")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["screening_id"], "SCR-TEST-PDF-A01")
        self.assertIn("/api/reports/SCR-TEST-PDF-A01/document", data["pdf_url"])

        pdf_path = pdf_service.output_dir / "SCR-TEST-PDF-A01_clinical_report.pdf"
        self.assertTrue(pdf_path.exists())

        pdf_text = self._extract_text_from_pdf(pdf_path)

        # Assert Patient A data is present
        self.assertIn("Aarav Sharma", pdf_text)
        self.assertIn("27 Yrs / Male", pdf_text)
        self.assertIn("ABHA-AARAV-1001", pdf_text)
        self.assertIn("Kashi Puram", pdf_text)
        self.assertIn("5.9%", pdf_text)
        self.assertIn("3 Years Known", pdf_text)
        self.assertIn("OD: 6/6 | OS: 6/9", pdf_text)
        self.assertIn("SCR-TEST-PDF-A01", pdf_text)
        self.assertIn("Mild DR", pdf_text)

        # Assert Patient B data is ABSENT
        self.assertNotIn("Sunita Devi", pdf_text)
        self.assertNotIn("68 Yrs", pdf_text)
        self.assertNotIn("ABHA-SUNITA-2002", pdf_text)
        self.assertNotIn("Rampur Central", pdf_text)
        self.assertNotIn("9.8%", pdf_text)
        self.assertNotIn("14 Years Known", pdf_text)
        self.assertNotIn("6/24", pdf_text)
        self.assertNotIn("SCR-TEST-PDF-B02", pdf_text)

        # Assert legacy hardcoded fallback data is ABSENT
        self.assertNotIn("Ramesh Kumar Verma", pdf_text)
        self.assertNotIn("91-4829-1029-4821", pdf_text)
        self.assertNotIn("8.6%", pdf_text)
        self.assertNotIn("58 Yrs", pdf_text)
        self.assertNotIn("6/12", pdf_text)
        self.assertNotIn("6/18", pdf_text)

    def test_04_pdf_b_contains_only_patient_b_data(self):
        """4. PDF for Screening B contains ONLY Patient B data throughout all sections and NO Patient A or fallback data."""
        res = self.client.post("/api/reports/SCR-TEST-PDF-B02/pdf")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["screening_id"], "SCR-TEST-PDF-B02")

        pdf_path = pdf_service.output_dir / "SCR-TEST-PDF-B02_clinical_report.pdf"
        self.assertTrue(pdf_path.exists())

        pdf_text = self._extract_text_from_pdf(pdf_path)

        # Assert Patient B data is present
        self.assertIn("Sunita Devi", pdf_text)
        self.assertIn("68 Yrs / Female", pdf_text)
        self.assertIn("ABHA-SUNITA-2002", pdf_text)
        self.assertIn("Rampur Central", pdf_text)
        self.assertIn("9.8%", pdf_text)
        self.assertIn("14 Years Known", pdf_text)
        self.assertIn("OD: 6/24 | OS: 6/36", pdf_text)
        self.assertIn("SCR-TEST-PDF-B02", pdf_text)
        self.assertIn("Severe DR", pdf_text)

        # Assert Patient A data is ABSENT
        self.assertNotIn("Aarav Sharma", pdf_text)
        self.assertNotIn("27 Yrs", pdf_text)
        self.assertNotIn("ABHA-AARAV-1001", pdf_text)
        self.assertNotIn("Kashi Puram", pdf_text)
        self.assertNotIn("5.9%", pdf_text)
        self.assertNotIn("3 Years Known", pdf_text)
        self.assertNotIn("SCR-TEST-PDF-A01", pdf_text)

        # Assert legacy hardcoded fallback data is ABSENT
        self.assertNotIn("Ramesh Kumar Verma", pdf_text)
        self.assertNotIn("91-4829-1029-4821", pdf_text)
        self.assertNotIn("8.6%", pdf_text)
        self.assertNotIn("58 Yrs", pdf_text)

    def test_05_missing_patient_relation_fails_safely(self):
        """5. A screening with broken/missing patient relation fails safely without mixing data."""
        res = self.client.post("/api/reports/SCR-NONEXISTENT-999/pdf")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Patient/report data could not be verified", res.json()["detail"])

        # Calling generate_clinical_report directly without patient_data raises ValueError
        with self.assertRaises(ValueError) as ctx:
            pdf_service.generate_clinical_report(screening_data={"id": "SCR-EMPTY"}, patient_data=None)
        self.assertIn("Patient/report data could not be verified", str(ctx.exception))

    def test_06_cross_patient_delivery_security_blocks(self):
        """6. Dispatches to wrong/mismatched patient phone or email are strictly blocked."""
        # Attempt to send Patient A's report to Patient B's phone
        res_wa = self.client.post(
            "/api/reports/SCR-TEST-PDF-A01/whatsapp/send",
            json={
                "screening_id": "SCR-TEST-PDF-A01",
                "recipient_phone": "+91 98777 66554",  # Patient B's phone
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res_wa.status_code, 400)
        self.assertIn("Unauthorized recipient phone", res_wa.json()["detail"])

        # Attempt to send Patient A's report to Patient B's email
        res_em = self.client.post(
            "/api/reports/SCR-TEST-PDF-A01/email/send",
            json={
                "screening_id": "SCR-TEST-PDF-A01",
                "recipient_email": "sunita.devi@ruralcare.org",  # Patient B's email
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res_em.status_code, 400)
        self.assertIn("Unauthorized recipient email", res_em.json()["detail"])


if __name__ == "__main__":
    unittest.main()
