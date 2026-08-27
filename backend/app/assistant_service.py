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

    # Phase 10 Longitudinal Intelligence Queries
    # 1. "What changed from the previous screening?"
    if any(k in msg_clean for k in ["what changed from the previous screening", "what changed from previous", "previous screening se kya badla", "kya badla", "पिछली स्क्रीनिंग से क्या बदला", "क्या बदला"]):
        long_summary = (
            screening_context.get("classification_change_summary")
            if screening_context
            else None
        )
        long_summary_hi = (
            screening_context.get("classification_change_summary_hi")
            if screening_context
            else None
        )
        prev_pred = (
            screening_context.get("previous_prediction")
            or screening_context.get("previous_class_name")
            if screening_context
            else None
        )
        curr_pred = (
            screening_context.get("prediction")
            or screening_context.get("className")
            if screening_context
            else None
        )

        if is_hi:
            if long_summary_hi:
                reply = (
                    f"पिछली स्क्रीनिंग की तुलना:\n\n"
                    f"• {long_summary_hi}\n"
                    f"• ध्यान दें: इसे 'स्क्रीनिंग क्लासिफिकेशन में बदलाव' कहा जाता है, स्वतंत्र बीमारी की प्रगति नहीं।\n"
                    f"• इस बदलाव की पुष्टि और सही व्याख्या के लिए डॉक्टर की समीक्षा आवश्यक है।"
                )
            elif prev_pred and curr_pred:
                reply = (
                    f"पिछली स्क्रीनिंग की तुलना:\n\n"
                    f"• पिछली स्क्रीनिंग: {prev_pred}\n"
                    f"• वर्तमान स्क्रीनिंग: {curr_pred}\n"
                    f"• स्थिति: स्क्रीनिंग क्लासिफिकेशन में बदलाव दर्ज किया गया है। विस्तृत नैदानिक व्याख्या के लिए डॉक्टर समीक्षा की सलाह दी जाती है।"
                )
            else:
                reply = (
                    "वर्तमान सत्र में पिछली स्क्रीनिंग का विवरण उपलब्ध नहीं है। "
                    "यदि इस मरीज की पुरानी जांच मौजूद है, तो डॉक्टर पोर्टल या पेशेंट रिपोर्ट में 'पिछली स्क्रीनिंग से तुलना करें' पर जाकर दोनों परिणामों की साथ-साथ तुलना देख सकते हैं।"
                )
        else:
            if long_summary:
                reply = (
                    f"Comparison with previous screening:\n\n"
                    f"• {long_summary}\n"
                    f"• Notice: This is categorized as a 'Screening Classification Change', not an autonomous diagnosis of disease progression.\n"
                    f"• Doctor review is recommended to interpret this change."
                )
            elif prev_pred and curr_pred:
                reply = (
                    f"Comparison with previous screening:\n\n"
                    f"• Previous Screening: {prev_pred}\n"
                    f"• Current Screening: {curr_pred}\n"
                    f"• Status: AI screening classification change recorded. Clinical doctor review is recommended to interpret this observation."
                )
            else:
                reply = (
                    "Previous screening history is not attached to the active session. "
                    "When previous records exist for the patient, you can select 'Compare With Previous Screening' in the Doctor Portal or Patient Report to inspect chronological side-by-side changes."
                )

        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Why is this not called disease progression?", "Why is doctor review needed?", "What does unchanged mean?"],
            "context_used": bool(long_summary or (prev_pred and curr_pred)),
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 2. "Why is this not called disease progression?" (Phase 10 Medical Safety)
    if any(k in msg_clean for k in ["why is this not called disease progression", "why not disease progression", "disease progression kyun nahi", "बीमारी की प्रगति क्यों नहीं", "रोग की प्रगति क्यों नहीं"]):
        if is_hi:
            reply = (
                "इसे 'बीमारी की प्रगति' (Disease Progression) क्यों नहीं कहा जाता:\n\n"
                "1. एआई मॉडल स्वतंत्र रूप से प्रत्येक छवि का एकल-दौरा (Single-Visit) वर्गीकरण करता है।\n"
                "2. छवि कोण, प्रकाश, या पुतली के फैलाव में मामूली अंतर से एआई स्कोर में थोड़ा अंतर आ सकता है।\n"
                "3. वास्तविक जैविक बीमारी की प्रगति केवल एक योग्य नेत्र विशेषज्ञ (Ophthalmologist) द्वारा संपूर्ण नैदानिक इतिहास और स्लिट-लैंप जांच के बाद ही स्थापित की जा सकती है।\n\n"
                "चिकित्सीय सुरक्षा के लिए हम इसे 'स्क्रीनिंग क्लासिफिकेशन में बदलाव' (Screening Classification Change) कहते हैं।"
            )
        else:
            reply = (
                "Why this is labeled 'Screening Classification Change' instead of 'Disease Progression':\n\n"
                "1. The AI model evaluates single-visit retinal image patterns independently without an autonomous longitudinal biophysical model.\n"
                "2. Slight variations in image illumination, camera field angle, or pupil dilation can produce classification differences between visits.\n"
                "3. True biological disease progression requires comprehensive clinical correlation, optical coherence tomography (OCT), or biomicroscopy by an ophthalmologist.\n\n"
                "Clinical Safety Standard: We strictly avoid claiming autonomous disease progression and recommend specialist review."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What changed from the previous screening?", "Why is doctor review needed?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 3. "What does unchanged mean?" (Phase 10)
    if any(k in msg_clean for k in ["what does unchanged mean", "unchanged ka matlab", "unchanged mean", "अपरिवर्तित का क्या अर्थ", "कोई बदलाव नहीं का क्या मतलब", "अपरिवर्तित का मतलब"]):
        if is_hi:
            reply = (
                "'अपरिवर्तित' (Unchanged) का अर्थ:\n\n"
                "• इसका अर्थ है कि वर्तमान और पिछली स्क्रीनिंग में एआई मॉडल ने एक ही डायबिटिक रेटिनोपैथी गंभीरता ग्रेड (उदा. दोनों बार Mild NPDR या दोनों बार No DR) का अनुमान लगाया है।\n"
                "• यह रेटिना की स्थिरता का सांख्यिकीय संकेत देता है, लेकिन मरीज को निर्धारित अंतराल पर नियमित नेत्र जांच जारी रखनी चाहिए।"
            )
        else:
            reply = (
                "Meaning of 'Unchanged' status:\n\n"
                "• It indicates that the AI screening model assigned the exact same ICDR diabetic retinopathy severity grade across both visits (e.g. Mild NPDR on both screenings).\n"
                "• This points to stable feature patterns between screenings, but does not eliminate the need for periodic clinical ophthalmic follow-ups."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What changed from the previous screening?", "How can I compare two screenings?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 4. "How can I compare two screenings?" (Phase 10)
    if any(k in msg_clean for k in ["how can i compare two screenings", "how to compare screenings", "compare two screenings", "screenings ki tulna kaise karein", "तुलना कैसे करें", "दो स्क्रीनिंग की तुलना"]):
        if is_hi:
            reply = (
                "दो स्क्रीनिंग की तुलना करने का तरीका:\n\n"
                "1. डॉक्टर पोर्टल (Doctor Portal) या पेशेंट प्रोफाइल में मरीज का चयन करें।\n"
                "2. 'स्क्रीनिंग इतिहास' (Screening History) या 'लॉन्गिट्यूडनल तुलना' (Longitudinal Overview) सेक्शन खोलें।\n"
                "3. सिस्टम स्वचालित रूप से सबसे हालिया तुलनीय स्क्रीनिंग का चयन करेगा, या आप ड्रॉपडाउन से कोई भी पिछली तारीख चुन सकते हैं।\n"
                "4. आप पिछली और वर्तमान फंडस फोटो, Grad-CAM हीटमैप, क्लासिफिकेशन में बदलाव, और डॉक्टर समीक्षा की साथ-साथ तुलना देख सकते हैं।"
            )
        else:
            reply = (
                "How to compare two screenings in MADOCS:\n\n"
                "1. Select the patient in the Doctor Portal, Screening History, or Patient Report.\n"
                "2. Open the 'Longitudinal Screening Overview' or 'Compare With Previous Screening' panel.\n"
                "3. The system automatically selects the most recent valid comparable screening, or you can manually choose any historical visit from the dropdown.\n"
                "4. Review side-by-side fundus images, Grad-CAM attention maps, DR classifications, confidence levels, and doctor verification notes."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What changed from the previous screening?", "Why is this not called disease progression?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 2. "Explain My Result" / "Why did AI give this result?"
    if any(k in msg_clean for k in ["explain", "result", "parinaam", "samjhao", "score", "prediction", "mera result", "why did ai give", "परिणाम", "रिजल्ट", "समझाओ", "क्यों दिया"]):
        reply = explain_screening_context(screening_context, language="hi" if is_hi else "en")
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is Grad-CAM?", "Next Step", "Why Rejected?"],
            "context_used": bool(screening_context and any(screening_context.values())),
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 3. "Why Rejected?" / Image Quality Help
    if any(k in msg_clean for k in ["reject", "quality", "blur", "dark", "bright", "asweekrit", "kharaab", "asafal", "अस्वीकृत", "गुणवत्ता", "खराब"]):
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

    # 4. "Difference between AI confidence and lesion confidence?" (Phase 9)
    if any(k in msg_clean for k in ["difference between ai confidence and lesion confidence", "confidence me antar", "घाव कॉन्फिडेंस में क्या अंतर", "कॉन्फिडेंस में क्या अंतर", "ai confidence vs lesion confidence", "confidence difference"]):
        if is_hi:
            reply = (
                "एआई वर्गीकरण कॉन्फिडेंस और घाव कॉन्फिडेंस में अंतर:\n\n"
                "1. एआई वर्गीकरण कॉन्फिडेंस: पूरे रेटिना स्कैन के आधार पर निर्धारित डीआर ग्रेड (उदा. Moderate NPDR) की समग्र सांख्यिकीय निश्चितता (उदा. 85%)।\n"
                "2. घाव कॉन्फिडेंस: किसी विशिष्ट घाव (उदा. माइक्रोएन्यूरिज्म) के व्यक्तिगत अस्तित्व की संभावना (उदा. 78%)।\n\n"
                "सुरक्षा नियम: MADOCS इन दोनों को कभी आपस में नहीं मिलाता।"
            )
        else:
            reply = (
                "Difference between AI Classification Confidence and Lesion Confidence:\n\n"
                "1. AI Classification Confidence: Statistical certainty across global image feature vectors for the whole DR grade (e.g. 85.0% for Moderate NPDR).\n"
                "2. Lesion Confidence: Individual probability score for a specific detected lesion entity (e.g. 78% for a localized microaneurysm).\n\n"
                "Clinical Safety Rule: MADOCS strictly separates these two and never merges them into a single opaque number."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What does confidence mean?", "What is lesion analysis?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 5. "What does confidence mean?" (Phase 8)
    if any(k in msg_clean for k in ["confidence mean", "confidence ka matlab", "what is confidence", "bharosa star", "model confidence", "कॉन्फिडेंस का क्या अर्थ", "भरोसा स्तर"]):
        if is_hi:
            reply = (
                "मॉडल कॉन्फिडेंस (Model Confidence) यह दर्शाता है कि एआई मॉडल अपने सांख्यिकीय पैटर्न पहचान में कितना आश्वस्त है।\n\n"
                "• उच्च कॉन्फिडेंस (≥85%): मॉडल के आंतरिक निर्णय अत्यधिक सुसंगत हैं।\n"
                "• मध्यम कॉन्फिडेंस (60-84%): मानक निर्णय समर्थन स्तर।\n"
                "• कम कॉन्फिडेंस (<60%): सीमा से कम; विशेषज्ञ डॉक्टर सत्यापन आवश्यक।\n\n"
                "महत्वपूर्ण: कॉन्फिडेंस सांख्यिकीय सहमति दर्शाता है, चिकित्सीय निश्चितता नहीं।"
            )
        else:
            reply = (
                "Model confidence represents the AI's internal statistical agreement over recognized retinal features.\n\n"
                "• High Confidence (≥85%): Strong feature agreement and consistent pattern matching.\n"
                "• Moderate Confidence (60-84%): Standard decision-support confidence.\n"
                "• Low Confidence (<60%): Below threshold; clinical review or re-capture required.\n\n"
                "Important: Confidence reflects statistical pattern agreement, not diagnostic certainty."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Why did AI give this result?", "Why is doctor review recommended?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 6. "Why is lesion analysis unavailable?" (Phase 9)
    if any(k in msg_clean for k in ["why is lesion analysis unavailable", "lesion analysis unavailable kyun", "घाव विश्लेषण क्यों उपलब्ध नहीं", "घाव विश्लेषण अनुपलब्ध क्यों", "घाव विश्लेषण अनुपलब्ध", "lesion unavailable"]):
        if is_hi:
            reply = (
                "घाव विश्लेषण (Lesion Analysis) इसलिए अनुपलब्ध है क्योंकि MADOCS में वर्तमान में केवल 5-क्लास डीआर क्लासिफायर (EfficientNet-B0) और Grad-CAM उपलब्ध है।\n\n"
                "• चिकित्सीय सुरक्षा के नियम के तहत हम कोई भी काल्पनिक या अनसत्यापित घाव डेटा नहीं दिखाते।\n"
                "• भविष्य में जब पूरी तरह से मान्य घाव मॉडल एकीकृत होगा, तब यह स्वतः सक्रिय हो जाएगा।"
            )
        else:
            reply = (
                "Lesion analysis is marked unavailable because MADOCS currently operates a validated 5-class DR classifier (dr_model.pth) and Grad-CAM saliency mapping.\n\n"
                "• Strict Clinical Safety: We refuse to fabricate fake lesion detections or invent counts when a dedicated lesion detector is not loaded.\n"
                "• The architecture is designed to seamlessly integrate a validated lesion model in future updates."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is lesion analysis?", "What does the Grad-CAM overlay mean?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 7. "What is Lesion Analysis?" (Phase 9)
    if any(k in msg_clean for k in ["what is lesion analysis", "lesion analysis kya", "घाव विश्लेषण", "असामान्य हिस्सों की जांच", "lesion analysis"]):
        if is_hi:
            reply = (
                "घाव विश्लेषण (Lesion Intelligence) रेटिना में विशिष्ट पैथोलॉजिकल विकृतियों (जैसे माइक्रोएन्यूरिज्म, रक्तस्राव, हार्ड एक्सयूडेट्स) का पता लगाने और उनका मानचित्रण करने की तकनीक है।\n\n"
                "• स्थिति: MADOCS में वर्तमान में केवल 5-स्तरीय डीआर वर्गीकरण और Grad-CAM सक्रिय है; समर्पित घाव डिटेक्टर मॉडल स्टैंडबाय पर है।\n"
                "• सुरक्षा: सिस्टम कोई भी नकली घाव पहचान या कृत्रिम आंकड़े नहीं दिखाता।"
            )
        else:
            reply = (
                "Lesion analysis refers to the dedicated detection and segmentation of specific retinal microvascular abnormalities (such as microaneurysms, dot/blot hemorrhages, hard exudates, and cotton-wool spots).\n\n"
                "• Status in MADOCS: Currently, whole-image EfficientNet-B0 DR classification and Grad-CAM are active. A dedicated lesion segmentation model is not yet connected.\n"
                "• Clinical Safety: MADOCS never generates fake lesion counts or fabricated detections."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is the difference between Grad-CAM and lesion detection?", "Why is lesion analysis unavailable?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 5. "Why is doctor review recommended?" (Phase 8)
    if any(k in msg_clean for k in ["why is doctor review", "doctor review recommended", "doctor ki samiksha kyun", "doctor review kyun", "डॉक्टर समीक्षा", "समीक्षा क्यों"]):
        ref = screening_context.get("referral_priority") if screening_context else None
        risk = screening_context.get("risk_category") if screening_context else None
        pred = screening_context.get("prediction") or screening_context.get("className") if screening_context else None

        if is_hi:
            reply = (
                f"डॉक्टर समीक्षा की सिफारिश इसलिए की गई है क्योंकि एआई एक स्क्रीनिंग समर्थन प्रणाली है। "
                f"{f'वर्तमान केस में {pred} (जोखिम: {risk}) का अनुमान लगाया गया है। ' if pred else ''}"
                "डायबिटिक रेटिनोपैथी के पुष्ट निदान और उपचार योजना (लेजर/दवा) के लिए नेत्र रोग विशेषज्ञ द्वारा स्लिट-लैंप और फंडस जांच आवश्यक है।"
            )
        else:
            reply = (
                f"Doctor review is recommended because MADOCS is an AI-assisted screening tool, not a diagnostic authority. "
                f"{f'The current scan was classified as {pred} ({risk} risk). ' if pred else ''}"
                "An ophthalmologist must perform biomicroscopy and dilated examination to verify findings and determine clinical management."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["Why did AI give this result?", "What does Grad-CAM show?"],
            "context_used": bool(screening_context),
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 6. "What happens after re-capture?" (Phase 8)
    if any(k in msg_clean for k in ["after re-capture", "after recapture", "recapture ke baad", "re-capture ke baad", "dobara photo ke baad", "री-कैप्चर", "दोबारा फोटो"]):
        if is_hi:
            reply = (
                "इमेज री-कैप्चर (Re-capture) के बाद की प्रक्रिया:\n"
                "1. स्वास्थ्य कार्यकर्ता नई, स्पष्ट फंडस छवि अपलोड करेंगे।\n"
                "2. AI Safety Gate नई छवि की गुणवत्ता (शार्पनेस/प्रकाश) की दोबारा पुष्टि करेगा।\n"
                "3. नया एआई स्क्रीनिंग विश्लेषण और Grad-CAM हीटमैप जनरेट होगा।\n"
                "4. पिछला परिणाम ऐतिहासिक डेटा (Historical AI Result) के रूप में सुरक्षित रहेगा और डॉक्टर नए स्कैन की समीक्षा करेंगे।"
            )
        else:
            reply = (
                "What happens after an image re-capture:\n"
                "1. The health worker captures and uploads a clearer fundus photograph.\n"
                "2. The AI Safety Gate automatically re-evaluates sharpness and illumination.\n"
                "3. Fresh model inference and Grad-CAM attention maps are computed.\n"
                "4. Previous AI findings are preserved as historical baseline data, and the reviewing doctor is notified of the updated scan."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["How to Use?", "Why Rejected?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 7. "What is Lesion Analysis?" (Phase 9)
    if any(k in msg_clean for k in ["what is lesion analysis", "lesion analysis kya", "घाव विश्लेषण", "असामान्य हिस्सों", "lesion analysis"]):
        if is_hi:
            reply = (
                "घाव विश्लेषण (Lesion Intelligence) रेटिना में विशिष्ट पैथोलॉजिकल विकृतियों (जैसे माइक्रोएन्यूरिज्म, रक्तस्राव, हार्ड एक्सयूडेट्स) का पता लगाने और उनका मानचित्रण करने की तकनीक है।\n\n"
                "• स्थिति: MADOCS में वर्तमान में केवल 5-स्तरीय डीआर वर्गीकरण और Grad-CAM सक्रिय है; समर्पित घाव डिटेक्टर मॉडल स्टैंडबाय पर है।\n"
                "• सुरक्षा: सिस्टम कोई भी नकली घाव पहचान या कृत्रिम आंकड़े नहीं दिखाता।"
            )
        else:
            reply = (
                "Lesion analysis refers to the dedicated detection and segmentation of specific retinal microvascular abnormalities (such as microaneurysms, dot/blot hemorrhages, hard exudates, and cotton-wool spots).\n\n"
                "• Status in MADOCS: Currently, whole-image EfficientNet-B0 DR classification and Grad-CAM are active. A dedicated lesion segmentation model is not yet connected.\n"
                "• Clinical Safety: MADOCS never generates fake lesion counts or fabricated detections."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is the difference between Grad-CAM and lesion detection?", "Why is lesion analysis unavailable?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 8. "Difference between Grad-CAM and lesion detection?" (Phase 9)
    if any(k in msg_clean for k in ["difference between grad-cam and lesion", "difference between gradcam and lesion", "grad-cam aur lesion me antar", "घाव पहचान में क्या अंतर", "gradcam vs lesion", "अंतर क्या है"]):
        if is_hi:
            reply = (
                "Grad-CAM और घाव पहचान में मूलभूत अंतर:\n\n"
                "1. Grad-CAM (मॉडल ध्यान): यह दिखाता है कि एआई ने पूरे रेटिना में किन क्षेत्रों को देखकर अपना डीआर ग्रेड निर्णय लिया (कंप्यूटेशनल अटेंशन)। यह घाव डिटेक्टर नहीं है।\n"
                "2. घाव पहचान (Lesion Detection): यह सीधे विशिष्ट घावों (जैसे माइक्रोएन्यूरिज्म) की गिनती और बाउंडिंग बॉक्स/मास्क तैयार करता है।\n\n"
                "महत्वपूर्ण: Grad-CAM के रंगीन क्षेत्रों को पुष्ट नैदानिक घाव नहीं माना जाना चाहिए।"
            )
        else:
            reply = (
                "Key differences between Grad-CAM and Lesion Detection:\n\n"
                "1. Grad-CAM (Model Attention): Visualizes which image regions contributed mathematically to the EfficientNet-B0 classification. It explains model behavior, not pathological diagnosis.\n"
                "2. Lesion Detection: Explicitly segments and counts individual clinical entities (e.g. microaneurysms, hemorrhages).\n\n"
                "Important: Grad-CAM attention regions must never be interpreted as confirmed clinical lesions."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What does the Grad-CAM overlay mean?", "What is the difference between AI confidence and lesion confidence?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 9. "Why is lesion analysis unavailable?" (Phase 9)
    if any(k in msg_clean for k in ["why is lesion analysis unavailable", "lesion analysis unavailable kyun", "घाव विश्लेषण क्यों उपलब्ध नहीं", "घाव विश्लेषण अनुपलब्ध", "lesion unavailable"]):
        if is_hi:
            reply = (
                "घाव विश्लेषण (Lesion Analysis) इसलिए अनुपलब्ध है क्योंकि MADOCS में वर्तमान में केवल 5-क्लास डीआर क्लासिफायर (EfficientNet-B0) और Grad-CAM उपलब्ध है।\n\n"
                "• चिकित्सीय सुरक्षा के नियम के तहत हम कोई भी काल्पनिक या अनसत्यापित घाव डेटा नहीं दिखाते।\n"
                "• भविष्य में जब पूरी तरह से मान्य घाव मॉडल एकीकृत होगा, तब यह स्वतः सक्रिय हो जाएगा।"
            )
        else:
            reply = (
                "Lesion analysis is marked unavailable because MADOCS currently operates a validated 5-class DR classifier (dr_model.pth) and Grad-CAM saliency mapping.\n\n"
                "• Strict Clinical Safety: We refuse to fabricate fake lesion detections or invent counts when a dedicated lesion detector is not loaded.\n"
                "• The architecture is designed to seamlessly integrate a validated lesion model in future updates."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is lesion analysis?", "What does the Grad-CAM overlay mean?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 10. "What does the Grad-CAM overlay mean?" (Phase 9)
    if any(k in msg_clean for k in ["what does the grad-cam overlay mean", "overlay mean", "overlay ka matlab", "ओवरले का क्या मतलब", "grad-cam ओवरले", "what does grad-cam show", "grad-cam kya dikhata"]):
        if is_hi:
            reply = (
                "Grad-CAM ओवरले का अर्थ:\n\n"
                "• यह फंडस फोटो के ऊपर 40% डिफ़ॉल्ट पारदर्शिता पर एक रंगीन हीटमैप प्रदर्शित करता है।\n"
                "• लाल और पीले रंग के क्षेत्र यह दर्शाते हैं कि एआई मॉडल ने डीआर ग्रेड का अनुमान लगाते समय किन रेटिना संरचनाओं पर सबसे अधिक ध्यान दिया।\n"
                "• यह मूल रेटिना रक्त वाहिकाओं को स्पष्ट रखता है ताकि नेत्र विशेषज्ञ इसका निष्पक्ष मूल्यांकन कर सकें।"
            )
        else:
            reply = (
                "The Grad-CAM overlay meaning:\n\n"
                "• It superimposes a 40% default opacity saliency heatmap directly onto the original fundus photograph.\n"
                "• Warm zones (red/yellow) indicate highest computational weight in the neural network's decision.\n"
                "• The overlay is calibrated so natural retinal vessels and optic disc remain clearly visible for clinical review."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What is the difference between Grad-CAM and lesion detection?", "What is the difference between AI confidence and lesion confidence?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 11. "Difference between AI confidence and lesion confidence?" (Phase 9)
    if any(k in msg_clean for k in ["difference between ai confidence and lesion confidence", "confidence me antar", "घाव कॉन्फिडेंस में क्या अंतर", "कॉन्फिडेंस में क्या अंतर", "ai confidence vs lesion confidence"]):
        if is_hi:
            reply = (
                "एआई वर्गीकरण कॉन्फिडेंस और घाव कॉन्फिडेंस में अंतर:\n\n"
                "1. एआई वर्गीकरण कॉन्फिडेंस: पूरे रेटिना स्कैन के आधार पर निर्धारित डीआर ग्रेड (उदा. Moderate NPDR) की समग्र सांख्यिकीय निश्चितता (उदा. 85%)।\n"
                "2. घाव कॉन्फिडेंस: किसी विशिष्ट घाव (उदा. माइक्रोएन्यूरिज्म) के व्यक्तिगत अस्तित्व की संभावना (उदा. 78%)।\n\n"
                "सुरक्षा नियम: MADOCS इन दोनों को कभी आपस में नहीं मिलाता।"
            )
        else:
            reply = (
                "Difference between AI Classification Confidence and Lesion Confidence:\n\n"
                "1. AI Classification Confidence: Statistical certainty across global image feature vectors for the whole DR grade (e.g. 85.0% for Moderate NPDR).\n"
                "2. Lesion Confidence: Individual probability score for a specific detected lesion entity (e.g. 78% for a localized microaneurysm).\n\n"
                "Clinical Safety Rule: MADOCS strictly separates these two and never merges them into a single opaque number."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What does confidence mean?", "What is lesion analysis?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 12. "What is Grad-CAM?" (General)
    if any(k in msg_clean for k in ["gradcam", "grad-cam", "heatmap", "overlay", "visualization", "rang", "हीटमैप", "दिखाता है"]):
        if is_hi:
            reply = (
                "Grad-CAM (Gradient-weighted Class Activation Mapping) एआई का व्याख्यात्मक विज़ुअलाइज़ेशन है:\n\n"
                "• यह फंडस फोटो के उन हिस्सों को रंगीन हीटमैप (40% डिफ़ॉल्ट पारदर्शिता) के रूप में दिखाता है जिन्होंने एआई निर्णय को सबसे ज्यादा प्रभावित किया।\n"
                "• महत्वपूर्ण: यह मॉडल के ध्यान क्षेत्र (Model Attention) को दर्शाता है और यह पुष्ट चिकित्सीय घाव (Lesions) नहीं हैं।"
            )
        else:
            reply = (
                "Grad-CAM (Gradient-weighted Class Activation Mapping) is an explainability visualizer:\n\n"
                "• It renders a transparent activation heatmap (40% default opacity) highlighting image regions that contributed most to the AI model's prediction.\n"
                "• Important: Grad-CAM shows computational model attention and does NOT represent confirmed clinical lesions."
            )
        return {
            "reply": reply,
            "language": "hi" if is_hi else "en",
            "suggested_actions": ["What does confidence mean?", "Why is doctor review recommended?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 8. "What is Safety Gate?"
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

    # 9. "Next Step" / Referral Guidance
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

    # 10. "How to Use?" / General Screening Flow
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
            "suggested_actions": ["Why did AI give this result?", "What is Grad-CAM?", "Why Rejected?"],
            "context_used": False,
            "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
        }

    # 11. Default Greeting / Friendly Fallback
    if is_hi:
        reply = (
            "नमस्ते! मैं मैडॉक्स (MADOCS) क्लिनिकल एविडेंस एवं स्क्रीनिंग सहायक हूँ। "
            "मैं एआई क्लिनिकल साक्ष्य, मॉडल कॉन्फिडेंस, Grad-CAM ध्यान क्षेत्र और डॉक्टर समीक्षा को समझने में आपकी सहायता कर सकता हूँ। "
            "नीचे दिए गए बटनों में से किसी एक को चुनें या अपना प्रश्न लिखें।"
        )
    else:
        reply = (
            "Hi! I'm the MADOCS Clinical Evidence & Safety Intelligence Assistant. "
            "I can help you understand AI clinical evidence, model confidence interpretations, Grad-CAM attention regions, and doctor review guidance. "
            "You can choose a quick action below or ask a question."
        )

    return {
        "reply": reply,
        "language": "hi" if is_hi else "en",
        "suggested_actions": [
            "Why did AI give this result?",
            "What does confidence mean?",
            "Why is doctor review recommended?",
            "What does Grad-CAM show?",
            "What happens after re-capture?",
        ],
        "context_used": False,
        "disclaimer": DISCLAIMER_HI if is_hi else DISCLAIMER_EN,
    }
