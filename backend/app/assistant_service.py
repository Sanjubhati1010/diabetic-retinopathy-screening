"""
Contextual AI Screening Assistant Service for MADOCS.
Specialized decision-support companion for community health workers (ASHAs and Vision Technicians) in rural screening camps.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("dr_backend.assistant_service")

# Safety Disclaimers
DISCLAIMER_EN = "The MADOCS Assistant is an AI-assisted screening support tool and does not provide clinical diagnoses or prescriptions."
DISCLAIMER_HI = "मैडॉक्स (MADOCS) सहायक एक एआई-सहायता प्राप्त स्क्रीनिंग टूल है और यह कोई नैदानिक दवा या अंतिम चिकित्सा निदान प्रदान नहीं करता है।"

# Medication / Diagnosis Refusal Keywords
MEDICAL_RESTRICTED_TERMS = [
    "medicine", "drug", "tablet", "dosage", "prescription", "cure", "treatment",
    "dawa", "dawai", "goli", "ilaaj", "ilaj", "treatment", "prescribe", "surgery"
]


def is_medical_treatment_query(message: str) -> bool:
    clean = message.lower()
    return any(term in clean for term in MEDICAL_RESTRICTED_TERMS)


def format_confidence_pct(conf: Optional[float]) -> str:
    if conf is None:
        return "N/A"
    val = conf * 100 if conf <= 1.0 else conf
    return f"{val:.1f}%"


def explain_screening_context(context: Optional[Dict[str, Any]], language: str = "en") -> str:
    """Produces conservative, faithful explanation of current screening results."""
    is_hi = language.startswith("hi")
    
    if not context or not any(context.values()):
        if is_hi:
            return "वर्तमान में कोई स्क्रीनिंग परिणाम उपलब्ध नहीं है। कृपया पहले रेटिना छवि अपलोड और एआई स्क्रीनिंग पूरी करें।"
        return "No screening result is currently available. Please complete the image validation and AI screening first."

    # Extract available context
    eye = context.get("eye", "Bilateral")
    pred = context.get("prediction") or context.get("className") or context.get("class_name")
    conf = context.get("confidence")
    safety = context.get("safety_status") or context.get("safetyStatus") or "READY_FOR_AI"
    risk = context.get("risk_category") or context.get("riskCategory") or "MODERATE"
    referral = context.get("referral_priority") or context.get("referralPriority") or "EYE SPECIALIST REVIEW RECOMMENDED"
    explain_avail = context.get("explainability_available", True)
    is_low_conf = context.get("is_low_confidence", False)

    # Check for Safety Gate block
    if safety in ["IMAGE_INVALID", "IMAGE_QUALITY_INSUFFICIENT", "AI_ANALYSIS_BLOCKED"]:
        if is_hi:
            return (
                f"रेटिना छवि एआई सुरक्षा जांच (Safety Gate) में सफल नहीं हुई (स्थिति: {safety})। "
                "छवि की गुणवत्ता अपर्याप्त होने के कारण एआई मॉडल ने भविष्यवाणी रोक दी है। "
                "कृपया बेहतर प्रकाश और फोकस के साथ पुनः फंडस फोटो लें।"
            )
        return (
            f"The retinal scan did not pass the AI Safety Gate (Status: {safety}). "
            "Because image validation or quality checks failed, model prediction was safely bypassed. "
            "Please capture a clearer fundus scan with proper illumination and focus."
        )

    # High / Low Confidence Explanation
    conf_str = f"{conf * 100:.1f}%" if (conf is not None and conf <= 1.0) else (f"{conf:.1f}%" if conf else "N/A")

    if is_hi:
        reply_parts = [
            f"एआई स्क्रीनिंग मॉडल ने रेटिना छवि में {pred or 'पहचाने गए पैटर्न'} का विश्लेषण किया है (मॉडल कॉन्फिडेंस: {conf_str})।",
            f"स्क्रीनिंग जोखिम (Risk): {risk}।",
            f"रेफरल अनुशंसा (Referral): {referral}।",
        ]
        if explain_avail:
            reply_parts.append("Grad-CAM हीटमैप उन क्षेत्रों को दर्शाता है जिन्होंने एआई के निर्णय में योगदान दिया (यह पुष्ट नैदानिक घाव नहीं बल्कि मॉडल का ध्यान है)।")
        if is_low_conf:
            reply_parts.append("सूचना: एआई कॉन्फिडेंस कम है। कृपया नेत्र विशेषज्ञ से परामर्श लें या पुनः फोटो लें।")
        reply_parts.append("यह परिणाम एआई-सहायता प्राप्त स्क्रीनिंग समर्थन है और किसी पेशेवर नेत्र चिकित्सक की जांच का विकल्प नहीं है।")
        return " ".join(reply_parts)
    else:
        reply_parts = [
            f"The AI screening model classified the retinal scan as {pred or 'evaluated patterns'} with {conf_str} model confidence.",
            f"The screening risk category is {risk}, and the referral priority is {referral}.",
        ]
        if explain_avail:
            reply_parts.append("The Grad-CAM visualization highlights retinal regions that contributed to the model's prediction (model attention, not confirmed clinical lesions).")
        if is_low_conf:
            reply_parts.append("Caution: Model confidence is below threshold. Specialist review or re-capture is recommended.")
        reply_parts.append("This result is AI-assisted screening support and does not replace professional clinical evaluation.")
        return " ".join(reply_parts)


def generate_assistant_reply(
    message: str,
    language: str = "en",
    page: Optional[str] = None,
    screening_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates contextual assistant responses in English or Hindi.
    """
    is_hi = language.startswith("hi") or any(word in message.lower() for word in ["kaise", "kyun", "kya", "batao", "karein", "madad"])
    msg_clean = message.lower().strip()

    # 1. Guardrail Check: Medical treatment/prescriptions
    if is_medical_treatment_query(msg_clean):
        reply = (
            "मैं एक एआई स्क्रीनिंग सहायक हूँ और दवाइयां या चिकित्सा उपचार निर्धारित नहीं कर सकता। "
            "कृपया उचित निदान और उपचार के लिए किसी योग्य नेत्र रोग विशेषज्ञ (Ophthalmologist) से परामर्श लें।"
            if is_hi
            else "I am an AI screening assistant and cannot prescribe medications or medical treatments. "
            "Please consult a qualified ophthalmologist or physician for clinical diagnosis and treatment planning."
        )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Explain My Result", "How to Use?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 2. "Explain My Result"
    if any(k in msg_clean for k in ["explain", "result", "parinaam", "samjhao", "score", "prediction", "mera result"]):
        reply = explain_screening_context(screening_context, language="hi" if is_hi else "en")
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is Grad-CAM?", "Next Step", "Why Rejected?"],
            "context_used": bool(screening_context and any(screening_context.values())),
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 3. "Why Rejected?" / Image Quality Help
    if any(k in msg_clean for k in ["reject", "quality", "blur", "dark", "bright", "asweekrit", "kharaab", "asafal"]):
        if is_hi:
            reply = (
                "छवि अस्वीकृत होने के मुख्य कारण हो सकते हैं:\n"
                "1. गैर-रेटिना फोटो (उदा. बाहरी आंख या अन्य वस्तु)\n"
                "2. धुंधली छवि (Blur / Sharpness < 15)\n"
                "3. बहुत अंधेरी या बहुत चमकीली छवि (Underexposed / Overexposed)\n"
                "4. कम रिज़ॉल्यूशन (< 224x224)\n\n"
                "समाधान: पुतली को केंद्रित रखें, कमरे की रोशनी कम करें, और कैमरे को स्थिर रखकर स्पष्ट फंडस स्कैन लें।"
            )
        else:
            reply = (
                "An image may be rejected by the validation gate due to:\n"
                "1. Non-retinal image (e.g. external eye or non-fundus photo)\n"
                "2. Blurriness (Laplacian variance sharpness < 15)\n"
                "3. Overexposure or underexposure (mean brightness outside 25-180)\n"
                "4. Resolution below 224x224 pixels.\n\n"
                "Tip: Ensure the patient's pupil is centered, dim ambient lighting, steady the camera, and re-capture."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["How to Use?", "What is Safety Gate?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 4. "What is Grad-CAM?"
    if any(k in msg_clean for k in ["gradcam", "grad-cam", "heatmap", "overlay", "visualization", "rang"]):
        if is_hi:
            reply = (
                "Grad-CAM (Gradient-weighted Class Activation Mapping) एक विज़ुअलाइज़ेशन तकनीक है "
                "जो फंडस छवि के उन हिस्सों को रंगीन हीटमैप (Heatmap) के रूप में दिखाती है जिन पर एआई मॉडल ने अपना ध्यान केंद्रित किया।\n\n"
                "महत्वपूर्ण: यह मॉडल के निर्णय व्यवहार को समझाता है और यह पुष्ट चिकित्सीय घाव (Lesions) नहीं हैं।"
            )
        else:
            reply = (
                "Grad-CAM (Gradient-weighted Class Activation Mapping) is an explainability technique "
                "that visualizes which regions of the fundus image the AI model focused on when making its prediction.\n\n"
                "Important Note: Grad-CAM explains model attention patterns and is not a definitive clinical lesion detector."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Explain My Result", "What is Safety Gate?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 5. "What is Safety Gate?"
    if any(k in msg_clean for k in ["safety gate", "safety", "suraksha", "gate"]):
        if is_hi:
            reply = (
                "AI Safety Gate एक दो-स्तरीय सुरक्षा जांच है जो मॉडल भविष्यवाणी से पहले चलती है:\n"
                "1. रेटिना सत्यापन: यह जांचता है कि अपलोड की गई छवि वास्तव में एक फंडस स्कैन है।\n"
                "2. गुणवत्ता जांच: यह शार्पनेस और ब्राइटनेस मापता है।\n\n"
                "यदि छवि असुरक्षित या अस्पष्ट है, तो मॉडल गलत अनुमान से बचने के लिए अनुमान को सुरक्षित रूप से रोक देता है।"
            )
        else:
            reply = (
                "The AI Safety Gate is a pre-inference clinical safety layer with two stages:\n"
                "1. Retinal Domain Validation: Verifies that the upload is an authentic retinal fundus scan.\n"
                "2. Image Quality Gate: Checks sharpness, illumination, and visible coverage.\n\n"
                "If the image fails, model inference is blocked to prevent hallucinated predictions."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Why Rejected?", "How to Use?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 6. "Next Step" / Referral Guidance
    if any(k in msg_clean for k in ["next step", "agla kadam", "referral", "kya karein", "what to do"]):
        if screening_context and screening_context.get("referral_priority"):
            ref = screening_context.get("referral_priority")
            risk = screening_context.get("risk_category", "MODERATE")
            if is_hi:
                reply = f"वर्तमान स्क्रीनिंग परिणाम के अनुसार रेफरल प्राथमिकता '{ref}' और जोखिम स्तर '{risk}' है। कृपया स्थानीय क्लिनिकल प्रोटोकॉल के अनुसार आगे की कार्रवाई करें।"
            else:
                reply = f"Based on the current screening result, the referral priority is '{ref}' with a risk level of '{risk}'. Please follow local protocol for tele-ophthalmology referral or patient counseling."
        else:
            if is_hi:
                reply = (
                    "स्क्रीनिंग के बाद के सामान्य कदम:\n"
                    "1. Low Risk (No DR): 1 वर्ष में नियमित अनुवर्ती जांच की सलाह दें।\n"
                    "2. Moderate Risk (Mild/Moderate): 1 महीने के भीतर नेत्र विशेषज्ञ को रेफर करें।\n"
                    "3. High Risk (Severe/PDR): प्राथमिकता के साथ 1-2 सप्ताह में विशेषज्ञ समीक्षा कराएं।\n"
                    "4. Unable to Assess: स्पष्ट छवि पुनः लें।"
                )
            else:
                reply = (
                    "Standard post-screening steps:\n"
                    "1. Low Risk (No DR): Counsel patient for annual rescreening.\n"
                    "2. Moderate Risk (Mild/Moderate NPDR): Eye specialist review recommended within 1 month.\n"
                    "3. High Risk (Severe/PDR): Priority specialist review recommended within 1-2 weeks.\n"
                    "4. Unable to Assess: Re-capture clear fundus image."
                )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Explain My Result", "How to Use?"],
            "context_used": bool(screening_context),
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 7. "How to Use?" / General Screening Flow
    if any(k in msg_clean for k in ["how to use", "guide", "madad", "kaise use", "upload", "shuru", "help"]):
        if is_hi:
            reply = (
                "MADOCS स्क्रीनिंग प्रक्रिया के सरल चरण:\n"
                "चरण 1: 'New Screening' में मरीज की जानकारी दर्ज करें।\n"
                "चरण 2: Right Eye (दाहिनी आंख) और Left Eye (बाईं आंख) की फंडस छवियां अपलोड करें।\n"
                "चरण 3: AI Safety Gate गुणवत्ता की पुष्टि करेगा।\n"
                "चरण 4: 'Start AI Screening' पर क्लिक करें।\n"
                "चरण 5: परिणाम, Grad-CAM हीटमैप और रेफरल प्राथमिकता की समीक्षा करें।"
            )
        else:
            reply = (
                "Simple steps to use MADOCS screening:\n"
                "Step 1: Register patient in 'New Screening'.\n"
                "Step 2: Upload Right Eye (OD) and Left Eye (OS) fundus images.\n"
                "Step 3: The AI Safety Gate validates image quality.\n"
                "Step 4: Click 'Start AI Screening' to run classification.\n"
                "Step 5: Review prediction, Grad-CAM attention heatmap, and referral recommendation."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Explain My Result", "Why Rejected?", "What is Grad-CAM?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 8. Default Greeting / Friendly Fallback
    if is_hi:
        reply = (
            "नमस्ते! मैं मैडॉक्स (MADOCS) स्क्रीनिंग सहायक हूँ। "
            "मैं रेटिना छवि अपलोड करने, AI Safety Gate, Grad-CAM हीटमैप और स्क्रीनिंग परिणामों को समझने में आपकी सहायता कर सकता हूँ। "
            "नीचे दिए गए बटनों में से किसी एक को चुनें या अपना प्रश्न लिखें।"
        )
    else:
        reply = (
            "Hi! I'm the MADOCS Screening Assistant. "
            "I can help you capture retinal images, navigate the AI Safety Gate, interpret Grad-CAM visualizations, and understand your screening results. "
            "You can choose a quick action below or ask a question."
        )

    return {
        "reply": reply,
        "language": "hi" if is_hi else "en",
        "suggested_actions": ["How to Use?", "Explain My Result", "What is Grad-CAM?", "Why Rejected?"],
        "context_used": False,
        "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
    }
