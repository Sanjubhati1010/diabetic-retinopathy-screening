from typing import Dict, Optional, List
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
    safety_status: str = Field(default="READY_FOR_AI", example="READY_FOR_AI", description="Safety Gate status: 'READY_FOR_AI', 'IMAGE_INVALID', 'IMAGE_QUALITY_INSUFFICIENT', 'AI_ANALYSIS_BLOCKED'")
    screening_status: str = Field(default="RELIABLE AI SCREENING", example="RELIABLE AI SCREENING", description="Final screening status: 'RELIABLE AI SCREENING', 'LOW CONFIDENCE', 'UNABLE TO ASSESS'")
    confidence_threshold: float = Field(default=0.60, example=0.60, description="Configured clinical confidence threshold")
    is_low_confidence: bool = Field(default=False, example=False, description="Whether predicted confidence is below the threshold")
    risk_category: str = Field(default="MODERATE", example="MODERATE", description="Risk category: LOW, MODERATE, HIGH, UNABLE TO ASSESS, LOW CONFIDENCE / REVIEW REQUIRED")
    referral_priority: str = Field(default="EYE SPECIALIST REVIEW RECOMMENDED", example="EYE SPECIALIST REVIEW RECOMMENDED", description="Referral priority: ROUTINE FOLLOW-UP, EYE SPECIALIST REVIEW RECOMMENDED, PRIORITY SPECIALIST REVIEW, IMAGE RE-CAPTURE REQUIRED")
    risk_explanation: str = Field(default="Features consistent with diabetic retinopathy detected.", description="Explanation of risk classification")
    referral_guidance: str = Field(default="Eye specialist review is recommended based on the AI-assisted screening result.", description="Guidance text for healthcare worker")
    safety_message: str = Field(default="AI Safety Gate cleared.", description="Clinical explanation of safety decision")
    next_step: str = Field(default="Continue to explanation / specialist review.", description="Actionable next step for healthcare worker")
    inference_time: float = Field(..., example=0.045, description="Model inference duration in seconds")


class ExplainResponse(BaseModel):
    predicted_class: int = Field(..., ge=0, le=4, example=2, description="Class index")
    class_name: str = Field(..., example="Moderate", description="Classification name")
    gradcam_url: str = Field(..., example="/results/e9c12a8f_gradcam.jpg", description="URL path to the generated Grad-CAM blended overlay")
    heatmap_url: Optional[str] = Field(default=None, example="/results/e9c12a8f_heatmap.jpg", description="URL path to pure Grad-CAM heatmap")
    explainability_available: bool = Field(default=True, example=True, description="Whether explainability map is successfully computed")
    risk_category: str = Field(default="MODERATE", example="MODERATE", description="Risk category")
    referral_priority: str = Field(default="EYE SPECIALIST REVIEW RECOMMENDED", example="EYE SPECIALIST REVIEW RECOMMENDED", description="Referral priority")
    risk_explanation: str = Field(default="Features consistent with diabetic retinopathy detected.", description="Explanation of risk classification")
    referral_guidance: str = Field(default="Eye specialist review is recommended based on the AI-assisted screening result.", description="Guidance text for healthcare worker")
    explanation: str = Field(..., description="Explainability clinical interpretation guide")
    simple_explanation: str = Field(
        default="The AI model considered the highlighted retinal regions more important for its prediction.",
        description="Simple explanation for community health workers and patients"
    )
    limitation_note: str = Field(
        default="This visualization explains model behavior and does not replace professional clinical interpretation. The highlighted regions show model attention and are not confirmed clinical lesions.",
        description="Clinical disclaimer on AI explanation limitations"
    )
    safety_status: str = Field(default="READY_FOR_AI", example="READY_FOR_AI", description="Safety Gate status")
    screening_status: str = Field(default="RELIABLE AI SCREENING", example="RELIABLE AI SCREENING", description="Final screening status")
    is_low_confidence: bool = Field(default=False, example=False, description="Whether predicted confidence is below the threshold")
    next_step: str = Field(default="Continue to explanation / specialist review.", description="Actionable next step")
    inference_time: float = Field(..., example=0.082, description="Grad-CAM computation duration in seconds")


class ScreeningAnalysisResponse(BaseModel):
    predicted_class: int = Field(..., ge=0, le=4, example=2, description="Class index")
    class_name: str = Field(..., example="Moderate", description="Classification name")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.942, description="Probability score for predicted class")
    probabilities: Dict[str, float] = Field(..., description="Probabilities across all 5 classes")
    gradcam_url: str = Field(..., example="/results/e9c12a8f_gradcam.jpg", description="URL path to the generated Grad-CAM blended overlay")
    heatmap_url: Optional[str] = Field(default=None, example="/results/e9c12a8f_heatmap.jpg", description="URL path to pure Grad-CAM heatmap")
    explainability_available: bool = Field(default=True, example=True, description="Whether explainability map is successfully computed")
    safety_status: str = Field(default="READY_FOR_AI", example="READY_FOR_AI", description="Safety Gate status: 'READY_FOR_AI', 'IMAGE_INVALID', 'IMAGE_QUALITY_INSUFFICIENT', 'AI_ANALYSIS_BLOCKED'")
    screening_status: str = Field(default="RELIABLE AI SCREENING", example="RELIABLE AI SCREENING", description="Final screening status: 'RELIABLE AI SCREENING', 'LOW CONFIDENCE', 'UNABLE TO ASSESS'")
    confidence_threshold: float = Field(default=0.60, example=0.60, description="Configured clinical confidence threshold")
    is_low_confidence: bool = Field(default=False, example=False, description="Whether predicted confidence is below the threshold")
    risk_category: str = Field(default="MODERATE", example="MODERATE", description="Risk category: LOW, MODERATE, HIGH, UNABLE TO ASSESS, LOW CONFIDENCE / REVIEW REQUIRED")
    referral_priority: str = Field(default="EYE SPECIALIST REVIEW RECOMMENDED", example="EYE SPECIALIST REVIEW RECOMMENDED", description="Referral priority: ROUTINE FOLLOW-UP, EYE SPECIALIST REVIEW RECOMMENDED, PRIORITY SPECIALIST REVIEW, IMAGE RE-CAPTURE REQUIRED")
    risk_explanation: str = Field(default="Features consistent with diabetic retinopathy detected.", description="Explanation of risk classification")
    referral_guidance: str = Field(default="Eye specialist review is recommended based on the AI-assisted screening result.", description="Guidance text for healthcare worker")
    safety_message: str = Field(default="AI Safety Gate cleared.", description="Clinical explanation of safety decision")
    next_step: str = Field(default="Continue to explanation / specialist review.", description="Actionable next step for healthcare worker")
    explanation: str = Field(
        default="Highlighted regions indicate image areas that contributed to the model's prediction. This visualization supports professional review and does not constitute a medical diagnosis.",
        description="Explainability guidance"
    )
    simple_explanation: str = Field(
        default="The AI model considered the highlighted retinal regions more important for its prediction.",
        description="Simple explanation for community health workers and patients"
    )
    limitation_note: str = Field(
        default="This visualization explains model behavior and does not replace professional clinical interpretation. The highlighted regions show model attention and are not confirmed clinical lesions.",
        description="Clinical disclaimer on AI explanation limitations"
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
