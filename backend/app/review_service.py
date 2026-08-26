"""
Human-in-the-Loop Doctor Review & Clinical Oversight Service for MADOCS.
Provides auditable specialist oversight, preserves original AI screening results,
and tracks complete chronological audit trails.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.schemas import DoctorReviewRequest, DoctorReviewResponse, ReviewAuditRecord

logger = logging.getLogger("dr_backend.review_service")

# Supported DR ICDR Classes
DR_CLASS_MAP = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative DR"
}

# In-memory auditable event store for screenings (keyed by screening_id)
AUDIT_TRAIL_STORE: Dict[str, List[Dict[str, Any]]] = {}


def get_current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_doctor_role(role: Optional[str]) -> bool:
    """Verifies whether the calling user has doctor or clinical administrator privileges."""
    if not role or role.lower() not in ["doctor", "specialist", "ophthalmologist", "admin"]:
        return False
    return True


def ensure_initial_ai_event(screening_id: str, original_ai_result: str, original_confidence: Optional[float]):
    """Ensures the baseline AI screening completion event is present in the audit log."""
    if screening_id not in AUDIT_TRAIL_STORE:
        AUDIT_TRAIL_STORE[screening_id] = []

    # Check if baseline AI screening event exists
    has_ai_event = any(e.get("event_type") == "AI_SCREENING_COMPLETED" for e in AUDIT_TRAIL_STORE[screening_id])
    if not has_ai_event:
        AUDIT_TRAIL_STORE[screening_id].append({
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
        })


def process_doctor_review(
    request: DoctorReviewRequest,
    original_ai_result: str,
    original_confidence: Optional[float],
    role: Optional[str] = "doctor",
) -> DoctorReviewResponse:
    """
    Executes Human-in-the-Loop review actions:
    1. ACCEPT: Doctor accepts the AI prediction.
    2. MODIFY: Doctor overrides the AI prediction with a required clinical comment.
    3. RECAPTURE: Doctor requests a clearer fundus scan.
    
    Permanently preserves original AI classification and updates audit trail.
    """
    # 1. Authorization check
    if not verify_doctor_role(role):
        raise PermissionError("Only qualified doctors or clinical specialists are authorized to perform screening reviews.")

    action = request.action.upper().strip()
    screening_id = request.screening_id
    ensure_initial_ai_event(screening_id, original_ai_result, original_confidence)

    timestamp = get_current_iso_timestamp()

    # 2. Action processing
    if action == "ACCEPT":
        review_status = "AI RESULT ACCEPTED"
        doctor_reviewed_result = original_ai_result
        event_type = "AI_RESULT_ACCEPTED"
        comment = request.review_comment or "Doctor verified and accepted the AI-assisted screening result."
        description = f"AI-assisted screening result ({original_ai_result}) accepted by {request.reviewer_name}."
        message = "AI-assisted screening result accepted by doctor."

    elif action == "MODIFY":
        # Override validation
        if not request.review_comment or not request.review_comment.strip():
            raise ValueError("A review reason/comment is required when modifying the AI screening result.")

        # Determine reviewed class name
        if request.reviewed_class is not None and request.reviewed_class in DR_CLASS_MAP:
            doctor_reviewed_result = DR_CLASS_MAP[request.reviewed_class]
        elif request.reviewed_class_name and request.reviewed_class_name.strip():
            doctor_reviewed_result = request.reviewed_class_name.strip()
        else:
            raise ValueError("A valid reviewed classification (0 to 4 or standard class name) must be provided.")

        review_status = "DOCTOR REVIEWED / MODIFIED"
        event_type = "RESULT_MODIFIED"
        comment = request.review_comment.strip()
        description = f"Screening result modified from '{original_ai_result}' to '{doctor_reviewed_result}' by {request.reviewer_name}. Reason: {comment}"
        message = "Screening result reviewed and modified by doctor."

    elif action in ["RECAPTURE", "REQUEST_RECAPTURE"]:
        review_status = "IMAGE RE-CAPTURE REQUESTED"
        doctor_reviewed_result = "Image Re-capture Required"
        event_type = "IMAGE_RECAPTURE_REQUESTED"
        comment = request.review_comment or "Please capture and upload a clearer fundus image for further screening."
        description = f"Image re-capture requested by {request.reviewer_name}. Guidance: {comment}"
        message = "Image re-capture requested. Please capture and upload a clearer fundus image for further screening."

    else:
        raise ValueError(f"Invalid doctor review action '{action}'. Supported actions: 'ACCEPT', 'MODIFY', 'RECAPTURE'.")

    # 3. Create Audit Record
    audit_record_dict = {
        "event_id": f"evt-{uuid.uuid4().hex[:8]}",
        "screening_id": screening_id,
        "event_type": event_type,
        "description": description,
        "actor_id": request.reviewer_id,
        "actor_role": role or "doctor",
        "original_ai_result": original_ai_result,
        "original_confidence": original_confidence,
        "reviewed_result": doctor_reviewed_result,
        "review_comment": comment,
        "timestamp": timestamp,
    }

    # Store event in chronological audit trail
    AUDIT_TRAIL_STORE[screening_id].append(audit_record_dict)

    audit_record = ReviewAuditRecord(**audit_record_dict)

    return DoctorReviewResponse(
        screening_id=screening_id,
        review_status=review_status,
        original_ai_result=original_ai_result,
        original_confidence=original_confidence,
        doctor_reviewed_result=doctor_reviewed_result,
        review_action=action,
        review_comment=comment,
        reviewer_name=request.reviewer_name,
        review_timestamp=timestamp,
        audit_record=audit_record,
        message=message,
    )


def get_audit_history(screening_id: str) -> List[ReviewAuditRecord]:
    """Retrieves full chronological audit log for a screening record."""
    events = AUDIT_TRAIL_STORE.get(screening_id, [])
    return [ReviewAuditRecord(**e) for e in events]
