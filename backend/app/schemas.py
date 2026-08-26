from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., example="ok", description="Server health status")
    model_loaded: bool = Field(..., example=True, description="Whether the PyTorch model weights are loaded")
    device: str = Field(..., example="cuda", description="Compute device (cuda / cpu)")
    model_path: str = Field(..., example="models/dr_model.pth", description="Configured model file path")


class PredictionResponse(BaseModel):
    predicted_class: int = Field(..., ge=0, le=4, example=2, description="Class index (0=No DR, 1=Mild, 2=Moderate, 3=Severe, 4=Proliferative DR)")
    class_name: str = Field(..., example="Moderate", description="Human-readable ICDR classification name")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.942, description="Probability score for predicted class")
    probabilities: Dict[str, float] = Field(..., description="Probabilities across all 5 Diabetic Retinopathy classes")
    inference_time: float = Field(..., example=0.045, description="Model inference duration in seconds")


class ExplainResponse(BaseModel):
    predicted_class: int = Field(..., ge=0, le=4, example=2, description="Class index")
    class_name: str = Field(..., example="Moderate", description="Classification name")
    gradcam_url: str = Field(..., example="/results/e9c12a8f_gradcam.jpg", description="URL path to the generated Grad-CAM heatmap visualization")
    explanation: str = Field(..., description="Explainability clinical interpretation guide")
    inference_time: float = Field(..., example=0.082, description="Grad-CAM computation duration in seconds")


class ScreeningAnalysisResponse(BaseModel):
    predicted_class: int = Field(..., ge=0, le=4, example=2, description="Class index")
    class_name: str = Field(..., example="Moderate", description="Classification name")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.942, description="Probability score for predicted class")
    probabilities: Dict[str, float] = Field(..., description="Probabilities across all 5 classes")
    gradcam_url: str = Field(..., example="/results/e9c12a8f_gradcam.jpg", description="URL path to the generated Grad-CAM heatmap visualization")
    explanation: str = Field(
        default="Highlighted regions indicate image areas that contributed to the model's prediction. This visualization supports professional review and does not constitute a medical diagnosis.",
        description="Explainability guidance"
    )
    disclaimer: str = Field(
        default="AI-assisted screening only. This result is not a medical diagnosis and must be reviewed by a qualified healthcare professional.",
        description="Clinical disclaimer"
    )
    inference_time: float = Field(..., example=0.095, description="Total pipeline execution duration in seconds")


class ImageQualityMetrics(BaseModel):
    resolution: str = Field(..., example="512x512", description="Image resolution width x height")
    sharpness_score: float = Field(..., example=120.5, description="Laplacian variance sharpness metric")
    brightness_score: float = Field(..., example=85.2, description="Mean illuminated pixel brightness")
    retinal_coverage: float = Field(..., example=0.82, description="Estimated percentage of visible retinal area")


class ImageValidationResponse(BaseModel):
    is_valid_file: bool = Field(..., example=True, description="Whether the file is a valid image")
    is_retinal: bool = Field(..., example=True, description="Whether the image is verified as a retinal fundus scan")
    quality_grade: str = Field(..., example="good", description="Quality grade: 'good', 'warning', or 'insufficient'")
    screening_status: str = Field(..., example="Ready for Screening", description="Screening status: 'Ready for Screening', 'Image Quality Warning', or 'Image Re-capture Required'")
    can_proceed: bool = Field(..., example=True, description="Whether the image meets clinical criteria for model inference")
    reasons: list[str] = Field(default_factory=list, description="User-friendly clinical explanations for quality or validation issues")
    metrics: ImageQualityMetrics = Field(..., description="Computed image quality and domain metrics")
    message: str = Field(..., example="Image validated successfully and ready for screening.", description="Overall summary message")


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="Trained model is not available.", description="Error message details")
