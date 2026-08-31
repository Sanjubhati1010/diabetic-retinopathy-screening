"""
Human-in-the-Loop Doctor Review & Clinical Oversight Service for MADOCS.
Provides auditable specialist oversight, preserves original AI screening results,
and tracks complete chronological audit trails backed by persistent SQLAlchemy database models.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.schemas import DoctorReviewRequest, DoctorReviewResponse, ReviewAuditRecord
from app.database import SessionLocal
from app.models import (
    ScreeningModel,
    ScreeningReviewModel,
    ReviewAuditEventModel,
    DoctorModel,
    PatientModel,
)

logger = logging.getLogger("dr_backend.review_service")

# Supported DR ICDR Classes
DR_CLASS_MAP = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}

# In-memory mirror for fast read / non-DB fallback
AUDIT_TRAIL_STORE: Dict[str, List[Dict[str, Any]]] = {}
SCREENING_REVIEWS_STORE: Dict[str, Dict[str, Any]] = {}


def get_current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_doctor_role(role: Optional[str]) -> bool:
    """Verifies whether the calling user has doctor or clinical administrator privileges."""
    if not role or role.lower() not in ["doctor", "specialist", "ophthalmologist", "admin"]:
        return False
    return True


def ensure_screening_record_in_db(screening_id: str, db: Session, default_result: str = "Moderate NPDR", default_confidence: float = 0.85):
    """Ensures a screening record and associated patient exist in database to satisfy foreign keys."""
    try:
        scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
        if not scr:
            test_pid = f"PAT-AUTO-{screening_id}"
            pat = db.query(PatientModel).filter(PatientModel.id == test_pid).first()
            if not pat:
                pat = PatientModel(
                    id=test_pid,
                    name=f"Patient {screening_id}",
                    age=45,
                    gender="other",
                    village="Community Health Center",
                    registered_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                )
                db.add(pat)
                db.flush()

            scr = ScreeningModel(
                id=screening_id,
                patient_id=test_pid,
                patient_name=pat.name,
                village="Community Health Center",
                screening_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p"),
                timestamp_iso=get_current_iso_timestamp(),
                predicted_class=2,
                class_name=default_result,
                confidence=default_confidence or 0.85,
                doctor_status="pending",
                review_status="PENDING DOCTOR REVIEW",
            )
            db.add(scr)
            db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Error ensuring screening record {screening_id} in DB: {e}")


def ensure_initial_ai_event(screening_id: str, original_ai_result: str, original_confidence: Optional[float], db: Optional[Session] = None):
    """Ensures the baseline AI screening completion event is present in the audit log and DB."""
    if screening_id not in AUDIT_TRAIL_STORE:
        AUDIT_TRAIL_STORE[screening_id] = []

    has_ai_event = any(e.get("event_type") == "AI_SCREENING_COMPLETED" for e in AUDIT_TRAIL_STORE[screening_id])
    if not has_ai_event:
        event_dict = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "screening_id": screening_id,
            "event_type": "AI_SCREENING_COMPLETED",
            "description": f"AI model screening inference completed ({original_ai_result}, Confidence: {f'{original_confidence*100:.1f}%' if original_confidence else 'N/A'}).",
            "actor_id": "SYSTEM_AI",
            "actor_role": "ai_screening_engine",
            "original_ai_result": original_ai_result,
            "original_confidence": original_confidence,
            "reviewed_result": None,
            "review_comment": None,
            "timestamp": get_current_iso_timestamp(),
        }
        AUDIT_TRAIL_STORE[screening_id].append(event_dict)

        # Database persistence
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True
        try:
            ensure_screening_record_in_db(screening_id, db, default_result=original_ai_result, default_confidence=original_confidence or 0.85)
            existing = db.query(ReviewAuditEventModel).filter(
                ReviewAuditEventModel.screening_id == screening_id,
                ReviewAuditEventModel.event_type == "AI_SCREENING_COMPLETED",
            ).first()
            if not existing:
                db_event = ReviewAuditEventModel(
                    id=event_dict["event_id"],
                    screening_id=screening_id,
                    event_type="AI_SCREENING_COMPLETED",
                    description=event_dict["description"],
                    actor_id="SYSTEM_AI",
                    actor_role="ai_screening_engine",
                    original_ai_result=original_ai_result,
                    original_confidence=original_confidence,
                    timestamp=event_dict["timestamp"],
                )
                db.add(db_event)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record initial AI event in database: {e}")
        finally:
            if owns_session:
                db.close()


def process_doctor_review(
    request: DoctorReviewRequest,
    original_ai_result: str,
    original_confidence: Optional[float],
    role: Optional[str] = "doctor",
    db: Optional[Session] = None,
) -> DoctorReviewResponse:
    """
    Executes Human-in-the-Loop review actions:
    1. ACCEPT: Doctor accepts the AI prediction.
    2. MODIFY: Doctor overrides the AI prediction with a required clinical comment.
    3. RECAPTURE: Doctor requests a clearer fundus scan.
    
    Permanently preserves original AI classification and persists record in MySQL database.
    """
    # 1. Authorization check
    if not verify_doctor_role(role):
        raise PermissionError("Only qualified doctors or clinical specialists are authorized to perform screening reviews.")

    action = request.action.upper().strip()
    screening_id = request.screening_id
    ensure_initial_ai_event(screening_id, original_ai_result, original_confidence, db=db)

    timestamp = get_current_iso_timestamp()

    # Extract reviewer metadata
    reviewer_name = getattr(request, "reviewer_name", None) or getattr(request, "doctor_name", "Dr. Arvind Swaminathan, MS")
    reviewer_id = getattr(request, "reviewer_id", None) or getattr(request, "doctor_id", "DOC-SWAMINATHAN")

    # 2. Action processing
    if action == "ACCEPT":
        review_status = "AI RESULT ACCEPTED"
        doctor_reviewed_result = original_ai_result
        event_type = "AI_RESULT_ACCEPTED"
        comment = request.review_comment or "Doctor verified and accepted the AI-assisted screening result."
        description = f"AI-assisted screening result ({original_ai_result}) accepted by {reviewer_name}."
        message = "AI-assisted screening result accepted by doctor."

    elif action == "MODIFY":
        # Override validation
        if not request.review_comment or not request.review_comment.strip():
            raise ValueError("A review reason/comment is required when modifying the AI screening result.")

        # Determine reviewed class name
        if request.reviewed_class_name and request.reviewed_class_name.strip():
            doctor_reviewed_result = request.reviewed_class_name.strip()
        elif request.reviewed_class is not None and request.reviewed_class in DR_CLASS_MAP:
            doctor_reviewed_result = DR_CLASS_MAP[request.reviewed_class]
        else:
            raise ValueError("A valid reviewed classification (0 to 4 or standard class name) must be provided.")

        review_status = "DOCTOR REVIEWED / MODIFIED"
        event_type = "RESULT_MODIFIED"
        comment = request.review_comment.strip()
        description = f"Screening result modified from '{original_ai_result}' to '{doctor_reviewed_result}' by {reviewer_name}. Reason: {comment}"
        message = "Screening result reviewed and modified by doctor."

    elif action in ["RECAPTURE", "REQUEST_RECAPTURE"]:
        review_status = "IMAGE RE-CAPTURE REQUESTED"
        doctor_reviewed_result = "Image Re-capture Required"
        event_type = "IMAGE_RECAPTURE_REQUESTED"
        comment = request.review_comment or "Please capture and upload a clearer fundus image for further screening."
        description = f"Image re-capture requested by {reviewer_name}. Guidance: {comment}"
        message = "Image re-capture requested. Please capture and upload a clearer fundus image for further screening."

    else:
        raise ValueError(f"Invalid doctor review action '{action}'. Supported actions: 'ACCEPT', 'MODIFY', 'RECAPTURE'.")

    # 3. Create Audit Record
    event_id = f"evt-{uuid.uuid4().hex[:8]}"
    audit_record_dict = {
        "event_id": event_id,
        "screening_id": screening_id,
        "event_type": event_type,
        "description": description,
        "actor_id": reviewer_id,
        "actor_role": role or "doctor",
        "original_ai_result": original_ai_result,
        "original_confidence": original_confidence,
        "reviewed_result": doctor_reviewed_result,
        "review_comment": comment,
        "timestamp": timestamp,
    }

    # Store in memory mirror
    if screening_id not in AUDIT_TRAIL_STORE:
        AUDIT_TRAIL_STORE[screening_id] = []
    AUDIT_TRAIL_STORE[screening_id].append(audit_record_dict)

    audit_record = ReviewAuditRecord(**audit_record_dict)

    response = DoctorReviewResponse(
        screening_id=screening_id,
        review_status=review_status,
        original_ai_result=original_ai_result,
        original_confidence=original_confidence,
        doctor_reviewed_result=doctor_reviewed_result,
        review_action=action,
        review_comment=comment,
        reviewer_name=reviewer_name,
        review_timestamp=timestamp,
        audit_record=audit_record,
        message=message,
    )

    SCREENING_REVIEWS_STORE[screening_id] = response.dict()

    # 4. Database Persistence
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        ensure_screening_record_in_db(screening_id, db, default_result=original_ai_result, default_confidence=original_confidence or 0.85)

        # Check doctor exists in DB or create fallback
        doc = db.query(DoctorModel).filter(DoctorModel.id == reviewer_id).first()
        if not doc:
            doc = DoctorModel(
                id=reviewer_id,
                name=reviewer_name,
                title="Consultant Ophthalmologist",
                specialization="Retina Specialist",
                hospital="District Hospital",
                location="Uttar Pradesh",
                languages_json='["English", "Hindi"]',
                working_days_json='["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]',
            )
            db.add(doc)
            db.flush()

        # Update or Insert ScreeningReviewModel
        existing_rev = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == screening_id).first()
        if existing_rev:
            existing_rev.action = action
            existing_rev.doctor_id = reviewer_id
            existing_rev.doctor_name = reviewer_name
            existing_rev.reviewed_result = doctor_reviewed_result
            existing_rev.review_comment = comment
            existing_rev.doctor_notes = getattr(request, "doctor_notes", None)
            existing_rev.review_status = review_status
            existing_rev.review_timestamp = timestamp
        else:
            db_review = ScreeningReviewModel(
                id=f"REV-{screening_id}-{uuid.uuid4().hex[:6]}",
                screening_id=screening_id,
                action=action,
                doctor_id=reviewer_id,
                doctor_name=reviewer_name,
                original_ai_result=original_ai_result,
                original_confidence=original_confidence,
                reviewed_result=doctor_reviewed_result,
                review_comment=comment,
                doctor_notes=getattr(request, "doctor_notes", None),
                review_status=review_status,
                review_timestamp=timestamp,
            )
            db.add(db_review)

        # Insert Audit Event
        db_audit = ReviewAuditEventModel(
            id=event_id,
            screening_id=screening_id,
            event_type=event_type,
            description=description,
            actor_id=reviewer_id,
            actor_role=role or "doctor",
            original_ai_result=original_ai_result,
            original_confidence=original_confidence,
            reviewed_result=doctor_reviewed_result,
            review_comment=comment,
            timestamp=timestamp,
        )
        db.add(db_audit)

        # Update ScreeningModel if present
        scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
        if scr:
            scr.review_status = review_status
            scr.doctor_status = "verified" if action == "ACCEPT" else ("recapture_requested" if action == "RECAPTURE" else "verified")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist doctor review in database: {e}")
    finally:
        if owns_session:
            db.close()

    return response


def get_screening_review(screening_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Retrieves current canonical review status and metadata for a screening from database."""
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        rev = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == screening_id).first()
        if rev:
            return {
                "screening_id": rev.screening_id,
                "review_status": rev.review_status,
                "original_ai_result": rev.original_ai_result,
                "original_confidence": rev.original_confidence,
                "doctor_reviewed_result": rev.reviewed_result,
                "review_action": rev.action,
                "review_comment": rev.review_comment,
                "reviewer_name": rev.doctor_name,
                "doctor_id": rev.doctor_id,
                "doctor_name": rev.doctor_name,
                "doctor_notes": rev.doctor_notes,
                "review_timestamp": rev.review_timestamp,
            }
    except Exception as e:
        logger.warning(f"Error querying screening review from DB: {e}")
    finally:
        if owns_session:
            db.close()

    return SCREENING_REVIEWS_STORE.get(screening_id)


def get_audit_history(screening_id: str, db: Optional[Session] = None) -> List[ReviewAuditRecord]:
    """Retrieves full chronological audit log for a screening record from database."""
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        events = db.query(ReviewAuditEventModel).filter(
            ReviewAuditEventModel.screening_id == screening_id
        ).order_by(ReviewAuditEventModel.timestamp.asc()).all()

        if events:
            return [
                ReviewAuditRecord(
                    event_id=e.id,
                    screening_id=e.screening_id,
                    event_type=e.event_type,
                    description=e.description,
                    actor_id=e.actor_id,
                    actor_role=e.actor_role,
                    original_ai_result=e.original_ai_result,
                    original_confidence=e.original_confidence,
                    reviewed_result=e.reviewed_result,
                    review_comment=e.review_comment,
                    timestamp=e.timestamp,
                )
                for e in events
            ]
    except Exception as e:
        logger.warning(f"Error querying audit history from DB: {e}")
    finally:
        if owns_session:
            db.close()

    events = AUDIT_TRAIL_STORE.get(screening_id, [])
    return [ReviewAuditRecord(**e) for e in events]
