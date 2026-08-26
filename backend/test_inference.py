import io
import torch
from PIL import Image
from app.model_service import DRModelService

def test_model_service_inference():
    # 1. Instantiate service pointing to dummy weights for self-testing
    service = DRModelService(model_path="models/test_model.pth")

    # Build and save architecture weights
    model = service._build_architecture()
    torch.save(model.state_dict(), "models/test_model.pth")

    # Reload service with the weights
    service = DRModelService(model_path="models/test_model.pth")
    assert service.is_loaded is True

    # 2. Load or generate valid sample fundus image
    import os
    sample_path = os.path.join("..", "public", "samples", "eyes.png")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            jpeg_bytes = f.read()
    else:
        from test_phase1_validation import generate_synthetic_fundus
        jpeg_bytes, _ = generate_synthetic_fundus()

    # 3. Test predict
    pred = service.predict(jpeg_bytes)
    print("Predict result:", pred)
    assert 0 <= pred["predicted_class"] <= 4
    assert len(pred["probabilities"]) == 5
    assert pred["class_name"] in service.class_names

    # 4. Test Grad-CAM
    cam = service.generate_gradcam(jpeg_bytes)
    print("Grad-CAM result:", cam)
    assert "/results/" in cam["gradcam_url"]
    assert "Highlighted regions" in cam["explanation"]

    # 5. Test combined analyze_screening
    analysis = service.analyze_screening(jpeg_bytes)
    print("Full screening analysis:", analysis)
    assert analysis["disclaimer"] is not None

    # Clean up test model file
    if os.path.exists("models/test_model.pth"):
        os.remove("models/test_model.pth")

    print("\nINFERENCE & GRAD-CAM PIPELINE VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_model_service_inference()
