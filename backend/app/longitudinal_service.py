"""
Phase 10: Longitudinal Screening Intelligence Service for MADOCS.
Provides chronological screening history retrieval, faithful multi-visit comparison,
and safe classification change metrics without autonomous diagnosis claims.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger("dr_backend.longitudinal_service")

# Class ID to Name mapping
DR_CLASS_NAMES = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
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


# In-memory repository of canonical screenings for Phase 10 demo & testing
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
        "class_name": "Moderate",
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
        "doctor_reviewed_result": "Moderate",
        "reviewer_name": "Dr. A. Swaminathan, MS",
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
        "class_name": "Mild",
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
        "doctor_reviewed_result": "Mild",
        "reviewer_name": "Dr. A. Swaminathan, MS",
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
        "class_name": "Mild",
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
        "doctor_reviewed_result": "Mild",
        "reviewer_name": "Dr. A. Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
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
        "screening_date": "2026-08-22 11:30 AM",
        "timestamp_iso": "2026-08-22T11:30:00Z",
        "predicted_class": 3,
        "class_name": "Severe",
        "confidence": 0.88,
        "dr_severity_od": "dr3",
        "dr_severity_os": "dr2",
        "overall_severity": "dr3",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "HIGH",
        "referral_priority": "PRIORITY SPECIALIST REVIEW",
        "doctor_status": "pending",
        "review_status": "PENDING DOCTOR REVIEW",
        "doctor_reviewed_result": "Pending Specialist Review",
        "reviewer_name": None,
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    {
        "screening_id": "SCR-2026-0680",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "village": "Shivpuri Taluk",
        "screening_date": "2026-05-15 02:00 PM",
        "timestamp_iso": "2026-05-15T14:00:00Z",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.84,
        "dr_severity_od": "dr2",
        "dr_severity_os": "dr2",
        "overall_severity": "dr2",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
        "doctor_reviewed_result": "Moderate",
        "reviewer_name": "Dr. A. Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": "/results/sample_od_gradcam.jpg",
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
    # Patient PAT-2026-083 (Balwinder Singh) - Single Visit (No history)
    {
        "screening_id": "SCR-2026-0850",
        "patient_id": "PAT-2026-083",
        "patient_name": "Balwinder Singh",
        "village": "Kolar Rural Block",
        "screening_date": "2026-08-21 10:00 AM",
        "timestamp_iso": "2026-08-21T10:00:00Z",
        "predicted_class": 0,
        "class_name": "No DR",
        "confidence": 0.94,
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
        "reviewer_name": "Dr. A. Swaminathan, MS",
        "image_od": "/samples/eyes.png",
        "image_os": "/samples/eyes_os.png",
        "gradcam_od": None,
        "gradcam_os": None,
        "is_recapture": False,
        "lesion_available": False,
    },
]


class LongitudinalService:
    def __init__(self):
        # Active screenings dictionary keyed by screening_id
        self._screenings: Dict[str, Dict[str, Any]] = {}
        for scr in MOCK_CANONICAL_SCREENINGS:
            self._screenings[scr["screening_id"]] = dict(scr)

    def register_or_update_screening(self, screening_data: Dict[str, Any]):
        """Registers or updates a screening record in memory."""
        sid = screening_data.get("screening_id") or screening_data.get("id")
        if not sid:
            return
        self._screenings[sid] = dict(screening_data)

    def get_screening(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a screening record by ID."""
        return self._screenings.get(screening_id)

    def get_patient_screening_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all screenings for a specific patient, sorted newest first.
        Strict patient ID isolation ensures zero cross-patient data exposure.
        """
        if not patient_id:
            return []
        
        patient_screenings = [
            scr for scr in self._screenings.values()
            if scr.get("patient_id") == patient_id or scr.get("patientId") == patient_id
        ]

        # Sort newest first by timestamp_iso or screening_date
        def sort_key(s):
            return s.get("timestamp_iso") or s.get("screening_date") or ""

        patient_screenings.sort(key=sort_key, reverse=True)
        return patient_screenings

    def get_latest_comparable_screening(
        self,
        current_screening_id: str,
        patient_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the most recent valid historical screening for the same patient
        prior to the current screening.
        """
        current = self.get_screening(current_screening_id)
        if current:
            pid = current.get("patient_id") or current.get("patientId")
        else:
            pid = patient_id

        if not pid:
            return None

        history = self.get_patient_screening_history(pid)
        # Exclude the current screening itself
        previous_candidates = [
            s for s in history
            if (s.get("screening_id") or s.get("id")) != current_screening_id
        ]

        if not previous_candidates:
            return None

        # Return newest previous
        return previous_candidates[0]

    def compare_screenings(
        self,
        current_screening: Dict[str, Any],
        previous_screening: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs safe, objective comparison between current and previous screening.
        Adheres to clinical safety standards:
        - Terminology: "Screening Classification Change" (NOT "Disease Progression")
        - Distinguishes AI classification change from Doctor-reviewed interpretation
        - Flags re-capture requests safely
        - Evaluates confidence separately
        """
        if not current_screening:
            raise ValueError("Current screening record is required for comparison.")

        curr_id = current_screening.get("screening_id") or current_screening.get("id") or "CURRENT"
        curr_pid = current_screening.get("patient_id") or current_screening.get("patientId") or "UNKNOWN"
        patient_name = current_screening.get("patient_name") or current_screening.get("patientName") or "Patient"
        village = current_screening.get("village") or "Rural Camp"

        # Case 1: No previous screening exists
        if not previous_screening:
            return {
                "patient_id": curr_pid,
                "patient_name": patient_name,
                "village": village,
                "current_screening": self._format_screening_summary(current_screening),
                "previous_screening": None,
                "has_previous_screening": False,
                "classification_change_status": "HISTORY UNAVAILABLE",
                "classification_change_summary": "Previous screening history is unavailable.",
                "classification_change_summary_hi": "पिछली स्क्रीनिंग उपलब्ध नहीं है।",
                "clinical_recommendation": "Baseline screening recorded. Routine clinical follow-up as indicated.",
                "clinical_recommendation_hi": "प्रारंभिक स्क्रीनिंग दर्ज की गई। आवश्यकतानुसार नियमित नैदानिक परामर्श लें।",
                "confidence_comparison": {
                    "current_confidence": current_screening.get("confidence"),
                    "previous_confidence": None,
                    "note": "Initial baseline confidence score.",
                },
                "image_comparison": {
                    "current_image_od": current_screening.get("image_od") or current_screening.get("imageOD"),
                    "current_image_os": current_screening.get("image_os") or current_screening.get("imageOS"),
                    "previous_image_od": None,
                    "previous_image_os": None,
                    "label": IMAGE_COMPARISON_LABEL,
                },
                "gradcam_comparison": {
                    "current_gradcam": current_screening.get("gradcam_od") or current_screening.get("gradCamOD"),
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
                    "previous_doctor_status": None,
                },
                "disclaimer": LONGITUDINAL_DISCLAIMER_EN,
                "disclaimer_hi": LONGITUDINAL_DISCLAIMER_HI,
            }

        prev_id = previous_screening.get("screening_id") or previous_screening.get("id") or "PREVIOUS"
        prev_pid = previous_screening.get("patient_id") or previous_screening.get("patientId")

        # Security check: Data Isolation
        if curr_pid and prev_pid and curr_pid != prev_pid:
            raise ValueError(
                f"Security Violation: Cannot compare screening {curr_id} (Patient {curr_pid}) with "
                f"{prev_id} (Patient {prev_pid}). Screenings must belong to the same patient."
            )

        # Re-capture check on current or previous screening
        curr_is_recapture = (
            current_screening.get("is_recapture") is True
            or current_screening.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"
            or current_screening.get("doctor_status") == "recapture_requested"
            or current_screening.get("safety_status") in ["IMAGE_INVALID", "IMAGE_QUALITY_INSUFFICIENT"]
        )

        prev_is_recapture = (
            previous_screening.get("is_recapture") is True
            or previous_screening.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"
            or previous_screening.get("doctor_status") == "recapture_requested"
        )

        curr_class = current_screening.get("predicted_class")
        prev_class = previous_screening.get("predicted_class")

        curr_name = (
            current_screening.get("class_name")
            or current_screening.get("className")
            or (DR_CLASS_NAMES.get(curr_class) if curr_class is not None else "Unknown")
        )
        prev_name = (
            previous_screening.get("class_name")
            or previous_screening.get("className")
            or (DR_CLASS_NAMES.get(prev_class) if prev_class is not None else "Unknown")
        )

        # Evaluate Progression / Classification Change
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
            summary_en = f"AI screening classification is unchanged ({curr_name})."
            summary_hi = f"एआई स्क्रीनिंग वर्गीकरण अपरिवर्तित है ({curr_name})।"
            rec_en = "Doctor review is recommended to confirm stable retinal status."
            rec_hi = "स्थिर रेटिना स्थिति की पुष्टि के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"
        elif curr_class > prev_class:
            status = "CLASSIFICATION INCREASED"
            summary_en = f"AI screening classification increased from {prev_name} to {curr_name}."
            summary_hi = f"एआई स्क्रीनिंग वर्गीकरण {prev_name} से बढ़कर {curr_name} हो गया है।"
            rec_en = "Doctor review is recommended to interpret this change."
            rec_hi = "इस बदलाव की व्याख्या के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"
        else: # curr_class < prev_class
            status = "CLASSIFICATION DECREASED"
            summary_en = f"AI screening classification decreased from {prev_name} to {curr_name}."
            summary_hi = f"एआई स्क्रीनिंग वर्गीकरण {prev_name} से घटकर {curr_name} हो गया है।"
            rec_en = "Doctor review is recommended to verify clinical interpretation."
            rec_hi = "नैदानिक व्याख्या को सत्यापित करने के लिए डॉक्टर की समीक्षा की सलाह दी जाती है।"

        # Format confidence comparison (honest separation, no fake improvement math)
        curr_conf = current_screening.get("confidence")
        prev_conf = previous_screening.get("confidence")

        conf_note = (
            f"Previous AI Confidence: {prev_conf * 100:.1f}%, Current AI Confidence: {curr_conf * 100:.1f}%. "
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
                "current_image_od": current_screening.get("image_od") or current_screening.get("imageOD"),
                "current_image_os": current_screening.get("image_os") or current_screening.get("imageOS"),
                "previous_image_od": previous_screening.get("image_od") or previous_screening.get("imageOD"),
                "previous_image_os": previous_screening.get("image_os") or previous_screening.get("imageOS"),
                "label": IMAGE_COMPARISON_LABEL,
            },
            "gradcam_comparison": {
                "current_gradcam": current_screening.get("gradcam_od") or current_screening.get("gradCamOD"),
                "previous_gradcam": previous_screening.get("gradcam_od") or previous_screening.get("gradCamOD"),
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
            "image_od": screening.get("image_od") or screening.get("imageOD"),
            "image_os": screening.get("image_os") or screening.get("imageOS"),
            "gradcam_od": screening.get("gradcam_od") or screening.get("gradCamOD"),
            "gradcam_os": screening.get("gradcam_os") or screening.get("gradCamOS"),
            "lesion_available": bool(screening.get("lesion_available", False)),
        }


# Singleton service instance
longitudinal_service = LongitudinalService()
