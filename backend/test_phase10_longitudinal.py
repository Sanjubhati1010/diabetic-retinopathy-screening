import sys
from fastapi.testclient import TestClient
from app.main import app
from app.longitudinal_service import longitudinal_service
from app.assistant_service import generate_assistant_reply

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

client = TestClient(app)

def test_phase10_longitudinal_suite():
    print("==================================================")
    print("RUNNING PHASE 10 LONGITUDINAL PATIENT TRACKING TESTS")
    print("==================================================")

    # Clean any temporary dynamic test screenings and their cascade relationships
    from app.database import SessionLocal
    from app.models import (
        ScreeningModel,
        ScreeningReviewModel,
        ReviewAuditEventModel,
        WhatsAppDeliveryModel,
        WhatsAppAuditEventModel,
        EmailDeliveryModel,
        EmailAuditEventModel,
        ReportModel,
        AppointmentModel,
    )
    db = SessionLocal()
    try:
        non_canon = db.query(ScreeningModel.id).filter(
            ScreeningModel.patient_id == "PAT-2026-081",
            ScreeningModel.id.notin_(["SCR-2026-0991", "SCR-2026-0740", "SCR-2026-0410"])
        ).all()
        non_canon_ids = [r[0] for r in non_canon]
        if non_canon_ids:
            db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(WhatsAppAuditEventModel).filter(WhatsAppAuditEventModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(EmailAuditEventModel).filter(EmailAuditEventModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(EmailDeliveryModel).filter(EmailDeliveryModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(ReportModel).filter(ReportModel.screening_id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.query(AppointmentModel).filter(AppointmentModel.screening_id.in_(non_canon_ids)).update({AppointmentModel.screening_id: None}, synchronize_session=False)
            db.query(ScreeningModel).filter(ScreeningModel.id.in_(non_canon_ids)).delete(synchronize_session=False)
            db.commit()
    except Exception as e:
        print("Cleanup warning:", e)
        db.rollback()
    finally:
        db.close()

    # ---------------------------------------------------------
    # TEST 1: Patient With Multiple Screenings (Chronological Order)
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Patient With Multiple Screenings (PAT-2026-081)...")
    history_81 = longitudinal_service.get_patient_screening_history("PAT-2026-081")
    assert len(history_81) == 3, f"Expected 3 screenings for PAT-2026-081, got {len(history_81)}"
    # Verify sorted newest first: Aug 2026 -> Jun 2026 -> Mar 2026
    assert history_81[0]["screening_id"] == "SCR-2026-0991"
    assert history_81[1]["screening_id"] == "SCR-2026-0740"
    assert history_81[2]["screening_id"] == "SCR-2026-0410"
    print(" [OK] Multiple screenings retrieved in reverse chronological order (newest first).")

    # ---------------------------------------------------------
    # TEST 2: Patient With Single Screening (No Previous History)
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Patient With Single Screening (PAT-2026-083)...")
    history_83 = longitudinal_service.get_patient_screening_history("PAT-2026-083")
    assert len(history_83) == 1
    curr_83 = history_83[0]
    comparison_83 = longitudinal_service.compare_screenings(current_screening=curr_83, previous_screening=None)
    assert comparison_83["has_previous_screening"] is False
    assert comparison_83["classification_change_status"] == "HISTORY UNAVAILABLE"
    assert "unavailable" in comparison_83["classification_change_summary"].lower()
    print(" [OK] Single screening correctly reported 'HISTORY UNAVAILABLE' without fabricating history.")

    # ---------------------------------------------------------
    # TEST 3: Classification Increased (Mild -> Moderate)
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Classification Increased (SCR-2026-0740 [Mild] -> SCR-2026-0991 [Moderate])...")
    curr_scr = longitudinal_service.get_screening("SCR-2026-0991") # Moderate NPDR (Class 2)
    prev_scr = longitudinal_service.get_screening("SCR-2026-0740") # Mild NPDR (Class 1)
    comp_inc = longitudinal_service.compare_screenings(current_screening=curr_scr, previous_screening=prev_scr)
    
    assert comp_inc["classification_change_status"] == "CLASSIFICATION INCREASED"
    assert "increased from Mild NPDR to Moderate NPDR" in comp_inc["classification_change_summary"]
    assert "Doctor review is recommended" in comp_inc["clinical_recommendation"]
    assert "disease progression" not in comp_inc["classification_change_summary"].lower()
    print(" - Summary:", comp_inc["classification_change_summary"])
    print(" [OK] Classification increase evaluated safely without 'disease progression' claim.")

    # ---------------------------------------------------------
    # TEST 4: Same DR Classification (Unchanged: Mild -> Mild)
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Unchanged Classification (SCR-2026-0410 [Mild] -> SCR-2026-0740 [Mild])...")
    curr_same = longitudinal_service.get_screening("SCR-2026-0740") # Mild NPDR (Class 1)
    prev_same = longitudinal_service.get_screening("SCR-2026-0410") # Mild NPDR (Class 1)
    comp_same = longitudinal_service.compare_screenings(current_screening=curr_same, previous_screening=prev_same)
    
    assert comp_same["classification_change_status"] == "UNCHANGED"
    assert comp_same["classification_change_summary"] == "AI screening classification is unchanged."
    print(" - Summary:", comp_same["classification_change_summary"])
    print(" [OK] Identical classifications correctly evaluated as 'UNCHANGED'.")

    # ---------------------------------------------------------
    # TEST 5: Lower Classification (Classification Decreased / Improved)
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Classification Decreased (Moderate -> Mild)...")
    synthetic_prev = dict(curr_scr, predicted_class=2, class_name="Moderate NPDR")
    synthetic_curr = dict(prev_scr, predicted_class=1, class_name="Mild NPDR")
    comp_dec = longitudinal_service.compare_screenings(current_screening=synthetic_curr, previous_screening=synthetic_prev)
    
    assert comp_dec["classification_change_status"] == "CLASSIFICATION DECREASED"
    assert "decreased from Moderate NPDR to Mild NPDR" in comp_dec["classification_change_summary"]
    print(" - Summary:", comp_dec["classification_change_summary"])
    print(" [OK] Lower classification correctly evaluated as 'CLASSIFICATION DECREASED'.")

    # ---------------------------------------------------------
    # TEST 6: Confidence Comparison (Honest Separation, No Fake Improvement)
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Confidence Comparison...")
    conf_comp = comp_inc["confidence_comparison"]
    assert conf_comp["current_confidence"] == 0.85
    assert conf_comp["previous_confidence"] == 0.78
    assert "Previous AI Confidence: 78.00%, Current AI Confidence: 85.00%" in conf_comp["note"]
    print(" - Confidence Note:", conf_comp["note"])
    print(" [OK] Confidences preserved separately without fake improvement math.")

    # ---------------------------------------------------------
    # TEST 7: Missing Confidence Handling
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing Missing Confidence Handling...")
    synthetic_curr_no_conf = dict(curr_scr, confidence=None)
    comp_no_conf = longitudinal_service.compare_screenings(current_screening=synthetic_curr_no_conf, previous_screening=prev_scr)
    assert comp_no_conf["confidence_comparison"]["current_confidence"] is None
    print(" [OK] Missing confidence gracefully handled.")

    # ---------------------------------------------------------
    # TEST 8: Missing Previous Image / Grad-CAM / Lesion Analysis
    # ---------------------------------------------------------
    print("\n[TEST 8] Testing Missing Images, Grad-CAM & Lesion Intelligence Compatibility...")
    synthetic_prev_no_img = dict(prev_scr, image_od=None, gradcam_od=None, lesion_available=False)
    comp_no_img = longitudinal_service.compare_screenings(current_screening=curr_scr, previous_screening=synthetic_prev_no_img)
    assert comp_no_img["image_comparison"]["previous_image_od"] is None
    assert comp_no_img["gradcam_comparison"]["previous_gradcam"] is None
    assert comp_no_img["lesion_comparison"]["previous_available"] is False
    assert comp_no_img["lesion_comparison"]["note"] == "Lesion-specific comparison unavailable."
    assert "model attention and is not a direct measurement of disease progression" in comp_no_img["gradcam_comparison"]["explanation"]
    print(" [OK] Grad-CAM disclaimer & Lesion-specific unavailable status verified.")

    # ---------------------------------------------------------
    # TEST 9: Current Screening Re-capture Requested (NOT COMPARABLE)
    # ---------------------------------------------------------
    print("\n[TEST 9] Testing Current Screening Re-capture Requested...")
    curr_recapture = dict(curr_scr, is_recapture=True, review_status="IMAGE RE-CAPTURE REQUESTED")
    comp_rec = longitudinal_service.compare_screenings(current_screening=curr_recapture, previous_screening=prev_scr)
    assert comp_rec["classification_change_status"] == "NOT COMPARABLE"
    assert "re-capture" in comp_rec["classification_change_summary"].lower()
    print(" - Summary:", comp_rec["classification_change_summary"])
    print(" [OK] Re-capture requested screening safely flagged as 'NOT COMPARABLE'.")

    # ---------------------------------------------------------
    # TEST 10: Previous Screening Re-capture Requested (NOT COMPARABLE)
    # ---------------------------------------------------------
    print("\n[TEST 10] Testing Previous Screening Re-capture Requested...")
    prev_recapture = dict(prev_scr, is_recapture=True, doctor_status="recapture_requested")
    comp_prev_rec = longitudinal_service.compare_screenings(current_screening=curr_scr, previous_screening=prev_recapture)
    assert comp_prev_rec["classification_change_status"] == "NOT COMPARABLE"
    print(" [OK] Incomplete previous screening safely flagged as 'NOT COMPARABLE'.")

    # ---------------------------------------------------------
    # TEST 11: Data Isolation Security Check (Different Patients)
    # ---------------------------------------------------------
    print("\n[TEST 11] Testing Data Safety: Cross-Patient Comparison Block...")
    scr_pat1 = longitudinal_service.get_screening("SCR-2026-0991") # PAT-2026-081
    scr_pat2 = longitudinal_service.get_screening("SCR-2026-0992") # PAT-2026-082
    try:
        longitudinal_service.compare_screenings(current_screening=scr_pat1, previous_screening=scr_pat2)
        assert False, "Security Violation: Cross-patient comparison did not raise ValueError!"
    except ValueError as e:
        print(" - Security Exception Caught:", str(e))
        assert "Security Violation" in str(e)
    print(" [OK] Cross-patient data isolation strictly enforced.")

    # ---------------------------------------------------------
    # TEST 12: Doctor Review Preservation & Distinction
    # ---------------------------------------------------------
    print("\n[TEST 12] Testing Doctor Override Distinction...")
    curr_overridden = dict(
        curr_scr,
        predicted_class=3,
        class_name="Severe",
        doctor_reviewed_result="Moderate",
        doctor_status="verified",
        review_status="DOCTOR REVIEWED / MODIFIED"
    )
    comp_over = longitudinal_service.compare_screenings(current_screening=curr_overridden, previous_screening=prev_scr)
    assert comp_over["current_screening"]["predicted_class"] == 3
    assert comp_over["current_screening"]["doctor_reviewed_result"] == "Moderate"
    assert comp_over["doctor_review_comparison"]["current_doctor_reviewed_result"] == "Moderate"
    print(" [OK] AI classification and doctor-confirmed interpretation maintained as separate records.")

    # ---------------------------------------------------------
    # TEST 13: FastAPI Endpoint: GET /api/patients/{patient_id}/screening-history
    # ---------------------------------------------------------
    print("\n[TEST 13] Testing GET /api/patients/{patient_id}/screening-history...")
    res_hist = client.get("/api/patients/PAT-2026-081/screening-history")
    assert res_hist.status_code == 200, f"Expected 200, got {res_hist.status_code}"
    data_hist = res_hist.json()
    assert data_hist["patient_id"] == "PAT-2026-081"
    assert data_hist["total_screenings"] == 3
    assert len(data_hist["screenings"]) == 3
    assert data_hist["screenings"][0]["screening_id"] == "SCR-2026-0991"
    print(" [OK] History endpoint passed.")

    # ---------------------------------------------------------
    # TEST 14: FastAPI Endpoint: GET /api/screenings/{id}/comparison/{prev_id}
    # ---------------------------------------------------------
    print("\n[TEST 14] Testing GET /api/screenings/{id}/comparison/{prev_id}...")
    res_comp = client.get("/api/screenings/SCR-2026-0991/comparison/SCR-2026-0740")
    assert res_comp.status_code == 200
    data_comp = res_comp.json()
    assert data_comp["classification_change_status"] == "CLASSIFICATION INCREASED"
    assert data_comp["has_previous_screening"] is True
    print(" [OK] Specific comparison endpoint passed.")

    # ---------------------------------------------------------
    # TEST 15: FastAPI Endpoint: GET /api/screenings/{id}/longitudinal (Auto-select)
    # ---------------------------------------------------------
    print("\n[TEST 15] Testing GET /api/screenings/{id}/longitudinal (Auto Most Recent)...")
    res_auto = client.get("/api/screenings/SCR-2026-0991/longitudinal")
    assert res_auto.status_code == 200
    data_auto = res_auto.json()
    assert data_auto["previous_screening"]["screening_id"] == "SCR-2026-0740"
    assert data_auto["classification_change_status"] == "CLASSIFICATION INCREASED"
    print(" [OK] Automated longitudinal comparison endpoint passed.")

    # ---------------------------------------------------------
    # TEST 16: AI Assistant Longitudinal Queries (English)
    # ---------------------------------------------------------
    print("\n[TEST 16] Testing AI Assistant: 'What changed from the previous screening?' (English)...")
    mock_context_long = {
        "prediction": "Moderate NPDR",
        "previous_prediction": "Mild NPDR",
        "classification_change_summary": "AI screening classification increased from Mild NPDR to Moderate NPDR.",
        "safety_status": "READY_FOR_AI",
    }
    reply_changed = generate_assistant_reply("What changed from the previous screening?", language="en", screening_context=mock_context_long)
    assert "increased from Mild NPDR to Moderate NPDR" in reply_changed["reply"]
    assert "Doctor review is recommended" in reply_changed["reply"]
    print(" - Reply:", reply_changed["reply"][:140], "...")
    print(" [OK] Assistant faithfully explained change using actual screening context.")

    # ---------------------------------------------------------
    # TEST 17: AI Assistant: 'Why is this not called disease progression?'
    # ---------------------------------------------------------
    print("\n[TEST 17] Testing AI Assistant: 'Why is this not called disease progression?'...")
    reply_why = generate_assistant_reply("Why is this not called disease progression?", language="en")
    assert "Screening Classification Change" in reply_why["reply"]
    assert "ophthalmologist" in reply_why["reply"].lower()
    print(" - Reply:", reply_why["reply"][:140], "...")
    print(" [OK] Assistant clearly articulated clinical reason for avoiding autonomous progression claim.")

    # ---------------------------------------------------------
    # TEST 18: AI Assistant: 'What does unchanged mean?' (Hindi)
    # ---------------------------------------------------------
    print("\n[TEST 18] Testing AI Assistant: 'Unchanged ka matlab kya hai?' (Hindi)...")
    reply_unchanged = generate_assistant_reply("Unchanged ka matlab kya hai?", language="hi")
    assert "अपरिवर्तित" in reply_unchanged["reply"] or "एक ही" in reply_unchanged["reply"]
    print(" - Reply:", reply_unchanged["reply"][:140], "...")
    print(" [OK] Hindi explanation of 'Unchanged' returned accurately.")

    # ---------------------------------------------------------
    # TEST 19: AI Assistant: 'How can I compare two screenings?'
    # ---------------------------------------------------------
    print("\n[TEST 19] Testing AI Assistant: 'How can I compare two screenings?'...")
    reply_how = generate_assistant_reply("How can I compare two screenings?", language="en")
    assert "Doctor Portal" in reply_how["reply"] or "Screening History" in reply_how["reply"]
    print(" [OK] Assistant provided clear navigation guidance.")

    # ---------------------------------------------------------
    # TEST 20: Mandatory Clinical Disclaimer Present
    # ---------------------------------------------------------
    print("\n[TEST 20] Verifying Mandatory Clinical Disclaimer...")
    assert "does not independently establish disease progression" in data_comp["disclaimer"]
    print(" [OK] Mandatory medical disclaimer verified.")

    print("\n==================================================")
    print("ALL 20 PHASE 10 LONGITUDINAL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_phase10_longitudinal_suite()
