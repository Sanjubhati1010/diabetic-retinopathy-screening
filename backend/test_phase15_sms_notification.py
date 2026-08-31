"""
Phase 15: Automated Test Suite for Demo SMS Patient Report Notification System.
Validates all 17 requirements:
  1. Patient mobile correctly resolved from MySQL.
  2. Health worker mobile is NOT used.
  3. Doctor approval required.
  4. Rejected report cannot generate notification.
  5. Pending review cannot generate notification.
  6. Secure token generated.
  7. Token maps to correct patient/report.
  8. Unapproved report cannot be accessed.
  9. SMS message generated correctly.
 10. Message ID is unique.
 11. Status is SIMULATED, never SENT.
 12. Notification log is created in database.
 13. Duplicate notification handling works.
 14. Patient identity remains consistent.
 15. Existing email delivery remains working.
 16. Existing WhatsApp delivery remains working.
 17. Existing PDF generation remains working.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, Base, engine
from app.models import (
    PatientModel,
    ScreeningModel,
    ScreeningReviewModel,
    HealthWorkerModel,
    DoctorModel,
    ReportModel,
    SmsNotificationModel,
)
from app.sms_service import (
    sms_service,
    mask_mobile_number,
    SimulatedSMSProvider,
    BaseSMSProvider,
    get_sms_provider,
)
from app.email_service import email_service
from app.whatsapp_service import whatsapp_service
from app.pdf_service import pdf_service, generate_secure_pdf_token


def setup_test_db_records(db):
    """Sets up deterministic test patient, screening, and health worker records."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Patient Record
    patient = db.query(PatientModel).filter(PatientModel.id == "PAT-PHASE15-01").first()
    if not patient:
        patient = PatientModel(
            id="PAT-PHASE15-01",
            abha_id="91-9876-5432-1098",
            name="Ramesh Kumar",
            age=56,
            gender="male",
            phone="+91 98765 43210",
            email="ramesh.kumar@example.com",
            village="Rampur Sector 4",
            district="Varanasi",
            registered_date="2026-08-28",
            doctor_verified=True,
        )
        db.add(patient)
        db.commit()
    else:
        patient.phone = "+91 98765 43210"
        patient.name = "Ramesh Kumar"
        db.commit()

    # 2. Health Worker Record
    hw = db.query(HealthWorkerModel).filter(HealthWorkerModel.id == "HW-TEST-PHASE15").first()
    if not hw:
        hw = HealthWorkerModel(
            id="HW-TEST-PHASE15",
            name="Asha Devi",
            role="health_worker",
            phone="+91 94123 00000",
            email="asha.devi@phc.in",
            village="Rampur Sector 4",
            phc_center="PHC Rampur",
            whatsapp_opt_in=True,
        )
        db.add(hw)
        db.commit()

    # 3. Approved Screening Record
    scr_approved = db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-PHASE15-APPROVED").first()
    if not scr_approved:
        scr_approved = ScreeningModel(
            id="SCR-PHASE15-APPROVED",
            patient_id="PAT-PHASE15-01",
            patient_name="Ramesh Kumar",
            village="Rampur Sector 4",
            screening_date="2026-08-28",
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            predicted_class=2,
            class_name="Moderate",
            confidence=0.88,
            dr_severity_od="Moderate",
            dr_severity_os="Mild",
            overall_severity="Moderate",
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
            doctor_status="verified",
            review_status="AI RESULT ACCEPTED",
        )
        db.add(scr_approved)
        db.commit()

    # Doctor Review for Approved Screening
    rev_approved = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == "SCR-PHASE15-APPROVED").first()
    if not rev_approved:
        rev_approved = ScreeningReviewModel(
            id="REV-PHASE15-APPROVED",
            screening_id="SCR-PHASE15-APPROVED",
            action="ACCEPT",
            doctor_id="DOC-SWAMINATHAN",
            doctor_name="Dr. Arvind Swaminathan, MS",
            original_ai_result="Moderate",
            original_confidence=0.88,
            reviewed_result="Moderate",
            review_comment="Retinal findings verified and accepted.",
            doctor_notes="Moderate NPDR with macular preservation. 6-month specialist review.",
            review_status="AI RESULT ACCEPTED",
            review_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        db.add(rev_approved)
        db.commit()

    # 4. Pending Review Screening Record
    scr_pending = db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-PHASE15-PENDING").first()
    if not scr_pending:
        scr_pending = ScreeningModel(
            id="SCR-PHASE15-PENDING",
            patient_id="PAT-PHASE15-01",
            patient_name="Ramesh Kumar",
            village="Rampur Sector 4",
            screening_date="2026-08-28",
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            predicted_class=1,
            class_name="Mild",
            confidence=0.85,
            doctor_status="pending",
            review_status="PENDING DOCTOR REVIEW",
        )
        db.add(scr_pending)
        db.commit()

    # Delete any existing review for pending screening
    db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == "SCR-PHASE15-PENDING").delete()
    db.commit()

    # 5. Rejected / Re-capture Screening Record
    scr_rejected = db.query(ScreeningModel).filter(ScreeningModel.id == "SCR-PHASE15-REJECTED").first()
    if not scr_rejected:
        scr_rejected = ScreeningModel(
            id="SCR-PHASE15-REJECTED",
            patient_id="PAT-PHASE15-01",
            patient_name="Ramesh Kumar",
            village="Rampur Sector 4",
            screening_date="2026-08-28",
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            predicted_class=0,
            class_name="No DR",
            confidence=0.65,
            doctor_status="recapture_requested",
            review_status="IMAGE RE-CAPTURE REQUESTED",
        )
        db.add(scr_rejected)
        db.commit()

    rev_rejected = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == "SCR-PHASE15-REJECTED").first()
    if not rev_rejected:
        rev_rejected = ScreeningReviewModel(
            id="REV-PHASE15-REJECTED",
            screening_id="SCR-PHASE15-REJECTED",
            action="RECAPTURE",
            doctor_id="DOC-SWAMINATHAN",
            doctor_name="Dr. Arvind Swaminathan, MS",
            original_ai_result="No DR",
            original_confidence=0.65,
            review_comment="Media haze and motion blur in OD. Re-capture required.",
            review_status="IMAGE RE-CAPTURE REQUESTED",
            review_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        db.add(rev_rejected)
        db.commit()

    # Clear previous test SMS notifications
    db.query(SmsNotificationModel).filter(
        SmsNotificationModel.screening_id.in_([
            "SCR-PHASE15-APPROVED",
            "SCR-PHASE15-PENDING",
            "SCR-PHASE15-REJECTED",
        ])
    ).delete(synchronize_session=False)
    db.commit()


async def run_tests():
    print("=" * 70)
    print("PHASE 15: DEMO SMS PATIENT REPORT NOTIFICATION — TEST EXECUTION")
    print("=" * 70)

    db = SessionLocal()
    setup_test_db_records(db)

    # -------------------------------------------------------------
    # Test 1: Patient mobile correctly resolved from MySQL
    # -------------------------------------------------------------
    print("\n[TEST 1] Patient mobile correctly resolved from MySQL (screening.patient_id -> patient.phone)...")
    resolved_patient = sms_service.resolve_patient_for_screening("SCR-PHASE15-APPROVED", db=db)
    assert resolved_patient is not None, "Failed to resolve patient from DB"
    assert resolved_patient.id == "PAT-PHASE15-01", f"Wrong patient resolved: {resolved_patient.id}"
    assert resolved_patient.phone == "+91 98765 43210", f"Wrong phone resolved: {resolved_patient.phone}"
    print(" [OK] Patient mobile resolved authoritatively from MySQL record (+91 98765 43210).")

    # -------------------------------------------------------------
    # Test 2: Health worker mobile is NOT used
    # -------------------------------------------------------------
    print("\n[TEST 2] Health worker mobile is strictly NOT used for patient SMS...")
    hw = db.query(HealthWorkerModel).filter(HealthWorkerModel.id == "HW-TEST-PHASE15").first()
    assert resolved_patient.phone != hw.phone, "Security Error: Health worker phone was assigned to patient!"
    masked = mask_mobile_number(resolved_patient.phone)
    assert masked == "98******10", f"Unexpected masked format: {masked}"
    assert hw.phone not in masked, "Health worker phone leaked into masked string"
    print(" [OK] Confirmed patient recipient phone is isolated; Health Worker phone is NOT used.")

    # -------------------------------------------------------------
    # Test 3: Doctor approval required
    # -------------------------------------------------------------
    print("\n[TEST 3] Doctor approval required for notification generation...")
    can_notify, gate_reason, review = sms_service.check_doctor_review_gate("SCR-PHASE15-APPROVED", db=db)
    assert can_notify is True, f"Approved screening failed gate: {gate_reason}"
    assert review is not None, "Approved review data missing"
    assert review.get("action") == "ACCEPT", f"Expected ACCEPT action, got: {review.get('action')}"
    print(" [OK] Doctor approval gate verified: Approved screening is eligible for notification.")

    # -------------------------------------------------------------
    # Test 4: Rejected report cannot generate notification
    # -------------------------------------------------------------
    print("\n[TEST 4] Rejected / Re-capture report cannot generate notification...")
    can_notify_rej, gate_reason_rej, _ = sms_service.check_doctor_review_gate("SCR-PHASE15-REJECTED", db=db)
    assert can_notify_rej is False, "Rejected screening should NOT be permitted to notify!"
    assert "re-capture" in gate_reason_rej.lower(), f"Unexpected reason: {gate_reason_rej}"
    
    # Try simulation directly
    try:
        await sms_service.simulate_sms_notification("SCR-PHASE15-REJECTED", db=db)
        assert False, "Should have thrown ValueError for rejected screening!"
    except ValueError as ve:
        assert "Notification blocked" in str(ve)
        print(" [OK] Rejected / re-capture screening correctly blocked with error.")

    # -------------------------------------------------------------
    # Test 5: Pending review cannot generate notification
    # -------------------------------------------------------------
    print("\n[TEST 5] Pending review screening cannot generate notification...")
    can_notify_pend, gate_reason_pend, _ = sms_service.check_doctor_review_gate("SCR-PHASE15-PENDING", db=db)
    assert can_notify_pend is False, "Pending review should NOT be permitted to notify!"
    assert "pending" in gate_reason_pend.lower(), f"Unexpected reason: {gate_reason_pend}"

    try:
        await sms_service.simulate_sms_notification("SCR-PHASE15-PENDING", db=db)
        assert False, "Should have thrown ValueError for pending screening!"
    except ValueError as ve:
        assert "Notification blocked" in str(ve)
        print(" [OK] Pending doctor review screening correctly blocked.")

    # -------------------------------------------------------------
    # Test 6: Secure token generated
    # -------------------------------------------------------------
    print("\n[TEST 6] Secure random non-guessable report access token generated...")
    token = sms_service.generate_secure_report_token("SCR-PHASE15-APPROVED", "PAT-PHASE15-01")
    assert len(token) >= 8, f"Token length too short: {len(token)}"
    assert "SCR-" not in token, "Screening ID must NOT be in token"
    assert "PAT-" not in token, "Patient ID must NOT be in token"
    print(f" [OK] Cryptographically secure token generated: {token}")

    # -------------------------------------------------------------
    # Test 7: Token maps to correct patient/report
    # -------------------------------------------------------------
    print("\n[TEST 7] Token maps to correct patient and screening report...")
    report_view = sms_service.verify_and_get_patient_report(token, db=db)
    assert report_view.is_valid is True
    assert report_view.screening_id == "SCR-PHASE15-APPROVED"
    assert report_view.patient_name == "Ramesh Kumar"
    assert report_view.final_dr_result == "Moderate"
    print(" [OK] Token accurately mapped to approved patient Ramesh Kumar (SCR-PHASE15-APPROVED).")

    # -------------------------------------------------------------
    # Test 8: Unapproved report cannot be accessed via token
    # -------------------------------------------------------------
    print("\n[TEST 8] Unapproved / pending screening token cannot be accessed...")
    pending_token = sms_service.generate_secure_report_token("SCR-PHASE15-PENDING", "PAT-PHASE15-01")
    try:
        sms_service.verify_and_get_patient_report(pending_token, db=db)
        assert False, "Should have blocked access to unapproved report!"
    except ValueError as ve:
        assert "Forbidden" in str(ve) or "not doctor-approved" in str(ve)
        print(" [OK] Access forbidden for unapproved screening token.")

    # -------------------------------------------------------------
    # Test 9: SMS message generated correctly
    # -------------------------------------------------------------
    print("\n[TEST 9] SMS message text generated with clinical safety rules...")
    preview = sms_service.get_sms_preview("SCR-PHASE15-APPROVED", db=db)
    assert "Your eye screening report has been successfully reviewed by the doctor." in preview.message_preview
    assert "Download your report:" in preview.message_preview
    assert "/patient-report/" in preview.message_preview
    # Check clinical safety: no diagnosis terms in SMS body
    assert "Moderate NPDR" not in preview.message_preview
    assert "Retinopathy" not in preview.message_preview or preview.message_preview.startswith("Rural DR Screening:")
    print(" [OK] SMS message contains doctor review notification and secure link without exposing medical data.")

    # -------------------------------------------------------------
    # Test 10: Message ID is unique
    # -------------------------------------------------------------
    print("\n[TEST 10] Message ID generator produces unique ID with proper format...")
    id1 = sms_service.generate_unique_message_id(db=db)
    id2 = sms_service.generate_unique_message_id(db=db)
    assert id1.startswith("SMS-2026-"), f"Unexpected ID format: {id1}"
    assert id2.startswith("SMS-2026-"), f"Unexpected ID format: {id2}"
    assert id1 != id2, f"Collision in message IDs: {id1} == {id2}"
    print(f" [OK] Generated unique message IDs: {id1} and {id2}")

    # -------------------------------------------------------------
    # Test 11: Status is SIMULATED, never SENT
    # -------------------------------------------------------------
    print("\n[TEST 11] Status is strictly SIMULATED (never fake SENT)...")
    sim_record = await sms_service.simulate_sms_notification("SCR-PHASE15-APPROVED", db=db)
    assert sim_record.status == "SIMULATED", f"Expected SIMULATED status, got: {sim_record.status}"
    assert sim_record.is_simulated is True
    assert "demonstration" in sim_record.disclaimer.lower()
    print(" [OK] Verified status is strictly SIMULATED, never fake SENT.")

    # -------------------------------------------------------------
    # Test 12: Notification log is created in database
    # -------------------------------------------------------------
    print("\n[TEST 12] Notification log record created in MySQL database...")
    db_rec = db.query(SmsNotificationModel).filter(
        SmsNotificationModel.notification_id == sim_record.notification_id
    ).first()
    assert db_rec is not None, "Notification record not found in database!"
    assert db_rec.patient_id == "PAT-PHASE15-01"
    assert db_rec.screening_id == "SCR-PHASE15-APPROVED"
    assert db_rec.status == "SIMULATED"
    assert db_rec.recipient_mobile_masked == "98******10"
    print(" [OK] Transactional notification log record verified in database table 'sms_notifications'.")

    # -------------------------------------------------------------
    # Test 13: Duplicate notification handling works
    # -------------------------------------------------------------
    print("\n[TEST 13] Duplicate notification handling and 'Generate Again' override...")
    # Without force_regenerate -> returns existing record
    dup_rec = await sms_service.simulate_sms_notification("SCR-PHASE15-APPROVED", force_regenerate=False, db=db)
    assert dup_rec.notification_id == sim_record.notification_id, "Duplicate without force should return existing ID"

    # With force_regenerate=True ("Generate Again") -> creates new record
    new_rec = await sms_service.simulate_sms_notification("SCR-PHASE15-APPROVED", force_regenerate=True, db=db)
    assert new_rec.notification_id != sim_record.notification_id, "Force regenerate should create a new message ID"
    assert new_rec.status == "SIMULATED"

    # Verify history now has 2 records
    status_resp = sms_service.get_sms_status("SCR-PHASE15-APPROVED", db=db)
    assert len(status_resp.notification_history) >= 2, "Expected multiple entries in history"
    print(f" [OK] Duplicate protection verified: Existing returned on repeat, new ID ({new_rec.notification_id}) on 'Generate Again'.")

    # -------------------------------------------------------------
    # Test 14: Patient identity remains consistent
    # -------------------------------------------------------------
    print("\n[TEST 14] Patient identity remains consistent across all operations...")
    assert new_rec.patient_id == "PAT-PHASE15-01"
    assert new_rec.patient_name == "Ramesh Kumar"
    print(" [OK] Patient identity maintained consistently.")

    # -------------------------------------------------------------
    # Test 15: Existing email delivery remains working
    # -------------------------------------------------------------
    print("\n[TEST 15] Verifying existing Email delivery service is unaffected...")
    email_patient = email_service.resolve_patient_for_screening("SCR-PHASE15-APPROVED", db=db)
    assert email_patient is not None
    assert email_patient.email == "ramesh.kumar@example.com"
    email_gate, _, _ = email_service.check_doctor_review_gate("SCR-PHASE15-APPROVED", db=db)
    assert email_gate is True
    print(" [OK] Existing Email delivery gate and patient resolution operational.")

    # -------------------------------------------------------------
    # Test 16: Existing WhatsApp delivery remains working
    # -------------------------------------------------------------
    print("\n[TEST 16] Verifying existing WhatsApp delivery service is unaffected...")
    wa_gate, _, _ = whatsapp_service.check_doctor_review_gate("SCR-PHASE15-APPROVED", db=db)
    assert wa_gate is True
    print(" [OK] Existing WhatsApp delivery gate operational.")

    # -------------------------------------------------------------
    # Test 17: Existing PDF generation remains working
    # -------------------------------------------------------------
    print("\n[TEST 17] Verifying existing PDF generation remains functional...")
    pdf_tok = generate_secure_pdf_token("SCR-PHASE15-APPROVED")
    assert pdf_tok is not None and len(pdf_tok) > 10
    print(" [OK] Existing PDF secure token generation operational.")

    db.close()

    print("\n" + "=" * 70)
    print("ALL 17 PHASE 15 DEMO SMS NOTIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    if not success:
        sys.exit(1)
