import unittest
import os
from pathlib import Path
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, SessionLocal
from app.models import (
    PatientModel,
    ScreeningModel,
    ScreeningReviewModel,
    HealthWorkerModel,
    DoctorModel,
)
from app.pdf_service import pdf_service, resolve_image_flowable
from app.email_service import email_service
from app.whatsapp_service import whatsapp_service


class TestFullFidelityClinicalPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db: Session = SessionLocal()

        # Seed Doctor
        doc = cls.db.query(DoctorModel).filter(DoctorModel.id == "DOC-SWAMINATHAN-01").first()
        if not doc:
            doc = DoctorModel(
                id="DOC-SWAMINATHAN-01",
                name="Dr. Arvind Swaminathan, MS",
                title="Chief Medical Officer",
                specialization="Retina Specialist & Consultant",
                hospital="Tele-Ophthalmology Network",
                location="Varanasi",
                languages_json='["Hindi", "English"]',
                working_days_json='["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]',
            )
            cls.db.add(doc)

        # Seed Health Worker
        hw = cls.db.query(HealthWorkerModel).filter(HealthWorkerModel.id == "HW-RAMPUR-TEST-01").first()
        if not hw:
            hw = HealthWorkerModel(
                id="HW-RAMPUR-TEST-01",
                name="Pooja Sharma (ASHA Worker)",
                role="health_worker",
                phone="+91 98765 43210",
                village="Rampur Gram Panchayat",
                phc_center="Primary Health Center Rampur Community Unit",
                whatsapp_opt_in=True,
            )
            cls.db.add(hw)

        # Seed Patient A (Primary test patient)
        cls.pat_a = cls.db.query(PatientModel).filter(PatientModel.id == "PAT-FULL-FIDELITY-001").first()
        if not cls.pat_a:
            cls.pat_a = PatientModel(
                id="PAT-FULL-FIDELITY-001",
                name="Vikramaditya Sharma",
                age=62,
                gender="male",
                abha_id="91-5544-3322-1100",
                village="Rampur Gram Panchayat",
                district="Varanasi",
                phone="+91 98765 11111",
                email="vikram.sharma@example.com",
                registered_date="2026-08-28",
                diabetes_duration=12,
                last_hba1c=8.4,
                insulin_use=True,
                visual_acuity_od="6/12",
                visual_acuity_os="6/9",
            )
            cls.db.add(cls.pat_a)

        # Seed Screening 1 (Baseline)
        cls.scr_base = cls.db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-FIDELITY-BASE").first()
        if not cls.scr_base:
            cls.scr_base = ScreeningModel(
                id="SCR-FIDELITY-BASE",
                patient_id="PAT-FULL-FIDELITY-001",
                patient_name="Vikramaditya Sharma",
                village="Rampur Gram Panchayat",
                screening_date="2025-08-15",
                timestamp_iso="2025-08-15T10:00:00Z",
                predicted_class=1,
                class_name="Mild DR",
                confidence=0.89,
                doctor_status="verified",
                review_status="AI RESULT ACCEPTED",
                image_od_path="public/samples/eyes.png",
                image_os_path="public/samples/eyes_os.png",
            )
            cls.db.add(cls.scr_base)

        # Seed Screening 2 (Current follow-up)
        cls.scr_current = cls.db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-FIDELITY-CURRENT").first()
        if not cls.scr_current:
            cls.scr_current = ScreeningModel(
                id="SCR-FIDELITY-CURRENT",
                patient_id="PAT-FULL-FIDELITY-001",
                patient_name="Vikramaditya Sharma",
                village="Rampur Gram Panchayat",
                screening_date="2026-08-28",
                timestamp_iso="2026-08-28T14:30:00Z",
                predicted_class=2,
                class_name="Moderate DR",
                confidence=0.87,
                dr_severity_od="Moderate DR",
                dr_severity_os="Mild DR",
                overall_severity="Moderate DR",
                safety_status="READY_FOR_AI",
                screening_status="RELIABLE AI SCREENING",
                risk_category="MODERATE RISK",
                referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
                doctor_status="verified",
                review_status="AI RESULT ACCEPTED",
                image_od_path="public/samples/eyes.png",
                image_os_path="public/samples/eyes_os.png",
            )
            cls.db.add(cls.scr_current)

        # Seed Doctor Review for Current Screening
        cls.rev = cls.db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == "SCR-FIDELITY-CURRENT").first()
        if not cls.rev:
            cls.rev = ScreeningReviewModel(
                id="REV-FIDELITY-CURRENT",
                screening_id="SCR-FIDELITY-CURRENT",
                doctor_id="DOC-SWAMINATHAN-01",
                doctor_name="Dr. Arvind Swaminathan, MS",
                action="ACCEPT",
                review_status="AI RESULT ACCEPTED",
                reviewed_result="Moderate DR",
                original_ai_result="Moderate DR",
                original_confidence=0.87,
                doctor_notes="Verified moderate diabetic retinopathy findings. Early microaneurysms noted in right eye. Continue strict glycaemic control.",
                review_timestamp="2026-08-28 14:45",
            )
            cls.db.add(cls.rev)

        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_generate_full_fidelity_clinical_pdf(self):
        """Verify generation of full-fidelity clinical PDF for screening."""
        pdf_path = pdf_service.generate_clinical_report_for_screening(
            screening_id="SCR-FIDELITY-CURRENT",
            db=self.db,
        )
        self.assertTrue(pdf_path.exists())
        self.assertGreater(pdf_path.stat().st_size, 10000)

        reader = PdfReader(str(pdf_path))
        self.assertGreaterEqual(len(reader.pages), 1)

        # Aggregate text across all pages and normalize whitespace
        raw_text = "\n".join([page.extract_text() for page in reader.pages])
        norm_text = " ".join(raw_text.split())

        # 1. Header & Organization
        self.assertIn("Diabetic Retinopathy Screening", norm_text)
        self.assertIn("SCR-FIDELITY-CURRENT", norm_text)

        # 2. Patient Demographics & Profile
        self.assertIn("1. PATIENT DEMOGRAPHICS & CLINICAL PROFILE", norm_text)
        self.assertIn("Vikramaditya Sharma", norm_text)
        self.assertIn("91-5544-3322-1100", norm_text)
        self.assertIn("62 Yrs", norm_text)
        self.assertIn("12 Years Known", norm_text)
        self.assertIn("8.4%", norm_text)
        self.assertIn("+91 98765 11111", norm_text)

        # 3. AI Diagnostic Assessment & Doctor Review
        self.assertIn("2. AI SCREENING ASSESSMENT & DOCTOR REVIEW", norm_text)
        self.assertIn("AI SCREENING RESULT", norm_text)
        self.assertIn("Moderate DR", norm_text)
        self.assertIn("DOCTOR-REVIEWED STATUS", norm_text)
        self.assertIn("Dr. Arvind Swaminathan, MS", norm_text)

        # 4. Bilateral Retinal Details (OD & OS)
        self.assertIn("3. BILATERAL RETINAL DETAILS", norm_text)
        self.assertIn("Right Eye (OD) Scan", norm_text)
        self.assertIn("Left Eye (OS) Scan", norm_text)
        self.assertIn("Laplacian Sharpness", norm_text)

        # 5. Retinal Images & Grad-CAM Explainability
        self.assertIn("4. RETINAL FUNDUS SCANS & GRAD-CAM EXPLAINABILITY", norm_text)
        self.assertIn("Right Eye (OD) Fundus Scan", norm_text)
        self.assertIn("Left Eye (OS) Fundus Scan", norm_text)
        self.assertIn("Grad-CAM Explainability Heatmap", norm_text)

        # 6. Clinical Evidence & Explainable AI Interpretation
        self.assertIn("5. CLINICAL EVIDENCE & EXPLAINABLE AI INTERPRETATION", norm_text)
        self.assertIn("Explainability Note (Grad-CAM)", norm_text)

        # 7. Longitudinal Previous Screening Context
        self.assertIn("6. PREVIOUS SCREENING CONTEXT", norm_text)
        self.assertIn("SCR-FIDELITY-BASE", norm_text)

        # 8. Doctor Clinical Impression & Remarks
        self.assertIn("7. DOCTOR CLINICAL IMPRESSION & REMARKS", norm_text)
        self.assertIn("Verified moderate diabetic retinopathy findings", norm_text)
        self.assertIn("Digitally Verified & Validated", norm_text)

        # 9. Bilingual Patient Advisory
        self.assertIn("8. BILINGUAL PATIENT ADVISORY", norm_text)
        self.assertIn("Note: This report is an early screening assessment", norm_text)

        # 10. Statutory Clinical Advisory Disclaimer & Signatures
        self.assertIn("MANDATORY CLINICAL ADVISORY", norm_text)
        self.assertIn("Consultant Ophthalmologist", norm_text)

    def test_02_embedded_images_present_in_pdf(self):
        """Verify that retinal images and Grad-CAM are physically embedded into the PDF as image objects."""
        pdf_path = pdf_service.generate_clinical_report_for_screening(
            screening_id="SCR-FIDELITY-CURRENT",
            db=self.db,
        )
        reader = PdfReader(str(pdf_path))

        # Check total embedded images across pages
        total_images = sum(len(page.images) for page in reader.pages)
        self.assertGreaterEqual(total_images, 3, f"Expected at least 3 embedded images, found {total_images}")

    def test_03_no_broken_urls_in_pdf(self):
        """Ensure no broken localhost URLs appear in the PDF text."""
        pdf_path = pdf_service.generate_clinical_report_for_screening(
            screening_id="SCR-FIDELITY-CURRENT",
            db=self.db,
        )
        reader = PdfReader(str(pdf_path))
        full_text = "\n".join([page.extract_text() for page in reader.pages])

        self.assertNotIn("http://localhost", full_text)
        self.assertNotIn("http://127.0.0.1", full_text)

    def test_04_baseline_screening_handling(self):
        """Verify that a screening with no previous records renders a clear baseline examination notice."""
        pat_b = self.db.query(PatientModel).filter(PatientModel.id == "PAT-FIDELITY-BASELINE").first()
        if not pat_b:
            pat_b = PatientModel(
                id="PAT-FIDELITY-BASELINE",
                name="Ananya Roy",
                age=45,
                gender="female",
                abha_id="91-9988-7766-5544",
                village="Shaktinagar Unit",
                phone="+91 98765 22222",
                email="ananya.roy@example.com",
                registered_date="2026-08-28",
            )
            self.db.add(pat_b)
            self.db.commit()

        scr_b = self.db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-FIDELITY-ONLY-01").first()
        if not scr_b:
            scr_b = ScreeningModel(
                id="SCR-FIDELITY-ONLY-01",
                patient_id="PAT-FIDELITY-BASELINE",
                patient_name="Ananya Roy",
                village="Shaktinagar Unit",
                screening_date="2026-08-28",
                timestamp_iso="2026-08-28T15:00:00Z",
                predicted_class=0,
                class_name="No DR",
                confidence=0.96,
                doctor_status="verified",
                review_status="AI RESULT ACCEPTED",
            )
            self.db.add(scr_b)
            self.db.commit()

        rev_b = self.db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == "SCR-FIDELITY-ONLY-01").first()
        if not rev_b:
            rev_b = ScreeningReviewModel(
                id="REV-FIDELITY-ONLY-01",
                screening_id="SCR-FIDELITY-ONLY-01",
                doctor_id="DOC-SWAMINATHAN-01",
                doctor_name="Dr. Arvind Swaminathan, MS",
                action="ACCEPT",
                review_status="AI RESULT ACCEPTED",
                reviewed_result="No DR",
                original_ai_result="No DR",
                original_confidence=0.96,
                doctor_notes="Normal fundus examination. Retinal vascular architecture intact.",
                review_timestamp="2026-08-28 15:10",
            )
            self.db.add(rev_b)
            self.db.commit()

        pdf_path = pdf_service.generate_clinical_report_for_screening(
            screening_id="SCR-FIDELITY-ONLY-01",
            db=self.db,
        )
        self.assertTrue(pdf_path.exists())

        reader = PdfReader(str(pdf_path))
        norm_text = " ".join("\n".join([page.extract_text() for page in reader.pages]).split())

        self.assertIn("Ananya Roy", norm_text)
        self.assertIn("91-9988-7766-5544", norm_text)
        self.assertIn("Baseline Examination", norm_text)
        self.assertIn("No prior screening records on file for this patient", norm_text)


if __name__ == "__main__":
    unittest.main()
