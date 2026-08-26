import io
import os
import cv2
import numpy as np
from PIL import Image
from app.model_service import DRModelService

def generate_synthetic_fundus(width=512, height=512, blur=False, dark=False, bright=False):
    """Generates a synthetic realistic fundus image matching anatomical color & spectral properties."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    center = (width // 2, height // 2)
    radius = int(min(width, height) * 0.45)

    # Circular retinal illumination mask
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)

    # Base retinal color (deep orange-red)
    # RGB: R ~ 180, G ~ 65, B ~ 20
    img[mask > 0] = [185, 70, 22]

    # Add gradient / macula darkening / optic disc
    disc_center = (int(center[0] - radius * 0.4), center[1])
    cv2.circle(img, disc_center, int(radius * 0.18), (240, 210, 110), -1) # bright optic disc
    cv2.circle(img, (int(center[0] + radius * 0.3), center[1]), int(radius * 0.22), (130, 40, 15), -1) # macula

    # Add retinal vascular tree
    for i in range(12):
        pt1 = disc_center
        angle = i * (2 * np.pi / 12)
        pt2 = (int(disc_center[0] + radius * 0.7 * np.cos(angle)), int(disc_center[1] + radius * 0.7 * np.sin(angle)))
        cv2.line(img, pt1, pt2, (110, 25, 10), 2)

    # Smooth the disc/vessels
    img = cv2.GaussianBlur(img, (5, 5), 0)

    if blur:
        img = cv2.GaussianBlur(img, (45, 45), 18.0)

    if dark:
        img = (img * 0.08).astype(np.uint8)

    if bright:
        img = np.clip(img.astype(np.int16) + 160, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return buf.getvalue(), pil_img


def run_phase1_tests():
    print("==================================================")
    print("RUNNING PHASE 1 VALIDATION & QUALITY CHECK TESTS")
    print("==================================================")

    svc = DRModelService()

    # 1. Test Valid Fundus Scan (from disk or synthetic)
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        sample_img = Image.open(sample_path).convert("RGB")
        res_valid = svc.validate_image_quality(sample_img)
    else:
        _, sample_img = generate_synthetic_fundus()
        res_valid = svc.validate_image_quality(sample_img)

    print("\n[TEST 1] Valid Fundus Scan:")
    print(" - Screening Status:", res_valid["screening_status"])
    print(" - Can Proceed:", res_valid["can_proceed"])
    print(" - Metrics:", res_valid["metrics"])
    assert res_valid["can_proceed"] is True
    assert res_valid["screening_status"] in ["Ready for Screening", "Image Quality Warning"]
    print(" [OK] TEST 1 PASSED: Valid fundus image accepted.")

    # 2. Test Non-Retinal Image (e.g. Scenery / Blue Sky / Selfie)
    selfie_img = Image.new("RGB", (300, 300), color=(50, 120, 220)) # Blue sky/photo
    res_non_retinal = svc.validate_image_quality(selfie_img)
    print("\n[TEST 2] Non-Retinal Image (Blue Sky / Photo):")
    print(" - Screening Status:", res_non_retinal["screening_status"])
    print(" - Can Proceed:", res_non_retinal["can_proceed"])
    print(" - Reasons:", res_non_retinal["reasons"])
    assert res_non_retinal["can_proceed"] is False
    assert res_non_retinal["is_retinal"] is False
    assert "Invalid retinal image" in res_non_retinal["reasons"][0]
    print(" [OK] TEST 2 PASSED: Non-retinal image correctly rejected.")

    # 3. Test Low-Resolution Image (< 224x224)
    low_res_img = Image.new("RGB", (120, 120), color=(180, 50, 20))
    res_low_res = svc.validate_image_quality(low_res_img)
    print("\n[TEST 3] Low Resolution Image (120x120):")
    print(" - Screening Status:", res_low_res["screening_status"])
    print(" - Can Proceed:", res_low_res["can_proceed"])
    print(" - Reasons:", res_low_res["reasons"])
    assert res_low_res["can_proceed"] is False
    assert any("resolution is too low" in r.lower() for r in res_low_res["reasons"])
    print(" [OK] TEST 3 PASSED: Low-resolution image correctly rejected.")

    # 4. Test Blurred Fundus Image
    _, blur_img = generate_synthetic_fundus(blur=True)
    res_blur = svc.validate_image_quality(blur_img)
    print("\n[TEST 4] Blurred Fundus Image:")
    print(" - Screening Status:", res_blur["screening_status"])
    print(" - Sharpness Score:", res_blur["metrics"]["sharpness_score"])
    print(" - Reasons:", res_blur["reasons"])
    assert res_blur["can_proceed"] is False
    assert any("blurry" in r.lower() for r in res_blur["reasons"])
    print(" [OK] TEST 4 PASSED: Blurred image correctly rejected with 'Image appears blurry.'")

    # 5. Test Very Dark / Underexposed Fundus Image
    _, dark_img = generate_synthetic_fundus(dark=True)
    res_dark = svc.validate_image_quality(dark_img)
    print("\n[TEST 5] Dark / Underexposed Fundus Image:")
    print(" - Screening Status:", res_dark["screening_status"])
    print(" - Brightness Score:", res_dark["metrics"]["brightness_score"])
    print(" - Reasons:", res_dark["reasons"])
    assert res_dark["can_proceed"] is False
    assert any("too dark" in r.lower() for r in res_dark["reasons"])
    print(" [OK] TEST 5 PASSED: Dark image correctly rejected with 'Image is too dark.'")

    # 6. Test Very Bright / Overexposed Image
    _, bright_img = generate_synthetic_fundus(bright=True)
    res_bright = svc.validate_image_quality(bright_img)
    print("\n[TEST 6] Bright / Overexposed Fundus Image:")
    print(" - Screening Status:", res_bright["screening_status"])
    print(" - Brightness Score:", res_bright["metrics"]["brightness_score"])
    print(" - Reasons:", res_bright["reasons"])
    assert res_bright["can_proceed"] is False
    assert any("too bright" in r.lower() or "overexposed" in r.lower() for r in res_bright["reasons"])
    print(" [OK] TEST 6 PASSED: Overexposed image correctly rejected with 'Image is too bright / overexposed.'")

    # 7. Test Predict Rejection on Non-Retinal Image
    print("\n[TEST 7] DR Model Rejection on Invalid Image:")
    buf_non_retinal = io.BytesIO()
    selfie_img.save(buf_non_retinal, format="JPEG")
    try:
        svc.predict(buf_non_retinal.getvalue())
        assert False, "Should have raised ValueError on non-retinal image"
    except ValueError as e:
        print(" - Predict threw expected ValueError:", str(e))
        assert "Invalid retinal image" in str(e)
    print(" [OK] TEST 7 PASSED: Predict safely refuses to run on invalid images.")

    print("\n==================================================")
    print("ALL 7 PHASE 1 VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_phase1_tests()
