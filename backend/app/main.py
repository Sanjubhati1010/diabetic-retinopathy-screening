import os
import io
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Header, WebSocket, WebSocketDisconnect, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal, Base, engine, check_db_health
from app.models import (
    PatientModel,
    ScreeningModel,
    DoctorModel,
    HealthWorkerModel,
    AppointmentModel,
    ScreeningReviewModel,
    ReviewAuditEventModel,
    ReportModel,
    WhatsAppDeliveryModel,
    WhatsAppAuditEventModel,
    EmailDeliveryModel,
    EmailAuditEventModel,
)
from app.db_seeder import seed_database_if_empty
from app.email_service import email_service
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
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    PatientListResponse,
    ScreeningCreateRequest,
    ScreeningRecordResponse,
    ScreeningListResponse,
    EmailDeliveryStatus,
    EmailSendRequest,
    EmailAuditEvent,
    EmailDeliveryRecord,
    EmailStatusResponse,
    EmailRetryRequest,
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
        "FastAPI Backend providing deep learning EfficientNet-B0 inference, "
        "Grad-CAM visual explainability maps, and persistent MySQL/SQLAlchemy clinical storage."
    ),
    version="1.13.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Ensure tables and seed exist at import time
try:
    Base.metadata.create_all(bind=engine)
    _db_init = SessionLocal()
    try:
        seed_database_if_empty(_db_init)
    finally:
        _db_init.close()
except Exception as e:
    logger.warning(f"Initial DB seed warning: {e}")

# Startup Hook: Initialize DB & Seed Demo Records
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database_if_empty(db)
        finally:
            db.close()
        logger.info("Database initialized and verified on startup.")
    except Exception as e:
        logger.error(f"Database initialization error on startup: {e}")

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

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file (.jpg, .jpeg, .png)."
        )

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
        "database": "connected" if check_db_health() else "degraded",
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
    """
    image_bytes = await validate_and_read_image(file)

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        validation_result = model_service.validate_image_quality(pil_image)
        return ImageValidationResponse(**validation_result)
    except Exception as e:
        logger.error(f"Image validation processing failed: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupt image content. Please upload a valid retinal fundus scan."
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
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.predict(image_bytes)
        return PredictionResponse(**result)
    except ValueError as e:
        error_msg = str(e) if str(e) else "Invalid retinal image. Please upload a valid fundus image."
        logger.warning(f"Validation rejected image: {error_msg}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI screening is temporarily unavailable. Please try again.")
    except Exception as e:
        logger.error(f"Inference execution failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI screening is temporarily unavailable. Please try again.")


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
async def explain_prediction(file: UploadFile = File(...)):
    image_bytes = await validate_and_read_image(file)

    try:
        result = model_service.generate_gradcam(image_bytes)
        return ExplainResponse(**result)
    except ValueError as e:
        error_msg = str(e) if str(e) else "Invalid retinal image. Please upload a valid fundus image."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI screening is temporarily unavailable. Please try again.")
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI screening is temporarily unavailable. Please try again.")


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
async def analyze_screening(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI screening is temporarily unavailable. Please try again.")
    except Exception as e:
        logger.error(f"Screening analysis pipeline failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI screening is temporarily unavailable. Please try again.")


# =====================================================================
# Phase 13: Persistent Patient Management Endpoints
# =====================================================================

@app.get(
    "/api/patients",
    response_model=PatientListResponse,
    tags=["Patients"],
    summary="Get List of Registered Patients",
)
async def list_patients(db: Session = Depends(get_db)):
    """Returns all registered patients from MySQL database."""
    try:
        patients = db.query(PatientModel).order_by(PatientModel.created_at.desc()).all()
        result = []
        for p in patients:
            symptoms = json.loads(p.symptoms_json) if p.symptoms_json else []
            result.append(
                PatientResponse(
                    id=p.id,
                    abha_id=p.abha_id,
                    name=p.name,
                    age=p.age,
                    gender=p.gender,
                    phone=p.phone,
                    mobile=p.phone,
                    email=p.email,
                    village=p.village,
                    district=p.district,
                    diabetes_duration=p.diabetes_duration,
                    last_hba1c=p.last_hba1c,
                    insulin_use=p.insulin_use,
                    visual_acuity_od=p.visual_acuity_od,
                    visual_acuity_os=p.visual_acuity_os,
                    symptoms=symptoms,
                    registered_date=p.registered_date,
                    last_screened=p.last_screened,
                    latest_status=p.latest_status,
                    referral_urgency=p.referral_urgency,
                    doctor_verified=p.doctor_verified,
                )
            )
        return PatientListResponse(total=len(result), patients=result)
    except Exception as e:
        logger.error(f"Error fetching patients from DB: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to fetch patients.")


@app.post(
    "/api/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"],
    summary="Register a New Patient",
)
async def create_patient(req: PatientCreateRequest, db: Session = Depends(get_db)):
    """Registers and persists a new patient into MySQL database."""
    try:
        # Validate email if provided
        clean_email = None
        effective_email = req.email or req.email_address
        if effective_email and effective_email.strip():
            clean_email = email_service.normalize_email(effective_email)
            if not clean_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format.")

        effective_phone = req.phone or req.mobile or req.mobile_number or req.phone_number

        count = db.query(PatientModel).count()
        pat_id = f"PAT-2026-{count + 81:03d}"
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        new_pat = PatientModel(
            id=pat_id,
            abha_id=req.abha_id,
            name=req.name,
            age=req.age,
            gender=req.gender,
            phone=effective_phone,
            email=clean_email,
            village=req.village,
            district=req.district,
            diabetes_duration=req.diabetes_duration,
            last_hba1c=req.last_hba1c,
            insulin_use=req.insulin_use,
            visual_acuity_od=req.visual_acuity_od or "6/6",
            visual_acuity_os=req.visual_acuity_os or "6/6",
            symptoms_json=json.dumps(req.symptoms or []),
            registered_date=now_date,
            last_screened="-",
            latest_status="drUncertain",
            referral_urgency="routine",
            doctor_verified=False,
        )
        db.add(new_pat)
        db.commit()
        db.refresh(new_pat)

        return PatientResponse(
            id=new_pat.id,
            abha_id=new_pat.abha_id,
            name=new_pat.name,
            age=new_pat.age,
            gender=new_pat.gender,
            phone=new_pat.phone,
            mobile=new_pat.phone,
            email=new_pat.email,
            village=new_pat.village,
            district=new_pat.district,
            diabetes_duration=new_pat.diabetes_duration,
            last_hba1c=new_pat.last_hba1c,
            insulin_use=new_pat.insulin_use,
            visual_acuity_od=new_pat.visual_acuity_od,
            visual_acuity_os=new_pat.visual_acuity_os,
            symptoms=req.symptoms or [],
            registered_date=new_pat.registered_date,
            last_screened=new_pat.last_screened,
            latest_status=new_pat.latest_status,
            referral_urgency=new_pat.referral_urgency,
            doctor_verified=new_pat.doctor_verified,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving patient to database: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save data. Please try again.")


@app.get(
    "/api/patients/{patient_id}",
    response_model=PatientResponse,
    tags=["Patients"],
    summary="Get Specific Patient by ID",
)
async def get_patient_detail(patient_id: str, db: Session = Depends(get_db)):
    pat = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
    if not pat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")
    symptoms = json.loads(pat.symptoms_json) if pat.symptoms_json else []
    return PatientResponse(
        id=pat.id,
        abha_id=pat.abha_id,
        name=pat.name,
        age=pat.age,
        gender=pat.gender,
        phone=pat.phone,
        mobile=pat.phone,
        email=pat.email,
        village=pat.village,
        district=pat.district,
        diabetes_duration=pat.diabetes_duration,
        last_hba1c=pat.last_hba1c,
        insulin_use=pat.insulin_use,
        visual_acuity_od=pat.visual_acuity_od,
        visual_acuity_os=pat.visual_acuity_os,
        symptoms=symptoms,
        registered_date=pat.registered_date,
        last_screened=pat.last_screened,
        latest_status=pat.latest_status,
        referral_urgency=pat.referral_urgency,
        doctor_verified=pat.doctor_verified,
    )


@app.patch(
    "/api/patients/{patient_id}",
    response_model=PatientResponse,
    tags=["Patients"],
    summary="Update Patient Record",
)
async def update_patient(patient_id: str, req: PatientUpdateRequest, db: Session = Depends(get_db)):
    pat = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
    if not pat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found.")
    try:
        effective_email = req.email or req.email_address
        if req.email is not None or req.email_address is not None:
            if effective_email and effective_email.strip():
                clean_email = email_service.normalize_email(effective_email)
                if not clean_email:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format.")
                pat.email = clean_email
            else:
                pat.email = None

        effective_phone = req.phone or req.mobile or req.mobile_number or req.phone_number
        if req.phone is not None or req.mobile is not None or req.mobile_number is not None or req.phone_number is not None:
            pat.phone = effective_phone

        if req.name is not None: pat.name = req.name
        if req.age is not None: pat.age = req.age
        if req.gender is not None: pat.gender = req.gender
        if req.village is not None: pat.village = req.village
        if req.district is not None: pat.district = req.district
        if req.abha_id is not None: pat.abha_id = req.abha_id
        if req.diabetes_duration is not None: pat.diabetes_duration = req.diabetes_duration
        if req.last_hba1c is not None: pat.last_hba1c = req.last_hba1c
        if req.insulin_use is not None: pat.insulin_use = req.insulin_use
        if req.visual_acuity_od is not None: pat.visual_acuity_od = req.visual_acuity_od
        if req.visual_acuity_os is not None: pat.visual_acuity_os = req.visual_acuity_os
        if req.symptoms is not None: pat.symptoms_json = json.dumps(req.symptoms)
        if req.last_screened is not None: pat.last_screened = req.last_screened
        if req.latest_status is not None: pat.latest_status = req.latest_status
        if req.referral_urgency is not None: pat.referral_urgency = req.referral_urgency
        if req.doctor_verified is not None: pat.doctor_verified = req.doctor_verified

        db.commit()
        db.refresh(pat)
        symptoms = json.loads(pat.symptoms_json) if pat.symptoms_json else []
        return PatientResponse(
            id=pat.id,
            abha_id=pat.abha_id,
            name=pat.name,
            age=pat.age,
            gender=pat.gender,
            phone=pat.phone,
            mobile=pat.phone,
            email=pat.email,
            village=pat.village,
            district=pat.district,
            diabetes_duration=pat.diabetes_duration,
            last_hba1c=pat.last_hba1c,
            insulin_use=pat.insulin_use,
            visual_acuity_od=pat.visual_acuity_od,
            visual_acuity_os=pat.visual_acuity_os,
            symptoms=symptoms,
            registered_date=pat.registered_date,
            last_screened=pat.last_screened,
            latest_status=pat.latest_status,
            referral_urgency=pat.referral_urgency,
            doctor_verified=pat.doctor_verified,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating patient {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save data. Please try again.")


# =====================================================================
# Phase 13: Screening Storage & Retrieval Endpoints
# =====================================================================

@app.post(
    "/api/screenings",
    response_model=ScreeningRecordResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Screening"],
    summary="Save a Completed Screening Record",
)
async def create_screening_record(req: ScreeningCreateRequest, db: Session = Depends(get_db)):
    """Persists a full screening session into MySQL."""
    try:
        count = db.query(ScreeningModel).count()
        sid = req.id or f"SCR-2026-{count + 991:04d}"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p")
        now_iso = datetime.now(timezone.utc).isoformat()

        scr = ScreeningModel(
            id=sid,
            patient_id=req.patient_id,
            patient_name=req.patient_name,
            village=req.village,
            screening_date=req.screening_date or now_str,
            timestamp_iso=req.timestamp_iso or now_iso,
            predicted_class=req.predicted_class,
            class_name=req.class_name,
            confidence=req.confidence,
            probabilities_json=json.dumps(req.probabilities or {}),
            dr_severity_od=req.dr_severity_od or "drUncertain",
            dr_severity_os=req.dr_severity_os or "drUncertain",
            overall_severity=req.overall_severity or "drUncertain",
            safety_status=req.safety_status or "READY_FOR_AI",
            screening_status=req.screening_status or "RELIABLE AI SCREENING",
            risk_category=req.risk_category or "MODERATE",
            referral_priority=req.referral_priority or "EYE SPECIALIST REVIEW RECOMMENDED",
            risk_explanation=req.risk_explanation,
            referral_guidance=req.referral_guidance,
            safety_message=req.safety_message,
            gradcam_url=req.gradcam_url,
            heatmap_url=req.heatmap_url,
            image_od_path=req.image_od_path,
            image_os_path=req.image_os_path,
            doctor_status=req.doctor_status or "pending",
            review_status=req.review_status or "PENDING DOCTOR REVIEW",
        )
        db.add(scr)

        # Update patient record
        pat = db.query(PatientModel).filter(PatientModel.id == req.patient_id).first()
        if pat:
            pat.last_screened = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            pat.latest_status = req.overall_severity or "drUncertain"
            pat.referral_urgency = req.risk_category or "routine"

        db.commit()
        db.refresh(scr)

        # Mirror to longitudinal service
        longitudinal_service.register_or_update_screening({
            "id": scr.id,
            "patient_id": scr.patient_id,
            "patient_name": scr.patient_name,
            "village": scr.village,
            "screening_date": scr.screening_date,
            "timestamp_iso": scr.timestamp_iso,
            "predicted_class": scr.predicted_class,
            "class_name": scr.class_name,
            "confidence": scr.confidence,
            "dr_severity_od": scr.dr_severity_od,
            "dr_severity_os": scr.dr_severity_os,
            "overall_severity": scr.overall_severity,
            "safety_status": scr.safety_status,
            "screening_status": scr.screening_status,
            "risk_category": scr.risk_category,
            "referral_priority": scr.referral_priority,
            "gradcam_url": scr.gradcam_url,
            "heatmap_url": scr.heatmap_url,
            "image_od_path": scr.image_od_path,
            "image_os_path": scr.image_os_path,
        }, db=db)

        probs = json.loads(scr.probabilities_json) if scr.probabilities_json else None
        return ScreeningRecordResponse(
            id=scr.id,
            patient_id=scr.patient_id,
            patient_name=scr.patient_name,
            village=scr.village,
            screening_date=scr.screening_date,
            timestamp_iso=scr.timestamp_iso,
            predicted_class=scr.predicted_class,
            class_name=scr.class_name,
            confidence=scr.confidence,
            probabilities=probs,
            dr_severity_od=scr.dr_severity_od,
            dr_severity_os=scr.dr_severity_os,
            overall_severity=scr.overall_severity,
            safety_status=scr.safety_status,
            screening_status=scr.screening_status,
            risk_category=scr.risk_category,
            referral_priority=scr.referral_priority,
            gradcam_url=scr.gradcam_url,
            heatmap_url=scr.heatmap_url,
            image_od_path=scr.image_od_path,
            image_os_path=scr.image_os_path,
            doctor_status=scr.doctor_status,
            review_status=scr.review_status,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving screening to DB: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save screening data.")


@app.get(
    "/api/screenings",
    response_model=ScreeningListResponse,
    tags=["Screening"],
    summary="Get List of All Screenings",
)
async def list_screenings(patient_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns all screening records from database with optional patient filter."""
    query = db.query(ScreeningModel)
    if patient_id:
        query = query.filter(ScreeningModel.patient_id == patient_id)
    scrs = query.order_by(ScreeningModel.created_at.desc()).all()

    result = []
    for s in scrs:
        probs = json.loads(s.probabilities_json) if s.probabilities_json else None
        result.append(
            ScreeningRecordResponse(
                id=s.id,
                patient_id=s.patient_id,
                patient_name=s.patient_name,
                village=s.village,
                screening_date=s.screening_date,
                timestamp_iso=s.timestamp_iso,
                predicted_class=s.predicted_class,
                class_name=s.class_name,
                confidence=s.confidence,
                probabilities=probs,
                dr_severity_od=s.dr_severity_od,
                dr_severity_os=s.dr_severity_os,
                overall_severity=s.overall_severity,
                safety_status=s.safety_status,
                screening_status=s.screening_status,
                risk_category=s.risk_category,
                referral_priority=s.referral_priority,
                gradcam_url=s.gradcam_url,
                heatmap_url=s.heatmap_url,
                image_od_path=s.image_od_path,
                image_os_path=s.image_os_path,
                doctor_status=s.doctor_status,
                review_status=s.review_status,
            )
        )
    return ScreeningListResponse(total=len(result), screenings=result)


@app.get(
    "/api/screenings/{screening_id}",
    response_model=ScreeningRecordResponse,
    tags=["Screening"],
    summary="Get Specific Screening by ID",
)
async def get_screening_detail(screening_id: str, db: Session = Depends(get_db)):
    scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
    if not scr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Screening '{screening_id}' not found.")
    probs = json.loads(scr.probabilities_json) if scr.probabilities_json else None
    return ScreeningRecordResponse(
        id=scr.id,
        patient_id=scr.patient_id,
        patient_name=scr.patient_name,
        village=scr.village,
        screening_date=scr.screening_date,
        timestamp_iso=scr.timestamp_iso,
        predicted_class=scr.predicted_class,
        class_name=scr.class_name,
        confidence=scr.confidence,
        probabilities=probs,
        dr_severity_od=scr.dr_severity_od,
        dr_severity_os=scr.dr_severity_os,
        overall_severity=scr.overall_severity,
        safety_status=scr.safety_status,
        screening_status=scr.screening_status,
        risk_category=scr.risk_category,
        referral_priority=scr.referral_priority,
        gradcam_url=scr.gradcam_url,
        heatmap_url=scr.heatmap_url,
        image_od_path=scr.image_od_path,
        image_os_path=scr.image_os_path,
        doctor_status=scr.doctor_status,
        review_status=scr.review_status,
    )


# =====================================================================
# Phase 5: Contextual AI Assistant
# =====================================================================

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
    - Interprets active screening context
    - Guardrails against unauthorized prescribing
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


# =====================================================================
# Phase 6: Doctor Review & Human-in-the-Loop Oversight
# =====================================================================

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
    db: Session = Depends(get_db),
):
    """
    Phase 6 Human-in-the-Loop Doctor Review:
    - Allows verified doctor to ACCEPT, MODIFY, or REQUEST RE-CAPTURE
    - Preserves original AI prediction permanently in MySQL
    - Requires review comment on MODIFY action
    - Logs an immutable event to the audit trail
    """
    try:
        response = process_doctor_review(
            request=review_req,
            original_ai_result=original_ai_result,
            original_confidence=original_confidence,
            role=x_user_role,
            db=db,
        )
        return response
    except PermissionError as e:
        logger.warning(f"Unauthorized doctor review attempt: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.warning(f"Invalid doctor review submission: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Doctor review submission failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save the review. Please try again.")


@app.get(
    "/api/screenings/{screening_id}/history",
    response_model=ReviewHistoryResponse,
    tags=["Doctor Review"],
    summary="Get Screening Audit Trail History",
)
async def get_screening_history(screening_id: str, db: Session = Depends(get_db)):
    """Retrieves the complete chronological audit history for a screening record from DB."""
    events = get_audit_history(screening_id, db=db)
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
async def get_canonical_screening_review(screening_id: str, db: Session = Depends(get_db)):
    """Retrieves the canonical review state for a screening record from DB."""
    review_data = get_screening_review(screening_id, db=db)
    if not review_data:
        return None
    return DoctorReviewResponse(**review_data)


# =====================================================================
# Phase 9: Lesion Intelligence Layer Endpoints
# =====================================================================

@app.get(
    "/api/screenings/{screening_id}/lesions",
    response_model=LesionEvidenceResponse,
    tags=["Lesion Intelligence"],
    summary="Get Lesion Intelligence & Evidence for Screening",
)
async def get_lesion_evidence(screening_id: str, eye: str = "OD"):
    analysis = lesion_service.get_lesion_analysis(screening_id=screening_id, eye=eye)
    return LesionEvidenceResponse(**analysis)


@app.post(
    "/api/lesions/analyze",
    response_model=LesionEvidenceResponse,
    tags=["Lesion Intelligence"],
    summary="Analyze Retinal Image for Lesions",
)
async def analyze_lesions(screening_id: str = "SCR-DIRECT", eye: str = "OD"):
    analysis = lesion_service.get_lesion_analysis(screening_id=screening_id, eye=eye)
    return LesionEvidenceResponse(**analysis)


# =====================================================================
# Phase 10: Longitudinal Patient Tracking & Progression Intelligence
# =====================================================================

@app.get(
    "/api/patients/{patient_id}/screening-history",
    response_model=PatientScreeningHistoryResponse,
    tags=["Longitudinal Intelligence"],
    summary="Get Patient Chronological Screening History",
)
async def get_patient_screening_history(patient_id: str, db: Session = Depends(get_db)):
    """
    Phase 10 Longitudinal Tracking:
    - Retrieves complete chronological screening sessions for a specific patient (newest first).
    - Preserves data isolation across patients.
    """
    history = longitudinal_service.get_patient_screening_history(patient_id, db=db)
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
async def compare_specific_screenings(screening_id: str, previous_screening_id: str, db: Session = Depends(get_db)):
    """
    Phase 10 Longitudinal Comparison:
    - Compares current screening with a manually selected historical screening from database.
    - Evaluates safe screening classification change without claiming autonomous disease progression.
    - Strictly prevents cross-patient comparisons.
    """
    current_scr = longitudinal_service.get_screening(screening_id, db=db)
    if not current_scr:
        rev = get_screening_review(screening_id, db=db)
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
                "reviewer_name": rev.get("doctor_name"),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Current screening '{screening_id}' not found.",
            )

    previous_scr = longitudinal_service.get_screening(previous_screening_id, db=db)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Longitudinal comparison failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to compare screenings at this time.")


@app.get(
    "/api/screenings/{screening_id}/longitudinal",
    response_model=ScreeningComparisonResponse,
    tags=["Longitudinal Intelligence"],
    summary="Get Automated Longitudinal Comparison for Screening",
)
async def get_automated_longitudinal_comparison(screening_id: str, patient_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Phase 10 Automated Comparison:
    - Automatically finds the most recent comparable historical screening for the patient.
    - Returns structured classification change status.
    """
    current_scr = longitudinal_service.get_screening(screening_id, db=db)
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
        db=db,
    )

    try:
        comparison = longitudinal_service.compare_screenings(
            current_screening=current_scr,
            previous_screening=previous_scr,
        )
        return ScreeningComparisonResponse(**comparison)
    except Exception as e:
        logger.error(f"Automated comparison failed: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to compute longitudinal comparison.")


# ==============================================================================
# Phase 11: Doctor Appointment & Tele-Ophthalmology Endpoints
# ==============================================================================

@app.get(
    "/api/doctors",
    response_model=DoctorListResponse,
    tags=["Tele-Ophthalmology"],
    summary="Get List of Verified Demo Doctors",
)
async def get_doctor_directory(db: Session = Depends(get_db)):
    """Returns list of registered tele-ophthalmology specialists from database."""
    doctors = appointment_service.get_doctors(db=db)
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
async def get_doctor_availability(doctor_id: str, date: str, db: Session = Depends(get_db)):
    """
    Returns 30-min consultation slots for the given date.
    Validates working hours, past-dates, and prevents double-booking.
    """
    try:
        avail = appointment_service.get_doctor_availability(doctor_id, date, db=db)
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
async def book_appointment(req: AppointmentCreateRequest, db: Session = Depends(get_db)):
    """
    Creates an appointment with server-side validation against working hours,
    past dates, and existing bookings using MySQL transactions.
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
            db=db,
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
    db: Session = Depends(get_db),
):
    """Lists appointments with optional doctor, health worker, patient, or status filter from DB."""
    apts = appointment_service.list_appointments(
        doctor_id=doctor_id,
        health_worker_id=health_worker_id,
        patient_id=patient_id,
        status_filter=status_filter,
        db=db,
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
async def get_appointment_details(appointment_id: str, db: Session = Depends(get_db)):
    """Returns single appointment by ID from DB."""
    apt = appointment_service.get_appointment_by_id(appointment_id, db=db)
    if not apt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment '{appointment_id}' not found.")
    return AppointmentResponse(**apt)


@app.patch(
    "/api/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
    tags=["Tele-Ophthalmology"],
    summary="Update Appointment Status (Accept, Decline, Reschedule, Cancel, Complete)",
)
async def update_appointment_status_endpoint(appointment_id: str, req: AppointmentUpdateRequest, db: Session = Depends(get_db)):
    """Transitions appointment status with role-based validation in DB."""
    try:
        updated = appointment_service.update_appointment_status(
            appointment_id=appointment_id,
            new_status=req.status,
            caller_role=req.caller_role,
            reason_or_comment=req.reason_or_comment,
            proposed_date=req.proposed_date,
            proposed_time=req.proposed_time,
            db=db,
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
async def add_doctor_notes(appointment_id: str, req: AppointmentNoteRequest, db: Session = Depends(get_db)):
    """Records doctor clinical notes, recommendation, and follow-up plan in DB."""
    try:
        updated = appointment_service.add_consultation_notes(
            appointment_id=appointment_id,
            doctor_id=req.doctor_id,
            doctor_notes=req.doctor_notes,
            recommendations=req.doctor_recommendation,
            follow_up_date=req.follow_up_date,
            db=db,
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
async def get_appointment_messages_endpoint(appointment_id: str, db: Session = Depends(get_db)):
    """Retrieves appointment-scoped communication messages from DB."""
    try:
        msgs = appointment_service.get_messages(appointment_id, db=db)
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
async def send_appointment_message_endpoint(appointment_id: str, req: AppointmentMessageRequest, db: Session = Depends(get_db)):
    """Sends a message within the authorized appointment conversation in DB."""
    try:
        msg = appointment_service.add_message(
            appointment_id=appointment_id,
            sender_id=req.sender_id,
            sender_name=req.sender_name,
            sender_role=req.sender_role,
            message=req.message,
            db=db,
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
async def get_video_session(appointment_id: str, user_id: str = "DOC-SWAMINATHAN", role: str = "doctor", db: Session = Depends(get_db)):
    """
    Authorizes participant access to the appointment WebRTC consultation room.
    Validates room access rights and returns STUN configuration.
    """
    try:
        session_info = appointment_service.authorize_video_session(
            appointment_id=appointment_id,
            user_id=user_id,
            role=role,
            db=db,
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
        await appointment_service.broadcast_signal(
            appointment_id,
            websocket,
            {"type": "peer_joined", "appointment_id": appointment_id}
        )

        while True:
            data = await websocket.receive_json()
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
async def list_health_workers(db: Session = Depends(get_db)):
    """Returns directory of registered community health workers from DB."""
    return whatsapp_service.get_all_health_workers(db=db)


@app.get("/api/health-workers/{hw_id}/profile", response_model=HealthWorkerProfile, tags=["Phase 12: WhatsApp"])
async def get_health_worker_profile(hw_id: str, db: Session = Depends(get_db)):
    """Returns profile and WhatsApp opt-in consent for a specific health worker from DB."""
    hw = whatsapp_service.get_health_worker(hw_id, db=db)
    if not hw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Health worker '{hw_id}' not found.")
    return hw


@app.patch("/api/health-workers/{hw_id}/opt-in", response_model=HealthWorkerProfile, tags=["Phase 12: WhatsApp"])
async def update_health_worker_opt_in(hw_id: str, req: HealthWorkerOptInRequest, db: Session = Depends(get_db)):
    """Updates WhatsApp consent opt-in status and registered phone number in DB."""
    updated = whatsapp_service.update_health_worker_opt_in(hw_id, req.whatsapp_opt_in, req.phone, db=db)
    return updated


@app.post("/api/reports/{screening_id}/pdf", response_model=ReportPdfResponse, tags=["Phase 12: WhatsApp"])
async def generate_screening_pdf_report(screening_id: str, db: Session = Depends(get_db)):
    """
    Generates or retrieves the official clinical PDF report for a screening.
    Ensures doctor-review gate has been completed before generating final report.
    """
    can_proceed, reason, review = whatsapp_service.check_doctor_review_gate(screening_id, db=db)
    if not can_proceed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    pdf_path = pdf_service.generate_clinical_report(
        screening_data={"id": screening_id, "screeningDate": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
        doctor_review=review,
    )
    token = generate_secure_pdf_token(screening_id)
    file_size = pdf_path.stat().st_size if pdf_path.exists() else 0

    return ReportPdfResponse(
        screening_id=screening_id,
        pdf_filename=pdf_path.name,
        pdf_url=f"/api/reports/{screening_id}/document?token={token}",
        file_size_bytes=file_size,
        generated_at=datetime.now(timezone.utc).isoformat(),
        is_final_doctor_approved=True,
    )


@app.get("/api/reports/{screening_id}/document", tags=["Phase 12: WhatsApp"])
async def download_secure_screening_pdf(screening_id: str, token: str = Query(..., description="Secure access token"), db: Session = Depends(get_db)):
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
        can_proceed, reason, review = whatsapp_service.check_doctor_review_gate(screening_id, db=db)
        if not can_proceed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        pdf_path = pdf_service.generate_clinical_report(
            screening_data={"id": screening_id, "screeningDate": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
            doctor_review=review,
        )

    return FileResponse(
        path=str(pdf_path),
        filename=pdf_path.name,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_path.name}"},
    )


@app.post("/api/reports/{screening_id}/whatsapp/send", response_model=WhatsAppDeliveryRecord, tags=["Phase 12: WhatsApp"])
async def send_whatsapp_report_endpoint(screening_id: str, req: WhatsAppSendRequest, db: Session = Depends(get_db)):
    """
    Requests secure WhatsApp delivery of the doctor-reviewed clinical PDF report.
    Enforces Doctor Review Gate, recipient phone verification, and opt-in consent.
    """
    try:
        delivery_record = await whatsapp_service.send_whatsapp_report(
            screening_id=screening_id,
            recipient_phone=req.recipient_phone,
            health_worker_id=req.health_worker_id,
            language=req.language,
            opt_in_confirmed=req.opt_in_confirmed,
            db=db,
        )
        return delivery_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to send WhatsApp report for {screening_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/reports/{screening_id}/whatsapp/status", response_model=WhatsAppStatusResponse, tags=["Phase 12: WhatsApp"])
async def get_whatsapp_status_endpoint(screening_id: str, hw_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Returns WhatsApp delivery status, doctor gate evaluation, patient recipient resolution, and complete audit trail from DB."""
    can_send, gate_reason, review = whatsapp_service.check_doctor_review_gate(screening_id, db=db)
    delivery_rec = whatsapp_service.get_delivery_status(screening_id, db=db)
    patient = whatsapp_service.resolve_patient_for_screening(screening_id=screening_id, db=db)
    hw = whatsapp_service.resolve_health_worker_for_screening(screening_id=screening_id, hw_id=hw_id, db=db)

    rev_status = review.get("review_status", "PENDING DOCTOR REVIEW") if review else "PENDING DOCTOR REVIEW"

    # Enforce: The recipient is the Patient. If patient is missing or mobile is unverified/missing, block sending.
    patient_phone = patient.phone if patient else None
    norm_patient_phone = normalize_phone_number(patient_phone) if patient_phone else ""
    has_valid_patient_recipient = bool(norm_patient_phone and len(re.sub(r"[^\d]", "", norm_patient_phone)) >= 10)

    if not has_valid_patient_recipient:
        can_send = False
        block_reason = "Patient mobile number not available/verified."
        resolved_recipient_phone = None
    else:
        resolved_recipient_phone = norm_patient_phone
        block_reason = None if can_send else gate_reason

    patient_id = delivery_rec.patient_id if (delivery_rec and delivery_rec.patient_id) else (getattr(patient, "id", None))
    patient_name = delivery_rec.patient_name if (delivery_rec and delivery_rec.patient_name) else (getattr(patient, "name", None))
    recipient_name = delivery_rec.recipient_name if (delivery_rec and delivery_rec.recipient_name) else patient_name

    return WhatsAppStatusResponse(
        screening_id=screening_id,
        status=delivery_rec.status if delivery_rec else WhatsAppDeliveryStatus.NOT_REQUESTED,
        recipient_phone=delivery_rec.recipient_phone if delivery_rec else resolved_recipient_phone,
        patient_id=patient_id,
        patient_name=patient_name,
        recipient_name=recipient_name,
        health_worker_id=delivery_rec.health_worker_id if delivery_rec else (hw.id if hw else None),
        health_worker_name=delivery_rec.health_worker_name if delivery_rec else (hw.name if hw else None),
        doctor_review_status=rev_status,
        can_send=can_send,
        block_reason=block_reason,
        delivery_record=delivery_rec,
        audit_events=delivery_rec.audit_events if delivery_rec else [],
    )


@app.post("/api/reports/{screening_id}/whatsapp/retry", response_model=WhatsAppDeliveryRecord, tags=["Phase 12: WhatsApp"])
async def retry_whatsapp_report_endpoint(screening_id: str, req: WhatsAppRetryRequest, db: Session = Depends(get_db)):
    """Retries failed report delivery for a screening in DB."""
    try:
        delivery_record = await whatsapp_service.retry_whatsapp_report(
            screening_id=screening_id,
            health_worker_id=req.health_worker_id,
            force_regenerate_pdf=req.force_regenerate_pdf,
            db=db,
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
    if not hub_mode or not hub_verify_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook parameters.")

    challenge = whatsapp_service.verify_webhook_challenge(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return PlainTextResponse(content=challenge, status_code=status.HTTP_200_OK)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")


@app.post("/api/whatsapp/webhook", tags=["Phase 12: WhatsApp"])
async def whatsapp_webhook_event(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        updates = whatsapp_service.process_webhook_status_update(payload, db=db)
        return {"status": "success", "processed_updates": len(updates), "updates": updates}
    except Exception as e:
        logger.warning(f"Error processing WhatsApp webhook payload: {e}")
        return {"status": "error", "detail": str(e)}


# =====================================================================
# Phase 14: Clinical Report Email Delivery Endpoints
# =====================================================================

@app.post("/api/reports/{screening_id}/email/send", response_model=EmailDeliveryRecord, tags=["Phase 14: Email Delivery"])
async def send_email_report_endpoint(screening_id: str, req: EmailSendRequest, db: Session = Depends(get_db)):
    """
    Requests secure Email delivery of the doctor-reviewed clinical PDF report to the patient.
    Enforces Doctor Review Gate, recipient email validation, and opt-in consent.
    """
    try:
        delivery_record = await email_service.send_email_report(
            screening_id=screening_id,
            recipient_email=req.recipient_email,
            language=req.language,
            opt_in_confirmed=req.opt_in_confirmed,
            db=db,
        )
        return delivery_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to send email report for {screening_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/reports/{screening_id}/email/status", response_model=EmailStatusResponse, tags=["Phase 14: Email Delivery"])
async def get_email_status_endpoint(screening_id: str, db: Session = Depends(get_db)):
    """Returns Email delivery status, doctor gate evaluation, patient recipient resolution, and audit trail."""
    can_send, gate_reason, review = email_service.check_doctor_review_gate(screening_id, db=db)
    delivery_rec = email_service.get_delivery_status(screening_id, db=db)
    patient = email_service.resolve_patient_for_screening(screening_id=screening_id, db=db)

    rev_status = review.get("review_status", "PENDING DOCTOR REVIEW") if review else "PENDING DOCTOR REVIEW"

    # Enforce: The recipient is the Patient. If patient is missing or email is missing/invalid, block sending.
    patient_email = getattr(patient, "email", None) if patient else None
    norm_patient_email = email_service.normalize_email(patient_email)

    if not norm_patient_email:
        can_send = False
        block_reason = "Patient email address not available."
        resolved_recipient_email = None
    else:
        resolved_recipient_email = norm_patient_email
        block_reason = None if can_send else gate_reason

    patient_id = delivery_rec.patient_id if (delivery_rec and delivery_rec.patient_id) else (getattr(patient, "id", None))
    patient_name = delivery_rec.patient_name if (delivery_rec and delivery_rec.patient_name) else (getattr(patient, "name", None))
    recipient_name = delivery_rec.recipient_name if (delivery_rec and delivery_rec.recipient_name) else patient_name

    return EmailStatusResponse(
        screening_id=screening_id,
        status=delivery_rec.status if delivery_rec else EmailDeliveryStatus.NOT_REQUESTED,
        recipient_email=delivery_rec.recipient_email if delivery_rec else resolved_recipient_email,
        patient_id=patient_id,
        patient_name=patient_name,
        recipient_name=recipient_name,
        doctor_review_status=rev_status,
        can_send=can_send,
        block_reason=block_reason,
        delivery_record=delivery_rec,
        audit_events=delivery_rec.audit_events if delivery_rec else [],
    )


@app.post("/api/reports/{screening_id}/email/retry", response_model=EmailDeliveryRecord, tags=["Phase 14: Email Delivery"])
async def retry_email_report_endpoint(screening_id: str, req: EmailRetryRequest, db: Session = Depends(get_db)):
    """Retries failed email report delivery for a screening in DB."""
    try:
        delivery_record = await email_service.retry_email_report(
            screening_id=screening_id,
            force_regenerate_pdf=req.force_regenerate_pdf,
            db=db,
        )
        return delivery_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

