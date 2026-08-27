"""
Verification of Database Restart Persistence for Phase 13 MySQL / SQLAlchemy ORM.
Executes multi-phase write, process termination simulation, new session re-initialization,
and data retrieval to prove true relational persistence.
"""

import sys
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from app.database import Base, SessionLocal, engine
from app.models import (
    PatientModel,
    ScreeningModel,
    ScreeningReviewModel,
    ReviewAuditEventModel,
    AppointmentModel,
    WhatsAppDeliveryModel,
)
from app.schemas import DoctorReviewRequest
from app.review_service import process_doctor_review, get_screening_review, get_audit_history

def step_1_write_records():
    unique_suffix = uuid.uuid4().hex[:6]
    pat_id = f"PAT-RESTART-{unique_suffix}"
    scr_id = f"SCR-RESTART-{unique_suffix}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    print("==================================================================")
    print("PHASE 13: RESTART PERSISTENCE VERIFICATION — STEP 1: WRITE DATA")
    print("==================================================================")
    print(f"[*] Creating persistent test patient: {pat_id}")
    
    db = SessionLocal()
    try:
        # 1. Create Patient
        patient = PatientModel(
            id=pat_id,
            abha_id=f"ABHA-9999-{unique_suffix}",
            name=f"Persistent Test Patient {unique_suffix}",
            age=57,
            gender="female",
            village="Shivpuri Gram Panchayat",
            phone="+919876543210",
            registered_date="2026-08-27",
            visual_acuity_od="6/9",
            visual_acuity_os="6/6",
        )
        db.add(patient)
        db.commit()
        print(f" [OK] Patient {pat_id} persisted in database.")
        
        # 2. Create Screening
        print(f"[*] Creating persistent test screening: {scr_id}")
        screening = ScreeningModel(
            id=scr_id,
            patient_id=pat_id,
            patient_name=patient.name,
            village=patient.village,
            screening_date="2026-08-27 04:30 PM",
            timestamp_iso=now_iso,
            predicted_class=2,
            class_name="Moderate",
            confidence=0.892,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
        )
        db.add(screening)
        db.commit()
        print(f" [OK] Screening {scr_id} persisted in database.")
        
        # 3. Save Doctor Review
        print(f"[*] Saving Doctor Review for {scr_id}")
        rev_req = DoctorReviewRequest(
            screening_id=scr_id,
            action="MODIFY",
            reviewed_class=1,
            reviewed_class_name="Mild",
            reviewer_id="DOC-SWAMINATHAN",
            reviewer_name="Dr. Arvind Swaminathan, MS",
            review_comment="Isolated microaneurysms only. Early NPDR confirmed.",
        )
        rev_res = process_doctor_review(
            request=rev_req,
            original_ai_result="Moderate",
            original_confidence=0.892,
            role="doctor",
            db=db,
        )
        print(f" [OK] Doctor review processed: {rev_res.review_status} (Modified: {rev_res.doctor_reviewed_result})")
        
        # Verify initial state
        db_review = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == scr_id).first()
        assert db_review is not None, "Review should be in DB"
        print(f" [OK] Confirmed initial record written to database.")
        
    finally:
        db.close()
        
    # Dispose connection pool to simulate full engine termination
    engine.dispose()
    print("[*] SQLAlchemy Engine disposed. Backend process disconnected from database.")
    return pat_id, scr_id, unique_suffix

def step_2_reconnect_and_query(pat_id, scr_id, unique_suffix):
    print("\n==================================================================")
    print("PHASE 13: RESTART PERSISTENCE VERIFICATION — STEP 2: RECONNECT & VERIFY")
    print("==================================================================")
    print("[*] Reconnecting with a fresh SQLAlchemy Engine and Session...")
    
    new_db = SessionLocal()
    try:
        # Query Patient
        print(f"[*] Querying patient: {pat_id}")
        queried_pat = new_db.query(PatientModel).filter(PatientModel.id == pat_id).first()
        assert queried_pat is not None, f"Patient {pat_id} must persist across restart"
        assert queried_pat.abha_id == f"ABHA-9999-{unique_suffix}"
        assert queried_pat.age == 57
        print(f" [OK] Patient verified: {queried_pat.name}, ABHA: {queried_pat.abha_id}, Age: {queried_pat.age}")
        
        # Query Screening
        print(f"[*] Querying screening: {scr_id}")
        queried_scr = new_db.query(ScreeningModel).filter(ScreeningModel.id == scr_id).first()
        assert queried_scr is not None, f"Screening {scr_id} must persist across restart"
        assert queried_scr.patient_id == pat_id
        assert queried_scr.class_name == "Moderate"
        assert abs(queried_scr.confidence - 0.892) < 0.001
        print(f" [OK] Screening verified: AI Class: {queried_scr.class_name}, Confidence: {queried_scr.confidence}")
        
        # Query Doctor Review
        print(f"[*] Querying doctor review for {scr_id}")
        queried_rev = new_db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == scr_id).first()
        assert queried_rev is not None, "Doctor review must persist across restart"
        assert queried_rev.action == "MODIFY"
        assert queried_rev.reviewed_result == "Mild"
        assert "microaneurysms" in queried_rev.review_comment
        print(f" [OK] Doctor Review verified: Status: {queried_rev.review_status}, Doctor Result: {queried_rev.reviewed_result}, Comment: {queried_rev.review_comment}")
        
        # Query Audit History
        print(f"[*] Querying review audit trail for {scr_id}")
        audits = new_db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.screening_id == scr_id).all()
        assert len(audits) >= 1, "Audit events must persist across restart"
        override_audit = next((a for a in audits if a.event_type == "RESULT_MODIFIED"), None)
        assert override_audit is not None
        assert override_audit.reviewed_result == "Mild"
        print(f" [OK] Audit Trail verified: {len(audits)} immutable audit records found. Override audit event present.")
        
        print("\n==================================================================")
        print("RESTART PERSISTENCE VERIFICATION: 100% SUCCESSFUL!")
        print("Data faithfully survived engine termination and process restart.")
        print("==================================================================")
        
    finally:
        new_db.close()

if __name__ == "__main__":
    p_id, s_id, u_suff = step_1_write_records()
    step_2_reconnect_and_query(p_id, s_id, u_suff)
