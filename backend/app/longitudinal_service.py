"""
Phase 10: Longitudinal Screening Intelligence Service for MADOCS.
Provides chronological screening history retrieval, faithful multi-visit comparison,
and safe classification change metrics without autonomous diagnosis claims,
backed by persistent SQLAlchemy database models.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScreeningModel, ScreeningReviewModel, PatientModel

logger = logging.getLogger("dr_backend.longitudinal_service")

# Class ID to Name mapping
DR_CLASS_NAMES = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}

# Standard Clinical Disclaimers
LONGITUDINAL_DISCLAIMER_EN = (
    "This comparison summarizes AI-assisted screening results across visits. "
    "It does not independently establish disease progression or replace clinical assessment."
)
LONGITUDINAL_DISCLAIMER_HI = (
    "यह तुलना विभिन्न दौरों के एआई-सहायता प्राप्त स्क्रीनिंग परिणामों को संक्षेप में प्रस्तुत करती है। "
    "यह स्वतंत्र रूप से बीमारी की प्रगति को स्थापित नहीं करती है और न ही नैदानिक मूल्यांकन का स्थान लेती है।"
)

GRADCAM_EXPLANATION_NOTE = (
    "Grad-CAM shows model attention and is not a direct measurement of disease progression."
)
IMAGE_COMPARISON_LABEL = "Visual comparison for clinical review."
LESION_COMPARISON_NOTE = "Lesion-specific comparison unavailable."


# In-memory repository of canonical screenings for Phase 10 fallback & testing
MOCK_CANONICAL_SCREENINGS: List[Dict[str, Any]] = [
    # Patient PAT-2026-081 (Ramesh Kumar Verma) - 3 Visits
    {
        "screening_id": "SCR-2026-0991",
        "patient_id": "PAT-2026-081",
        "patient_name": "Ramesh Kumar Verma",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-08-22 10:45 AM",
        "timestamp_iso": "2026-08-22T10:45:00Z",
        "predicted_class": 2,
        "class_name": "Moderate NPDR",
        "confidence": 0.85,
        "dr_severity_od": "dr2",
        "dr_severity_os": "dr1",
        "overall_severity": "dr2",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Moderate NPDR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    {
        "screening_id": "SCR-2026-0740",
        "patient_id": "PAT-2026-081",
        "patient_name": "Ramesh Kumar Verma",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-06-12 11:15 AM",
        "timestamp_iso": "2026-06-12T11:15:00Z",
        "predicted_class": 1,
        "class_name": "Mild NPDR",
        "confidence": 0.78,
        "dr_severity_od": "dr1",
        "dr_severity_os": "dr0",
        "overall_severity": "dr1",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Mild NPDR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    {
        "screening_id": "SCR-2026-0410",
        "patient_id": "PAT-2026-081",
        "patient_name": "Ramesh Kumar Verma",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-03-20 09:30 AM",
        "timestamp_iso": "2026-03-20T09:30:00Z",
        "predicted_class": 1,
        "class_name": "Mild NPDR",
        "confidence": 0.82,
        "dr_severity_od": "dr1",
        "dr_severity_os": "dr0",
        "overall_severity": "dr1",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Mild NPDR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": None,
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    # Patient PAT-2026-082 (Sunita Devi) - 2 Visits
    {
        "screening_id": "SCR-2026-0992",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "village": "Shivpuri Taluk",
        "screening_date": "2026-08-22 02:30 PM",
        "timestamp_iso": "2026-08-22T14:30:00Z",
        "predicted_class": 3,
        "class_name": "Severe NPDR",
        "confidence": 0.89,
        "dr_severity_od": "dr3",
        "dr_severity_os": "dr2",
        "overall_severity": "dr3",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "HIGH",
        "referral_priority": "PRIORITY SPECIALIST REVIEW",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Severe NPDR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    {
        "screening_id": "SCR-2026-0612",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "village": "Shivpuri Taluk",
        "screening_date": "2026-05-10 10:00 AM",
        "timestamp_iso": "2026-05-10T10:00:00Z",
        "predicted_class": 2,
        "class_name": "Moderate NPDR",
        "confidence": 0.82,
        "dr_severity_od": "dr2",
        "dr_severity_os": "dr1",
        "overall_severity": "dr2",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Moderate NPDR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    # Patient PAT-2026-083 (Balwinder Singh) - 1 Visit
    {
        "screening_id": "SCR-2026-0993",
        "patient_id": "PAT-2026-083",
        "patient_name": "Balwinder Singh",
        "village": "Kolar Rural Block",
        "screening_date": "2026-08-21 03:45 PM",
        "timestamp_iso": "2026-08-21T15:45:00Z",
        "predicted_class": 0,
        "class_name": "No DR",
        "confidence": 0.96,
        "dr_severity_od": "dr0",
        "dr_severity_os": "dr0",
        "overall_severity": "dr0",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "No DR",
        "reviewer_name": "Dr. Arvind Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": None,
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
]


def _screening_model_to_dict(scr: ScreeningModel) -> Dict[str, Any]:
    return {
        "screening_id": scr.id,
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
        "doctor_status": scr.doctor_status,
        "review_status": scr.review_status,
        "image_od": scr.image_od_path,
        "image_os": scr.image_os_path,
        "gradcam_od": scr.gradcam_url,
        "gradcam_os": None,
        "heatmap_od": scr.heatmap_url,
        "is_recapture": scr.doctor_status == "recapture_requested",
        "lesion_available": False,
    }


class LongitudinalService:
    def __init__(self):
        self._screenings: Dict[str, Dict[str, Any]] = {}
        for scr in MOCK_CANONICAL_SCREENINGS:
            self._screenings[scr["screening_id"]] = dict(scr)

    def register_or_update_screening(self, screening_data: Dict[str, Any], db: Optional[Session] = None):
        """Registers or updates a screening record in database and memory."""
        sid = screening_data.get("screening_id") or screening_data.get("id")
        if not sid:
            return
        self._screenings[sid] = dict(screening_data)

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            existing = db.query(ScreeningModel).filter(ScreeningModel.id == sid).first()
            if not existing:
                new_scr = ScreeningModel(
                    id=sid,
                    patient_id=screening_data.get("patient_id") or screening_data.get("patientId") or "PAT-2026-081",
                    patient_name=screening_data.get("patient_name") or screening_data.get("patientName") or "Patient",
                    village=screening_data.get("village", "Rampur"),
                    screening_date=screening_data.get("screening_date") or screening_data.get("screeningDate") or datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p"),
                    timestamp_iso=screening_data.get("timestamp_iso") or datetime.now(timezone.utc).isoformat(),
                    predicted_class=screening_data.get("predicted_class", 2),
                    class_name=screening_data.get("class_name") or screening_data.get("className", "Moderate"),
                    confidence=screening_data.get("confidence", 0.85),
                    dr_severity_od=screening_data.get("dr_severity_od", "drUncertain"),
                    dr_severity_os=screening_data.get("dr_severity_os", "drUncertain"),
                    overall_severity=screening_data.get("overall_severity", "drUncertain"),
                    safety_status=screening_data.get("safety_status", "READY_FOR_AI"),
                    screening_status=screening_data.get("screening_status", "RELIABLE AI SCREENING"),
                    risk_category=screening_data.get("risk_category", "MODERATE"),
                    referral_priority=screening_data.get("referral_priority", "EYE SPECIALIST REVIEW RECOMMENDED"),
                    gradcam_url=screening_data.get("gradcam_url") or screening_data.get("gradcam_od"),
                    heatmap_url=screening_data.get("heatmap_url") or screening_data.get("heatmap_od"),
                    image_od_path=screening_data.get("image_od_path") or screening_data.get("image_od"),
                    image_os_path=screening_data.get("image_os_path") or screening_data.get("image_os"),
                    doctor_status=screening_data.get("doctor_status", "pending"),
                    review_status=screening_data.get("review_status", "PENDING DOCTOR REVIEW"),
                )
                db.add(new_scr)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist screening {sid} in DB: {e}")
        finally:
            if owns_session:
                db.close()

    def get_screening(self, screening_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a screening record by ID from database."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
            if scr:
                return _screening_model_to_dict(scr)
        except Exception as e:
            logger.warning(f"Error querying screening {screening_id} from DB: {e}")
        finally:
            if owns_session:
                db.close()

        return self._screenings.get(screening_id)

    def get_patient_screening_history(self, patient_id: str, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all screenings for a specific patient, sorted newest first from database.
        Strict patient ID isolation ensures zero cross-patient data exposure.
        """
        if not patient_id:
            return []

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            scrs = db.query(ScreeningModel).filter(
                ScreeningModel.patient_id == patient_id
            ).order_by(ScreeningModel.timestamp_iso.desc()).all()

            if scrs:
                return [_screening_model_to_dict(s) for s in scrs]
        except Exception as e:
            logger.warning(f"Error querying patient screening history from DB: {e}")
        finally:
            if owns_session:
                db.close()

        patient_screenings = [
            scr for scr in self._screenings.values()
            if scr.get("patient_id") == patient_id or scr.get("patientId") == patient_id
        ]

        def sort_key(s):
            return s.get("timestamp_iso") or s.get("screening_date") or ""

        patient_screenings.sort(key=sort_key, reverse=True)
        return patient_screenings

    def get_latest_comparable_screening(
        self,
        current_screening_id: str,
        patient_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the most recent valid historical screening for the same patient
        prior to the current screening.
        """
        current_scr = self.get_screening(current_screening_id, db=db)
        target_patient_id = patient_id
        current_timestamp = None

        if current_scr:
            target_patient_id = current_scr.get("patient_id") or target_patient_id
            current_timestamp = current_scr.get("timestamp_iso") or current_scr.get("screening_date")

        if not target_patient_id:
            return None

        history = self.get_patient_screening_history(target_patient_id, db=db)

        candidates = [
            s for s in history
            if (s.get("screening_id") != current_screening_id and s.get("id") != current_screening_id)
            and not s.get("is_recapture", False)
            and s.get("predicted_class") is not None
        ]

        if not candidates:
            return None

        if current_timestamp:
            prior_candidates = [
                s for s in candidates
                if (s.get("timestamp_iso") or s.get("screening_date") or "") < current_timestamp
            ]
            if prior_candidates:
                return prior_candidates[0]

        return candidates[0]

    def _format_screening_summary(self, screening: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes and extracts structured screening summary fields."""
        sid = screening.get("screening_id") or screening.get("id")
        p_class = screening.get("predicted_class")
        c_name = screening.get("class_name") or screening.get("className") or (DR_CLASS_NAMES.get(p_class) if p_class is not None else "Unknown")

        return {
            "screening_id": sid,
            "screening_date": screening.get("screening_date") or screening.get("date") or "Unknown Date",
            "predicted_class": p_class,
            "class_name": c_name,
            "confidence": screening.get("confidence"),
            "dr_severity_od": screening.get("dr_severity_od") or screening.get("drSeverityOD"),
            "dr_severity_os": screening.get("dr_severity_os") or screening.get("drSeverityOS"),
            "overall_severity": screening.get("overall_severity") or screening.get("overallSeverity"),
            "safety_status": screening.get("safety_status") or screening.get("safetyStatus") or "READY_FOR_AI",
            "screening_status": screening.get("screening_status") or screening.get("screeningStatus") or "RELIABLE AI SCREENING",
            "risk_category": screening.get("risk_category") or screening.get("riskCategory") or "MODERATE",
            "referral_priority": screening.get("referral_priority") or screening.get("referralPriority") or "EYE SPECIALIST REVIEW RECOMMENDED",
            "doctor_status": screening.get("doctor_status") or screening.get("doctorStatus") or "pending",
            "review_status": screening.get("review_status") or screening.get("reviewStatus"),
            "doctor_reviewed_result": screening.get("doctor_reviewed_result") or screening.get("doctorReviewedResult"),
            "reviewer_name": screening.get("reviewer_name") or screening.get("reviewerName"),
            "is_recapture": bool(
                screening.get("is_recapture") is True
                or screening.get("doctor_status") == "recapture_requested"
                or screening.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"
            ),
            "image_od": screening.get("image_od") or screening.get("imageOD") or screening.get("image_od_path"),
            "image_os": screening.get("image_os") or screening.get("imageOS") or screening.get("image_os_path"),
            "gradcam_od": screening.get("gradcam_od") or screening.get("gradCamOD") or screening.get("gradcam_url"),
            "gradcam_os": screening.get("gradcam_os") or screening.get("gradCamOS"),
            "lesion_available": bool(screening.get("lesion_available", False)),
        }

    def compare_screenings(
        self,
        current_screening: Any,
        previous_screening: Optional[Any],
        language: str = "en",
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Faithfully compares two screenings for the same patient.
        Ensures strict mathematical logic, honest confidence separation, and safety guardrails.
        """
        if isinstance(current_screening, str):
            current_screening = self.get_screening(current_screening, db=db) or {"screening_id": current_screening}
        if isinstance(previous_screening, str):
            previous_screening = self.get_screening(previous_screening, db=db)

        curr_pid = current_screening.get("patient_id") or current_screening.get("patientId")
        patient_name = current_screening.get("patient_name") or current_screening.get("patientName") or "Patient"
        village = current_screening.get("village", "Community Camp")

        if previous_screening is None:
            return {
                "patient_id": curr_pid,
                "patient_name": patient_name,
                "village": village,
                "current_screening": self._format_screening_summary(current_screening),
                "previous_screening": None,
                "has_previous_screening": False,
                "classification_change_status": "HISTORY UNAVAILABLE",
                "classification_change_summary": "Previous screening history is unavailable for comparison.",
                "classification_change_summary_hi": "तुलना के लिए पिछला स्क्रीनिंग इतिहास उपलब्ध नहीं है।",
                "clinical_recommendation": "Doctor review is recommended for initial clinical assessment.",
                "clinical_recommendation_hi": "प्रारंभिक नैदानिक मूल्यांकन के लिए डॉक्टर समीक्षा की सलाह दी जाती है।",
                "confidence_comparison": {
                    "current_confidence": current_screening.get("confidence"),
                    "previous_confidence": None,
                    "note": "Single screening recorded. AI model confidence reflects baseline visit.",
                },
                "image_comparison": {
                    "current_image_od": current_screening.get("image_od") or current_screening.get("imageOD") or current_screening.get("image_od_path"),
                    "current_image_os": current_screening.get("image_os") or current_screening.get("imageOS") or current_screening.get("image_os_path"),
                    "previous_image_od": None,
                    "previous_image_os": None,
                    "label": IMAGE_COMPARISON_LABEL,
                },
                "gradcam_comparison": {
                    "current_gradcam": current_screening.get("gradcam_od") or current_screening.get("gradCamOD") or current_screening.get("gradcam_url"),
                    "previous_gradcam": None,
                    "explanation": GRADCAM_EXPLANATION_NOTE,
                },
                "lesion_comparison": {
                    "current_available": bool(current_screening.get("lesion_available", False)),
                    "previous_available": False,
                    "note": LESION_COMPARISON_NOTE,
                },
                "doctor_review_comparison": {
                    "current_doctor_status": current_screening.get("doctor_status") or current_screening.get("doctorStatus") or "pending",
                    "current_doctor_reviewed_result": current_screening.get("doctor_reviewed_result") or current_screening.get("doctorReviewedResult"),
                    "previous_doctor_status": None,
                    "previous_doctor_reviewed_result": None,
                },
                "disclaimer": LONGITUDINAL_DISCLAIMER_EN,
                "disclaimer_hi": LONGITUDINAL_DISCLAIMER_HI,
            }

        prev_pid = previous_screening.get("patient_id") or previous_screening.get("patientId")
        if curr_pid and prev_pid and curr_pid != prev_pid:
            raise ValueError(
                f"Security Violation: Cross-patient screening comparison blocked between patient '{curr_pid}' and '{prev_pid}'."
            )

        curr_is_recapture = bool(
            current_screening.get("is_recapture") is True
            or current_screening.get("doctor_status") == "recapture_requested"
            or current_screening.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"
        )
        prev_is_recapture = bool(
            previous_screening.get("is_recapture") is True
            or previous_screening.get("doctor_status") == "recapture_requested"
            or previous_screening.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"
        )

        curr_class = current_screening.get("predicted_class")
        prev_class = previous_screening.get("predicted_class")

        curr_name = DR_CLASS_NAMES.get(curr_class, "Unknown")
        prev_name = DR_CLASS_NAMES.get(prev_class, "Unknown")

        if curr_is_recapture:
            status = "NOT COMPARABLE"
            summary_en = "Current screening requires image re-capture and cannot be evaluated as a finalized result."
            summary_hi = "वर्तमान स्क्रीनिंग में इमेज पुनः कैप्चर की आवश्यकता है और इसे अंतिम परिणाम के रूप में मूल्यांकित नहीं किया जा सकता है।"
            rec_en = "Please re-capture fundus image before evaluating screening classification change."
            rec_hi = "स्क्रीनिंग वर्गीकरण में बदलाव का मूल्यांकन करने से पहले कृपया पुनः फंडस फोटो लें।"
        elif prev_is_recapture or curr_class is None or prev_class is None:
            status = "NOT COMPARABLE"
            summary_en = "Previous screening is incomplete or invalid. Direct classification comparison is not possible."
            summary_hi = "पिछली स्क्रीनिंग अधूरी या अमान्य है। सीधा वर्गीकरण तुलना संभव नहीं है।"
            rec_en = "Doctor review is recommended to assess patient eye health."
            rec_hi = "मरीज के नेत्र स्वास्थ्य का आकलन करने के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"
        elif curr_class == prev_class:
            status = "UNCHANGED"
            summary_en = "AI screening classification is unchanged."
            summary_hi = "एआई स्क्रीनिंग वर्गीकरण अपरिवर्तित है।"
            rec_en = "Doctor review is recommended to confirm stable retinal status."
            rec_hi = "स्थिर रेटिना स्थिति की पुष्टि के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"
        elif curr_class > prev_class:
            status = "CLASSIFICATION INCREASED"
            summary_en = f"AI screening classification increased from {prev_name} to {curr_name}."
            summary_hi = f"एआई स्क्रीनिंग वर्गीकरण {prev_name} से बढ़कर {curr_name} हो गया है।"
            rec_en = "Doctor review is recommended to interpret this change."
            rec_hi = "इस बदलाव की व्याख्या के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"
        else:
            status = "CLASSIFICATION DECREASED"
            summary_en = f"AI screening classification decreased from {prev_name} to {curr_name}."
            summary_hi = f"एआई स्क्रीनिंग वर्गीकरण {prev_name} से घटकर {curr_name} हो गया है।"
            rec_en = "Doctor review is recommended to verify clinical interpretation."
            rec_hi = "नैदानिक व्याख्या को सत्यापित करने के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"

        curr_conf = current_screening.get("confidence")
        prev_conf = previous_screening.get("confidence")

        conf_note = (
            f"Previous AI Confidence: {prev_conf * 100:.2f}%, Current AI Confidence: {curr_conf * 100:.2f}%. "
            "Confidence reflects single-image model probability and is not a measure of clinical change."
            if (curr_conf is not None and prev_conf is not None)
            else "AI model confidence recorded per screening visit."
        )

        return {
            "patient_id": curr_pid,
            "patient_name": patient_name,
            "village": village,
            "current_screening": self._format_screening_summary(current_screening),
            "previous_screening": self._format_screening_summary(previous_screening),
            "has_previous_screening": True,
            "classification_change_status": status,
            "classification_change_summary": summary_en,
            "classification_change_summary_hi": summary_hi,
            "clinical_recommendation": rec_en,
            "clinical_recommendation_hi": rec_hi,
            "confidence_comparison": {
                "current_confidence": curr_conf,
                "previous_confidence": prev_conf,
                "note": conf_note,
            },
            "image_comparison": {
                "current_image_od": current_screening.get("image_od") or current_screening.get("imageOD") or current_screening.get("image_od_path"),
                "current_image_os": current_screening.get("image_os") or current_screening.get("imageOS") or current_screening.get("image_os_path"),
                "previous_image_od": previous_screening.get("image_od") or previous_screening.get("imageOD") or previous_screening.get("image_od_path"),
                "previous_image_os": previous_screening.get("image_os") or previous_screening.get("imageOS") or previous_screening.get("image_os_path"),
                "label": IMAGE_COMPARISON_LABEL,
            },
            "gradcam_comparison": {
                "current_gradcam": current_screening.get("gradcam_od") or current_screening.get("gradCamOD") or current_screening.get("gradcam_url"),
                "previous_gradcam": previous_screening.get("gradcam_od") or previous_screening.get("gradCamOD") or previous_screening.get("gradcam_url"),
                "explanation": GRADCAM_EXPLANATION_NOTE,
            },
            "lesion_comparison": {
                "current_available": bool(current_screening.get("lesion_available", False)),
                "previous_available": bool(previous_screening.get("lesion_available", False)),
                "note": LESION_COMPARISON_NOTE,
            },
            "doctor_review_comparison": {
                "current_doctor_status": current_screening.get("doctor_status") or current_screening.get("doctorStatus") or "pending",
                "current_doctor_reviewed_result": current_screening.get("doctor_reviewed_result") or current_screening.get("doctorReviewedResult"),
                "previous_doctor_status": previous_screening.get("doctor_status") or previous_screening.get("doctorStatus") or "verified",
                "previous_doctor_reviewed_result": previous_screening.get("doctor_reviewed_result") or previous_screening.get("doctorReviewedResult"),
            },
            "disclaimer": LONGITUDINAL_DISCLAIMER_EN,
            "disclaimer_hi": LONGITUDINAL_DISCLAIMER_HI,
        }


longitudinal_service = LongitudinalService()
