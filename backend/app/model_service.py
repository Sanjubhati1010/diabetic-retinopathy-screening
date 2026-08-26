import os
import time
import uuid
import io
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
import timm
from PIL import Image
import numpy as np
import cv2

from app.risk_service import evaluate_risk_and_referral, aggregate_two_eye_screening

logger = logging.getLogger("dr_backend.model_service")

CLASS_NAMES = [
    "No DR",
    "Mild",
    "Moderate",
    "Severe",
    "Proliferative DR"
]

EXPLANATION_TEXT = (
    "Highlighted regions indicate image areas that contributed to the model's prediction. "
    "This visualization supports professional review and does not constitute a medical diagnosis."
)

CLINICAL_DISCLAIMER = (
    "AI-assisted screening only. This result is not a medical diagnosis and "
    "must be reviewed by a qualified healthcare professional."
)


# Configurable clinical confidence threshold (default: 0.60 or 60%)
DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("DR_CONFIDENCE_THRESHOLD", "0.60"))


class DRModelService:
    def __init__(self, model_path: Optional[str] = None, results_dir: Optional[str] = None, confidence_threshold: Optional[float] = None):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.model_path = Path(model_path) if model_path else self.base_dir / "models" / "dr_model.pth"
        self.results_dir = Path(results_dir) if results_dir else self.base_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = CLASS_NAMES
        self.num_classes = len(self.class_names)
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else DEFAULT_CONFIDENCE_THRESHOLD
        
        # Standard clinical preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        self.model: Optional[nn.Module] = None
        self.is_loaded: bool = False
        self._load_model()

    def _build_architecture(self) -> nn.Module:
        """Constructs timm EfficientNet-B0 architecture with 5 output classes."""
        return timm.create_model("efficientnet_b0", pretrained=False, num_classes=self.num_classes)

    def _load_model(self) -> None:
        """Loads trained weights from dr_model.pth strictly into timm EfficientNet-B0."""
        if not self.model_path.is_file():
            logger.warning(f"Model file not found at {self.model_path}. Running in standby mode.")
            self.model = None
            self.is_loaded = False
            return

        try:
            logger.info(f"Loading model weights from {self.model_path} onto {self.device}...")
            model = self._build_architecture()
            checkpoint = torch.load(self.model_path, map_location=self.device)

            if isinstance(checkpoint, dict):
                if "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                elif "model_state_dict" in checkpoint:
                    state_dict = checkpoint["model_state_dict"]
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                else:
                    state_dict = checkpoint
            elif isinstance(checkpoint, nn.Module):
                state_dict = checkpoint.state_dict()
            else:
                raise ValueError(f"Unrecognized checkpoint format: {type(checkpoint)}")
            
            # Clean common prefixes (e.g. module., model.)
            cleaned_state_dict = {}
            for k, v in state_dict.items():
                clean_k = k
                if clean_k.startswith("module."):
                    clean_k = clean_k[7:]
                if clean_k.startswith("model."):
                    clean_k = clean_k[6:]
                cleaned_state_dict[clean_k] = v

            # Strict load - fail clearly if weights do not match
            model.load_state_dict(cleaned_state_dict, strict=True)
            
            model.to(self.device)
            model.eval()
            self.model = model
            self.is_loaded = True

            param_count = sum(p.numel() for p in model.parameters())
            logger.info(
                f"trained checkpoint loaded successfully "
                f"({len(cleaned_state_dict)} parameter tensors, {param_count:,} parameters loaded onto {self.device})."
            )
        except Exception as e:
            logger.error(f"CRITICAL: Failed to strictly load model from {self.model_path}: {e}")
            self.model = None
            self.is_loaded = False

    def ensure_model_available(self) -> None:
        """Raises RuntimeError if trained model is not available."""
        if not self.is_loaded or self.model is None:
            # Check once more in case model file was placed while server was running
            self._load_model()
            if not self.is_loaded or self.model is None:
                raise RuntimeError("Trained model is not available or failed strict checkpoint loading.")

    def validate_image_quality(self, pil_image: Image.Image) -> Dict:
        """
        Phase 1 Comprehensive Multi-Criteria Quality & Retinal Domain Validation Gate.
        
        Evaluates:
        1. Resolution: Minimum dimensions (>= 224x224).
        2. Contrast: Non-solid, non-corrupt byte structure.
        3. Sharpness / Focus: Laplacian variance blur estimation.
        4. Illumination: Underexposed (too dark) vs. overexposed (too bright/glare).
        5. Retinal Coverage: Sufficient visible non-background retinal disc/macula area.
        6. Retinal Spectral Domain: Hemoglobin red spectral dominance & depleted blue absorption.
        7. HSV Hue Clustering: Natural retinal red/amber/orange cluster distribution.
        """
        img_rgb = np.array(pil_image.convert("RGB"))
        h, w, _ = img_rgb.shape
        resolution_str = f"{w}x{h}"

        reasons = []
        is_retinal = True
        quality_grade = "good"
        screening_status = "Ready for Screening"
        can_proceed = True

        # 1. Minimum Resolution Check (< 224x224)
        if h < 224 or w < 224:
            return {
                "is_valid_file": True,
                "is_retinal": False,
                "quality_grade": "insufficient",
                "screening_status": "Image Re-capture Required",
                "can_proceed": False,
                "reasons": [
                    "Image resolution is too low. Minimum resolution is 224x224 pixels.",
                    "Image quality is insufficient. Please capture or upload a clearer fundus image."
                ],
                "metrics": {
                    "resolution": resolution_str,
                    "sharpness_score": 0.0,
                    "brightness_score": 0.0,
                    "retinal_coverage": 0.0,
                },
                "message": "Image resolution is too low. Please upload a higher resolution fundus photograph."
            }

        # 2. Insufficient contrast / solid color / extreme darkness check
        std_rgb = float(np.std(img_rgb))
        mean_overall = float(np.mean(img_rgb))
        if std_rgb < 8.0:
            if mean_overall < 22.0:
                contrast_reasons = [
                    "Image quality is insufficient. Please capture or upload a clearer fundus image.",
                    "Image is too dark."
                ]
                msg = "Image is too dark. Please capture or upload a clearer fundus image."
            else:
                contrast_reasons = ["Invalid retinal image: insufficient contrast or solid color."]
                msg = "Invalid retinal image. Please upload a valid fundus image."

            return {
                "is_valid_file": True,
                "is_retinal": False,
                "quality_grade": "insufficient",
                "screening_status": "Image Re-capture Required",
                "can_proceed": False,
                "reasons": contrast_reasons,
                "metrics": {
                    "resolution": resolution_str,
                    "sharpness_score": 0.0,
                    "brightness_score": mean_overall,
                    "retinal_coverage": 0.0,
                },
                "message": msg
            }

        # 3. Extract illuminated / non-black retinal region (ignoring camera circular border)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        mask_illuminated = gray > 18
        illuminated_count = int(np.sum(mask_illuminated))
        total_pixels = h * w
        retinal_coverage = round(float(illuminated_count / total_pixels), 3)

        if illuminated_count > (0.05 * total_pixels):
            illuminated_pixels = img_rgb[mask_illuminated]
            illuminated_gray = gray[mask_illuminated]
        else:
            illuminated_pixels = img_rgb.reshape(-1, 3)
            illuminated_gray = gray.reshape(-1)

        mean_brightness = round(float(np.mean(illuminated_gray)), 2)
        r = illuminated_pixels[:, 0].astype(float)
        g = illuminated_pixels[:, 1].astype(float)
        b = illuminated_pixels[:, 2].astype(float)

        mean_r = float(np.mean(r))
        mean_g = float(np.mean(g))
        mean_b = float(np.mean(b))

        # 4. Sharpness & Focus Assessment (Laplacian Variance on gray & green channels)
        # Fundus pathology is clearest on the green channel (vascular absorption)
        green_channel = img_rgb[:, :, 1]
        laplacian_var = round(float(cv2.Laplacian(green_channel, cv2.CV_64F).var()), 2)

        # 5. Domain Retinal Spectrum & Color Signature Check
        is_spectral_red = (mean_r > mean_g) and (mean_r > mean_b * 1.08)
        blue_red_ratio = mean_b / (mean_r + 1e-5)

        # HSV Hue Clustering (reds: 0-34 & 155-180)
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        hsv_illuminated = hsv[mask_illuminated] if illuminated_count > 100 else hsv.reshape(-1, 3)
        hues = hsv_illuminated[:, 0]
        sats = hsv_illuminated[:, 1]
        is_retinal_hue = ((hues <= 34) | (hues >= 155)) & (sats >= 15)
        retinal_hue_ratio = round(float(np.mean(is_retinal_hue)), 3)

        # Check: Very Bright / Overexposed / Washed-out
        overexposed_pixels = np.sum(illuminated_gray > 235) / (len(illuminated_gray) + 1e-5)
        is_overexposed = mean_brightness > 190.0 or overexposed_pixels > 0.20
        if is_overexposed:
            reasons.append("Image is too bright / overexposed.")

        # Determine if image is a true retinal fundus photograph
        if not is_spectral_red or (blue_red_ratio > 0.72 and not is_overexposed) or (retinal_hue_ratio < 0.30 and not is_overexposed):
            is_retinal = False
            reasons.append("Invalid retinal image. Please upload a valid fundus image.")

        # 6. Quality Checks (Illumination, Blur, Coverage)
        # Check: Very Dark / Underexposed
        if mean_brightness < 22.0 or mean_r < 25.0:
            reasons.append("Image is too dark.")

        # Check: Insufficient visible retinal area
        if retinal_coverage < 0.16 and not is_overexposed:
            reasons.append("Retinal area is not clearly visible.")

        # Check: Excessive Blur / Poor Focus
        # A Laplacian variance below 18.0 indicates significant defocus or motion blur
        if laplacian_var < 18.0 and not is_overexposed:
            reasons.append("Image appears blurry.")
        elif laplacian_var < 30.0 and len(reasons) == 0:
            # Mild blur -> warning only, not fatal
            quality_grade = "warning"
            screening_status = "Image Quality Warning"
            reasons.append("Image focus is slightly soft. Please ensure proper camera stabilization.")

        # 7. Final Classification & Status Aggregation
        metrics = {
            "resolution": resolution_str,
            "sharpness_score": laplacian_var,
            "brightness_score": mean_brightness,
            "retinal_coverage": retinal_coverage,
        }

        if not is_retinal:
            quality_grade = "insufficient"
            screening_status = "Image Re-capture Required"
            can_proceed = False
            message = "Invalid retinal image. Please upload a valid fundus image."
        elif any(r in reasons for r in ["Image is too dark.", "Image is too bright / overexposed.", "Retinal area is not clearly visible.", "Image appears blurry."]):
            quality_grade = "insufficient"
            screening_status = "Image Re-capture Required"
            can_proceed = False
            reasons.insert(0, "Image quality is insufficient. Please capture or upload a clearer fundus image.")
            message = "Image quality is insufficient. Please capture or upload a clearer fundus image."
        elif quality_grade == "warning":
            can_proceed = True
            screening_status = "Image Quality Warning"
            message = "Image quality warning detected. Screening can proceed, but a clearer image is recommended."
        else:
            quality_grade = "good"
            screening_status = "Ready for Screening"
            can_proceed = True
            reasons = []
            message = "Image validated successfully and ready for screening."

        return {
            "is_valid_file": True,
            "is_retinal": is_retinal,
            "quality_grade": quality_grade,
            "screening_status": screening_status,
            "can_proceed": can_proceed,
            "reasons": reasons,
            "metrics": metrics,
            "message": message,
        }

    def evaluate_safety_gate(self, pil_image: Image.Image) -> Dict:
        """
        Phase 2 AI Safety Gate: Evaluates retinal validation and image quality.
        Determines whether the image is eligible for model inference.
        
        Possible states:
        - READY_FOR_AI
        - IMAGE_INVALID
        - IMAGE_QUALITY_INSUFFICIENT
        - AI_ANALYSIS_BLOCKED
        """
        validation_res = self.validate_image_quality(pil_image)
        
        if not validation_res["is_valid_file"] or not validation_res["is_retinal"]:
            return {
                "safety_status": "IMAGE_INVALID",
                "can_proceed_to_ai": False,
                "safety_message": "AI cannot reliably assess this image. Please capture another image or request specialist review.",
                "screening_status": "UNABLE TO ASSESS",
                "next_step": "Recapture fundus image or request specialist clinical examination.",
                "validation_res": validation_res
            }
        
        if not validation_res["can_proceed"] or validation_res["quality_grade"] == "insufficient":
            return {
                "safety_status": "IMAGE_QUALITY_INSUFFICIENT",
                "can_proceed_to_ai": False,
                "safety_message": "AI cannot reliably assess this image. Please capture another image or request specialist review.",
                "screening_status": "UNABLE TO ASSESS",
                "next_step": "Recapture fundus image with proper illumination and focus or request specialist review.",
                "validation_res": validation_res
            }
            
        if not self.is_loaded:
            return {
                "safety_status": "AI_ANALYSIS_BLOCKED",
                "can_proceed_to_ai": False,
                "safety_message": "AI screening is temporarily unavailable. Please try again.",
                "screening_status": "UNABLE TO ASSESS",
                "next_step": "Please retry after model initialization or refer for direct ophthalmologist exam.",
                "validation_res": validation_res
            }
            
        return {
            "safety_status": "READY_FOR_AI",
            "can_proceed_to_ai": True,
            "safety_message": "Image cleared AI Safety Gate for deep neural network inference.",
            "screening_status": "READY_FOR_AI",
            "next_step": "Proceed to model prediction and confidence evaluation.",
            "validation_res": validation_res
        }

    def validate_retinal_fundus(self, pil_image: Image.Image) -> Tuple[bool, str]:
        """
        Quality and domain validation gate invoking Phase 1 multi-criteria assessment.
        Returns (is_valid, reason_message).
        """
        res = self.validate_image_quality(pil_image)
        if not res["can_proceed"]:
            primary_reason = res["reasons"][0] if res["reasons"] else res["message"]
            return False, primary_reason
        return True, res["message"]

    def preprocess_image(self, image_bytes: bytes) -> Tuple[torch.Tensor, Image.Image, Dict]:
        """Validates, applies AI Safety Gate, and preprocesses image bytes into a PyTorch tensor and PIL Image."""
        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Please upload a valid image file. ({e})")

        safety_decision = self.evaluate_safety_gate(pil_image)
        if not safety_decision["can_proceed_to_ai"]:
            # If invalid retinal image, raise the exact validation rejection
            if safety_decision["safety_status"] == "IMAGE_INVALID":
                raise ValueError("Invalid retinal image. Please upload a valid fundus image.")
            else:
                raise ValueError(safety_decision["safety_message"])

        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        return tensor, pil_image, safety_decision

    def predict(self, image_bytes: bytes) -> Dict:
        """Runs PyTorch inference on retinal fundus image with Safety Gate & Confidence Check."""
        self.ensure_model_available()
        start_time = time.perf_counter()

        tensor, _, safety_decision = self.preprocess_image(image_bytes)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities_tensor = F.softmax(logits, dim=1)[0]

        probs = probabilities_tensor.cpu().numpy()
        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])
        inference_time = round(time.perf_counter() - start_time, 4)

        prob_dict = {
            self.class_names[i]: round(float(probs[i]), 4)
            for i in range(self.num_classes)
        }

        # Confidence Decision Layer
        is_low_conf = confidence < self.confidence_threshold
        if is_low_conf:
            screening_status = "LOW CONFIDENCE"
            safety_message = "AI confidence is low. Please capture a clearer image or request specialist review."
            next_step = "Recapture image or request specialist review."
        else:
            screening_status = "RELIABLE AI SCREENING"
            safety_message = "Model confidence indicates strong classification agreement."
            next_step = "Continue to explanation / specialist review."

        # Risk & Referral Evaluation
        risk_res = evaluate_risk_and_referral(
            predicted_class=predicted_class,
            confidence=confidence,
            safety_status=safety_decision["safety_status"],
            is_low_confidence=is_low_conf,
        )

        return {
            "predicted_class": predicted_class,
            "class_name": self.class_names[predicted_class],
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "safety_status": safety_decision["safety_status"],
            "screening_status": screening_status,
            "confidence_threshold": self.confidence_threshold,
            "is_low_confidence": is_low_conf,
            "risk_category": risk_res["risk_category"],
            "referral_priority": risk_res["referral_priority"],
            "risk_explanation": risk_res["risk_explanation"],
            "referral_guidance": risk_res["referral_guidance"],
            "safety_message": safety_message,
            "next_step": next_step,
            "inference_time": inference_time,
        }

    def generate_gradcam(self, image_bytes: bytes, target_class: Optional[int] = None) -> Dict:
        """
        Generates Grad-CAM activation map over the final convolutional layer (conv_head) of timm EfficientNet-B0.
        Overlays heatmap on the original retinal image and saves output to the results directory.
        """
        self.ensure_model_available()
        start_time = time.perf_counter()

        tensor, pil_image, safety_decision = self.preprocess_image(image_bytes)
        target_layer = self.model.conv_head

        # Container for activations and gradients
        feature_activations = []
        feature_gradients = []

        def forward_hook(module, input, output):
            feature_activations.append(output)

        def backward_hook(module, grad_in, grad_out):
            feature_gradients.append(grad_out[0])

        f_handle = target_layer.register_forward_hook(forward_hook)
        b_handle = target_layer.register_full_backward_hook(backward_hook)

        try:
            self.model.zero_grad()
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1)[0]

            if target_class is None:
                target_class = int(torch.argmax(probs).item())

            confidence = float(probs[target_class].item())
            is_low_conf = confidence < self.confidence_threshold

            # Target score for backpropagation
            score = logits[0, target_class]
            score.backward()

            # Global average pooling of gradients
            gradients = feature_gradients[0][0]  # [C, H, W]
            activations = feature_activations[0][0]  # [C, H, W]

            weights = torch.mean(gradients, dim=(1, 2), keepdim=True)  # [C, 1, 1]
            cam = torch.sum(weights * activations, dim=0)  # [H, W]
            cam = F.relu(cam)

            # Normalize CAM
            cam_np = cam.detach().cpu().numpy()
            cam_min, cam_max = cam_np.min(), cam_np.max()
            if cam_max > cam_min:
                cam_normalized = (cam_np - cam_min) / (cam_max - cam_min)
            else:
                cam_normalized = np.zeros_like(cam_np)

            # Resize CAM to original PIL image size
            orig_w, orig_h = pil_image.size
            cam_resized = cv2.resize(cam_normalized, (orig_w, orig_h))

            # Apply COLORMAP_JET
            heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
            heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

            orig_np = np.array(pil_image)

            # Preserve natural circular fundus canvas (keep non-retinal black border black)
            bg_mask = (orig_np[:, :, 0] < 12) & (orig_np[:, :, 1] < 12) & (orig_np[:, :, 2] < 12)
            heatmap[bg_mask] = [0, 0, 0]

            # Blend with original image
            blended = np.uint8(0.6 * orig_np + 0.4 * heatmap)

            # Save pure heatmap visualization and blended overlay visualization
            file_stem = uuid.uuid4().hex
            heatmap_filename = f"{file_stem}_heatmap.jpg"
            overlay_filename = f"{file_stem}_gradcam.jpg"

            Image.fromarray(heatmap).save(self.results_dir / heatmap_filename, format="JPEG", quality=92)
            Image.fromarray(blended).save(self.results_dir / overlay_filename, format="JPEG", quality=92)

            inference_time = round(time.perf_counter() - start_time, 4)

            # Risk & Referral Evaluation
            risk_res = evaluate_risk_and_referral(
                predicted_class=target_class,
                confidence=confidence,
                safety_status=safety_decision["safety_status"],
                is_low_confidence=is_low_conf,
            )

            return {
                "predicted_class": target_class,
                "class_name": self.class_names[target_class],
                "gradcam_url": f"/results/{overlay_filename}",
                "heatmap_url": f"/results/{heatmap_filename}",
                "explainability_available": True,
                "risk_category": risk_res["risk_category"],
                "referral_priority": risk_res["referral_priority"],
                "risk_explanation": risk_res["risk_explanation"],
                "referral_guidance": risk_res["referral_guidance"],
                "explanation": EXPLANATION_TEXT,
                "simple_explanation": "The AI model considered the highlighted retinal regions more important for its prediction.",
                "limitation_note": "This visualization explains model behavior and does not replace professional clinical interpretation. The highlighted regions show model attention and are not confirmed clinical lesions.",
                "safety_status": safety_decision["safety_status"],
                "screening_status": "LOW CONFIDENCE" if is_low_conf else "RELIABLE AI SCREENING",
                "is_low_confidence": is_low_conf,
                "next_step": "Recapture image or request specialist review." if is_low_conf else "Continue to explanation / specialist review.",
                "inference_time": inference_time,
            }
        finally:
            f_handle.remove()
            b_handle.remove()

    def analyze_screening(self, image_bytes: bytes) -> Dict:
        """Combined pipeline: classification + probabilities + Grad-CAM heatmap generation + Risk & Referral."""
        self.ensure_model_available()
        start_time = time.perf_counter()

        pred_res = self.predict(image_bytes)
        predicted_class = pred_res["predicted_class"]

        cam_res = self.generate_gradcam(image_bytes, target_class=predicted_class)
        total_time = round(time.perf_counter() - start_time, 4)

        return {
            "predicted_class": predicted_class,
            "class_name": pred_res["class_name"],
            "confidence": pred_res["confidence"],
            "probabilities": pred_res["probabilities"],
            "gradcam_url": cam_res["gradcam_url"],
            "heatmap_url": cam_res.get("heatmap_url"),
            "explainability_available": True,
            "safety_status": pred_res.get("safety_status", "READY_FOR_AI"),
            "screening_status": pred_res.get("screening_status", "RELIABLE AI SCREENING"),
            "confidence_threshold": self.confidence_threshold,
            "is_low_confidence": pred_res.get("is_low_confidence", False),
            "risk_category": pred_res.get("risk_category", "MODERATE"),
            "referral_priority": pred_res.get("referral_priority", "EYE SPECIALIST REVIEW RECOMMENDED"),
            "risk_explanation": pred_res.get("risk_explanation", "Features consistent with diabetic retinopathy detected."),
            "referral_guidance": pred_res.get("referral_guidance", "Eye specialist review is recommended based on the AI-assisted screening result."),
            "safety_message": pred_res.get("safety_message", "AI Safety Gate cleared."),
            "next_step": pred_res.get("next_step", "Continue to explanation / specialist review."),
            "explanation": EXPLANATION_TEXT,
            "simple_explanation": cam_res.get("simple_explanation", "The AI model considered the highlighted retinal regions more important for its prediction."),
            "limitation_note": cam_res.get("limitation_note", "This visualization explains model behavior and does not replace professional clinical interpretation. The highlighted regions show model attention and are not confirmed clinical lesions."),
            "disclaimer": CLINICAL_DISCLAIMER,
            "inference_time": total_time,
        }
