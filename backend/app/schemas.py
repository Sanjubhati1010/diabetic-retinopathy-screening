from typing import Dict, Optional, List, Any
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
    audit_record: ReviewAuditRecord = Field(..., description="Generated audit trail record")
    message: str = Field(..., description="Confirmation message")


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
    message: Optional[str] = Field(default=None, description="Optional informational notice")


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
    patient_age: int = Field(..., description="Patient age")
    patient_gender: str = Field(..., description="Patient gender")
    village: str = Field(..., description="Patient village")
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



