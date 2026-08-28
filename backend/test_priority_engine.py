"""
Comprehensive Test Suite for Rural Care Priority Engine (Phase 15).
Validates deterministic triage scoring, safety guardrails, AI uncertainty gate,
longitudinal change sensitivity, missing data handling, doctor authority,
auditability, and REST API endpoints.
"""

import os
import sys
import json
from fastapi.testclient import TestClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.main import app
from app.priority_engine import (
    calculate_screening_priority,
    get_priority_queue,
    get_priority_stats,
    ALGORITHM_VERSION,
    PRIORITY_P1,
    PRIORITY_P2,
    PRIORITY_P3,
    PRIORITY_VERIFICATION_REQUIRED,
    PRIORITY_RECAPTURE_REQUIRED,
    LABEL_P1,
    LABEL_P2,
    LABEL_P3,
    LABEL_UNCERTAINTY,
    LABEL_RECAPTURE,
)
from app.database import SessionLocal
from app.models import PatientModel, ScreeningModel

client = TestClient(app)


def run_priority_engine_tests():
    print("==================================================")
    print("RUNNING RURAL CARE PRIORITY ENGINE COMPREHENSIVE TESTS")
    print("==================================================")

    # -------------------------------------------------------------
    # TEST 1: No DR -> Routine (P3)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing No DR -> P3 Routine Priority...")
    scr_no_dr = {
        "id": "SCR-TEST-001",
        "patient_id": "PAT-TEST-001",
        "patient_name": "Neha Sharma",
        "predicted_class": 0,
        "class_name": "No DR",
        "confidence": 0.96,
        "safety_status": "READY_FOR_AI",
    }
    pat_normal = {
        "id": "PAT-TEST-001",
        "name": "Neha Sharma",
        "visual_acuity_od": "6/6",
        "visual_acuity_os": "6/6",
        "diabetes_duration": 2,
        "last_hba1c": 6.5,
    }
    res1 = calculate_screening_priority(scr_no_dr, pat_normal)
    assert res1["priority_level"] == PRIORITY_P3, f"Expected P3, got {res1['priority_level']}"
    assert res1["priority_label"] == LABEL_P3
    assert res1["priority_score"] < 2.5
    assert res1["color"] == "emerald"
    print(f" [OK] No DR correctly triaged to {res1['priority_label']} (Score: {res1['priority_score']})")

    # -------------------------------------------------------------
    # TEST 2: Mild DR -> Appropriate Priority
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Mild DR -> Appropriate Baseline Priority...")
    scr_mild = {
        "id": "SCR-TEST-002",
        "patient_id": "PAT-TEST-002",
        "patient_name": "Kavita Devi",
        "predicted_class": 1,
        "class_name": "Mild",
        "confidence": 0.88,
        "safety_status": "READY_FOR_AI",
    }
    res2 = calculate_screening_priority(scr_mild, pat_normal)
    assert res2["priority_level"] in [PRIORITY_P3, PRIORITY_P2]
    print(f" [OK] Mild DR triaged to {res2['priority_label']} (Score: {res2['priority_score']})")

    # -------------------------------------------------------------
    # TEST 3: Moderate DR -> P2 Priority
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Moderate DR -> P2 Priority...")
    scr_mod = {
        "id": "SCR-TEST-003",
        "patient_id": "PAT-TEST-003",
        "patient_name": "Amit Kumar",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.88,
        "safety_status": "READY_FOR_AI",
    }
    pat_reduced_va = {
        "id": "PAT-TEST-003",
        "name": "Amit Kumar",
        "visual_acuity_od": "6/18",
        "visual_acuity_os": "6/12",
        "diabetes_duration": 7,
        "last_hba1c": 8.1,
    }
    res3 = calculate_screening_priority(scr_mod, pat_reduced_va)
    assert res3["priority_level"] in [PRIORITY_P2, PRIORITY_P1]
    assert res3["priority_score"] >= 2.5
    print(f" [OK] Moderate DR triaged to {res3['priority_label']} (Score: {res3['priority_score']})")

    # -------------------------------------------------------------
    # TEST 4: Severe DR -> P1 Urgent
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Severe DR -> P1 Urgent Priority...")
    scr_severe = {
        "id": "SCR-TEST-004",
        "patient_id": "PAT-TEST-004",
        "patient_name": "Sunita Devi",
        "predicted_class": 3,
        "class_name": "Severe",
        "confidence": 0.92,
        "safety_status": "READY_FOR_AI",
    }
    res4 = calculate_screening_priority(scr_severe, pat_normal)
    assert res4["priority_level"] == PRIORITY_P1, f"Expected P1, got {res4['priority_level']}"
    assert res4["priority_label"] == LABEL_P1
    assert res4["color"] == "rose"
    print(f" [OK] Severe DR triaged to {res4['priority_label']} (Score: {res4['priority_score']})")

    # -------------------------------------------------------------
    # TEST 5: Proliferative DR -> P1 Urgent
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Proliferative DR -> P1 Urgent Priority...")
    scr_pdr = {
        "id": "SCR-TEST-005",
        "patient_id": "PAT-TEST-005",
        "patient_name": "Balwinder Singh",
        "predicted_class": 4,
        "class_name": "Proliferative DR",
        "confidence": 0.95,
        "safety_status": "READY_FOR_AI",
    }
    res5 = calculate_screening_priority(scr_pdr, pat_normal)
    assert res5["priority_level"] == PRIORITY_P1
    assert res5["priority_label"] == LABEL_P1
    assert res5["priority_score"] >= 6.0
    print(f" [OK] Proliferative DR triaged to {res5['priority_label']} (Score: {res5['priority_score']})")

    # -------------------------------------------------------------
    # TEST 6: High AI Confidence
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing High AI Confidence Integration...")
    assert res5["confidence_status"] == "HIGH"
    assert any("High AI confidence" in r for r in res5["detailed_reasons"])
    print(f" [OK] High AI confidence correctly documented in evidence checklist.")

    # -------------------------------------------------------------
    # TEST 7: Low AI Confidence Uncertainty Gate
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing Low AI Confidence (<60%) Safety Gate...")
    scr_low_conf = {
        "id": "SCR-TEST-007",
        "patient_id": "PAT-TEST-007",
        "patient_name": "Rajesh Gupta",
        "predicted_class": 0,  # Even if model predicted No DR
        "class_name": "No DR",
        "confidence": 0.48,  # Low confidence
        "safety_status": "READY_FOR_AI",
    }
    res7 = calculate_screening_priority(scr_low_conf, pat_normal)
    assert res7["priority_level"] == PRIORITY_VERIFICATION_REQUIRED
    assert res7["priority_label"] == LABEL_UNCERTAINTY
    assert res7["is_low_confidence"] is True
    assert "AI UNCERTAINTY" in res7["detailed_reasons"][0]
    assert "Doctor verification / image re-capture required." in res7["recommended_action"]
    print(f" [OK] Low confidence case safely intercepted as {res7['priority_label']} (Never marked low risk).")

    # -------------------------------------------------------------
    # TEST 8: Failed Image Quality Safety Gate Block
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Failed Image Quality Gate Block...")
    scr_bad_quality = {
        "id": "SCR-TEST-008",
        "patient_id": "PAT-TEST-008",
        "patient_name": "Mohan Lal",
        "predicted_class": None,
        "class_name": "Unable to Assess",
        "confidence": None,
        "safety_status": "IMAGE_QUALITY_INSUFFICIENT",
    }
    res8 = calculate_screening_priority(scr_bad_quality, pat_normal)
    assert res8["priority_level"] == PRIORITY_RECAPTURE_REQUIRED
    assert res8["priority_label"] == LABEL_RECAPTURE
    assert res8["is_safety_blocked"] is True
    assert res8["priority_score"] == 0.0
    print(f" [OK] Failed quality image successfully blocked with {res8['priority_label']}.")

    # -------------------------------------------------------------
    # TEST 9: Previous Screening Unchanged
    # -------------------------------------------------------------
    print("\n[TEST 9] Testing Previous Screening Unchanged (Moderate -> Moderate)...")
    prev_scr = {
        "id": "SCR-PREV-009",
        "predicted_class": 2,
        "class_name": "Moderate",
        "screening_date": "2026-04-10",
    }
    curr_scr_mod = {
        "id": "SCR-CURR-009",
        "patient_id": "PAT-TEST-009",
        "patient_name": "Sita Ram",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.89,
        "safety_status": "READY_FOR_AI",
    }
    res9 = calculate_screening_priority(curr_scr_mod, pat_normal, previous_screening=prev_scr)
    assert res9["longitudinal_change_status"] == "UNCHANGED"
    assert "stable" in res9["detailed_reasons"][1].lower() or "unchanged" in res9["longitudinal_summary"].lower()
    print(f" [OK] Stable longitudinal screening recognized as UNCHANGED.")

    # -------------------------------------------------------------
    # TEST 10: Previous Screening Worsened (Mild -> Moderate) -> Escalates Priority
    # -------------------------------------------------------------
    print("\n[TEST 10] Testing Longitudinal Worsening (Mild -> Moderate)...")
    prev_mild = {
        "id": "SCR-PREV-010",
        "predicted_class": 1,
        "class_name": "Mild",
        "screening_date": "2026-06-12",
    }
    curr_mod = {
        "id": "SCR-CURR-010",
        "patient_id": "PAT-TEST-010",
        "patient_name": "Ramesh Kumar Verma",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.85,
        "safety_status": "READY_FOR_AI",
    }
    res10 = calculate_screening_priority(curr_mod, pat_normal, previous_screening=prev_mild)
    assert res10["longitudinal_change_status"] == "WORSENED"
    assert res10["priority_level"] == PRIORITY_P1  # Moderate + Worsening escalates to P1 URGENT
    assert "increased from Mild to Moderate" in res10["longitudinal_summary"]
    print(f" [OK] Worsened screening (Mild -> Moderate) escalated to {res10['priority_label']}.")

    # -------------------------------------------------------------
    # TEST 11: Missing HbA1c Excluded from Scoring and Recorded
    # -------------------------------------------------------------
    print("\n[TEST 11] Testing Missing HbA1c Handling...")
    pat_no_hba1c = {
        "id": "PAT-TEST-011",
        "name": "Geeta Sharma",
        "visual_acuity_od": "6/6",
        "diabetes_duration": 4,
        "last_hba1c": None,  # Missing
    }
    res11 = calculate_screening_priority(curr_scr_mod, pat_no_hba1c)
    assert "HbA1c not available" in res11["missing_factors"]
    assert res11["evidence_checklist"]["last_hba1c"] == "Not available"
    print(f" [OK] Missing HbA1c properly excluded and logged in missing_factors.")

    # -------------------------------------------------------------
    # TEST 12: Missing Previous Screening (Baseline)
    # -------------------------------------------------------------
    print("\n[TEST 12] Testing Missing Previous Screening (Baseline)...")
    res12 = calculate_screening_priority(curr_scr_mod, pat_normal, previous_screening=None)
    assert res12["longitudinal_change_status"] == "BASELINE"
    assert "Baseline screening" in res12["longitudinal_summary"]
    print(f" [OK] Baseline screening safely marked without historical assumption.")

    # -------------------------------------------------------------
    # TEST 13: Missing Visual Acuity
    # -------------------------------------------------------------
    print("\n[TEST 13] Testing Missing Visual Acuity...")
    pat_no_va = {
        "id": "PAT-TEST-013",
        "name": "Anil Verma",
        "visual_acuity_od": None,
        "visual_acuity_os": None,
    }
    res13 = calculate_screening_priority(curr_scr_mod, pat_no_va)
    assert any("Visual acuity" in mf for mf in res13["missing_factors"])
    assert res13["evidence_checklist"]["visual_acuity"] == "Not recorded"
    print(f" [OK] Missing visual acuity handled safely without crashing.")

    # -------------------------------------------------------------
    # TEST 14: Doctor Review Preservation & Authoritative Disclaimer
    # -------------------------------------------------------------
    print("\n[TEST 14] Testing Doctor Review Preservation...")
    scr_reviewed = {
        "id": "SCR-REV-014",
        "patient_id": "PAT-TEST-014",
        "patient_name": "Ramesh Kumar Verma",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.85,
        "safety_status": "READY_FOR_AI",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Moderate",
    }
    res14 = calculate_screening_priority(scr_reviewed, pat_normal)
    assert res14["is_doctor_verified"] is True
    assert res14["doctor_status"] == "verified"
    assert "Priority is an AI-assisted triage recommendation and does not replace clinical judgment." in res14["disclaimer"]
    print(f" [OK] Doctor verification preserved with strict clinical disclaimer.")

    # -------------------------------------------------------------
    # TEST 15 & 16: Real Patient Database Integration & Zero Fake Data
    # -------------------------------------------------------------
    print("\n[TEST 15 & 16] Testing Real Database Screening Priority Queue...")
    db = SessionLocal()
    try:
        queue = get_priority_queue(db=db)
        stats = get_priority_stats(db=db)
        assert len(queue) > 0, "Priority queue should contain real DB records"
        assert stats["total_screened"] == len(queue)
        assert stats["urgent_count"] + stats["priority_count"] + stats["routine_count"] + stats["verification_required_count"] + stats["recapture_required_count"] == len(queue)
        print(f" [OK] Real Database Priority Queue evaluated: Total {stats['total_screened']} Screened (Urgent: {stats['urgent_count']}, Priority: {stats['priority_count']}, Routine: {stats['routine_count']})")
    finally:
        db.close()

    # -------------------------------------------------------------
    # TEST 17: Explanation Checklist Matches Calculated Priority
    # -------------------------------------------------------------
    print("\n[TEST 17] Testing Evidence Checklist Completeness...")
    for item in queue[:5]:
        chk = item["evidence_checklist"]
        assert "current_dr" in chk
        assert "ai_confidence" in chk
        assert "image_quality" in chk
        assert "visual_acuity" in chk
        assert "longitudinal_change" in chk
        assert len(item["primary_reason"]) > 0
    print(f" [OK] All priority items contain valid explainability checklists.")

    # -------------------------------------------------------------
    # TEST 18: Priority REST API Endpoints
    # -------------------------------------------------------------
    print("\n[TEST 18] Testing Priority REST API Endpoints...")
    # A. GET /api/priority/queue
    resp_q = client.get("/api/priority/queue")
    assert resp_q.status_code == 200, f"Queue API failed: {resp_q.text}"
    q_data = resp_q.json()
    assert "queue" in q_data
    assert "total" in q_data
    assert q_data["algorithm_version"] == ALGORITHM_VERSION

    # B. GET /api/priority/queue?filter=P1
    resp_p1 = client.get("/api/priority/queue?filter=P1")
    assert resp_p1.status_code == 200
    p1_data = resp_p1.json()
    for item in p1_data["queue"]:
        assert item["priority_level"] == "P1"

    # C. GET /api/priority/stats
    resp_stats = client.get("/api/priority/stats")
    assert resp_stats.status_code == 200
    s_data = resp_stats.json()
    assert "total_screened" in s_data
    assert "urgent_count" in s_data

    # D. GET /api/priority/screening/{id}
    first_sid = q_data["queue"][0]["screening_id"]
    resp_detail = client.get(f"/api/priority/screening/{first_sid}")
    assert resp_detail.status_code == 200
    det_data = resp_detail.json()
    assert det_data["priority_item"]["screening_id"] == first_sid
    print(f" [OK] All Priority REST endpoints passed with HTTP 200 OK.")

    # -------------------------------------------------------------
    # TEST 19: Algorithm Version and Audit Timestamps
    # -------------------------------------------------------------
    print("\n[TEST 19] Testing Audit Metadata...")
    assert det_data["priority_item"]["algorithm_version"] == "RCP-1.0"
    assert "T" in det_data["priority_item"]["calculated_at"]
    print(f" [OK] Audit version RCP-1.0 and ISO timestamps verified.")

    print("\n==================================================")
    print("ALL 19 RURAL CARE PRIORITY ENGINE TESTS PASSED!")
    print("==================================================")
    return True


if __name__ == "__main__":
    run_priority_engine_tests()
