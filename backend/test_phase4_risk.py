import io
import os
from PIL import Image
from app.model_service import DRModelService
from app.risk_service import (
    evaluate_risk_and_referral,
    aggregate_two_eye_screening,
    RISK_LOW,
    RISK_MODERATE,
    RISK_HIGH,
    RISK_UNABLE,
    RISK_LOW_CONF,
    REFERRAL_ROUTINE,
    REFERRAL_SPECIALIST_RECOMMENDED,
    REFERRAL_PRIORITY_SPECIALIST,
    REFERRAL_RECAPTURE_REQUIRED,
)
from test_phase1_validation import generate_synthetic_fundus

def test_phase4_risk_and_referral():
    print("==================================================")
    print("RUNNING PHASE 4 RISK ASSESSMENT & REFERRAL TESTS")
    print("==================================================")

    # ---------------------------------------------------------
    # TEST 1: Class 0 (No DR, High Confidence) -> Low Risk
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Class 0 (No DR, High Confidence)...")
    res_c0 = evaluate_risk_and_referral(predicted_class=0, confidence=0.95, safety_status="READY_FOR_AI")
    print(" - Risk:", res_c0["risk_category"])
    print(" - Referral:", res_c0["referral_priority"])
    assert res_c0["risk_category"] == RISK_LOW
    assert res_c0["referral_priority"] == REFERRAL_ROUTINE
    print(" [OK] Class 0 mapped to Low Risk & Routine Follow-up.")

    # ---------------------------------------------------------
    # TEST 2: Class 1 (Mild NPDR, High Confidence) -> Moderate Risk
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Class 1 (Mild NPDR, High Confidence)...")
    res_c1 = evaluate_risk_and_referral(predicted_class=1, confidence=0.88, safety_status="READY_FOR_AI")
    assert res_c1["risk_category"] == RISK_MODERATE
    assert res_c1["referral_priority"] == REFERRAL_SPECIALIST_RECOMMENDED
    print(" [OK] Class 1 mapped to Moderate Risk & Specialist Review Recommended.")

    # ---------------------------------------------------------
    # TEST 3: Class 2 (Moderate NPDR, High Confidence) -> Moderate Risk
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Class 2 (Moderate NPDR, High Confidence)...")
    res_c2 = evaluate_risk_and_referral(predicted_class=2, confidence=0.82, safety_status="READY_FOR_AI")
    assert res_c2["risk_category"] == RISK_MODERATE
    assert res_c2["referral_priority"] == REFERRAL_SPECIALIST_RECOMMENDED
    print(" [OK] Class 2 mapped to Moderate Risk & Specialist Review Recommended.")

    # ---------------------------------------------------------
    # TEST 4: Class 3 (Severe NPDR, High Confidence) -> High Risk
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Class 3 (Severe NPDR, High Confidence)...")
    res_c3 = evaluate_risk_and_referral(predicted_class=3, confidence=0.91, safety_status="READY_FOR_AI")
    assert res_c3["risk_category"] == RISK_HIGH
    assert res_c3["referral_priority"] == REFERRAL_PRIORITY_SPECIALIST
    print(" [OK] Class 3 mapped to High Risk & Priority Specialist Review.")

    # ---------------------------------------------------------
    # TEST 5: Class 4 (PDR, High Confidence) -> High Risk
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Class 4 (Proliferative DR, High Confidence)...")
    res_c4 = evaluate_risk_and_referral(predicted_class=4, confidence=0.96, safety_status="READY_FOR_AI")
    assert res_c4["risk_category"] == RISK_HIGH
    assert res_c4["referral_priority"] == REFERRAL_PRIORITY_SPECIALIST
    print(" [OK] Class 4 mapped to High Risk & Priority Specialist Review.")

    # ---------------------------------------------------------
    # TEST 6: Low Confidence Prediction (< Threshold)
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Low Confidence Prediction (< 60%)...")
    res_low = evaluate_risk_and_referral(predicted_class=2, confidence=0.52, safety_status="READY_FOR_AI", is_low_confidence=True)
    print(" - Risk:", res_low["risk_category"])
    print(" - Referral:", res_low["referral_priority"])
    print(" - Guidance:", res_low["referral_guidance"])
    assert res_low["risk_category"] == RISK_LOW_CONF
    assert res_low["referral_priority"] == REFERRAL_SPECIALIST_RECOMMENDED
    assert "Consider image re-capture or specialist review" in res_low["referral_guidance"]
    print(" [OK] Low-confidence prediction mapped to Review Required with cautious referral.")

    # ---------------------------------------------------------
    # TEST 7: Safety Gate Blocked (Invalid Image / Poor Quality)
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing Safety Gate Blocked States (Unable to Assess)...")
    res_inv = evaluate_risk_and_referral(predicted_class=None, confidence=None, safety_status="IMAGE_INVALID")
    assert res_inv["risk_category"] == RISK_UNABLE
    assert res_inv["referral_priority"] == REFERRAL_RECAPTURE_REQUIRED

    res_qual = evaluate_risk_and_referral(predicted_class=None, confidence=None, safety_status="IMAGE_QUALITY_INSUFFICIENT")
    assert res_qual["risk_category"] == RISK_UNABLE
    assert res_qual["referral_priority"] == REFERRAL_RECAPTURE_REQUIRED

    res_block = evaluate_risk_and_referral(predicted_class=None, confidence=None, safety_status="AI_ANALYSIS_BLOCKED")
    assert res_block["risk_category"] == RISK_UNABLE
    assert res_block["referral_priority"] == REFERRAL_RECAPTURE_REQUIRED
    print(" [OK] Safety-blocked states safely mapped to UNABLE TO ASSESS & IMAGE RE-CAPTURE REQUIRED.")

    # ---------------------------------------------------------
    # TEST 8: Two-Eye Aggregation: OD Moderate, OS Low -> OD Higher Risk
    # ---------------------------------------------------------
    print("\n[TEST 8] Testing Two-Eye Aggregation (OD Moderate, OS Low)...")
    agg_od_higher = aggregate_two_eye_screening(res_c2, res_c0)
    print(" - Highest Risk Eye:", agg_od_higher["highest_risk_eye"])
    print(" - Overall Risk:", agg_od_higher["overall_risk"])
    print(" - Overall Referral:", agg_od_higher["overall_referral"])
    assert agg_od_higher["highest_risk_eye"] == "Right Eye (OD)"
    assert agg_od_higher["overall_risk"] == RISK_MODERATE
    assert agg_od_higher["overall_referral"] == REFERRAL_SPECIALIST_RECOMMENDED
    print(" [OK] Two-eye aggregation correctly attributes highest risk to OD and adopts worse-eye referral.")

    # ---------------------------------------------------------
    # TEST 9: Two-Eye Aggregation: OD Low, OS High -> OS Higher Risk
    # ---------------------------------------------------------
    print("\n[TEST 9] Testing Two-Eye Aggregation (OD Low, OS High)...")
    agg_os_higher = aggregate_two_eye_screening(res_c0, res_c3)
    assert agg_os_higher["highest_risk_eye"] == "Left Eye (OS)"
    assert agg_os_higher["overall_risk"] == RISK_HIGH
    assert agg_os_higher["overall_referral"] == REFERRAL_PRIORITY_SPECIALIST
    print(" [OK] Two-eye aggregation correctly attributes highest risk to OS.")

    # ---------------------------------------------------------
    # TEST 10: Two-Eye Aggregation: Both High Risk
    # ---------------------------------------------------------
    print("\n[TEST 10] Testing Two-Eye Aggregation (Both High Risk)...")
    agg_both_high = aggregate_two_eye_screening(res_c3, res_c4)
    assert agg_both_high["highest_risk_eye"] == "Both Eyes"
    assert agg_both_high["overall_risk"] == RISK_HIGH
    assert agg_both_high["overall_referral"] == REFERRAL_PRIORITY_SPECIALIST
    print(" [OK] Two-eye aggregation correctly attributes highest risk to Both Eyes.")

    # ---------------------------------------------------------
    # TEST 11: Two-Eye Aggregation: One Blocked, One Evaluated
    # ---------------------------------------------------------
    print("\n[TEST 11] Testing Two-Eye Aggregation (OD Blocked, OS Low Risk)...")
    agg_one_blocked = aggregate_two_eye_screening(res_inv, res_c0)
    assert agg_one_blocked["highest_risk_eye"] == "Left Eye (OS)"
    assert agg_one_blocked["overall_risk"] == RISK_LOW
    assert "Right eye image re-capture is required" in agg_one_blocked["overall_guidance"]
    print(" [OK] Evaluated eye drives risk while blocked eye flags recapture requirement.")

    # ---------------------------------------------------------
    # TEST 12: Two-Eye Aggregation: Both Eyes Blocked
    # ---------------------------------------------------------
    print("\n[TEST 12] Testing Two-Eye Aggregation (Both Eyes Blocked)...")
    agg_both_blocked = aggregate_two_eye_screening(res_inv, res_qual)
    assert agg_both_blocked["overall_risk"] == RISK_UNABLE
    assert agg_both_blocked["highest_risk_eye"] == "Unable to Assess"
    assert agg_both_blocked["overall_referral"] == REFERRAL_RECAPTURE_REQUIRED
    print(" [OK] Bilateral block correctly maps to UNABLE TO ASSESS.")

    # ---------------------------------------------------------
    # TEST 13: Live Model Service Integration Test
    # ---------------------------------------------------------
    print("\n[TEST 13] Testing Live Model Service End-to-End Pipeline...")
    service = DRModelService()
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            valid_bytes = f.read()
    else:
        valid_bytes, _ = generate_synthetic_fundus()

    pred_res = service.predict(valid_bytes)
    print(" - Live Prediction Class:", pred_res["class_name"])
    print(" - Live Risk Category:", pred_res["risk_category"])
    print(" - Live Referral Priority:", pred_res["referral_priority"])
    print(" - Live Referral Guidance:", pred_res["referral_guidance"])
    assert "risk_category" in pred_res
    assert "referral_priority" in pred_res
    assert pred_res["risk_category"] in [RISK_LOW, RISK_MODERATE, RISK_HIGH]

    analysis_res = service.analyze_screening(valid_bytes)
    assert "risk_category" in analysis_res
    assert "referral_priority" in analysis_res
    assert analysis_res["risk_category"] in [RISK_LOW, RISK_MODERATE, RISK_HIGH]
    print(" [OK] Live ModelService correctly attaches Phase 4 risk and referral payload.")

    print("\n==================================================")
    print("ALL 13 PHASE 4 RISK & REFERRAL TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_phase4_risk_and_referral()
