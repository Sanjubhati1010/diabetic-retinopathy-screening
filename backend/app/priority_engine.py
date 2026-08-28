"""
Rural Care Priority Engine for MADOCS.
Deterministic, explainable clinical decision-support and triage prioritization module.
Answers: "Among screened patients, which patients should receive specialist attention first, and why?"
Adheres to clinical safety rules:
- Failsafe image quality blocking
- AI uncertainty gate for low confidence (never silently downgraded)
- Doctor review preservation and authoritative clinical disclaimer
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ScreeningModel, PatientModel, ScreeningReviewModel
from app.longitudinal_service import longitudinal_service, DR_CLASS_NAMES

logger = logging.getLogger("dr_backend.priority_engine")

# Algorithm Metadata for Auditability
ALGORITHM_VERSION = "RCP-1.0"
DISCLAIMER_TEXT = "Priority is an AI-assisted triage recommendation and does not replace clinical judgment."
SCORE_LABEL = "Decision-support priority score"

# Priority Levels
PRIORITY_P1 = "P1"
PRIORITY_P2 = "P2"
PRIORITY_P3 = "P3"
PRIORITY_VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
PRIORITY_RECAPTURE_REQUIRED = "RECAPTURE_REQUIRED"

# Display Labels
LABEL_P1 = "P1 — URGENT"
LABEL_P2 = "P2 — PRIORITY"
LABEL_P3 = "P3 — ROUTINE"
LABEL_UNCERTAINTY = "AI UNCERTAINTY"
LABEL_RECAPTURE = "RE-CAPTURE REQUIRED"

# Color Codes
COLOR_P1 = "rose"       # Red / High attention
COLOR_P2 = "amber"      # Orange / Medium attention
COLOR_P3 = "emerald"    # Green / Routine
COLOR_UNCERTAINTY = "amber"
COLOR_RECAPTURE = "rose"

# Severity Score Weights (Deterministic)
DR_SEVERITY_WEIGHTS = {
    0: 0.0,  # No DR
    1: 1.0,  # Mild NPDR
    2: 3.0,  # Moderate NPDR
    3: 5.0,  # Severe NPDR
    4: 6.0,  # Proliferative DR
}

CONFIDENCE_RELIABLE_THRESHOLD = 0.60


def _parse_visual_acuity_reduced(va_str: Optional[str]) -> bool:
    """Evaluates whether visual acuity notation indicates reduced vision (< 6/12 or standard impaired notation)."""
    if not va_str or not isinstance(va_str, str):
        return False
    clean = va_str.strip().lower()
    if clean in ["6/6", "6/9", "normal", "20/20", "20/25", "20/30"]:
        return False
    # Check for reduced notations like 6/12, 6/18, 6/24, 6/36, 6/60, 20/40, 20/50, 20/70, 20/100, 20/200, reduced, impaired, poor, blur, loss
    reduced_markers = ["6/12", "6/18", "6/24", "6/36", "6/60", "20/40", "20/50", "20/70", "20/100", "20/200", "reduced", "impaired", "poor", "blur", "loss"]
    for marker in reduced_markers:
        if marker in clean:
            return True
    # If standard fraction 6/X with X >= 12
    if clean.startswith("6/"):
        try:
            denom = int(clean.split("/")[1].split()[0])
            if denom >= 12:
                return True
        except Exception:
            pass
    return False


def calculate_screening_priority(
    screening: Dict[str, Any],
    patient: Optional[Dict[str, Any]] = None,
    previous_screening: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Calculates deterministic priority score and explainable triage recommendation for a screened patient.
    
    Factors considered:
    A. DR severity (0 to 6 base points)
    B. AI confidence (reliable vs uncertainty gate)
    C. Image quality / safety gate status (safety block check)
    D. Visual acuity (reduced vision modifier)
    E. Diabetes duration (glycemic chronicity modifier)
    F. HbA1c when available (glycemic control modifier)
    G. Previous screening result & longitudinal change
    H. Doctor review status (preserves doctor verification)
    """
    sid = screening.get("id") or screening.get("screening_id") or "SCR-UNKNOWN"
    pid = screening.get("patient_id") or screening.get("patientId") or (patient.get("id") if patient else "PAT-UNKNOWN")
    pname = screening.get("patient_name") or screening.get("patientName") or (patient.get("name") if patient else "Patient")
    village = screening.get("village") or (patient.get("village") if patient else "Rampur")

    # Fetch patient record if not provided
    if (not patient or not isinstance(patient, dict) or not patient.get("id")) and pid and db:
        pat_model = db.query(PatientModel).filter(PatientModel.id == pid).first()
        if pat_model:
            symptoms = json.loads(pat_model.symptoms_json) if pat_model.symptoms_json else []
            patient = {
                "id": pat_model.id,
                "name": pat_model.name,
                "age": pat_model.age,
                "gender": pat_model.gender,
                "village": pat_model.village,
                "diabetes_duration": pat_model.diabetes_duration,
                "last_hba1c": pat_model.last_hba1c,
                "insulin_use": pat_model.insulin_use,
                "visual_acuity_od": pat_model.visual_acuity_od,
                "visual_acuity_os": pat_model.visual_acuity_os,
                "symptoms": symptoms,
            }

    if patient is None:
        patient = {}

    # Extract screening fields
    predicted_class = screening.get("predicted_class")
    class_name = screening.get("class_name") or screening.get("className") or (
        DR_CLASS_NAMES.get(predicted_class, "Unknown") if predicted_class is not None else "Unknown"
    )
    confidence = screening.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
            if confidence > 1.0:
                confidence = confidence / 100.0
        except Exception:
            confidence = None

    safety_status = screening.get("safety_status") or screening.get("safetyStatus") or "READY_FOR_AI"
    doctor_status = screening.get("doctor_status") or screening.get("doctorStatus") or "pending"
    review_status = screening.get("review_status") or screening.get("reviewStatus") or "PENDING DOCTOR REVIEW"
    doctor_reviewed_result = screening.get("doctor_reviewed_result") or screening.get("doctorReviewedResult")
    is_doctor_verified = doctor_status == "verified" or review_status in ["AI RESULT ACCEPTED", "DOCTOR REVIEWED / MODIFIED"]

    is_recapture_requested = (
        doctor_status == "recapture_requested"
        or review_status == "IMAGE RE-CAPTURE REQUESTED"
        or screening.get("is_recapture") is True
    )

    reasons: List[str] = []
    detailed_reasons: List[str] = []
    missing_factors: List[str] = []
    score_components: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # 1. SAFETY GATE CHECK (Failed Quality / Safety Block)
    # ------------------------------------------------------------------
    is_safety_blocked = (
        safety_status != "READY_FOR_AI"
        or predicted_class is None
        or is_recapture_requested
    )

    if is_safety_blocked:
        primary_reason = (
            "Image quality failed safety gate or image re-capture requested — AI-based prioritization is blocked."
            if not is_recapture_requested
            else "Doctor requested image re-capture — AI prioritization blocked until fresh image is captured."
        )
        return {
            "screening_id": sid,
            "patient_id": pid,
            "patient_name": pname,
            "village": village,
            "dr_result": class_name if not is_recapture_requested else "Re-capture Requested",
            "predicted_class": predicted_class,
            "confidence": confidence,
            "confidence_percentage": f"{confidence * 100:.1f}%" if confidence is not None else "N/A",
            "confidence_status": "UNAVAILABLE",
            "priority_level": PRIORITY_RECAPTURE_REQUIRED,
            "priority_label": LABEL_RECAPTURE,
            "priority_score": 0.0,
            "score_label": SCORE_LABEL,
            "color": COLOR_RECAPTURE,
            "safety_status": safety_status,
            "is_safety_blocked": True,
            "is_low_confidence": False,
            "primary_reason": primary_reason,
            "detailed_reasons": [
                f"Safety Status: {safety_status}",
                "Image clarity or retinal features are insufficient for reliable automated prioritization.",
                "AI-assisted prioritization is disabled to ensure patient safety.",
            ],
            "missing_factors": missing_factors,
            "evidence_checklist": {
                "current_dr": class_name,
                "ai_confidence": f"{confidence * 100:.1f}%" if confidence is not None else "N/A",
                "previous_dr": "N/A",
                "longitudinal_change": "BLOCKED",
                "longitudinal_detail": "Safety gate blocked",
                "image_quality": "Failed / Insufficient Quality",
                "visual_acuity": "N/A",
                "diabetes_duration": "N/A",
                "last_hba1c": "N/A",
            },
            "longitudinal_change_status": "NOT COMPARABLE",
            "longitudinal_summary": "Prioritization blocked by safety gate.",
            "previous_screening_id": None,
            "previous_screening_date": None,
            "previous_dr_result": None,
            "doctor_status": doctor_status,
            "doctor_reviewed_result": doctor_reviewed_result,
            "is_doctor_verified": is_doctor_verified,
            "recommended_action": "Doctor verification / image re-capture required.",
            "algorithm_version": ALGORITHM_VERSION,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": DISCLAIMER_TEXT,
        }

    # ------------------------------------------------------------------
    # 2. AI UNCERTAINTY GATE (Low Confidence)
    # ------------------------------------------------------------------
    is_low_confidence = confidence is not None and confidence < CONFIDENCE_RELIABLE_THRESHOLD

    if is_low_confidence:
        conf_pct = f"{confidence * 100:.1f}%" if confidence is not None else "Unknown"
        primary_reason = f"AI confidence ({conf_pct}) is insufficient for reliable automated prioritization. Doctor verification is required."
        return {
            "screening_id": sid,
            "patient_id": pid,
            "patient_name": pname,
            "village": village,
            "dr_result": class_name,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "confidence_percentage": conf_pct,
            "confidence_status": "LOW",
            "priority_level": PRIORITY_VERIFICATION_REQUIRED,
            "priority_label": LABEL_UNCERTAINTY,
            "priority_score": 1.0,
            "score_label": SCORE_LABEL,
            "color": COLOR_UNCERTAINTY,
            "safety_status": safety_status,
            "is_safety_blocked": False,
            "is_low_confidence": True,
            "primary_reason": primary_reason,
            "detailed_reasons": [
                f"⚠️ AI UNCERTAINTY: AI confidence ({conf_pct}) is below the reliable clinical threshold of 60.0%.",
                "Low confidence does NOT imply low clinical risk.",
                "Automated prioritization cannot be safely determined without human verification.",
            ],
            "missing_factors": missing_factors,
            "evidence_checklist": {
                "current_dr": class_name,
                "ai_confidence": f"{conf_pct} (Below 60% Threshold)",
                "previous_dr": "Pending verification",
                "longitudinal_change": "UNVERIFIED",
                "longitudinal_detail": "Low confidence screening result",
                "image_quality": "Good",
                "visual_acuity": patient.get("visual_acuity_od") or "Not recorded",
                "diabetes_duration": f"{patient.get('diabetes_duration')} yrs" if patient.get("diabetes_duration") is not None else "Not available",
                "last_hba1c": f"{patient.get('last_hba1c')}%" if patient.get("last_hba1c") is not None else "Not available",
            },
            "longitudinal_change_status": "UNVERIFIED",
            "longitudinal_summary": "AI uncertainty: Confidence below reliable threshold.",
            "previous_screening_id": None,
            "previous_screening_date": None,
            "previous_dr_result": None,
            "doctor_status": doctor_status,
            "doctor_reviewed_result": doctor_reviewed_result,
            "is_doctor_verified": is_doctor_verified,
            "recommended_action": "Doctor verification / image re-capture required.",
            "algorithm_version": ALGORITHM_VERSION,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": DISCLAIMER_TEXT,
        }

    # ------------------------------------------------------------------
    # 3. NORMAL SCORING PIPELINE (Cleared for AI Triage)
    # ------------------------------------------------------------------
    total_score = 0.0

    # A. DR Severity Base Score
    base_dr_score = DR_SEVERITY_WEIGHTS.get(predicted_class, 0.0)
    total_score += base_dr_score
    score_components["dr_severity"] = base_dr_score
    detailed_reasons.append(f"Current DR severity: {class_name} (base score: {base_dr_score:.1f})")

    # B. AI Confidence Context
    if confidence is not None:
        if confidence >= 0.85:
            conf_status = "HIGH"
            detailed_reasons.append(f"High AI confidence ({confidence * 100:.1f}%) supports triage evidence.")
        else:
            conf_status = "MODERATE"
            detailed_reasons.append(f"AI confidence ({confidence * 100:.1f}%) in standard acceptable range.")
    else:
        conf_status = "UNAVAILABLE"
        missing_factors.append("AI confidence score not available")

    # C. Longitudinal Comparison
    if previous_screening is None and pid:
        # Attempt to discover previous comparable screening
        previous_screening = longitudinal_service.get_latest_comparable_screening(
            current_screening_id=sid,
            patient_id=pid,
            db=db,
        )

    longitudinal_status = "BASELINE"
    longitudinal_summary = "Baseline screening — no previous comparison available."
    prev_sid = None
    prev_date = None
    prev_name = None
    longitudinal_score = 0.0

    if previous_screening:
        prev_sid = previous_screening.get("id") or previous_screening.get("screening_id")
        prev_date = previous_screening.get("screening_date") or previous_screening.get("date")
        prev_class = previous_screening.get("predicted_class")
        prev_name = previous_screening.get("class_name") or previous_screening.get("className") or (
            DR_CLASS_NAMES.get(prev_class, "Unknown") if prev_class is not None else "Unknown"
        )

        if prev_class is not None and predicted_class is not None:
            if predicted_class == prev_class:
                longitudinal_status = "UNCHANGED"
                longitudinal_summary = f"Screening classification unchanged ({class_name})."
                detailed_reasons.append(f"Longitudinal history: Classification stable at {class_name} since previous visit.")
            elif predicted_class > prev_class:
                longitudinal_status = "WORSENED"
                delta = predicted_class - prev_class
                if prev_class == 1 and predicted_class == 2:
                    # Mild -> Moderate
                    longitudinal_score = 2.0
                    longitudinal_summary = "Screening classification increased from Mild to Moderate."
                    detailed_reasons.append("⚠ Longitudinal alert: Classification worsened from Mild to Moderate (+2.0 points).")
                elif prev_class == 2 and predicted_class in [3, 4]:
                    # Moderate -> Severe / Proliferative
                    longitudinal_score = 3.0
                    longitudinal_summary = f"Screening classification worsened significantly from Moderate to {class_name}."
                    detailed_reasons.append(f"⚠ Longitudinal alert: Significant classification worsening from Moderate to {class_name} (+3.0 points).")
                else:
                    longitudinal_score = 1.5 * delta
                    longitudinal_summary = f"Screening classification increased from {prev_name} to {class_name}."
                    detailed_reasons.append(f"⚠ Longitudinal alert: Classification increased from {prev_name} to {class_name} (+{longitudinal_score:.1f} points).")
            else:
                longitudinal_status = "IMPROVED"
                longitudinal_summary = f"Screening classification improved from {prev_name} to {class_name}."
                detailed_reasons.append(f"Longitudinal history: Classification improved from {prev_name} to {class_name}.")
    else:
        detailed_reasons.append("Baseline screening: No previous historical screening available.")
        missing_factors.append("Previous screening history")

    total_score += longitudinal_score
    score_components["longitudinal_change"] = longitudinal_score

    # D. Clinical Context: Visual Acuity
    va_od = patient.get("visual_acuity_od") or screening.get("visual_acuity_od")
    va_os = patient.get("visual_acuity_os") or screening.get("visual_acuity_os")
    va_reduced = _parse_visual_acuity_reduced(va_od) or _parse_visual_acuity_reduced(va_os)
    va_score = 0.0

    if va_od or va_os:
        va_str = f"OD: {va_od or 'N/A'}, OS: {va_os or 'N/A'}"
        if va_reduced:
            va_score = 1.5
            detailed_reasons.append(f"Reduced visual acuity recorded ({va_str}) (+1.5 points).")
        else:
            detailed_reasons.append(f"Visual acuity within normal/mild range ({va_str}).")
    else:
        missing_factors.append("Visual acuity not recorded")
        va_str = "Not recorded"

    total_score += va_score
    score_components["visual_acuity"] = va_score

    # E. Clinical Context: Diabetes Duration
    diabetes_dur = patient.get("diabetes_duration")
    dur_score = 0.0
    if diabetes_dur is not None:
        try:
            dur_val = float(diabetes_dur)
            if dur_val >= 10.0:
                dur_score = 1.0
                detailed_reasons.append(f"Long-standing diabetes duration ({dur_val:.0f} years) increases chronic risk (+1.0 point).")
            elif dur_val >= 5.0:
                dur_score = 0.5
                detailed_reasons.append(f"Diabetes duration ({dur_val:.0f} years) (+0.5 points).")
            else:
                detailed_reasons.append(f"Diabetes duration ({dur_val:.0f} years) within early phase.")
        except Exception:
            missing_factors.append("Diabetes duration invalid")
    else:
        missing_factors.append("Diabetes duration not available")

    total_score += dur_score
    score_components["diabetes_duration"] = dur_score

    # F. Clinical Context: HbA1c
    hba1c = patient.get("last_hba1c")
    hba1c_score = 0.0
    if hba1c is not None:
        try:
            hba1c_val = float(hba1c)
            if hba1c_val >= 9.0:
                hba1c_score = 1.5
                detailed_reasons.append(f"Elevated HbA1c ({hba1c_val:.1f}%) indicates high glycemic risk (+1.5 points).")
            elif hba1c_val >= 8.0:
                hba1c_score = 1.0
                detailed_reasons.append(f"Suboptimal HbA1c ({hba1c_val:.1f}%) (+1.0 point).")
            else:
                detailed_reasons.append(f"HbA1c ({hba1c_val:.1f}%) in target/acceptable range.")
        except Exception:
            missing_factors.append("HbA1c invalid")
    else:
        missing_factors.append("HbA1c not available")

    total_score += hba1c_score
    score_components["hba1c"] = hba1c_score

    # G. Clinical Context: Insulin Therapy
    insulin_use = patient.get("insulin_use")
    if insulin_use is True:
        total_score += 0.5
        score_components["insulin_use"] = 0.5
        detailed_reasons.append("Patient on insulin therapy (+0.5 points).")

    # Round total priority score to 1 decimal place
    total_score = round(total_score, 1)

    # ------------------------------------------------------------------
    # 4. DETERMINE PRIORITY LEVEL
    # ------------------------------------------------------------------
    # P1 — URGENT: Severe/Proliferative DR (class 3, 4) OR Total Score >= 6.0 OR Moderate DR with worsening
    # P2 — PRIORITY: Moderate DR (class 2) OR Mild DR with worsening/elevated risk OR 2.5 <= Score < 6.0
    # P3 — ROUTINE: No DR (class 0) OR stable Mild DR with low risk (Score < 2.5)

    if predicted_class in [3, 4] or total_score >= 6.0 or (predicted_class == 2 and longitudinal_status == "WORSENED"):
        priority_level = PRIORITY_P1
        priority_label = LABEL_P1
        color = COLOR_P1
        recommended_action = "Specialist review according to clinical protocol — urgent appointment recommended."
        if longitudinal_status == "WORSENED":
            primary_reason = f"Classification worsened since previous visit ({prev_name} → {class_name})"
        elif predicted_class in [3, 4]:
            primary_reason = f"{class_name} DR detected by AI screening — requires urgent specialist examination."
        else:
            primary_reason = f"Elevated clinical priority score ({total_score:.1f}) across retinal and contextual factors."
    elif predicted_class == 2 or total_score >= 2.5 or (predicted_class == 1 and longitudinal_status == "WORSENED"):
        priority_level = PRIORITY_P2
        priority_label = LABEL_P2
        color = COLOR_P2
        recommended_action = "Specialist review according to clinical protocol."
        if va_reduced:
            primary_reason = f"{class_name} DR + reduced visual acuity"
        elif longitudinal_status == "WORSENED":
            primary_reason = f"Classification worsened since previous visit ({prev_name} → {class_name})"
        else:
            primary_reason = f"{class_name} DR with moderate priority profile"
    else:
        priority_level = PRIORITY_P3
        priority_label = LABEL_P3
        color = COLOR_P3
        recommended_action = "Routine annual follow-up according to local clinical protocol."
        if predicted_class == 0:
            primary_reason = "No significant risk indicators — routine screening schedule."
        else:
            primary_reason = "Stable mild DR with low contextual risk."

    # Doctor Verification Note
    if is_doctor_verified:
        detailed_reasons.append(f"Doctor review completed: {doctor_reviewed_result or review_status}.")

    # Build evidence checklist
    evidence_checklist = {
        "current_dr": class_name,
        "ai_confidence": f"{confidence * 100:.1f}%" if confidence is not None else "Not available",
        "previous_dr": prev_name or "None (Baseline)",
        "longitudinal_change": longitudinal_status,
        "longitudinal_detail": longitudinal_summary,
        "image_quality": "Good",
        "visual_acuity": va_str if (va_od or va_os) else "Not recorded",
        "diabetes_duration": f"{diabetes_dur} years" if diabetes_dur is not None else "Not available",
        "last_hba1c": f"{hba1c}%" if hba1c is not None else "Not available",
    }

    return {
        "screening_id": sid,
        "patient_id": pid,
        "patient_name": pname,
        "village": village,
        "dr_result": class_name,
        "predicted_class": predicted_class,
        "confidence": confidence,
        "confidence_percentage": f"{confidence * 100:.1f}%" if confidence is not None else "N/A",
        "confidence_status": conf_status,
        "priority_level": priority_level,
        "priority_label": priority_label,
        "priority_score": total_score,
        "score_label": SCORE_LABEL,
        "color": color,
        "safety_status": safety_status,
        "is_safety_blocked": False,
        "is_low_confidence": False,
        "primary_reason": primary_reason,
        "detailed_reasons": detailed_reasons,
        "missing_factors": missing_factors,
        "evidence_checklist": evidence_checklist,
        "longitudinal_change_status": longitudinal_status,
        "longitudinal_summary": longitudinal_summary,
        "previous_screening_id": prev_sid,
        "previous_screening_date": prev_date,
        "previous_dr_result": prev_name,
        "doctor_status": doctor_status,
        "doctor_reviewed_result": doctor_reviewed_result,
        "is_doctor_verified": is_doctor_verified,
        "recommended_action": recommended_action,
        "algorithm_version": ALGORITHM_VERSION,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER_TEXT,
    }


def get_priority_queue(
    db: Optional[Session] = None,
    filter_level: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "priority",
    sort_order: str = "desc",
) -> List[Dict[str, Any]]:
    """
    Computes priority items for all screened patients from the relational database or longitudinal memory.
    Supports filtering and multi-dimensional sorting.
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        # Query all screenings and patients from DB
        screenings = db.query(ScreeningModel).order_by(ScreeningModel.timestamp_iso.desc()).all()
        patients = {p.id: p for p in db.query(PatientModel).all()}

        queue: List[Dict[str, Any]] = []

        for scr in screenings:
            pat_model = patients.get(scr.patient_id)
            patient_dict = None
            if pat_model:
                symptoms = json.loads(pat_model.symptoms_json) if pat_model.symptoms_json else []
                patient_dict = {
                    "id": pat_model.id,
                    "name": pat_model.name,
                    "age": pat_model.age,
                    "gender": pat_model.gender,
                    "village": pat_model.village,
                    "diabetes_duration": pat_model.diabetes_duration,
                    "last_hba1c": pat_model.last_hba1c,
                    "insulin_use": pat_model.insulin_use,
                    "visual_acuity_od": pat_model.visual_acuity_od,
                    "visual_acuity_os": pat_model.visual_acuity_os,
                    "symptoms": symptoms,
                }

            screening_dict = {
                "id": scr.id,
                "screening_id": scr.id,
                "patient_id": scr.patient_id,
                "patient_name": scr.patient_name,
                "village": scr.village,
                "screening_date": scr.screening_date,
                "timestamp_iso": scr.timestamp_iso,
                "predicted_class": scr.predicted_class,
                "class_name": scr.class_name,
                "confidence": scr.confidence,
                "safety_status": scr.safety_status,
                "dr_severity_od": scr.dr_severity_od,
                "dr_severity_os": scr.dr_severity_os,
                "overall_severity": scr.overall_severity,
                "doctor_status": scr.doctor_status,
                "review_status": scr.review_status,
                "doctor_reviewed_result": scr.review.reviewed_result if scr.review else None,
                "image_od_path": scr.image_od_path,
                "image_os_path": scr.image_os_path,
                "gradcam_url": scr.gradcam_url,
            }

            priority_item = calculate_screening_priority(
                screening=screening_dict,
                patient=patient_dict,
                db=db,
            )
            queue.append(priority_item)

        # Apply search filter if provided
        if search and search.strip():
            q_clean = search.strip().lower()
            queue = [
                item for item in queue
                if (
                    q_clean in (item.get("patient_name") or "").lower()
                    or q_clean in (item.get("patient_id") or "").lower()
                    or q_clean in (item.get("village") or "").lower()
                    or q_clean in (item.get("dr_result") or "").lower()
                    or q_clean in (item.get("screening_id") or "").lower()
                )
            ]

        # Apply priority filter
        if filter_level and filter_level.lower() != "all":
            fl = filter_level.upper()
            if fl in ["P1", "URGENT"]:
                queue = [item for item in queue if item.get("priority_level") == PRIORITY_P1]
            elif fl in ["P2", "PRIORITY"]:
                queue = [item for item in queue if item.get("priority_level") == PRIORITY_P2]
            elif fl in ["P3", "ROUTINE"]:
                queue = [item for item in queue if item.get("priority_level") == PRIORITY_P3]
            elif fl in ["VERIFICATION_REQUIRED", "VERIFICATION", "UNCERTAINTY"]:
                queue = [item for item in queue if item.get("priority_level") == PRIORITY_VERIFICATION_REQUIRED]
            elif fl in ["RECAPTURE_REQUIRED", "RECAPTURE"]:
                queue = [item for item in queue if item.get("priority_level") == PRIORITY_RECAPTURE_REQUIRED]

        # Priority Level numeric rank for sorting
        def get_priority_rank(item: Dict[str, Any]) -> float:
            level = item.get("priority_level")
            score = item.get("priority_score", 0.0)
            if level == PRIORITY_P1:
                return 100.0 + score
            elif level == PRIORITY_P2:
                return 50.0 + score
            elif level == PRIORITY_VERIFICATION_REQUIRED:
                return 30.0 + score
            elif level == PRIORITY_RECAPTURE_REQUIRED:
                return 20.0 + score
            else:
                return 10.0 + score

        # Apply sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "priority":
            queue.sort(key=get_priority_rank, reverse=reverse)
        elif sort_by == "severity":
            queue.sort(key=lambda x: (x.get("predicted_class") if x.get("predicted_class") is not None else -1), reverse=reverse)
        elif sort_by == "confidence":
            queue.sort(key=lambda x: (x.get("confidence") if x.get("confidence") is not None else -1.0), reverse=reverse)
        elif sort_by in ["date", "latest"]:
            queue.sort(key=lambda x: (x.get("calculated_at") or ""), reverse=reverse)
        else:
            queue.sort(key=get_priority_rank, reverse=reverse)

        return queue

    finally:
        if owns_session:
            db.close()


def get_priority_stats(db: Optional[Session] = None) -> Dict[str, Any]:
    """Computes summary statistics for the Rural Care Priority Dashboard."""
    queue = get_priority_queue(db=db)
    total = len(queue)
    urgent_count = sum(1 for item in queue if item.get("priority_level") == PRIORITY_P1)
    priority_count = sum(1 for item in queue if item.get("priority_level") == PRIORITY_P2)
    routine_count = sum(1 for item in queue if item.get("priority_level") == PRIORITY_P3)
    verification_count = sum(1 for item in queue if item.get("priority_level") == PRIORITY_VERIFICATION_REQUIRED)
    recapture_count = sum(1 for item in queue if item.get("priority_level") == PRIORITY_RECAPTURE_REQUIRED)

    return {
        "total_screened": total,
        "urgent_count": urgent_count,
        "priority_count": priority_count,
        "routine_count": routine_count,
        "verification_required_count": verification_count,
        "recapture_required_count": recapture_count,
        "algorithm_version": ALGORITHM_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
