"""
Centralized AI-Assisted Risk Assessment and Referral Support Module for MADOCS.
Deterministic, transparent, rule-driven evaluation of Diabetic Retinopathy screening risk and referral priority.
"""

from typing import Dict, Any, Optional

# Standardized Categories
RISK_LOW = "LOW"
RISK_MODERATE = "MODERATE"
RISK_HIGH = "HIGH"
RISK_UNABLE = "UNABLE TO ASSESS"
RISK_LOW_CONF = "LOW CONFIDENCE / REVIEW REQUIRED"

REFERRAL_ROUTINE = "ROUTINE FOLLOW-UP"
REFERRAL_SPECIALIST_RECOMMENDED = "EYE SPECIALIST REVIEW RECOMMENDED"
REFERRAL_PRIORITY_SPECIALIST = "PRIORITY SPECIALIST REVIEW"
REFERRAL_RECAPTURE_REQUIRED = "IMAGE RE-CAPTURE REQUIRED"

# Explanations
EXPLANATION_LOW = "No diabetic retinopathy lesions detected. Low risk of vision impairment."
EXPLANATION_MODERATE = "Features consistent with non-proliferative diabetic retinopathy detected. Moderate risk profile."
EXPLANATION_HIGH = "Features consistent with severe non-proliferative or proliferative diabetic retinopathy detected. High risk profile."
EXPLANATION_UNABLE = "Image quality or retinal validation checks failed. Risk cannot be reliably computed."
EXPLANATION_LOW_CONF = "Model confidence is below the clinical threshold. Risk assessment requires specialist verification."

GUIDANCE_ROUTINE = "Routine annual follow-up may be appropriate according to local clinical protocol."
GUIDANCE_SPECIALIST = "Eye specialist review is recommended based on the AI-assisted screening result."
GUIDANCE_PRIORITY = "Priority specialist review is recommended based on the AI-assisted screening result."
GUIDANCE_RECAPTURE = "Please capture a clearer fundus image or request specialist clinical examination."
GUIDANCE_LOW_CONF = "Consider image re-capture or specialist review."


def evaluate_risk_and_referral(
    predicted_class: Optional[int],
    confidence: Optional[float],
    safety_status: str = "READY_FOR_AI",
    is_low_confidence: bool = False,
) -> Dict[str, Any]:
    """
    Evaluates risk category and referral priority for an individual eye.
    
    Rules:
    1. If safety_status is not 'READY_FOR_AI' -> UNABLE TO ASSESS, IMAGE RE-CAPTURE REQUIRED
    2. If is_low_confidence is True -> LOW CONFIDENCE / REVIEW REQUIRED, EYE SPECIALIST REVIEW RECOMMENDED / RECAPTURE
    3. If predicted_class == 0 (No DR) -> LOW, ROUTINE FOLLOW-UP
    4. If predicted_class in [1, 2] (Mild, Moderate DR) -> MODERATE, EYE SPECIALIST REVIEW RECOMMENDED
    5. If predicted_class in [3, 4] (Severe, Proliferative DR) -> HIGH, PRIORITY SPECIALIST REVIEW
    """
    # Safety Gate Check
    if safety_status != "READY_FOR_AI" or predicted_class is None:
        return {
            "risk_category": RISK_UNABLE,
            "referral_priority": REFERRAL_RECAPTURE_REQUIRED,
            "risk_explanation": EXPLANATION_UNABLE,
            "referral_guidance": GUIDANCE_RECAPTURE,
            "risk_level_numeric": -1,  # -1 = invalid/unable
        }

    # Low Confidence Check
    if is_low_confidence:
        return {
            "risk_category": RISK_LOW_CONF,
            "referral_priority": REFERRAL_SPECIALIST_RECOMMENDED,
            "risk_explanation": EXPLANATION_LOW_CONF,
            "referral_guidance": GUIDANCE_LOW_CONF,
            "risk_level_numeric": 1,  # Triage as review required
        }

    # Class-Based Risk Triage
    if predicted_class == 0:
        return {
            "risk_category": RISK_LOW,
            "referral_priority": REFERRAL_ROUTINE,
            "risk_explanation": EXPLANATION_LOW,
            "referral_guidance": GUIDANCE_ROUTINE,
            "risk_level_numeric": 0,
        }
    elif predicted_class in [1, 2]:
        return {
            "risk_category": RISK_MODERATE,
            "referral_priority": REFERRAL_SPECIALIST_RECOMMENDED,
            "risk_explanation": EXPLANATION_MODERATE,
            "referral_guidance": GUIDANCE_SPECIALIST,
            "risk_level_numeric": 2,
        }
    elif predicted_class in [3, 4]:
        return {
            "risk_category": RISK_HIGH,
            "referral_priority": REFERRAL_PRIORITY_SPECIALIST,
            "risk_explanation": EXPLANATION_HIGH,
            "referral_guidance": GUIDANCE_PRIORITY,
            "risk_level_numeric": 3,
        }
    else:
        return {
            "risk_category": RISK_UNABLE,
            "referral_priority": REFERRAL_RECAPTURE_REQUIRED,
            "risk_explanation": EXPLANATION_UNABLE,
            "referral_guidance": GUIDANCE_RECAPTURE,
            "risk_level_numeric": -1,
        }


def aggregate_two_eye_screening(
    od_eval: Optional[Dict[str, Any]],
    os_eval: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes overall two-eye screening risk and referral summary using the Max-Risk Rule.
    
    Determines highest screening risk attribution:
    - 'Right Eye (OD)'
    - 'Left Eye (OS)'
    - 'Both Eyes'
    - 'Unable to Assess'
    """
    od_level = od_eval.get("risk_level_numeric", -1) if od_eval else -1
    os_level = os_eval.get("risk_level_numeric", -1) if os_eval else -1

    od_cat = od_eval.get("risk_category", RISK_UNABLE) if od_eval else RISK_UNABLE
    os_cat = os_eval.get("risk_category", RISK_UNABLE) if os_eval else RISK_UNABLE

    # Case: Both eyes unable to assess
    if od_level == -1 and os_level == -1:
        return {
            "overall_risk": RISK_UNABLE,
            "highest_risk_eye": "Unable to Assess",
            "overall_referral": REFERRAL_RECAPTURE_REQUIRED,
            "overall_guidance": "Bilateral image capture did not pass AI safety checks. Please capture clearer fundus scans.",
        }

    # Case: One eye unable to assess, other eye evaluated
    if od_level == -1:
        return {
            "overall_risk": os_cat,
            "highest_risk_eye": "Left Eye (OS)",
            "overall_referral": os_eval["referral_priority"],
            "overall_guidance": f"Left eye evaluated as {os_cat}. Right eye image re-capture is required.",
        }
    if os_level == -1:
        return {
            "overall_risk": od_cat,
            "highest_risk_eye": "Right Eye (OD)",
            "overall_referral": od_eval["referral_priority"],
            "overall_guidance": f"Right eye evaluated as {od_cat}. Left eye image re-capture is required.",
        }

    # Case: Both evaluated - determine maximum
    if od_level > os_level:
        highest_eye = "Right Eye (OD)"
        worse_eval = od_eval
    elif os_level > od_level:
        highest_eye = "Left Eye (OS)"
        worse_eval = os_eval
    else:
        highest_eye = "Both Eyes"
        worse_eval = od_eval

    return {
        "overall_risk": worse_eval["risk_category"],
        "highest_risk_eye": highest_eye,
        "overall_referral": worse_eval["referral_priority"],
        "overall_guidance": worse_eval["referral_guidance"],
    }
