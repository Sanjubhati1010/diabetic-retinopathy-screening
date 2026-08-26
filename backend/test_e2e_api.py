import io
import os
import cv2
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from test_phase1_validation import generate_synthetic_fundus

def run_e2e_api_tests():
    print("==================================================")
    print("RUNNING FASTAPI END-TO-END ENDPOINT TESTS")
    print("==================================================")

    client = TestClient(app)

    # 1. Health Check
    res_health = client.get("/api/health")
    print("[API 1] GET /api/health -> Status:", res_health.status_code, res_health.json())
    assert res_health.status_code == 200
    assert res_health.json()["model_loaded"] is True
    print(" [OK] Health Check passed.")

    # 2. Prepare Images
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            valid_bytes = f.read()
    else:
        valid_bytes, _ = generate_synthetic_fundus()

    selfie_img = Image.new("RGB", (300, 300), color=(50, 120, 220))
    buf_selfie = io.BytesIO()
    selfie_img.save(buf_selfie, format="JPEG")
    selfie_bytes = buf_selfie.getvalue()

    low_res_img = Image.new("RGB", (100, 100), color=(180, 50, 20))
    buf_low_res = io.BytesIO()
    low_res_img.save(buf_low_res, format="JPEG")
    low_res_bytes = buf_low_res.getvalue()

    # 3. Test POST /api/validate-quality on Valid Retinal Image
    res_val_good = client.post(
        "/api/validate-quality",
        files={"file": ("retinal_scan.png", valid_bytes, "image/png")}
    )
    print("\n[API 2] POST /api/validate-quality (Valid Image) -> Status:", res_val_good.status_code)
    val_json = res_val_good.json()
    print(" - Screening Status:", val_json["screening_status"])
    print(" - Can Proceed:", val_json["can_proceed"])
    print(" - Metrics:", val_json["metrics"])
    assert res_val_good.status_code == 200
    assert val_json["can_proceed"] is True
    print(" [OK] Valid image validation endpoint passed.")

    # 4. Test POST /api/validate-quality on Non-Retinal Image
    res_val_bad = client.post(
        "/api/validate-quality",
        files={"file": ("selfie.jpg", selfie_bytes, "image/jpeg")}
    )
    print("\n[API 3] POST /api/validate-quality (Non-Retinal Image) -> Status:", res_val_bad.status_code)
    bad_json = res_val_bad.json()
    print(" - Screening Status:", bad_json["screening_status"])
    print(" - Can Proceed:", bad_json["can_proceed"])
    print(" - Reasons:", bad_json["reasons"])
    assert res_val_bad.status_code == 200
    assert bad_json["can_proceed"] is False
    assert bad_json["screening_status"] == "Image Re-capture Required"
    assert "Invalid retinal image" in bad_json["reasons"][0]
    print(" [OK] Non-retinal rejection endpoint passed.")

    # 5. Test POST /api/validate-quality on Invalid / Corrupt File
    res_corrupt = client.post(
        "/api/validate-quality",
        files={"file": ("corrupt.jpg", b"corrupted_bytes_header_invalid", "image/jpeg")}
    )
    print("\n[API 4] POST /api/validate-quality (Corrupt File) -> Status:", res_corrupt.status_code)
    assert res_corrupt.status_code == 400
    assert "Invalid or corrupt image" in res_corrupt.json()["detail"]
    print(" [OK] Corrupt file error handling passed.")

    # 6. Test POST /api/validate-quality on Non-Image Format
    res_txt = client.post(
        "/api/validate-quality",
        files={"file": ("document.txt", b"plain text", "text/plain")}
    )
    print("\n[API 5] POST /api/validate-quality (Unsupported Extension) -> Status:", res_txt.status_code)
    assert res_txt.status_code == 400
    assert "Please upload a valid image file" in res_txt.json()["detail"]
    print(" [OK] Unsupported format rejection passed.")

    # 7. Test POST /api/predict on Valid Image
    res_pred_good = client.post(
        "/api/predict",
        files={"file": ("retinal_scan.png", valid_bytes, "image/png")}
    )
    print("\n[API 6] POST /api/predict (Valid Fundus) -> Status:", res_pred_good.status_code)
    pred_data = res_pred_good.json()
    print(" - Predicted Class:", pred_data["predicted_class"], "(", pred_data["class_name"], ")")
    print(" - Confidence:", pred_data["confidence"])
    assert res_pred_good.status_code == 200
    assert 0 <= pred_data["predicted_class"] <= 4
    print(" [OK] Model prediction on valid scan passed.")

    # 8. Test POST /api/predict on Non-Retinal Image (Must Reject with 400)
    res_pred_bad = client.post(
        "/api/predict",
        files={"file": ("selfie.jpg", selfie_bytes, "image/jpeg")}
    )
    print("\n[API 7] POST /api/predict (Non-Retinal Image) -> Status:", res_pred_bad.status_code)
    print(" - Error Detail:", res_pred_bad.json()["detail"])
    assert res_pred_bad.status_code == 400
    assert "Invalid retinal image" in res_pred_bad.json()["detail"]
    print(" [OK] Predict endpoint safely rejects invalid retinal images.")

    # 9. Test POST /api/screenings/analyze on Valid Image
    res_ana_good = client.post(
        "/api/screenings/analyze",
        files={"file": ("retinal_scan.png", valid_bytes, "image/png")}
    )
    print("\n[API 8] POST /api/screenings/analyze (Valid Fundus) -> Status:", res_ana_good.status_code)
    ana_data = res_ana_good.json()
    print(" - Grad-CAM URL:", ana_data["gradcam_url"])
    print(" - Class:", ana_data["class_name"])
    assert res_ana_good.status_code == 200
    assert "/results/" in ana_data["gradcam_url"]
    print(" [OK] Combined screening analysis and Grad-CAM generation passed.")

    # 10. Test POST /api/screenings/analyze on Non-Retinal Image (Must Reject with 400)
    res_ana_bad = client.post(
        "/api/screenings/analyze",
        files={"file": ("selfie.jpg", selfie_bytes, "image/jpeg")}
    )
    print("\n[API 9] POST /api/screenings/analyze (Non-Retinal Image) -> Status:", res_ana_bad.status_code)
    print(" - Error Detail:", res_ana_bad.json()["detail"])
    assert res_ana_bad.status_code == 400
    assert "Invalid retinal image" in res_ana_bad.json()["detail"]
    print(" [OK] Screening analyze endpoint safely rejects invalid images.")

    print("\n==================================================")
    print("ALL 9 E2E FASTAPI ENDPOINT TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_api_tests()
