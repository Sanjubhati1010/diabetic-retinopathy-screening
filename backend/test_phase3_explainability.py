import io
import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from app.model_service import DRModelService
from test_phase1_validation import generate_synthetic_fundus

def test_phase3_explainability():
    print("==================================================")
    print("RUNNING PHASE 3 EXPLAINABLE AI & GRAD-CAM TESTS")
    print("==================================================")

    service = DRModelService()
    assert service.is_loaded is True, "DR Model should be loaded."
    print("Service initialized with results directory:", service.results_dir)

    # 1. Prepare Test Images
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            valid_bytes = f.read()
        valid_pil = Image.open(io.BytesIO(valid_bytes)).convert("RGB")
    else:
        valid_bytes, valid_pil = generate_synthetic_fundus()

    selfie_img = Image.new("RGB", (300, 300), color=(50, 120, 220))
    buf_selfie = io.BytesIO()
    selfie_img.save(buf_selfie, format="JPEG")
    selfie_bytes = buf_selfie.getvalue()

    fundus_arr = np.array(valid_pil)
    blurred_arr = cv2.GaussianBlur(fundus_arr, (51, 51), 0)
    blurred_pil = Image.fromarray(blurred_arr)
    buf_blur = io.BytesIO()
    blurred_pil.save(buf_blur, format="JPEG")
    blur_bytes = buf_blur.getvalue()

    # ---------------------------------------------------------
    # TEST 1: Grad-CAM Overlay & Heatmap Generation on Right Eye (OD)
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Grad-CAM Generation on Valid Right Eye (OD)...")
    cam_od = service.generate_gradcam(valid_bytes)
    print(" - Predicted Class:", cam_od["class_name"])
    print(" - Overlay URL (Grad-CAM):", cam_od["gradcam_url"])
    print(" - Pure Heatmap URL:", cam_od["heatmap_url"])
    print(" - Explainability Available:", cam_od["explainability_available"])
    print(" - Simple Explanation:", cam_od["simple_explanation"])
    print(" - Limitation Note:", cam_od["limitation_note"])

    assert cam_od["explainability_available"] is True
    assert cam_od["gradcam_url"] is not None and "/results/" in cam_od["gradcam_url"]
    assert cam_od["heatmap_url"] is not None and "/results/" in cam_od["heatmap_url"]
    assert "highlighted retinal regions" in cam_od["simple_explanation"].lower()
    assert "does not replace professional clinical interpretation" in cam_od["limitation_note"].lower()

    # Verify physical file creation on disk
    overlay_disk_path = service.base_dir / cam_od["gradcam_url"].lstrip("/")
    heatmap_disk_path = service.base_dir / cam_od["heatmap_url"].lstrip("/")
    assert overlay_disk_path.is_file(), f"Overlay file not found on disk: {overlay_disk_path}"
    assert heatmap_disk_path.is_file(), f"Heatmap file not found on disk: {heatmap_disk_path}"
    print(" [OK] Right-eye Grad-CAM overlay and heatmap verified on disk.")

    # ---------------------------------------------------------
    # TEST 2: Combined Screening Analysis Pipeline (Prediction + Explainability)
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Complete Screening Analysis Pipeline (Left Eye OS)...")
    analysis_os = service.analyze_screening(valid_bytes)
    print(" - Prediction:", analysis_os["class_name"])
    print(" - Confidence:", analysis_os["confidence"])
    print(" - Screening Status:", analysis_os["screening_status"])
    print(" - Grad-CAM URL:", analysis_os["gradcam_url"])
    print(" - Heatmap URL:", analysis_os["heatmap_url"])

    assert analysis_os["explainability_available"] is True
    assert analysis_os["gradcam_url"] is not None
    assert analysis_os["heatmap_url"] is not None
    assert analysis_os["screening_status"] == "RELIABLE AI SCREENING"
    print(" [OK] Combined screening analysis with full explainability passed.")

    # ---------------------------------------------------------
    # TEST 3: Low Confidence Prediction Explainability
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing Low-Confidence Explainability Handling...")
    service_strict = DRModelService(confidence_threshold=0.999)
    cam_low = service_strict.generate_gradcam(valid_bytes)
    print(" - Strict Threshold:", service_strict.confidence_threshold)
    print(" - Is Low Confidence:", cam_low["is_low_confidence"])
    print(" - Screening Status:", cam_low["screening_status"])
    print(" - Next Step:", cam_low["next_step"])

    assert cam_low["is_low_confidence"] is True
    assert cam_low["screening_status"] == "LOW CONFIDENCE"
    assert "Recapture image or request specialist review" in cam_low["next_step"]
    assert cam_low["explainability_available"] is True
    print(" [OK] Low-confidence explainability successfully preserves transparent visualization with clinical caution.")

    # ---------------------------------------------------------
    # TEST 4: Safety Gate Integration - Invalid Non-Retinal Image
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Safety Gate Block for Non-Retinal Image (No Grad-CAM)...")
    try:
        service.generate_gradcam(selfie_bytes)
        assert False, "Grad-CAM should NOT be generated for non-retinal image!"
    except ValueError as e:
        print(" - Correctly blocked Grad-CAM generation with message:", e)
        assert "Invalid retinal image" in str(e)
    print(" [OK] Non-retinal image safely rejected before Grad-CAM generation.")

    # ---------------------------------------------------------
    # TEST 5: Safety Gate Integration - Blurry / Low Quality Image
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Safety Gate Block for Blurry Image (No Grad-CAM)...")
    try:
        service.generate_gradcam(blur_bytes)
        assert False, "Grad-CAM should NOT be generated for blurry image!"
    except ValueError as e:
        print(" - Correctly blocked Grad-CAM generation with message:", e)
        assert "AI cannot reliably assess this image" in str(e) or "blurry" in str(e).lower()
    print(" [OK] Blurry image safely rejected before Grad-CAM generation.")

    # ---------------------------------------------------------
    # TEST 6: Standby / Unloaded Model Fallback
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Model Standby / Unloaded Fallback...")
    standby_service = DRModelService(model_path="non_existent_model.pth")
    assert standby_service.is_loaded is False
    try:
        standby_service.generate_gradcam(valid_bytes)
        assert False, "Standby service should raise RuntimeError!"
    except RuntimeError as e:
        print(" - Correctly raised RuntimeError for unloaded model:", e)
    print(" [OK] Standby service fallback handled gracefully.")

    # ---------------------------------------------------------
    # TEST 7: Independent Bilateral Explainability Workflow
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing Independent Bilateral Explainability...")
    # Right Eye: valid fundus
    od_res = service.analyze_screening(valid_bytes)
    # Left Eye: blurry image (blocked)
    os_res = None
    try:
        os_res = service.analyze_screening(blur_bytes)
    except ValueError as e:
        print(" - Left eye correctly rejected by Safety Gate:", e)

    print(f" - Right Eye (OD): Explainability Available={od_res['explainability_available']}, Overlay={od_res['gradcam_url']}")
    print(f" - Left Eye (OS): Blocked (Result is None)")
    assert od_res["explainability_available"] is True
    assert os_res is None
    print(" [OK] Independent bilateral explainability verified.")

    print("\n==================================================")
    print("ALL 7 PHASE 3 EXPLAINABILITY & GRAD-CAM TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_phase3_explainability()
