import os
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Header, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
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
    LesionEvidenceResponse,
    ScreeningHistoryRecord,
    PatientScreeningHistoryResponse,
    ScreeningComparisonResponse,
    DoctorRecord,
    DoctorListResponse,
    DoctorAvailabilityResponse,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentNoteRequest,
    AppointmentMessageRequest,
    AppointmentMessageResponse,
    AppointmentMessageListResponse,
    VideoSessionResponse,
    WhatsAppDeliveryStatus,
    WhatsAppSendRequest,
    WhatsAppAuditEvent,
    WhatsAppDeliveryRecord,
    WhatsAppStatusResponse,
    WhatsAppRetryRequest,
    HealthWorkerProfile,
    HealthWorkerOptInRequest,
    ReportPdfResponse,
)
from app.model_service import DRModelService
from app.assistant_service import generate_assistant_reply
from app.review_service import process_doctor_review, get_audit_history, get_screening_review
from app.lesion_service import lesion_service
from app.longitudinal_service import longitudinal_service
from app.appointment_service import appointment_service
from app.pdf_service import pdf_service, verify_secure_pdf_token, generate_secure_pdf_token
from app.whatsapp_service import whatsapp_service, normalize_phone_number

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


@app.get(
    "/api/screenings/{screening_id}/review",
    response_model=Optional[DoctorReviewResponse],
    tags=["Doctor Review"],
    summary="Get Canonical Screening Review Status",
)
async def get_canonical_screening_review(screening_id: str):
    """
    Retrieves the canonical review state for a screening record.
    """
    review_data = get_screening_review(screening_id)
    if not review_data:
        return None
    return DoctorReviewResponse(**review_data)


# Phase 9: Lesion Intelligence Layer Endpoints
@app.get(
    "/api/screenings/{screening_id}/lesions",
    response_model=LesionEvidenceResponse,
    tags=["Lesion Intelligence"],
    summary="Get Lesion Intelligence & Evidence for Screening",
)
async def get_lesion_evidence(screening_id: str, eye: str = "OD"):
    """
    Phase 9 Lesion Intelligence Layer:
    - Provides dedicated lesion evidence abstraction
    - Distinct from DR Classification and Grad-CAM Attention
    - Honest non-fabricated state when no dedicated lesion model is connected
    """
    analysis = lesion_service.get_lesion_analysis(screening_id=screening_id, eye=eye)
    return LesionEvidenceResponse(**analysis)


@app.post(
    "/api/lesions/analyze",
    response_model=LesionEvidenceResponse,
    tags=["Lesion Intelligence"],
    summary="Analyze Retinal Image for Lesions",
)
async def analyze_lesions(screening_id: str = "SCR-DIRECT", eye: str = "OD"):
    """
    Direct lesion analysis endpoint for future validated model inference.
    """
    analysis = lesion_service.get_lesion_analysis(screening_id=screening_id, eye=eye)
    return LesionEvidenceResponse(**analysis)


# Phase 10: Longitudinal Patient Tracking & Progression Intelligence Endpoints
@app.get(
    "/api/patients/{patient_id}/screening-history",
    response_model=PatientScreeningHistoryResponse,
    tags=["Longitudinal Intelligence"],
    summary="Get Patient Chronological Screening History",
)
async def get_patient_screening_history(patient_id: str):
    """
    Phase 10 Longitudinal Tracking:
    - Retrieves complete chronological screening sessions for a specific patient (newest first).
    - Preserves data isolation across patients.
    """
    history = longitudinal_service.get_patient_screening_history(patient_id)
    patient_name = history[0].get("patient_name") if history else "Patient"
    
    formatted_screenings = [
        ScreeningHistoryRecord(**longitudinal_service._format_screening_summary(scr))
        for scr in history
    ]
    
    return PatientScreeningHistoryResponse(
        patient_id=patient_id,
        patient_name=patient_name,
        total_screenings=len(formatted_screenings),
        screenings=formatted_screenings,
    )


@app.get(
    "/api/screenings/{screening_id}/comparison/{previous_screening_id}",
    response_model=ScreeningComparisonResponse,
    tags=["Longitudinal Intelligence"],
    summary="Compare Current vs Specific Previous Screening",
)
async def compare_specific_screenings(screening_id: str, previous_screening_id: str):
    """
    Phase 10 Longitudinal Comparison:
    - Compares current screening with a manually selected historical screening.
    - Evaluates safe screening classification change without claiming autonomous disease progression.
    - Strictly prevents cross-patient comparisons.
    """
    current_scr = longitudinal_service.get_screening(screening_id)
    if not current_scr:
        # Fallback to reviewing active cache if exists
        rev = get_screening_review(screening_id)
        if rev:
            current_scr = {
                "screening_id": screening_id,
                "patient_id": "PAT-2026-081",
                "patient_name": "Ramesh Kumar Verma",
                "village": "Rampur Gram Panchayat",
                "screening_date": rev.get("review_timestamp", "2026-08-22"),
                "predicted_class": 2,
                "class_name": rev.get("original_ai_result", "Moderate"),
                "confidence": rev.get("original_confidence", 0.85),
                "doctor_status": "verified" if rev.get("review_status") == "AI RESULT ACCEPTED" else "pending",
                "review_status": rev.get("review_status"),
                "doctor_reviewed_result": rev.get("doctor_reviewed_result"),
                "reviewer_name": rev.get("reviewer_name"),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Current screening '{screening_id}' not found.",
            )

    previous_scr = longitudinal_service.get_screening(previous_screening_id)
    if not previous_scr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Previous screening '{previous_screening_id}' not found.",
        )

    try:
        comparison = longitudinal_service.compare_screenings(
            current_screening=current_scr,
            previous_screening=previous_scr,
        )
        return ScreeningComparisonResponse(**comparison)
    except ValueError as e:
        logger.warning(f"Longitudinal comparison rejected: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Longitudinal comparison failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to compare screenings at this time.",
        )


@app.get(
    "/api/screenings/{screening_id}/longitudinal",
    response_model=ScreeningComparisonResponse,
    tags=["Longitudinal Intelligence"],
    summary="Get Automated Longitudinal Comparison for Screening",
)
async def get_automated_longitudinal_comparison(screening_id: str, patient_id: Optional[str] = None):
    """
    Phase 10 Automated Comparison:
    - Automatically finds the most recent comparable historical screening for the patient.
    - Returns structured classification change status or 'HISTORY UNAVAILABLE' if none exists.
    """
    current_scr = longitudinal_service.get_screening(screening_id)
    if not current_scr:
        current_scr = {
            "screening_id": screening_id,
            "patient_id": patient_id or "PAT-2026-081",
            "patient_name": "Ramesh Kumar Verma",
            "village": "Rampur Gram Panchayat",
            "screening_date": "2026-08-22 10:45 AM",
            "predicted_class": 2,
            "class_name": "Moderate",
            "confidence": 0.85,
            "safety_status": "READY_FOR_AI",
            "doctor_status": "verified",
            "image_od": "/samples/eyes.png",
            "image_os": "/samples/eyes_os.png",
            "gradcam_od": "/results/sample_od_gradcam.jpg",
        }

    pid = current_scr.get("patient_id") or patient_id
    previous_scr = longitudinal_service.get_latest_comparable_screening(
        current_screening_id=screening_id,
        patient_id=pid,
    )

    try:
        comparison = longitudinal_service.compare_screenings(
            current_screening=current_scr,
            previous_screening=previous_scr,
        )
        return ScreeningComparisonResponse(**comparison)
    except Exception as e:
        logger.error(f"Automated comparison failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to compute longitudinal comparison.",
        )


# ==============================================================================
# Phase 11: Doctor Appointment & Tele-Ophthalmology Endpoints
# ==============================================================================

@app.get(
    "/api/doctors",
    response_model=DoctorListResponse,
    tags=["Tele-Ophthalmology"],
    summary="Get List of Verified Demo Doctors",
)
async def get_doctor_directory():
    """Returns list of registered tele-ophthalmology specialists with demo labeling."""
    doctors = appointment_service.get_doctors()
    return DoctorListResponse(
        doctors=[DoctorRecord(**d) for d in doctors],
        total_count=len(doctors),
    )


@app.get(
    "/api/doctors/{doctor_id}/availability",
    response_model=DoctorAvailabilityResponse,
    tags=["Tele-Ophthalmology"],
    summary="Get Doctor Available Time Slots for Date",
)
async def get_doctor_availability(doctor_id: str, date: str):
    """
    Returns 30-min consultation slots for the given date.
    Validates working hours, past-dates, and prevents double-booking.
    """
    try:
        avail = appointment_service.get_doctor_availability(doctor_id, date)
        return DoctorAvailabilityResponse(**avail)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching availability for {doctor_id}: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to retrieve doctor availability.")


@app.post(
    "/api/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tele-Ophthalmology"],
    summary="Book a Tele-Ophthalmology Appointment",
)
async def book_appointment(req: AppointmentCreateRequest):
    """
    Creates an appointment with server-side validation against working hours,
    past dates, and existing bookings.
    """
    try:
        apt = appointment_service.create_appointment(
            doctor_id=req.doctor_id,
            health_worker_id=req.health_worker_id,
            health_worker_name=req.health_worker_name,
            health_worker_email=req.health_worker_email,
            patient_id=req.patient_id,
            patient_name=req.patient_name,
            patient_age=req.patient_age,
            patient_gender=req.patient_gender,
            village=req.village,
            screening_id=req.screening_id,
            screening_summary=req.screening_summary,
            date_str=req.date,
            start_time_str=req.start_time,
            reason=req.reason,
        )
        return AppointmentResponse(**apt)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating appointment: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create appointment.")


@app.get(
    "/api/appointments",
    response_model=AppointmentListResponse,
    tags=["Tele-Ophthalmology"],
    summary="List Appointments with Optional Filters",
)
async def list_appointments(
    doctor_id: Optional[str] = None,
    health_worker_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """Lists appointments with optional doctor, health worker, patient, or status filter."""
    apts = appointment_service.list_appointments(
        doctor_id=doctor_id,
        health_worker_id=health_worker_id,
        patient_id=patient_id,
        status=status_filter,
    )
    return AppointmentListResponse(
        appointments=[AppointmentResponse(**a) for a in apts],
        total_count=len(apts),
    )


@app.get(
    "/api/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    tags=["Tele-Ophthalmology"],
    summary="Get Single Appointment Details",
)
async def get_appointment_details(appointment_id: str):
    """Returns single appointment by ID."""
    apt = appointment_service.get_appointment_by_id(appointment_id)
    if not apt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment '{appointment_id}' not found.")
    return AppointmentResponse(**apt)


@app.patch(
    "/api/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
    tags=["Tele-Ophthalmology"],
    summary="Update Appointment Status (Accept, Decline, Reschedule, Cancel, Complete)",
)
async def update_appointment_status(appointment_id: str, req: AppointmentUpdateRequest):
    """Transitions appointment status with role-based validation."""
    try:
        updated = appointment_service.update_appointment_status(
            appointment_id=appointment_id,
            new_status=req.status,
            caller_role=req.caller_role,
            reason_or_comment=req.reason_or_comment,
            proposed_date=req.proposed_date,
            proposed_time=req.proposed_time,
        )
        return AppointmentResponse(**updated)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Error updating appointment status for {appointment_id}: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update appointment status.")


@app.post(
    "/api/appointments/{appointment_id}/notes",
    response_model=AppointmentResponse,
    tags=["Tele-Ophthalmology"],
    summary="Add Doctor Clinical Consultation Notes",
)
async def add_doctor_notes(appointment_id: str, req: AppointmentNoteRequest):
    """Records doctor clinical notes, recommendation, and follow-up plan."""
    try:
        updated = appointment_service.add_consultation_notes(
            appointment_id=appointment_id,
            doctor_id=req.doctor_id,
            doctor_notes=req.doctor_notes,
            recommendations=req.doctor_recommendation,
            follow_up_date=req.follow_up_date,
        )
        return AppointmentResponse(**updated)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Error saving doctor notes for {appointment_id}: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save consultation notes.")


@app.get(
    "/api/appointments/{appointment_id}/messages",
    response_model=AppointmentMessageListResponse,
    tags=["Tele-Ophthalmology"],
    summary="Get Appointment Chat Messages",
)
async def get_appointment_messages(appointment_id: str):
    """Retrieves appointment-scoped communication messages."""
    try:
        msgs = appointment_service.get_messages(appointment_id)
        return AppointmentMessageListResponse(
            appointment_id=appointment_id,
            messages=[AppointmentMessageResponse(**m) for m in msgs],
            total_messages=len(msgs),
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@app.post(
    "/api/appointments/{appointment_id}/messages",
    response_model=AppointmentMessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tele-Ophthalmology"],
    summary="Send Message in Appointment Chat",
)
async def send_appointment_message(appointment_id: str, req: AppointmentMessageRequest):
    """Sends a message within the authorized appointment conversation."""
    try:
        msg = appointment_service.add_message(
            appointment_id=appointment_id,
            sender_id=req.sender_id,
            sender_name=req.sender_name,
            sender_role=req.sender_role,
            message=req.message,
        )
        return AppointmentMessageResponse(**msg)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@app.get(
    "/api/appointments/{appointment_id}/video/session",
    response_model=VideoSessionResponse,
    tags=["Tele-Ophthalmology"],
    summary="Authorize and Initialize Video Consultation Session",
)
async def get_video_session(appointment_id: str, user_id: str = "DOC-SWAMINATHAN", role: str = "doctor"):
    """
    Authorizes participant access to the appointment WebRTC consultation room.
    Validates room access rights and returns STUN configuration.
    """
    try:
        session_info = appointment_service.authorize_video_session(
            appointment_id=appointment_id,
            user_id=user_id,
            role=role,
        )
        return VideoSessionResponse(**session_info)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))


@app.websocket("/ws/appointments/{appointment_id}/signal")
async def websocket_signaling_endpoint(websocket: WebSocket, appointment_id: str):
    """
    Real-time WebRTC Signaling WebSocket endpoint.
    Exchanges offers, answers, ICE candidates, and peer state between authorized participants.
    """
    await websocket.accept()
    await appointment_service.register_websocket(appointment_id, websocket)
    logger.info(f"WebSocket client connected to signaling room {appointment_id}")

    try:
        # Notify existing room peers that a new participant arrived
        await appointment_service.broadcast_signal(
            appointment_id,
            websocket,
            {"type": "peer_joined", "appointment_id": appointment_id}
        )

        while True:
            data = await websocket.receive_json()
            # Relay signal message (offer, answer, ice_candidate, mute_state, etc.)
            await appointment_service.broadcast_signal(appointment_id, websocket, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from signaling room {appointment_id}")
    except Exception as e:
        logger.warning(f"WebSocket signaling error in {appointment_id}: {e}")
    finally:
        await appointment_service.unregister_websocket(appointment_id, websocket)
        await appointment_service.broadcast_signal(
            appointment_id,
            websocket,
            {"type": "peer_left", "appointment_id": appointment_id}
        )


# =====================================================================
# Phase 12: WhatsApp Clinical Report Delivery & Health Worker Endpoints
# =====================================================================

@app.get("/api/health-workers", response_model=List[HealthWorkerProfile], tags=["Phase 12: WhatsApp"])
async def list_health_workers():
    """Returns directory of registered community health workers."""
    return whatsapp_service.get_all_health_workers()


@app.get("/api/health-workers/{hw_id}/profile", response_model=HealthWorkerProfile, tags=["Phase 12: WhatsApp"])
async def get_health_worker_profile(hw_id: str):
    """Returns profile and WhatsApp opt-in consent for a specific health worker."""
    hw = whatsapp_service.get_health_worker(hw_id)
    if not hw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Health worker '{hw_id}' not found.")
    return hw


@app.patch("/api/health-workers/{hw_id}/opt-in", response_model=HealthWorkerProfile, tags=["Phase 12: WhatsApp"])
async def update_health_worker_opt_in(hw_id: str, req: HealthWorkerOptInRequest):
    """Updates WhatsApp consent opt-in status and registered phone number."""
    updated = whatsapp_service.update_health_worker_opt_in(hw_id, req.whatsapp_opt_in, req.phone)
    return updated


@app.post("/api/reports/{screening_id}/pdf", response_model=ReportPdfResponse, tags=["Phase 12: WhatsApp"])
async def generate_screening_pdf_report(screening_id: str):
    """
    Generates or retrieves the official clinical PDF report for a screening.
    Ensures doctor-review gate has been completed before generating final report.
    """
    can_proceed, reason, review = whatsapp_service.check_doctor_review_gate(screening_id)
    if not can_proceed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    pdf_path = pdf_service.generate_clinical_report(
        screening_data={"id": screening_id, "screeningDate": datetime.utcnow().strftime("%Y-%m-%d")},
        doctor_review=review,
    )
    token = generate_secure_pdf_token(screening_id)
    file_size = pdf_path.stat().st_size if pdf_path.exists() else 0

    return ReportPdfResponse(
        screening_id=screening_id,
        pdf_filename=pdf_path.name,
        pdf_url=f"/api/reports/{screening_id}/document?token={token}",
        file_size_bytes=file_size,
        generated_at=datetime.utcnow().isoformat(),
        is_final_doctor_approved=True,
    )


@app.get("/api/reports/{screening_id}/document", tags=["Phase 12: WhatsApp"])
async def download_secure_screening_pdf(screening_id: str, token: str = Query(..., description="Secure access token")):
    """
    Secure authenticated download endpoint for the clinical PDF report.
    Requires a valid cryptographically generated token.
    """
    if not verify_secure_pdf_token(screening_id, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Invalid or expired document access token.",
        )

    pdf_path = pdf_service.output_dir / f"{screening_id}_clinical_report.pdf"
    if not pdf_path.exists():
        # Generate on the fly if verified
        can_proceed, reason, review = whatsapp_service.check_doctor_review_gate(screening_id)
        if not can_proceed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        pdf_path = pdf_service.generate_clinical_report(
            screening_data={"id": screening_id, "screeningDate": datetime.utcnow().strftime("%Y-%m-%d")},
            doctor_review=review,
        )

    return FileResponse(
        path=str(pdf_path),
        filename=pdf_path.name,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_path.name}"},
    )


@app.post("/api/reports/{screening_id}/whatsapp/send", response_model=WhatsAppDeliveryRecord, tags=["Phase 12: WhatsApp"])
async def send_whatsapp_report_endpoint(screening_id: str, req: WhatsAppSendRequest):
    """
    Requests secure WhatsApp delivery of the doctor-reviewed clinical PDF report.
    Enforces:
    1. Doctor Review Gate (must be approved / accepted, re-capture requests blocked)
    2. Health Worker Phone Verification (must match registered HW record)
    3. Explicit Opt-in Consent Verification
    4. Duplicate-send prevention
    """
    try:
        delivery_record = await whatsapp_service.send_whatsapp_report(
            screening_id=screening_id,
            recipient_phone=req.recipient_phone,
            health_worker_id=req.health_worker_id,
            language=req.language,
            opt_in_confirmed=req.opt_in_confirmed,
        )
        return delivery_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Failed to send WhatsApp report for %s: %s", screening_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/reports/{screening_id}/whatsapp/status", response_model=WhatsAppStatusResponse, tags=["Phase 12: WhatsApp"])
async def get_whatsapp_status_endpoint(screening_id: str, hw_id: Optional[str] = Query("HW-RAMPUR-01")):
    """
    Returns the current WhatsApp delivery status, doctor gate evaluation, and complete audit trail.
    """
    can_send, gate_reason, review = whatsapp_service.check_doctor_review_gate(screening_id)
    delivery_rec = whatsapp_service.get_delivery_status(screening_id)
    hw = whatsapp_service.get_health_worker(hw_id or "HW-RAMPUR-01")

    rev_status = review.get("review_status", "PENDING DOCTOR REVIEW") if review else "PENDING DOCTOR REVIEW"

    return WhatsAppStatusResponse(
        screening_id=screening_id,
        status=delivery_rec.status if delivery_rec else WhatsAppDeliveryStatus.NOT_REQUESTED,
        recipient_phone=delivery_rec.recipient_phone if delivery_rec else (hw.phone if hw else None),
        health_worker_name=delivery_rec.health_worker_name if delivery_rec else (hw.name if hw else None),
        doctor_review_status=rev_status,
        can_send=can_send,
        block_reason=None if can_send else gate_reason,
        delivery_record=delivery_rec,
        audit_events=delivery_rec.audit_events if delivery_rec else [],
    )


@app.post("/api/reports/{screening_id}/whatsapp/retry", response_model=WhatsAppDeliveryRecord, tags=["Phase 12: WhatsApp"])
async def retry_whatsapp_report_endpoint(screening_id: str, req: WhatsAppRetryRequest):
    """
    Retries failed report delivery for a screening with duplicate protection.
    """
    try:
        delivery_record = await whatsapp_service.retry_whatsapp_report(
            screening_id=screening_id,
            health_worker_id=req.health_worker_id,
            force_regenerate_pdf=req.force_regenerate_pdf,
        )
        return delivery_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/whatsapp/webhook", tags=["Phase 12: WhatsApp"])
async def whatsapp_webhook_verification(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta WhatsApp Cloud API Webhook verification endpoint.
    Responds to hub.challenge during initial webhook subscription handshake.
    """
    if not hub_mode or not hub_verify_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook parameters.")

    challenge = whatsapp_service.verify_webhook_challenge(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return PlainTextResponse(content=challenge, status_code=status.HTTP_200_OK)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")


@app.post("/api/whatsapp/webhook", tags=["Phase 12: WhatsApp"])
async def whatsapp_webhook_event(request: Request):
    """
    Meta WhatsApp Cloud API incoming webhook for message delivery status updates.
    Handles 'sent', 'delivered', 'read', and 'failed' statuses securely.
    """
    try:
        payload = await request.json()
        updates = whatsapp_service.process_webhook_status_update(payload)
        return {"status": "success", "processed_updates": len(updates), "updates": updates}
    except Exception as e:
        logger.warning("Error processing WhatsApp webhook payload: %s", e)
        return {"status": "error", "detail": str(e)}




