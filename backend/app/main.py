import os
import io
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image

from app.schemas import (
    HealthResponse,
    PredictionResponse,
    ExplainResponse,
    ScreeningAnalysisResponse,
    ImageValidationResponse,
    ErrorResponse,
    AssistantChatRequest,
    AssistantChatResponse,
    DoctorReviewRequest,
    DoctorReviewResponse,
    ReviewHistoryResponse,
)
from app.model_service import DRModelService
from app.assistant_service import generate_assistant_reply
from app.review_service import process_doctor_review, get_audit_history

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dr_backend.main")

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file specifications
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

# Initialize FastAPI App
app = FastAPI(
    title="Explainable AI for Diabetic Retinopathy Screening in Rural India",
    description=(
        "FastAPI Backend providing deep learning EfficientNet-B0 inference and "
        "Grad-CAM visual explainability maps for Diabetic Retinopathy community screening."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_origins = os.getenv("CORS_ORIGINS", "")
if env_origins:
    allowed_origins = [orig.strip() for orig in env_origins.split(",") if orig.strip()]
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for results
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

# Initialize Model Service
model_service = DRModelService(
    model_path=str(MODELS_DIR / "dr_model.pth"),
    results_dir=str(RESULTS_DIR),
)


async def validate_and_read_image(file: UploadFile) -> bytes:
    """
    Validates uploaded file format, size, and image integrity.
    Returns the raw image bytes if valid.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file. No file was provided."
        )

    # Check extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file (.jpg, .jpeg, .png)."
        )

    # Read and check size
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded image file."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file. The uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB. Please upload a smaller image file."
        )

    # Verify PIL image integrity
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as e:
        logger.warning(f"Corrupt image upload rejected: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupt image content. Please upload a valid retinal fundus scan."
        )

    return content


@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Explainable AI for Diabetic Retinopathy Screening in Rural India",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API and PyTorch Model Health",
)
async def health_check():
    """Returns backend service health and model loading readiness."""
    return HealthResponse(
        status="ok",
        model_loaded=model_service.is_loaded,
        device=str(model_service.device),
        model_path=str(model_service.model_path.name),
    )


@app.post(
    "/api/validate-quality",
    response_model=ImageValidationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file format or corrupt image"},
    },
    tags=["Validation"],
    summary="Validate Retinal Fundus & Assess Image Quality",
)
async def validate_image(file: UploadFile = File(...)):
    """
    Phase 1 Pre-Inference Validation & Quality Assessment Gate:
    - Verifies file format, integrity & resolution (>= 224x224)
    - Verifies retinal fundus spectral & hue domain signature
    - Evaluates sharpness/focus (Laplacian blur score), illumination & visible coverage
    - Assigns structured screening status ('Ready for Screening', 'Image Quality Warning', or 'Image Re-capture Required')
    """
    image_bytes = await validate_and_read_image(file)

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        result = model_service.validate_image_quality(pil_image)
        return ImageValidationResponse(**result)
    except Exception as e:
        logger.error(f"Image validation gate encountered an error: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file."
        )


@app.post(
    "/api/predict",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image or format error"},
        503: {"model": ErrorResponse, "description": "Trained model is not available"},
        500: {"model": ErrorResponse, "description": "Inference computation failure"},
    },
    tags=["Inference"],
    summary="Predict Diabetic Retinopathy Severity",
)
async def predict_retinopathy(file: UploadFile = File(...)):
    """
    Accepts a retinal fundus scan and outputs predicted ICDR severity and probability scores across all 5 classes.
    """
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.predict(image_bytes)
        return PredictionResponse(**result)
    except ValueError as e:
        error_msg = str(e) if str(e) else "Invalid retinal image. Please upload a valid fundus image."
        logger.warning(f"Validation rejected image: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except RuntimeError as e:
        logger.warning(f"Prediction requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI screening is temporarily unavailable. Please try again."
        )
    except Exception as e:
        logger.error(f"Inference execution failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI screening is temporarily unavailable. Please try again."
        )


@app.post(
    "/api/explain",
    response_model=ExplainResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image or format error"},
        503: {"model": ErrorResponse, "description": "Trained model is not available"},
        500: {"model": ErrorResponse, "description": "Grad-CAM generation failure"},
    },
    tags=["Explainability"],
    summary="Generate Grad-CAM Visual Explainability Heatmap",
)
async def explain_prediction(
    file: UploadFile = File(...),
):
    """
    Computes a Grad-CAM localization heatmap for the input fundus scan.
    """
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.generate_gradcam(image_bytes)
        return ExplainResponse(**result)
    except ValueError as e:
        error_msg = str(e) if str(e) else "Invalid retinal image. Please upload a valid fundus image."
        logger.warning(f"Validation rejected image during explain: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except RuntimeError as e:
        logger.warning(f"Explain requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI screening is temporarily unavailable. Please try again."
        )
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI screening is temporarily unavailable. Please try again."
        )


@app.post(
    "/api/screenings/analyze",
    response_model=ScreeningAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image or format error"},
        503: {"model": ErrorResponse, "description": "Trained model is not available"},
        500: {"model": ErrorResponse, "description": "Analysis pipeline failure"},
    },
    tags=["Screening"],
    summary="Complete Retinal Screening: AI Prediction + Explainable Grad-CAM",
)
async def analyze_screening(
    file: UploadFile = File(...),
):
    """
    Combined Phase 2 Screening Pipeline:
    - Pre-inference validation & quality assessment
    - AI Safety Gate check
    - EfficientNet-B0 inference & confidence check
    - Grad-CAM heatmap visualization
    - Clinical disclaimer & triage guidance
    """
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.analyze_screening(image_bytes)
        return ScreeningAnalysisResponse(**result)
    except ValueError as e:
        error_msg = str(e) if str(e) else "Invalid retinal image. Please upload a valid fundus image."
        logger.warning(f"Validation rejected image in screening analysis: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except RuntimeError as e:
        logger.warning(f"Analysis requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI screening is temporarily unavailable. Please try again."
        )
    except Exception as e:
        logger.error(f"Screening analysis pipeline failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI screening is temporarily unavailable. Please try again."
        )


@app.post(
    "/api/assistant/chat",
    response_model=AssistantChatResponse,
    tags=["Assistant"],
    summary="Contextual AI Screening Assistant Chat",
)
async def assistant_chat(request: AssistantChatRequest):
    """
    Phase 5 Contextual AI Screening Assistant:
    - Provides bilingual decision support (English & Hindi)
    - Interprets active screening context (Prediction, Confidence, Safety Gate, Risk, Referral, Grad-CAM)
    - Explains image validation failures, quality rules, and Grad-CAM visualizations
    - Guardrails against unauthorized medical prescribing or clinical certainty
    """
    try:
        reply_dict = generate_assistant_reply(
            message=request.message,
            language=request.language,
            page=request.page,
            screening_context=request.screening_context,
        )
        return AssistantChatResponse(**reply_dict)
    except Exception as e:
        logger.error(f"Assistant service error: {e}", exc_info=False)
        return AssistantChatResponse(
            reply="The MADOCS Assistant is temporarily experiencing connection difficulty. You can continue with standard screening or review quick help.",
            language=request.language,
            suggested_actions=["How to Use?", "Why Rejected?"],
            context_used=False,
        )


@app.post(
    "/api/screenings/{screening_id}/review",
    response_model=DoctorReviewResponse,
    tags=["Doctor Review"],
    summary="Submit Human-in-the-Loop Doctor Review",
)
async def submit_doctor_review(
    screening_id: str,
    review_req: DoctorReviewRequest,
    x_user_role: Optional[str] = Header(default="doctor", alias="X-User-Role"),
    original_ai_result: str = "Moderate",
    original_confidence: Optional[float] = 0.85,
):
    """
    Phase 6 Human-in-the-Loop Doctor Review:
    - Allows verified doctor to ACCEPT, MODIFY, or REQUEST RE-CAPTURE
    - Preserves original AI prediction permanently
    - Requires review comment on MODIFY action
    - Logs an immutable event to the audit trail
    """
    try:
        response = process_doctor_review(
            request=review_req,
            original_ai_result=original_ai_result,
            original_confidence=original_confidence,
            role=x_user_role,
        )
        return response
    except PermissionError as e:
        logger.warning(f"Unauthorized doctor review attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        logger.warning(f"Invalid doctor review submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Doctor review submission failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the review. Please try again.",
        )


@app.get(
    "/api/screenings/{screening_id}/history",
    response_model=ReviewHistoryResponse,
    tags=["Doctor Review"],
    summary="Get Screening Audit Trail History",
)
async def get_screening_history(screening_id: str):
    """
    Retrieves the complete chronological audit history for a screening record.
    """
    events = get_audit_history(screening_id)
    return ReviewHistoryResponse(
        screening_id=screening_id,
        events=events,
    )
