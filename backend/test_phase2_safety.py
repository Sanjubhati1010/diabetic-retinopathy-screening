import io
import os
import cv2
import numpy as np
from PIL import Image
import torch
from app.model_service import DRModelService
from test_phase1_validation import generate_synthetic_fundus

def test_phase2_safety_and_confidence():
    print("==================================================")
    print("RUNNING PHASE 2 AI SAFETY GATE & CONFIDENCE TESTS")
    print("==================================================")

    # Initialize Service
    service = DRModelService()
    assert service.is_loaded is True, "DR Model should be loaded."
    print("Service initialized with confidence threshold:", service.confidence_threshold)

    # 1. Prepare Test Images
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            valid_bytes = f.read()
        valid_pil = Image.open(io.BytesIO(valid_bytes)).convert("RGB")
    else:
        valid_bytes, valid_pil = generate_synthetic_fundus()

    # Non-retinal selfie (blue/cyan background)
    selfie_img = Image.new("RGB", (300, 300), color=(50, 120, 220))
    buf_selfie = io.BytesIO()
    selfie_img.save(buf_selfie, format="JPEG")
    selfie_bytes = buf_selfie.getvalue()

    # Blurry image
    fundus_arr = np.array(valid_pil)
    blurred_arr = cv2.GaussianBlur(fundus_arr, (51, 51), 0)
    blurred_pil = Image.fromarray(blurred_arr)
    buf_blur = io.BytesIO()
    blurred_pil.save(buf_blur, format="JPEG")
    blur_bytes = buf_blur.getvalue()

    # ---------------------------------------------------------
    # TEST 1: High-Confidence Valid Right-Eye Image
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Valid Right-Eye Image through Safety Gate...")
    safety_od = service.evaluate_safety_gate(valid_pil)
    print(" - Safety Decision:", safety_od["safety_status"])
    print(" - Can Proceed to AI:", safety_od["can_proceed_to_ai"])
    assert safety_od["safety_status"] == "READY_FOR_AI"
    assert safety_od["can_proceed_to_ai"] is True

    pred_od = service.predict(valid_bytes)
    print(" - Prediction:", pred_od["class_name"])
    print(" - Model Confidence:", pred_od["confidence"])
    print(" - Screening Status:", pred_od["screening_status"])
    print(" - Next Step:", pred_od["next_step"])
    assert pred_od["safety_status"] == "READY_FOR_AI"
    assert pred_od["screening_status"] == "RELIABLE AI SCREENING"
    assert pred_od["is_low_confidence"] is False
    assert pred_od["confidence"] >= service.confidence_threshold
    print(" [OK] High-confidence prediction passed.")

    # ---------------------------------------------------------
    # TEST 2: High-Confidence Valid Left-Eye Image (Full Screening)
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Valid Left-Eye Screening Analysis & Grad-CAM...")
    analysis_os = service.analyze_screening(valid_bytes)
    print(" - Prediction:", analysis_os["class_name"])
    print(" - Model Confidence:", analysis_os["confidence"])
    print(" - Screening Status:", analysis_os["screening_status"])
    print(" - Grad-CAM URL:", analysis_os["gradcam_url"])
    assert analysis_os["safety_status"] == "READY_FOR_AI"
    assert analysis_os["screening_status"] == "RELIABLE AI SCREENING"
    assert "/results/" in analysis_os["gradcam_url"]
    print(" [OK] Left-eye screening analysis and Grad-CAM passed.")

    # ---------------------------------------------------------
    # TEST 3: Configurable Confidence Threshold & Low Confidence State
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Configurable Confidence Threshold (Low Confidence Detection)...")
    # Set threshold to 0.999 to strictly test low-confidence behavior
    service_strict = DRModelService(confidence_threshold=0.999)
    pred_low = service_strict.predict(valid_bytes)
    print(" - Predicted Confidence:", pred_low["confidence"])
    print(" - Strict Threshold:", pred_low["confidence_threshold"])
    print(" - Is Low Confidence:", pred_low["is_low_confidence"])
    print(" - Screening Status:", pred_low["screening_status"])
    print(" - Safety Message:", pred_low["safety_message"])
    print(" - Next Step:", pred_low["next_step"])
    assert pred_low["is_low_confidence"] is True
    assert pred_low["screening_status"] == "LOW CONFIDENCE"
    assert "AI confidence is low" in pred_low["safety_message"]
    assert "Recapture image or request specialist review" in pred_low["next_step"]
    print(" [OK] Low-confidence detection and messaging passed.")

    # ---------------------------------------------------------
    # TEST 4: Invalid Non-Retinal Image Blocked by Safety Gate
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Invalid Non-Retinal Image Blocked by Safety Gate...")
    safety_invalid = service.evaluate_safety_gate(selfie_img)
    print(" - Safety Status:", safety_invalid["safety_status"])
    print(" - Can Proceed to AI:", safety_invalid["can_proceed_to_ai"])
    print(" - Screening Status:", safety_invalid["screening_status"])
    assert safety_invalid["safety_status"] == "IMAGE_INVALID"
    assert safety_invalid["can_proceed_to_ai"] is False
    assert safety_invalid["screening_status"] == "UNABLE TO ASSESS"

    try:
        service.predict(selfie_bytes)
        assert False, "Model prediction should NOT have executed on invalid image!"
    except ValueError as e:
        print(" - Correctly blocked predict call with message:", e)
        assert "Invalid retinal image" in str(e)
    print(" [OK] Non-retinal image blocked by Safety Gate.")

    # ---------------------------------------------------------
    # TEST 5: Poor Quality (Blurry) Image Blocked by Safety Gate
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Poor Quality (Blurry) Image Blocked by Safety Gate...")
    safety_blur = service.evaluate_safety_gate(blurred_pil)
    print(" - Safety Status:", safety_blur["safety_status"])
    print(" - Can Proceed to AI:", safety_blur["can_proceed_to_ai"])
    print(" - Screening Status:", safety_blur["screening_status"])
    assert safety_blur["safety_status"] == "IMAGE_QUALITY_INSUFFICIENT"
    assert safety_blur["can_proceed_to_ai"] is False
    assert safety_blur["screening_status"] == "UNABLE TO ASSESS"

    try:
        service.predict(blur_bytes)
        assert False, "Model prediction should NOT have executed on blurry image!"
    except ValueError as e:
        print(" - Correctly blocked predict call with message:", e)
        assert "AI cannot reliably assess this image" in str(e) or "blurry" in str(e).lower()
    print(" [OK] Blurry image blocked by Safety Gate.")

    # ---------------------------------------------------------
    # TEST 6: Model Standby / Unloaded Safety Gate Block
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Safety Gate Block when Model is Unloaded...")
    standby_service = DRModelService(model_path="non_existent_model.pth")
    assert standby_service.is_loaded is False
    safety_standby = standby_service.evaluate_safety_gate(valid_pil)
    print(" - Standby Safety Status:", safety_standby["safety_status"])
    print(" - Standby Message:", safety_standby["safety_message"])
    assert safety_standby["safety_status"] == "AI_ANALYSIS_BLOCKED"
    assert safety_standby["can_proceed_to_ai"] is False
    print(" [OK] Standby mode safety block passed.")

    # ---------------------------------------------------------
    # TEST 7: Independent Bilateral Workflow (OD Ready, OS Blocked)
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing Independent Two-Eye Workflow...")
    # Right Eye: valid
    od_gate = service.evaluate_safety_gate(valid_pil)
    od_result = service.predict(valid_bytes) if od_gate["can_proceed_to_ai"] else None
    # Left Eye: blurry
    os_gate = service.evaluate_safety_gate(blurred_pil)
    os_result = service.predict(blur_bytes) if os_gate["can_proceed_to_ai"] else None

    print(f" - Right Eye (OD): Safety={od_gate['safety_status']}, Screening={od_result['screening_status']}, Class={od_result['class_name']}")
    print(f" - Left Eye (OS): Safety={os_gate['safety_status']}, Screening={os_gate['screening_status']}, Result={os_result}")
    assert od_result is not None
    assert od_result["screening_status"] == "RELIABLE AI SCREENING"
    assert os_result is None
    assert os_gate["safety_status"] == "IMAGE_QUALITY_INSUFFICIENT"
    assert os_gate["screening_status"] == "UNABLE TO ASSESS"
    print(" [OK] Independent bilateral workflow verified successfully.")

    # ---------------------------------------------------------
    # TEST 8: Softmax Probability Summation & Non-Fabricated Confidence
    # ---------------------------------------------------------
    print("\n[TEST 8] Validating Non-Fabricated Softmax Probabilities...")
    prob_sum = sum(pred_od["probabilities"].values())
    print(" - Sum of 5 class probabilities:", prob_sum)
    assert abs(prob_sum - 1.0) < 0.01, "Probabilities across all classes must sum to 1.0"
    assert pred_od["confidence"] == pred_od["probabilities"][pred_od["class_name"]]
    print(" [OK] Softmax probabilities and confidence are technically authentic.")

    # ---------------------------------------------------------
    # TEST 9: Grad-CAM Explainability Response Structure
    # ---------------------------------------------------------
    print("\n[TEST 9] Validating Grad-CAM Explanation Response with Phase 2 Fields...")
    cam_data = service.generate_gradcam(valid_bytes)
    assert "gradcam_url" in cam_data
    assert cam_data["safety_status"] == "READY_FOR_AI"
    assert cam_data["screening_status"] in ["RELIABLE AI SCREENING", "LOW CONFIDENCE"]
    print(" [OK] Grad-CAM output contains all required Phase 2 metadata.")

    print("\n==================================================")
    print("ALL 9 PHASE 2 SAFETY GATE & CONFIDENCE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_phase2_safety_and_confidence()
