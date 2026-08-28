from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, model_validator


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


class AssistantChatRequest(BaseModel):
    message: str = Field(..., example="Explain my screening result", description="User question or prompt")
    language: str = Field(default="en", example="en", description="Language code: 'en' or 'hi'")
    page: Optional[str] = Field(default=None, example="/screenings/result", description="Current frontend page context")
    screening_context: Optional[Dict[str, Any]] = Field(default=None, description="Sanitized active screening context")


class AssistantChatResponse(BaseModel):
    reply: str = Field(..., description="Assistant response text")
    language: str = Field(default="en", description="Language used in response")
    suggested_actions: list[str] = Field(default_factory=list, description="Follow-up quick action prompts")
    context_used: bool = Field(default=False, description="Whether screening context was utilized in generating the response")
    disclaimer: str = Field(
        default="The MADOCS Assistant is an AI-assisted screening support tool and does not provide clinical diagnoses or prescriptions.",
        description="Clinical safety disclaimer"
    )


# Phase 6: Human-in-the-Loop Doctor Review Schemas
class DoctorReviewRequest(BaseModel):
    screening_id: str = Field(..., example="SCR-2026-081", description="Unique screening record identifier")
    action: str = Field(..., example="ACCEPT", description="Doctor action: 'ACCEPT', 'MODIFY', 'RECAPTURE'")
    reviewed_class: Optional[int] = Field(default=None, ge=0, le=4, example=2, description="Reviewed DR ICDR class index (0-4)")
    reviewed_class_name: Optional[str] = Field(default=None, example="Moderate", description="Reviewed class name")
    review_comment: Optional[str] = Field(default=None, example="Clinical agreement with AI screening output.", description="Specialist review notes / reason")
    reviewer_id: str = Field(default="DOC-SWAMINATHAN", example="DOC-SWAMINATHAN", description="Unique reviewer ID")
    reviewer_name: str = Field(default="Dr. A. Swaminathan, MS", example="Dr. A. Swaminathan, MS", description="Doctor display name")


class ReviewAuditRecord(BaseModel):
    event_id: str = Field(..., description="Unique event ID")
    screening_id: str = Field(..., description="Screening identifier")
    event_type: str = Field(..., description="Event type: 'AI_SCREENING_COMPLETED', 'DOCTOR_REVIEW_STARTED', 'AI_RESULT_ACCEPTED', 'RESULT_MODIFIED', 'IMAGE_RECAPTURE_REQUESTED'")
    description: str = Field(..., description="Detailed event summary")
    actor_id: str = Field(..., description="Actor ID (System / Doctor / Health Worker)")
    actor_role: str = Field(..., description="Actor role")
    original_ai_result: Optional[str] = Field(default=None, description="Preserved original AI prediction")
    original_confidence: Optional[float] = Field(default=None, description="Preserved original AI confidence")
    reviewed_result: Optional[str] = Field(default=None, description="Doctor confirmed / modified diagnosis")
    review_comment: Optional[str] = Field(default=None, description="Review reason / notes")
    timestamp: str = Field(..., description="ISO timestamp")


class DoctorReviewResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    review_status: str = Field(..., example="AI RESULT ACCEPTED", description="Updated review status")
    original_ai_result: str = Field(..., description="Permanently preserved original AI prediction")
    original_confidence: Optional[float] = Field(default=None, description="Permanently preserved original confidence")
    doctor_reviewed_result: str = Field(..., description="Specialist final classification")
    review_action: str = Field(..., description="Review action executed")
    review_comment: Optional[str] = Field(default=None, description="Doctor review notes")
    reviewer_name: str = Field(..., description="Reviewing doctor name")
    review_timestamp: str = Field(..., description="Review completion timestamp")
    audit_record: Optional[ReviewAuditRecord] = Field(default=None, description="Generated audit trail record")
    message: str = Field(default="Screening review processed successfully.", description="Confirmation message")


class ReviewHistoryResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    events: List[ReviewAuditRecord] = Field(default_factory=list, description="Chronological audit history events")


# Phase 9: Lesion Intelligence & Dual-Evidence Schemas
class LesionEvidenceResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    eye: str = Field(default="OD", description="Eye analyzed (OD/OS)")
    available: bool = Field(default=False, description="Whether lesion-specific analysis is available")
    model_name: str = Field(..., description="Lesion model identifier or status")
    supported_categories: List[str] = Field(default_factory=list, description="Supported lesion categories")
    detected_lesions: List[Dict[str, Any]] = Field(default_factory=list, description="Detected lesion entities")
    lesion_masks: List[Dict[str, Any]] = Field(default_factory=list, description="Pixel/segmentation masks")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Lesion-specific confidences")
    status_message: str = Field(..., description="Clinical status message")
    status_message_hi: str = Field(..., description="Hindi clinical status message")
    explainability_note: str = Field(..., description="Grad-CAM explainability clarification note")


class DualEvidenceSummary(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    dr_classification: Dict[str, Any] = Field(..., description="DR classification evidence")
    lesion_evidence: LesionEvidenceResponse = Field(..., description="Lesion intelligence evidence")
    gradcam_attention: Dict[str, Any] = Field(..., description="Grad-CAM attention evidence")
    doctor_review: Optional[Dict[str, Any]] = Field(default=None, description="Doctor review status")


# Phase 10: Longitudinal Patient Tracking & Screening Progression Intelligence Schemas
class ScreeningHistoryRecord(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    screening_date: str = Field(..., description="Date of screening")
    predicted_class: Optional[int] = Field(default=None, ge=0, le=4, description="ICDR severity grade index")
    class_name: Optional[str] = Field(default=None, description="Human readable DR classification name")
    confidence: Optional[float] = Field(default=None, description="AI model confidence score")
    dr_severity_od: Optional[str] = Field(default=None, description="Right eye severity")
    dr_severity_os: Optional[str] = Field(default=None, description="Left eye severity")
    overall_severity: Optional[str] = Field(default=None, description="Overall bilateral severity")
    safety_status: str = Field(default="READY_FOR_AI", description="Safety gate status")
    screening_status: str = Field(default="RELIABLE AI SCREENING", description="Screening status")
    risk_category: str = Field(default="MODERATE", description="Risk category")
    referral_priority: str = Field(default="EYE SPECIALIST REVIEW RECOMMENDED", description="Referral priority")
    doctor_status: str = Field(default="pending", description="Doctor review status: 'pending' | 'verified' | 'recapture_requested'")
    review_status: Optional[str] = Field(default=None, description="Canonical doctor review status")
    doctor_reviewed_result: Optional[str] = Field(default=None, description="Doctor confirmed / modified diagnosis")
    reviewer_name: Optional[str] = Field(default=None, description="Doctor display name")
    is_recapture: bool = Field(default=False, description="Whether screening requires image re-capture")
    image_od: Optional[str] = Field(default=None, description="Right eye fundus image URL")
    image_os: Optional[str] = Field(default=None, description="Left eye fundus image URL")
    gradcam_od: Optional[str] = Field(default=None, description="Right eye Grad-CAM URL")
    gradcam_os: Optional[str] = Field(default=None, description="Left eye Grad-CAM URL")
    lesion_available: bool = Field(default=False, description="Whether lesion analysis is available")


class PatientScreeningHistoryResponse(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    patient_name: str = Field(..., description="Patient name")
    total_screenings: int = Field(..., description="Total historical screenings count")
    screenings: List[ScreeningHistoryRecord] = Field(default_factory=list, description="Chronological screenings, newest first")


class ScreeningComparisonResponse(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Patient name")
    village: str = Field(..., description="Patient village/community")
    current_screening: ScreeningHistoryRecord = Field(..., description="Active/current screening session")
    previous_screening: Optional[ScreeningHistoryRecord] = Field(default=None, description="Compared previous screening session")
    has_previous_screening: bool = Field(..., description="Whether previous screening exists")
    classification_change_status: str = Field(
        ...,
        description="Safe comparison status: 'IMPROVED', 'UNCHANGED', 'CLASSIFICATION INCREASED', 'CLASSIFICATION DECREASED', 'NOT COMPARABLE', 'HISTORY UNAVAILABLE'"
    )
    classification_change_summary: str = Field(..., description="Clinical summary of AI classification change")
    classification_change_summary_hi: str = Field(..., description="Hindi clinical summary of AI classification change")
    clinical_recommendation: str = Field(..., description="Clinical next step guidance")
    clinical_recommendation_hi: str = Field(..., description="Hindi clinical next step guidance")
    confidence_comparison: Dict[str, Any] = Field(..., description="Separate previous and current confidence scores")
    image_comparison: Dict[str, Any] = Field(..., description="Visual image URLs for clinical review")
    gradcam_comparison: Dict[str, Any] = Field(..., description="Grad-CAM attention maps with explainability limitation note")
    lesion_comparison: Dict[str, Any] = Field(..., description="Lesion evidence availability status")
    doctor_review_comparison: Dict[str, Any] = Field(..., description="Doctor review statuses across screenings")
    disclaimer: str = Field(..., description="Mandatory clinical disclaimer on longitudinal comparison")
    disclaimer_hi: str = Field(..., description="Hindi mandatory clinical disclaimer")


# ==============================================================================
# Phase 11: Doctor Appointment & Tele-Ophthalmology Schemas
# ==============================================================================

class DoctorRecord(BaseModel):
    id: str = Field(..., description="Unique doctor identifier")
    name: str = Field(..., description="Doctor full name")
    title: str = Field(..., description="Professional title")
    specialization: str = Field(..., description="Clinical specialization")
    hospital: str = Field(..., description="Affiliated tele-center / hospital")
    location: str = Field(..., description="District and state location")
    languages: List[str] = Field(default_factory=list, description="Consultation languages supported")
    experience_years: int = Field(..., description="Years of clinical experience")
    is_demo: bool = Field(default=True, description="Clearly marked demo doctor label")
    status: str = Field(default="Available", description="Current status: Available, Busy, Offline")
    avatar_badge: str = Field(..., description="2-letter avatar initials")
    working_days: List[str] = Field(default_factory=list, description="Days of week on duty")
    working_hours_start: str = Field(..., description="Shift start time (HH:MM)")
    working_hours_end: str = Field(..., description="Shift end time (HH:MM)")
    slot_duration_minutes: int = Field(default=30, description="Consultation slot duration")
    rating: float = Field(default=4.9, description="Tele-consultation quality rating")
    total_consultations: int = Field(default=0, description="Total completed consultations count")


class DoctorListResponse(BaseModel):
    doctors: List[DoctorRecord] = Field(default_factory=list, description="List of verified demo doctors")
    total_count: int = Field(..., description="Total doctors count")


class DoctorAvailabilitySlot(BaseModel):
    start_time: str = Field(..., description="Slot start time (HH:MM)")
    end_time: str = Field(..., description="Slot end time (HH:MM)")
    available: bool = Field(..., description="Whether slot is available for booking")
    reason: str = Field(..., description="Slot availability status reason")


class DoctorAvailabilityResponse(BaseModel):
    doctor_id: str = Field(..., description="Doctor identifier")
    doctor_name: str = Field(..., description="Doctor full name")
    date: str = Field(..., description="Selected query date (YYYY-MM-DD)")
    day_name: str = Field(..., description="Day of week")
    is_working_day: bool = Field(..., description="Whether doctor is scheduled on this day")
    slots: List[DoctorAvailabilitySlot] = Field(default_factory=list, description="Generated 30-min time slots")
    total_slots: int = Field(default=0, description="Total slots count")
    available_slots_count: int = Field(default=0, description="Available slots count")
    available_slots: Optional[int] = Field(default=0, description="Available slots count alias")
    message: Optional[str] = Field(default=None, description="Optional informational notice")
    reason: Optional[str] = Field(default=None, description="Optional informational notice alias")


class AppointmentCreateRequest(BaseModel):
    doctor_id: str = Field(..., description="Assigned doctor identifier")
    health_worker_id: str = Field(default="HW-RAMPUR-01", description="Health worker PHC ID")
    health_worker_name: str = Field(default="Pooja Sharma (ASHA Worker)", description="Health worker display name")
    health_worker_email: str = Field(default="asha.rampur@phc.in", description="Health worker contact email")
    patient_id: str = Field(..., description="Patient ID")
    patient_name: str = Field(..., description="Patient Name")
    patient_age: Optional[int] = Field(default=None, ge=1, le=120, description="Patient age")
    patient_gender: Optional[str] = Field(default=None, description="Patient gender")
    village: Optional[str] = Field(default=None, description="Patient village")
    screening_id: Optional[str] = Field(default=None, description="Linked screening ID (optional)")
    screening_summary: Optional[str] = Field(default=None, description="Linked screening AI summary")
    date: str = Field(..., description="Scheduled appointment date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Slot start time (HH:MM)")
    reason: str = Field(..., min_length=3, description="Clinical reason for tele-consultation request")


class AppointmentUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: CONFIRMED, DECLINED, RESCHEDULE_REQUESTED, CANCELLED, COMPLETED")
    caller_role: str = Field(default="doctor", description="Role of requesting caller: doctor, health_worker, admin")
    reason_or_comment: Optional[str] = Field(default=None, description="Clinical note or reason for change")
    proposed_date: Optional[str] = Field(default=None, description="New proposed date for reschedule")
    proposed_time: Optional[str] = Field(default=None, description="New proposed time for reschedule")


class AppointmentNoteRequest(BaseModel):
    doctor_id: str = Field(..., description="Reviewing doctor ID")
    doctor_notes: str = Field(..., min_length=5, description="Doctor-entered clinical consultation notes")
    doctor_recommendation: str = Field(..., min_length=3, description="Doctor clinical recommendation")
    follow_up_date: Optional[str] = Field(default=None, description="Optional suggested follow-up date")


class AppointmentResponse(BaseModel):
    id: str = Field(..., description="Appointment identifier")
    doctor_id: str = Field(..., description="Doctor identifier")
    doctor_name: str = Field(..., description="Doctor name")
    health_worker_id: str = Field(..., description="Health worker identifier")
    health_worker_name: str = Field(..., description="Health worker name")
    health_worker_email: str = Field(..., description="Health worker email")
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Patient name")
    patient_age: Optional[int] = Field(default=None, description="Patient age")
    patient_gender: Optional[str] = Field(default=None, description="Patient gender")
    village: Optional[str] = Field(default=None, description="Patient village")
    screening_id: Optional[str] = Field(default=None, description="Linked screening ID")
    screening_summary: Optional[str] = Field(default=None, description="Linked screening summary")
    date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    reason: str = Field(..., description="Reason for consultation")
    status: str = Field(..., description="Current status")
    created_at: str = Field(..., description="Creation ISO timestamp")
    updated_at: str = Field(..., description="Update ISO timestamp")
    doctor_notes: Optional[str] = Field(default=None, description="Doctor-entered consultation note")
    doctor_recommendation: Optional[str] = Field(default=None, description="Doctor clinical recommendation")
    follow_up_date: Optional[str] = Field(default=None, description="Suggested follow-up date")
    reschedule_proposed_date: Optional[str] = Field(default=None, description="Reschedule proposed date")
    reschedule_proposed_time: Optional[str] = Field(default=None, description="Reschedule proposed time")


class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse] = Field(default_factory=list, description="Appointments list")
    total_count: int = Field(..., description="Total appointments matching query")


class AppointmentMessageRequest(BaseModel):
    sender_id: str = Field(..., description="Message sender ID")
    sender_name: str = Field(..., description="Message sender display name")
    sender_role: str = Field(..., description="Message sender role: doctor, health_worker, system")
    message: str = Field(..., min_length=1, description="Message text content")


class AppointmentMessageResponse(BaseModel):
    id: str = Field(..., description="Unique message ID")
    appointment_id: str = Field(..., description="Associated appointment ID")
    sender_id: str = Field(..., description="Message sender ID")
    sender_name: str = Field(..., description="Message sender display name")
    sender_role: str = Field(..., description="Sender role")
    message: str = Field(..., description="Message text content")
    created_at: str = Field(..., description="Creation ISO timestamp")


class AppointmentMessageListResponse(BaseModel):
    appointment_id: str = Field(..., description="Associated appointment ID")
    messages: List[AppointmentMessageResponse] = Field(default_factory=list, description="Chat messages history")
    total_messages: int = Field(..., description="Total message count")


class VideoSessionResponse(BaseModel):
    appointment_id: str = Field(..., description="Appointment identifier")
    room_id: str = Field(..., description="WebRTC session room identifier")
    authorized: bool = Field(..., description="Whether participant is authorized")
    participant_id: str = Field(..., description="Participant user ID")
    participant_role: str = Field(..., description="Participant role")
    doctor_name: str = Field(..., description="Assigned doctor name")
    patient_name: str = Field(..., description="Patient name")
    screening_id: Optional[str] = Field(default=None, description="Linked screening ID")
    ice_servers: List[Dict[str, Any]] = Field(default_factory=list, description="STUN / TURN server configuration")


# Phase 12: WhatsApp Clinical Report Delivery Schemas
class WhatsAppDeliveryStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WhatsAppSendRequest(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    recipient_phone: str = Field(..., description="Authorized patient WhatsApp phone number with country code (e.g. +917378216613)")
    health_worker_id: Optional[str] = Field(default="HW-RAMPUR-01", description="Health worker identifier requesting delivery for attribution")
    language: str = Field(default="en", description="Language preference: 'en' or 'hi'")
    opt_in_confirmed: bool = Field(default=True, description="Explicit recipient WhatsApp opt-in verification")


class WhatsAppAuditEvent(BaseModel):
    event_type: str = Field(..., description="Audit event type")
    timestamp: str = Field(..., description="ISO 8601 event timestamp")
    screening_id: str = Field(..., description="Screening identifier")
    actor: str = Field(default="system", description="Actor performing or triggering the event")
    delivery_status: str = Field(default="PROCESSING", description="Status at time of event")
    provider_message_id: Optional[str] = Field(default=None, description="WhatsApp provider message ID if available")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional non-sensitive audit metadata")



class WhatsAppDeliveryRecord(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    recipient_phone: str = Field(..., description="Recipient phone number (Patient registered mobile)")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name (Patient)")
    health_worker_id: Optional[str] = Field(default=None, description="Attributed health worker ID")
    health_worker_name: Optional[str] = Field(default=None, description="Attributed health worker name")
    status: WhatsAppDeliveryStatus = Field(default=WhatsAppDeliveryStatus.NOT_REQUESTED, description="Current delivery status")
    provider_message_id: Optional[str] = Field(default=None, description="Provider message tracking ID")
    provider_status: Optional[str] = Field(default=None, description="Raw provider status string")
    sent_at: Optional[str] = Field(default=None, description="Timestamp message was accepted by provider")
    delivered_at: Optional[str] = Field(default=None, description="Timestamp confirmed delivered")
    read_at: Optional[str] = Field(default=None, description="Timestamp confirmed read")
    error_message: Optional[str] = Field(default=None, description="Error reason if delivery failed")
    retry_count: int = Field(default=0, description="Number of delivery retries performed")
    pdf_filename: Optional[str] = Field(default=None, description="Generated PDF filename")
    pdf_download_url: Optional[str] = Field(default=None, description="Secure tokenized document download URL")
    template_name: str = Field(default="clinical_report_delivery_v1", description="WhatsApp template name")
    language: str = Field(default="en", description="Template language: en / hi")
    is_demo: bool = Field(default=True, description="Whether delivery ran in demo/development mode")
    audit_events: List[WhatsAppAuditEvent] = Field(default_factory=list, description="Delivery lifecycle audit trail")


class WhatsAppStatusResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    status: WhatsAppDeliveryStatus = Field(..., description="Current delivery status")
    recipient_phone: Optional[str] = Field(default=None, description="Authorized recipient phone (Patient registered mobile)")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name (Patient)")
    health_worker_id: Optional[str] = Field(default=None, description="Attributed health worker ID")
    health_worker_name: Optional[str] = Field(default=None, description="Attributed health worker name")
    doctor_review_status: str = Field(..., description="Current doctor review status")
    can_send: bool = Field(..., description="Whether doctor-review gate and consent permit delivery")
    block_reason: Optional[str] = Field(default=None, description="Reason why sending is blocked if can_send is false")
    delivery_record: Optional[WhatsAppDeliveryRecord] = Field(default=None, description="Latest delivery record")
    audit_events: List[WhatsAppAuditEvent] = Field(default_factory=list, description="Audit trail history")


class WhatsAppRetryRequest(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    health_worker_id: str = Field(..., description="Health worker identifier")
    force_regenerate_pdf: bool = Field(default=False, description="Whether to regenerate PDF before retrying")


class HealthWorkerProfile(BaseModel):
    id: str = Field(..., description="Health worker ID")
    name: str = Field(..., description="Full name")
    role: str = Field(default="health_worker", description="User role")
    phone: str = Field(..., description="Registered mobile number (e.g. +91 98765 43210)")
    email: str = Field(..., description="Email / PHC user identifier")
    village: str = Field(..., description="Assigned village / sub-center")
    phc_center: str = Field(..., description="Primary Health Center name")
    whatsapp_opt_in: bool = Field(default=True, description="Explicit WhatsApp report delivery consent")
    whatsapp_opt_in_date: Optional[str] = Field(default=None, description="Timestamp when consent was recorded")


class HealthWorkerOptInRequest(BaseModel):
    whatsapp_opt_in: bool = Field(..., description="Opt-in consent flag")
    phone: Optional[str] = Field(default=None, description="Updated phone number if changing")


class ReportPdfResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    pdf_filename: str = Field(..., description="PDF filename")
    pdf_url: str = Field(..., description="Secure tokenized document download URL")
    file_size_bytes: int = Field(..., description="File size in bytes")
    generated_at: str = Field(..., description="ISO 8601 timestamp of generation")
    is_final_doctor_approved: bool = Field(..., description="Whether report has completed doctor review sign-off")


class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="Patient full name")
    age: int = Field(..., ge=1, le=120, description="Patient age")
    gender: str = Field(..., description="Gender (male, female, other)")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    mobile: Optional[str] = Field(default=None, description="Contact mobile number")
    mobile_number: Optional[str] = Field(default=None, description="Mobile number alias")
    phone_number: Optional[str] = Field(default=None, description="Phone number alias")
    email: Optional[str] = Field(default=None, description="Patient registered email address")
    email_address: Optional[str] = Field(default=None, description="Patient registered email address alias")
    village: Optional[str] = Field(default=None, description="Village or neighborhood")
    district: Optional[str] = Field(default=None, description="District / Location")
    abha_id: Optional[str] = Field(default=None, description="Ayushman Bharat Health Account ID")
    diabetes_duration: Optional[int] = Field(default=None, ge=0, description="Duration of diabetes in years")
    last_hba1c: Optional[float] = Field(default=None, ge=3.0, le=20.0, description="Most recent HbA1c level")
    insulin_use: bool = Field(default=False, description="Whether patient is taking insulin")
    visual_acuity_od: Optional[str] = Field(default="6/6", description="Visual acuity right eye")
    visual_acuity_os: Optional[str] = Field(default="6/6", description="Visual acuity left eye")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Reported visual symptoms")

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            phone_val = (
                data.get("phone")
                or data.get("mobile")
                or data.get("mobile_number")
                or data.get("mobileNumber")
                or data.get("phone_number")
                or data.get("phoneNumber")
            )
            if phone_val is not None:
                data["phone"] = phone_val
                data["mobile"] = phone_val
            email_val = (
                data.get("email")
                or data.get("email_address")
                or data.get("emailAddress")
            )
            if email_val is not None:
                data["email"] = email_val
                data["email_address"] = email_val
            if "abhaId" in data and "abha_id" not in data:
                data["abha_id"] = data["abhaId"]
            if "diabetesDuration" in data and "diabetes_duration" not in data:
                data["diabetes_duration"] = data["diabetesDuration"]
            if "lastHba1c" in data and "last_hba1c" not in data:
                data["last_hba1c"] = data["lastHba1c"]
            if "insulinUse" in data and "insulin_use" not in data:
                data["insulin_use"] = data["insulinUse"]
            if "visualAcuityOD" in data and "visual_acuity_od" not in data:
                data["visual_acuity_od"] = data["visualAcuityOD"]
            if "visualAcuityOS" in data and "visual_acuity_os" not in data:
                data["visual_acuity_os"] = data["visualAcuityOS"]
        return data


class PatientUpdateRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    mobile_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    email_address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    abha_id: Optional[str] = None
    diabetes_duration: Optional[int] = None
    last_hba1c: Optional[float] = None
    insulin_use: Optional[bool] = None
    visual_acuity_od: Optional[str] = None
    visual_acuity_os: Optional[str] = None
    symptoms: Optional[List[str]] = None
    last_screened: Optional[str] = None
    latest_status: Optional[str] = None
    referral_urgency: Optional[str] = None
    doctor_verified: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            phone_val = (
                data.get("phone")
                or data.get("mobile")
                or data.get("mobile_number")
                or data.get("mobileNumber")
                or data.get("phone_number")
                or data.get("phoneNumber")
            )
            if phone_val is not None:
                data["phone"] = phone_val
                data["mobile"] = phone_val
            email_val = (
                data.get("email")
                or data.get("email_address")
                or data.get("emailAddress")
            )
            if email_val is not None:
                data["email"] = email_val
                data["email_address"] = email_val
            if "abhaId" in data and "abha_id" not in data:
                data["abha_id"] = data["abhaId"]
            if "diabetesDuration" in data and "diabetes_duration" not in data:
                data["diabetes_duration"] = data["diabetesDuration"]
            if "lastHba1c" in data and "last_hba1c" not in data:
                data["last_hba1c"] = data["lastHba1c"]
            if "insulinUse" in data and "insulin_use" not in data:
                data["insulin_use"] = data["insulinUse"]
            if "visualAcuityOD" in data and "visual_acuity_od" not in data:
                data["visual_acuity_od"] = data["visualAcuityOD"]
            if "visualAcuityOS" in data and "visual_acuity_os" not in data:
                data["visual_acuity_os"] = data["visualAcuityOS"]
        return data


class PatientResponse(BaseModel):
    id: str
    abha_id: Optional[str] = None
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    email_address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    diabetes_duration: Optional[int] = None
    last_hba1c: Optional[float] = None
    insulin_use: bool = False
    visual_acuity_od: Optional[str] = "6/6"
    visual_acuity_os: Optional[str] = "6/6"
    symptoms: List[str] = Field(default_factory=list)
    registered_date: str
    last_screened: str = "-"
    latest_status: str = "drUncertain"
    referral_urgency: str = "routine"
    doctor_verified: bool = False

    @model_validator(mode="before")
    @classmethod
    def sync_contact_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            phone_val = data.get("phone") or data.get("mobile")
            if phone_val is not None:
                data["phone"] = phone_val
                data["mobile"] = phone_val
            email_val = data.get("email") or data.get("email_address")
            if email_val is not None:
                data["email"] = email_val
                data["email_address"] = email_val
        return data


class PatientListResponse(BaseModel):
    total: int
    patients: List[PatientResponse]


class ScreeningCreateRequest(BaseModel):
    id: Optional[str] = None
    patient_id: str
    patient_name: str
    village: Optional[str] = None
    screening_date: Optional[str] = None
    timestamp_iso: Optional[str] = None
    predicted_class: int = Field(default=0, ge=0, le=4)
    class_name: str = "No DR"
    confidence: float = 0.85
    probabilities: Optional[Dict[str, float]] = None
    dr_severity_od: Optional[str] = "drUncertain"
    dr_severity_os: Optional[str] = "drUncertain"
    overall_severity: Optional[str] = "drUncertain"
    safety_status: Optional[str] = "READY_FOR_AI"
    screening_status: Optional[str] = "RELIABLE AI SCREENING"
    risk_category: Optional[str] = "MODERATE"
    referral_priority: Optional[str] = "EYE SPECIALIST REVIEW RECOMMENDED"
    risk_explanation: Optional[str] = None
    referral_guidance: Optional[str] = None
    safety_message: Optional[str] = None
    gradcam_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    image_od_path: Optional[str] = None
    image_os_path: Optional[str] = None
    doctor_status: Optional[str] = "pending"
    review_status: Optional[str] = "PENDING DOCTOR REVIEW"

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "patientId" in data and "patient_id" not in data:
                data["patient_id"] = data["patientId"]
            if "patientName" in data and "patient_name" not in data:
                data["patient_name"] = data["patientName"]
            if "screeningDate" in data and "screening_date" not in data:
                data["screening_date"] = data["screeningDate"]
            if "timestampIso" in data and "timestamp_iso" not in data:
                data["timestamp_iso"] = data["timestampIso"]
            if "predictedClass" in data and "predicted_class" not in data:
                data["predicted_class"] = data["predictedClass"]
            if "className" in data and "class_name" not in data:
                data["class_name"] = data["className"]
            if "drSeverityOD" in data and "dr_severity_od" not in data:
                data["dr_severity_od"] = data["drSeverityOD"]
            if "drSeverityOS" in data and "dr_severity_os" not in data:
                data["dr_severity_os"] = data["drSeverityOS"]
            if "overallSeverity" in data and "overall_severity" not in data:
                data["overall_severity"] = data["overallSeverity"]
            if "safetyStatus" in data and "safety_status" not in data:
                data["safety_status"] = data["safetyStatus"]
            if "screeningStatus" in data and "screening_status" not in data:
                data["screening_status"] = data["screeningStatus"]
            if "riskCategory" in data and "risk_category" not in data:
                data["risk_category"] = data["riskCategory"]
            if "referralPriority" in data and "referral_priority" not in data:
                data["referral_priority"] = data["referralPriority"]
            if "gradCamUrl" in data and "gradcam_url" not in data:
                data["gradcam_url"] = data["gradCamUrl"]
            if "heatmapUrl" in data and "heatmap_url" not in data:
                data["heatmap_url"] = data["heatmapUrl"]
            if "imageOdPath" in data and "image_od_path" not in data:
                data["image_od_path"] = data["imageOdPath"]
            if "imageOsPath" in data and "image_os_path" not in data:
                data["image_os_path"] = data["imageOsPath"]
            if "doctorStatus" in data and "doctor_status" not in data:
                data["doctor_status"] = data["doctorStatus"]
            if "reviewStatus" in data and "review_status" not in data:
                data["review_status"] = data["reviewStatus"]
        return data


class ScreeningRecordResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    village: Optional[str] = None
    screening_date: str
    timestamp_iso: str
    predicted_class: int
    class_name: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None
    dr_severity_od: Optional[str] = "drUncertain"
    dr_severity_os: Optional[str] = "drUncertain"
    overall_severity: Optional[str] = "drUncertain"
    safety_status: str
    screening_status: str
    risk_category: str
    referral_priority: str
    gradcam_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    image_od_path: Optional[str] = None
    image_os_path: Optional[str] = None
    doctor_status: str = "pending"
    review_status: str = "PENDING DOCTOR REVIEW"


class ScreeningListResponse(BaseModel):
    total: int
    screenings: List[ScreeningRecordResponse]


# =====================================================================
# Phase 14: Clinical Report Email Delivery Schemas
# =====================================================================

class EmailDeliveryStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class EmailSendRequest(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    recipient_email: str = Field(..., description="Patient registered email address")
    language: str = Field(default="en", description="Language: 'en' or 'hi'")
    opt_in_confirmed: bool = Field(default=True, description="Explicit recipient consent confirmation")


class EmailAuditEvent(BaseModel):
    event_type: str = Field(..., description="Audit event type")
    timestamp: str = Field(..., description="ISO 8601 event timestamp")
    screening_id: str = Field(..., description="Screening identifier")
    actor: str = Field(default="system", description="Actor triggering the event")
    delivery_status: str = Field(default="PENDING", description="Status at time of event")
    provider_message_id: Optional[str] = Field(default=None, description="Email provider tracking ID")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional audit metadata")


class EmailDeliveryRecord(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    recipient_email: str = Field(..., description="Recipient email (Patient registered email)")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name (Patient)")
    status: EmailDeliveryStatus = Field(default=EmailDeliveryStatus.NOT_REQUESTED, description="Current email status")
    subject: Optional[str] = Field(default=None, description="Email subject line")
    provider_message_id: Optional[str] = Field(default=None, description="Email message tracking ID")
    sent_at: Optional[str] = Field(default=None, description="Timestamp message was sent")
    failure_reason: Optional[str] = Field(default=None, description="Failure reason if delivery failed")
    error_message: Optional[str] = Field(default=None, description="Technical error detail")
    pdf_filename: Optional[str] = Field(default=None, description="Attached PDF filename")
    pdf_download_url: Optional[str] = Field(default=None, description="Document download URL")
    is_demo: bool = Field(default=True, description="Whether delivery ran in demo/test mode")
    audit_events: List[EmailAuditEvent] = Field(default_factory=list, description="Email audit trail")


class EmailStatusResponse(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    status: EmailDeliveryStatus = Field(..., description="Current email status")
    recipient_email: Optional[str] = Field(default=None, description="Authorized recipient email (Patient registered email)")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name (Patient)")
    doctor_review_status: str = Field(..., description="Current doctor review status")
    can_send: bool = Field(..., description="Whether doctor-review gate and patient email permit sending")
    block_reason: Optional[str] = Field(default=None, description="Reason why email dispatch is blocked if can_send is false")
    delivery_record: Optional[EmailDeliveryRecord] = Field(default=None, description="Latest email delivery record")
    audit_events: List[EmailAuditEvent] = Field(default_factory=list, description="Email audit trail")


class EmailRetryRequest(BaseModel):
    screening_id: str = Field(..., description="Screening identifier")
    force_regenerate_pdf: bool = Field(default=False, description="Whether to regenerate PDF before retrying")







