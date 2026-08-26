import sys
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import DoctorReviewRequest
from app.review_service import process_doctor_review, get_audit_history, verify_doctor_role

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_phase6_doctor_review_suite():
    print("==================================================")
    print("RUNNING PHASE 6 HUMAN-IN-THE-LOOP DOCTOR REVIEW TESTS")
    print("==================================================")

    # ---------------------------------------------------------
    # TEST 1: Doctor Action - ACCEPT AI Screening Result
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Doctor Action: ACCEPT AI Result...")
    req_accept = DoctorReviewRequest(
        screening_id="SCR-P6-001",
        action="ACCEPT",
        reviewer_id="DOC-SWAMINATHAN",
        reviewer_name="Dr. A. Swaminathan, MS",
        review_comment="Fundus findings align with AI prediction of Moderate DR.",
    )
    res_accept = process_doctor_review(
        request=req_accept,
        original_ai_result="Moderate",
        original_confidence=0.875,
        role="doctor",
    )
    print(" - Status:", res_accept.review_status)
    print(" - Original AI:", res_accept.original_ai_result)
    print(" - Reviewed Result:", res_accept.doctor_reviewed_result)
    assert res_accept.review_status == "AI RESULT ACCEPTED"
    assert res_accept.original_ai_result == "Moderate"
    assert res_accept.doctor_reviewed_result == "Moderate"
    print(" [OK] Accept action confirmed with status 'AI RESULT ACCEPTED'.")

    # ---------------------------------------------------------
    # TEST 2: Doctor Action - MODIFY / OVERRIDE AI Result (with Comment)
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Doctor Action: MODIFY / OVERRIDE (with mandatory comment)...")
    req_modify = DoctorReviewRequest(
        screening_id="SCR-P6-002",
        action="MODIFY",
        reviewed_class=1,
        reviewed_class_name="Mild",
        reviewer_id="DOC-SWAMINATHAN",
        reviewer_name="Dr. A. Swaminathan, MS",
        review_comment="Only microaneurysms visible in OD. Classified as Mild NPDR.",
    )
    res_modify = process_doctor_review(
        request=req_modify,
        original_ai_result="Moderate",
        original_confidence=0.74,
        role="doctor",
    )
    print(" - Status:", res_modify.review_status)
    print(" - Preserved Original AI:", res_modify.original_ai_result)
    print(" - Doctor Reviewed:", res_modify.doctor_reviewed_result)
    print(" - Review Comment:", res_modify.review_comment)
    assert res_modify.review_status == "DOCTOR REVIEWED / MODIFIED"
    assert res_modify.original_ai_result == "Moderate"
    assert res_modify.doctor_reviewed_result == "Mild"
    assert "microaneurysms" in res_modify.review_comment
    print(" [OK] Modify action successfully preserved original AI result while recording doctor override.")

    # ---------------------------------------------------------
    # TEST 3: Doctor Action - MODIFY WITHOUT Comment (Must Fail)
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Mandatory Review Reason for MODIFY (Expect Rejection)...")
    req_no_comment = DoctorReviewRequest(
        screening_id="SCR-P6-003",
        action="MODIFY",
        reviewed_class=0,
        reviewed_class_name="No DR",
        reviewer_id="DOC-SWAMINATHAN",
        reviewer_name="Dr. A. Swaminathan, MS",
        review_comment="",  # Empty comment
    )
    try:
        process_doctor_review(
            request=req_no_comment,
            original_ai_result="Moderate",
            original_confidence=0.80,
            role="doctor",
        )
        assert False, "Should have thrown ValueError for empty review comment!"
    except ValueError as e:
        print(" - Expected Error Caught:", str(e))
        assert "review reason/comment is required" in str(e)
    print(" [OK] Override without comment safely rejected.")

    # ---------------------------------------------------------
    # TEST 4: Doctor Action - REQUEST IMAGE RE-CAPTURE
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Doctor Action: REQUEST IMAGE RE-CAPTURE...")
    req_recapture = DoctorReviewRequest(
        screening_id="SCR-P6-004",
        action="RECAPTURE",
        reviewer_id="DOC-SWAMINATHAN",
        reviewer_name="Dr. A. Swaminathan, MS",
        review_comment="Media opacity / blur in macula. Re-capture required after pupil dilation.",
    )
    res_recapture = process_doctor_review(
        request=req_recapture,
        original_ai_result="Moderate",
        original_confidence=0.62,
        role="doctor",
    )
    print(" - Status:", res_recapture.review_status)
    print(" - Original AI Preserved:", res_recapture.original_ai_result)
    print(" - Guidance:", res_recapture.message)
    assert res_recapture.review_status == "IMAGE RE-CAPTURE REQUESTED"
    assert res_recapture.original_ai_result == "Moderate"
    print(" [OK] Image re-capture request recorded properly.")

    # ---------------------------------------------------------
    # TEST 5: Unauthorized User Role Attempting Doctor Action
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Role Authorization Check (Health Worker Attempting Review)...")
    try:
        process_doctor_review(
            request=req_accept,
            original_ai_result="Moderate",
            original_confidence=0.85,
            role="health_worker",  # Non-doctor
        )
        assert False, "Should have thrown PermissionError for non-doctor role!"
    except PermissionError as e:
        print(" - Expected Error Caught:", str(e))
        assert "Only qualified doctors" in str(e)
    print(" [OK] Role security check passed.")

    # ---------------------------------------------------------
    # TEST 6: Chronological Audit Trail Integrity
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Chronological Audit Trail History...")
    history = get_audit_history("SCR-P6-002")
    print(f" - Audit trail contains {len(history)} events:")
    for idx, ev in enumerate(history):
        print(f"   [{idx+1}] Type: {ev.event_type} | Actor: {ev.actor_id} ({ev.actor_role}) | Desc: {ev.description[:60]}...")
    assert len(history) >= 2
    assert history[0].event_type == "AI_SCREENING_COMPLETED"
    assert history[-1].event_type == "RESULT_MODIFIED"
    print(" [OK] Complete immutable audit trail verified.")

    # ---------------------------------------------------------
    # TEST 7: FastAPI Endpoints - POST /api/screenings/{id}/review (ACCEPT)
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing FastAPI Endpoint: POST /api/screenings/{id}/review (ACCEPT)...")
    client = TestClient(app)
    res_api_accept = client.post(
        "/api/screenings/SCR-E2E-001/review",
        json={
            "screening_id": "SCR-E2E-001",
            "action": "ACCEPT",
            "reviewer_id": "DOC-SWAMINATHAN",
            "reviewer_name": "Dr. A. Swaminathan, MS",
            "review_comment": "Verified AI screening output.",
        },
        headers={"X-User-Role": "doctor"},
    )
    assert res_api_accept.status_code == 200
    data_accept = res_api_accept.json()
    assert data_accept["review_status"] == "AI RESULT ACCEPTED"
    print(" [OK] Endpoint returned 200 with review_status 'AI RESULT ACCEPTED'.")

    # ---------------------------------------------------------
    # TEST 8: FastAPI Endpoints - POST /api/screenings/{id}/review (MODIFY)
    # ---------------------------------------------------------
    print("\n[TEST 8] Testing FastAPI Endpoint: POST /api/screenings/{id}/review (MODIFY)...")
    res_api_modify = client.post(
        "/api/screenings/SCR-E2E-002/review",
        json={
            "screening_id": "SCR-E2E-002",
            "action": "MODIFY",
            "reviewed_class": 3,
            "reviewed_class_name": "Severe",
            "reviewer_id": "DOC-SWAMINATHAN",
            "reviewer_name": "Dr. A. Swaminathan, MS",
            "review_comment": "Venous beading in 2 quadrants observed.",
        },
        headers={"X-User-Role": "doctor"},
    )
    assert res_api_modify.status_code == 200
    data_modify = res_api_modify.json()
    assert data_modify["review_status"] == "DOCTOR REVIEWED / MODIFIED"
    assert data_modify["doctor_reviewed_result"] == "Severe"
    print(" [OK] Endpoint returned 200 with review_status 'DOCTOR REVIEWED / MODIFIED'.")

    # ---------------------------------------------------------
    # TEST 9: FastAPI Endpoints - POST /api/screenings/{id}/review (MODIFY w/o Comment -> 400)
    # ---------------------------------------------------------
    print("\n[TEST 9] Testing FastAPI Endpoint: POST /api/screenings/{id}/review (MODIFY w/o Comment)...")
    res_api_err = client.post(
        "/api/screenings/SCR-E2E-003/review",
        json={
            "screening_id": "SCR-E2E-003",
            "action": "MODIFY",
            "reviewed_class": 0,
            "review_comment": "",
        },
        headers={"X-User-Role": "doctor"},
    )
    assert res_api_err.status_code == 400
    print(" - 400 Detail:", res_api_err.json()["detail"])
    print(" [OK] Endpoint safely returned 400 Bad Request.")

    # ---------------------------------------------------------
    # TEST 10: FastAPI Endpoints - POST /api/screenings/{id}/review (Unauthorized -> 403)
    # ---------------------------------------------------------
    print("\n[TEST 10] Testing FastAPI Endpoint: POST /api/screenings/{id}/review (Non-Doctor Role)...")
    res_api_auth = client.post(
        "/api/screenings/SCR-E2E-004/review",
        json={
            "screening_id": "SCR-E2E-004",
            "action": "ACCEPT",
        },
        headers={"X-User-Role": "health_worker"},
    )
    assert res_api_auth.status_code == 403
    print(" - 403 Detail:", res_api_auth.json()["detail"])
    print(" [OK] Endpoint safely returned 403 Forbidden.")

    # ---------------------------------------------------------
    # TEST 11: FastAPI Endpoints - GET /api/screenings/{id}/history
    # ---------------------------------------------------------
    print("\n[TEST 11] Testing FastAPI Endpoint: GET /api/screenings/{id}/history...")
    res_api_hist = client.get("/api/screenings/SCR-E2E-002/history")
    assert res_api_hist.status_code == 200
    data_hist = res_api_hist.json()
    assert data_hist["screening_id"] == "SCR-E2E-002"
    assert len(data_hist["events"]) >= 2
    print(f" - Fetched {len(data_hist['events'])} historical audit events via GET.")
    print(" [OK] Audit history endpoint passed.")

    print("\n==================================================")
    print("ALL 11 PHASE 6 HUMAN-IN-THE-LOOP DOCTOR REVIEW TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_phase6_doctor_review_suite()
