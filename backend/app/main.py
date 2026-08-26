import os
import io
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image

from app.schemas import (
    HealthResponse,
    PredictionResponse,
    ExplainResponse,
    ScreeningAnalysisResponse,
    ErrorResponse,
)
from app.model_service import DRModelService

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
            detail="No retinal fundus image file was provided."
        )

    # Check extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # Read and check size
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded file."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty."
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
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
        logger.warning(f"Validation rejected image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid retinal image. Please upload a valid fundus photograph."
        )
    except RuntimeError as e:
        logger.warning(f"Prediction requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trained model is not available."
        )
    except Exception as e:
        logger.error(f"Inference execution failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during model inference."
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
async def explain_retinopathy(file: UploadFile = File(...)):
    """
    Computes activation gradients over the final convolutional layer of EfficientNet-B0
    and saves the Grad-CAM heatmap visualization.
    """
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.generate_gradcam(image_bytes)
        return ExplainResponse(**result)
    except ValueError as e:
        logger.warning(f"Validation rejected image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid retinal image. Please upload a valid fundus photograph."
        )
    except RuntimeError as e:
        logger.warning(f"Grad-CAM requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trained model is not available."
        )
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the Grad-CAM visualization."
        )


@app.post(
    "/api/screenings/analyze",
    response_model=ScreeningAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image or format error"},
        503: {"model": ErrorResponse, "description": "Trained model is not available"},
        500: {"model": ErrorResponse, "description": "Screening analysis failure"},
    },
    tags=["Screening Pipeline"],
    summary="Full End-to-End Retinal Screening Analysis (Prediction + Grad-CAM)",
)
async def analyze_screening(file: UploadFile = File(...)):
    """
    Performs complete end-to-end retinal image analysis:
    - Preprocessing & Retinal Quality Gate
    - Classification & Probabilities
    - Grad-CAM Heatmap Generation
    - Clinical Interpretation Guidelines
    """
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.analyze_screening(image_bytes)
        return ScreeningAnalysisResponse(**result)
    except ValueError as e:
        logger.warning(f"Validation rejected image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid retinal image. Please upload a valid fundus photograph."
        )
    except RuntimeError as e:
        logger.warning(f"Screening analysis requested while model not loaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trained model is not available."
        )
    except Exception as e:
        logger.error(f"Screening analysis failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during screening analysis."
        )

