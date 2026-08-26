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


class DRModelService:
    def __init__(self, model_path: Optional[str] = None, results_dir: Optional[str] = None):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.model_path = Path(model_path) if model_path else self.base_dir / "models" / "dr_model.pth"
        self.results_dir = Path(results_dir) if results_dir else self.base_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = CLASS_NAMES
        self.num_classes = len(self.class_names)
        
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

    def validate_retinal_fundus(self, pil_image: Image.Image) -> Tuple[bool, str]:
        """
        Quality and domain validation gate to confirm the input image is a retinal fundus photograph
        before submitting to deep neural network classification.
        
        Evaluates:
        1. Dimension and minimum contrast threshold.
        2. Spectral red-dominance (melanin + hemoglobin vascular signature).
        3. Blue light absorption profile (depleted blue reflectance in retina).
        4. HSV retinal hue clustering (red, orange, amber spectrum).
        """
        img_rgb = np.array(pil_image.convert("RGB"))
        h, w, c = img_rgb.shape

        if h < 64 or w < 64:
            return False, "Image resolution is too low for clinical evaluation."

        # 1. Check for blank / solid / corrupt images
        std_rgb = float(np.std(img_rgb))
        if std_rgb < 8.0:
            return False, "Invalid retinal image: insufficient contrast or solid color."

        # 2. Extract illuminated / non-black pixels (ignoring fundus camera dark circular borders)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        mask_illuminated = gray > 15
        illuminated_pixels = img_rgb[mask_illuminated]

        if len(illuminated_pixels) < (0.15 * h * w):
            illuminated_pixels = img_rgb.reshape(-1, 3)

        r = illuminated_pixels[:, 0].astype(float)
        g = illuminated_pixels[:, 1].astype(float)
        b = illuminated_pixels[:, 2].astype(float)

        mean_r = float(np.mean(r))
        mean_g = float(np.mean(g))
        mean_b = float(np.mean(b))

        # 3. Spectral Red Dominance Check:
        if mean_r < 25.0:
            return False, "Invalid retinal image: underexposed or completely dark."

        if mean_r <= mean_g:
            return False, "Invalid retinal image. Please upload a valid fundus photograph."

        if mean_r <= mean_b * 1.15:
            return False, "Invalid retinal image. Please upload a valid fundus photograph."

        # Blue-to-Red ratio check (retina absorbs blue light)
        blue_red_ratio = mean_b / (mean_r + 1e-5)
        if blue_red_ratio > 0.65:
            return False, "Invalid retinal image. Please upload a valid fundus photograph."

        # 4. HSV Retinal Hue Clustering:
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        if np.sum(mask_illuminated) > (0.15 * h * w):
            hsv_illuminated = hsv[mask_illuminated]
        else:
            hsv_illuminated = hsv.reshape(-1, 3)

        hues = hsv_illuminated[:, 0]
        sats = hsv_illuminated[:, 1]

        # Retinal red-orange-amber hues with moderate saturation
        is_retinal_hue = ((hues <= 34) | (hues >= 160)) & (sats >= 20)
        retinal_hue_ratio = float(np.mean(is_retinal_hue))

        if retinal_hue_ratio < 0.40:
            return False, "Invalid retinal image. Please upload a valid fundus photograph."

        return True, "Valid retinal fundus photograph verified."

    def preprocess_image(self, image_bytes: bytes) -> Tuple[torch.Tensor, Image.Image]:
        """Validates and preprocesses image bytes into a PyTorch tensor and PIL Image."""
        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid image format or corrupted file: {e}")

        # Retinal fundus quality & domain validation gate
        is_valid, reason = self.validate_retinal_fundus(pil_image)
        if not is_valid:
            raise ValueError(f"Invalid retinal image. Please upload a valid fundus photograph. ({reason})")

        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        return tensor, pil_image

    def predict(self, image_bytes: bytes) -> Dict:
        """Runs PyTorch inference on retinal fundus image."""
        self.ensure_model_available()
        start_time = time.perf_counter()

        tensor, _ = self.preprocess_image(image_bytes)

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

        return {
            "predicted_class": predicted_class,
            "class_name": self.class_names[predicted_class],
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "inference_time": inference_time,
        }

    def generate_gradcam(self, image_bytes: bytes, target_class: Optional[int] = None) -> Dict:
        """
        Generates Grad-CAM activation map over the final convolutional layer (conv_head) of timm EfficientNet-B0.
        Overlays heatmap on the original retinal image and saves output to the results directory.
        """
        self.ensure_model_available()
        start_time = time.perf_counter()

        tensor, pil_image = self.preprocess_image(image_bytes)
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

            # Blend with original image
            orig_np = np.array(pil_image)
            blended = np.uint8(0.6 * orig_np + 0.4 * heatmap)

            # Save result visualization
            unique_filename = f"{uuid.uuid4().hex}_gradcam.jpg"
            output_filepath = self.results_dir / unique_filename
            Image.fromarray(blended).save(output_filepath, format="JPEG", quality=92)

            inference_time = round(time.perf_counter() - start_time, 4)

            return {
                "predicted_class": target_class,
                "class_name": self.class_names[target_class],
                "gradcam_url": f"/results/{unique_filename}",
                "explanation": EXPLANATION_TEXT,
                "inference_time": inference_time,
            }
        finally:
            f_handle.remove()
            b_handle.remove()

    def analyze_screening(self, image_bytes: bytes) -> Dict:
        """Combined pipeline: classification + probabilities + Grad-CAM heatmap generation."""
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
            "explanation": EXPLANATION_TEXT,
            "disclaimer": CLINICAL_DISCLAIMER,
            "inference_time": total_time,
        }
