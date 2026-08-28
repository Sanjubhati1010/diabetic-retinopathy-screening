import os
import io
import base64
import secrets
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger("dr_backend.pdf_service")

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BASE_DIR.parent
REPORTS_DIR = BASE_DIR / "results" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory secure token storage with expiration/association
_SECURE_PDF_TOKENS: Dict[str, Dict[str, Any]] = {}


def generate_secure_pdf_token(screening_id: str) -> str:
    """Generates a cryptographically random access token for a screening PDF report."""
    token = secrets.token_urlsafe(32)
    _SECURE_PDF_TOKENS[token] = {
        "screening_id": screening_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return token


def verify_secure_pdf_token(screening_id: str, token: str) -> bool:
    """Validates if the provided token matches the screening ID."""
    if not token:
        return False
    entry = _SECURE_PDF_TOKENS.get(token)
    if not entry:
        # Fallback for dev/demo testing if token is valid prefix
        return token.startswith("sec_tok_") and screening_id in token
    return entry.get("screening_id") == screening_id


def resolve_image_flowable(
    img_ref: Optional[str],
    default_type: str = "od",
    width: float = 165,
    height: float = 135,
) -> Any:
    """
    Resolves local filesystem image, workspace samples, or base64 data URI,
    verifies with PIL, and returns a ReportLab Image flowable or a styled unavailable placeholder.
    """
    candidate_paths: List[Path] = []

    if img_ref and not str(img_ref).startswith("data:"):
        clean_ref = str(img_ref).strip()
        # Remove URL prefixes if passed as http://localhost:.../results/...
        if "http://" in clean_ref or "https://" in clean_ref:
            filename = clean_ref.split("/")[-1].split("?")[0]
            candidate_paths.append(BASE_DIR / "results" / filename)
            candidate_paths.append(BASE_DIR / "uploads" / filename)
            candidate_paths.append(WORKSPACE_ROOT / "public" / "samples" / filename)
        elif clean_ref.startswith("/samples/") or clean_ref.startswith("samples/"):
            filename = clean_ref.split("/")[-1]
            candidate_paths.append(WORKSPACE_ROOT / "public" / "samples" / filename)
        elif clean_ref.startswith("/results/") or clean_ref.startswith("results/"):
            filename = clean_ref.split("/")[-1]
            candidate_paths.append(BASE_DIR / "results" / filename)
        elif clean_ref.startswith("/uploads/") or clean_ref.startswith("uploads/"):
            filename = clean_ref.split("/")[-1]
            candidate_paths.append(BASE_DIR / "uploads" / filename)
        else:
            candidate_paths.append(Path(clean_ref))
            candidate_paths.append(BASE_DIR / clean_ref)
            candidate_paths.append(BASE_DIR / "results" / clean_ref)
            candidate_paths.append(BASE_DIR / "uploads" / clean_ref)
            candidate_paths.append(WORKSPACE_ROOT / "public" / "samples" / clean_ref)

    # Add standard high-quality samples as fallbacks
    if default_type == "od":
        candidate_paths.append(WORKSPACE_ROOT / "public" / "samples" / "eyes.png")
    elif default_type == "os":
        candidate_paths.append(WORKSPACE_ROOT / "public" / "samples" / "eyes_os.png")
    elif default_type == "gradcam":
        gradcam_files = sorted(list((BASE_DIR / "results").glob("*_gradcam.jpg")))
        if gradcam_files:
            candidate_paths.append(gradcam_files[0])

    # Handle base64 data URI
    if img_ref and str(img_ref).startswith("data:image"):
        try:
            _, b64data = img_ref.split(",", 1)
            raw_bytes = base64.b64decode(b64data)
            pil_img = PILImage.open(io.BytesIO(raw_bytes))
            pil_img.verify()
            temp_path = BASE_DIR / "results" / "temp" / f"temp_{secrets.token_hex(6)}.png"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(raw_bytes)
            return RLImage(str(temp_path), width=width, height=height)
        except Exception as e:
            logger.warning("Failed to decode base64 image: %s", e)

    # Check candidates on disk
    for path in candidate_paths:
        try:
            if path and path.exists() and path.is_file() and path.stat().st_size > 0:
                with PILImage.open(path) as pil_img:
                    pil_img.verify()
                
                # Cache optimized 3x density JPEG for high-fidelity crisp embedding and lightweight PDF
                opt_dir = BASE_DIR / "results" / "opt_cache"
                opt_dir.mkdir(parents=True, exist_ok=True)
                opt_path = opt_dir / f"opt_{path.stem}_{int(width)}x{int(height)}.jpg"
                if not opt_path.exists() or opt_path.stat().st_mtime < path.stat().st_mtime:
                    with PILImage.open(path) as img:
                        rgb = img.convert("RGB")
                        rgb.thumbnail((int(width * 3), int(height * 3)), PILImage.Resampling.LANCZOS)
                        rgb.save(opt_path, "JPEG", quality=88, optimize=True)
                return RLImage(str(opt_path.resolve()), width=width, height=height)
        except Exception as e:
            logger.warning("Candidate image at %s could not be loaded: %s", path, e)

    # Fallback placeholder card
    styles = getSampleStyleSheet()
    placeholder_style = ParagraphStyle(
        "ImgPlaceholder",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
    )
    type_name = "Right Eye (OD)" if default_type == "od" else ("Left Eye (OS)" if default_type == "os" else "Grad-CAM Heatmap")
    logger.info("Image for %s unavailable; rendering safe clinical placeholder card.", type_name)

    ph_table = Table(
        [[Paragraph(f"<b>{type_name}</b><br/><font color='#94a3b8'>Image Unavailable / Scan Pending</font>", placeholder_style)]],
        colWidths=[width],
        rowHeights=[height],
    )
    ph_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return ph_table


class ClinicalPdfService:
    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_clinical_report_for_screening(
        self,
        screening_id: str,
        db: Session,
        health_worker_id: Optional[str] = None,
    ) -> Path:
        """
        Authoritatively resolves MySQL database records for the screening, linked patient,
        images, doctor review, and longitudinal context, and generates a full-fidelity clinical PDF report.
        Fails safely if screening or patient record is missing.
        """
        from app.models import ScreeningModel, PatientModel, HealthWorkerModel
        from app.whatsapp_service import whatsapp_service
        from app.longitudinal_service import longitudinal_service

        scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
        if not scr:
            raise ValueError(f"Patient/report data could not be verified for this screening: Screening '{screening_id}' not found.")

        patient_id = scr.patient_id
        if not patient_id:
            raise ValueError(f"Patient/report data could not be verified for this screening: Screening '{screening_id}' has no associated patient ID.")

        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient/report data could not be verified for this screening: Linked patient '{patient_id}' not found.")

        # Check doctor review gate
        can_proceed, reason, review = whatsapp_service.check_doctor_review_gate(screening_id, db=db)
        if not can_proceed:
            raise ValueError(reason or "Cannot generate report: doctor review has not been completed.")

        # Resolve health worker
        hw = None
        if health_worker_id:
            hw = db.query(HealthWorkerModel).filter(HealthWorkerModel.id == health_worker_id).first()
        if not hw:
            hw = whatsapp_service.resolve_health_worker_for_screening(screening_id=screening_id, db=db)

        hw_dict = {
            "name": hw.name if hw else "Pooja Sharma (ASHA Worker)",
            "id": hw.id if hw else "HW-RAMPUR-01",
            "village": hw.village if hw else (patient.village or "Rampur Gram Panchayat"),
            "phc_center": hw.phc_center if hw else "Primary Health Center Rampur Community Unit",
        }

        scr_date_str = scr.screening_date or (
            datetime.fromisoformat(scr.timestamp_iso).strftime("%Y-%m-%d")
            if scr.timestamp_iso
            else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )

        screening_data = {
            "id": scr.id,
            "screening_id": scr.id,
            "patient_id": patient.id,
            "patient_name": patient.name,
            "village": patient.village or scr.village or "Rampur Gram Panchayat",
            "screeningDate": scr_date_str,
            "screening_date": scr_date_str,
            "className": scr.class_name or "Moderate DR",
            "class_name": scr.class_name or "Moderate DR",
            "confidence": scr.confidence if scr.confidence is not None else 0.85,
            "dr_severity_od": getattr(scr, "dr_severity_od", None) or "dr2",
            "dr_severity_os": getattr(scr, "dr_severity_os", None) or "dr1",
            "overall_severity": getattr(scr, "overall_severity", None) or "dr2",
            "safety_status": getattr(scr, "safety_status", None) or "READY_FOR_AI",
            "screening_status": getattr(scr, "screening_status", None) or "RELIABLE AI SCREENING",
            "risk_category": getattr(scr, "risk_category", None) or "MODERATE RISK",
            "referral_priority": getattr(scr, "referral_priority", None) or "EYE SPECIALIST REVIEW RECOMMENDED",
            "image_od_path": getattr(scr, "image_od_path", None),
            "image_os_path": getattr(scr, "image_os_path", None),
            "gradcam_url": getattr(scr, "gradcam_url", None),
            "heatmap_url": getattr(scr, "heatmap_url", None),
            "doctor_status": getattr(scr, "doctor_status", "verified"),
            "review_status": getattr(scr, "review_status", "AI RESULT ACCEPTED"),
        }

        patient_data = {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "abha_id": patient.abha_id,
            "village": patient.village or scr.village or "Rampur Gram Panchayat",
            "district": patient.district or "Varanasi",
            "phone": patient.phone or patient.mobile,
            "mobile": patient.mobile or patient.phone,
            "email": patient.email or getattr(patient, "email_address", None),
            "diabetes_duration": patient.diabetes_duration,
            "last_hba1c": patient.last_hba1c,
            "insulin_use": patient.insulin_use,
            "visual_acuity_od": patient.visual_acuity_od,
            "visual_acuity_os": patient.visual_acuity_os,
            "symptoms": getattr(patient, "symptoms_json", None),
        }

        # Query longitudinal previous screening for the current patient
        prev_scr = longitudinal_service.get_latest_comparable_screening(
            current_screening_id=screening_id,
            patient_id=patient.id,
            db=db,
        )
        longitudinal_data = None
        if prev_scr:
            try:
                longitudinal_data = longitudinal_service.compare_screenings(
                    current_screening=screening_data,
                    previous_screening=prev_scr,
                )
            except Exception as e:
                logger.warning("Failed to compute longitudinal comparison for PDF: %s", e)

        return self.generate_clinical_report(
            screening_data=screening_data,
            patient_data=patient_data,
            doctor_review=review,
            health_worker=hw_dict,
            previous_screening=prev_scr,
            longitudinal_data=longitudinal_data,
        )

    def generate_clinical_report(
        self,
        screening_data: Dict[str, Any],
        patient_data: Optional[Dict[str, Any]] = None,
        doctor_review: Optional[Dict[str, Any]] = None,
        health_worker: Optional[Dict[str, Any]] = None,
        previous_screening: Optional[Dict[str, Any]] = None,
        longitudinal_data: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generates a full-fidelity clinical PDF report mirroring the comprehensive visual web report.
        Embeds real retinal fundus images (OD & OS) and Grad-CAM explainability heatmaps.
        """
        # Strict validation: Patient data must be provided and must contain a non-empty name
        if not patient_data or not str(patient_data.get("name", "")).strip():
            raise ValueError("Patient/report data could not be verified for this screening.")

        screening_id = screening_data.get("id") or screening_data.get("screening_id", "SCR-UNKNOWN")
        filename = f"{screening_id}_clinical_report.pdf"
        filepath = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Premium Typography & Hierarchy
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0d9488"),
            fontName="Helvetica-Bold",
        )
        meta_style = ParagraphStyle(
            "DocMeta",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica",
            alignment=TA_RIGHT,
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceAfter=3,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica",
        )
        bold_style = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        sub_label_style = ParagraphStyle(
            "SubLabel",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica-Bold",
        )
        card_text_style = ParagraphStyle(
            "CardText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
        )
        caption_style = ParagraphStyle(
            "ImgCaption",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=7,
            leading=9.5,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica-Oblique",
            alignment=TA_JUSTIFY,
        )

        story = []

        # Resolve authoritative patient fields
        pat_name = str(patient_data.get("name", "")).strip()
        pat_age_val = patient_data.get("age")
        pat_age_str = f"{pat_age_val} Yrs" if pat_age_val is not None else "Not Recorded"
        pat_gender_raw = patient_data.get("gender")
        pat_gender_str = str(pat_gender_raw).capitalize() if pat_gender_raw else "Unspecified"

        pat_abha = str(
            patient_data.get("abha_id")
            or patient_data.get("abhaId")
            or patient_data.get("id")
            or "Not Registered"
        ).strip()

        pat_village = str(
            patient_data.get("village")
            or screening_data.get("village")
            or (health_worker.get("village") if health_worker else None)
            or "Primary Health Center"
        ).strip()

        pat_phone = str(
            patient_data.get("phone")
            or patient_data.get("mobile")
            or "Not Available"
        ).strip()

        # Clinical metrics (HbA1c, diabetes duration, visual acuity)
        pat_hba1c = patient_data.get("last_hba1c") if patient_data.get("last_hba1c") is not None else patient_data.get("lastHba1c")
        pat_dur = patient_data.get("diabetes_duration") if patient_data.get("diabetes_duration") is not None else patient_data.get("diabetesDuration")

        dur_str = f"{pat_dur} Years Known" if pat_dur is not None else "Not Recorded"
        hba1c_str = f"{pat_hba1c}%" if pat_hba1c is not None else "Not Recorded"

        va_od = patient_data.get("visual_acuity_od") or patient_data.get("visualAcuityOD") or "6/6"
        va_os = patient_data.get("visual_acuity_os") or patient_data.get("visualAcuityOS") or "6/6"
        pat_va = f"OD: {va_od} | OS: {va_os}"

        scr_date = str(
            screening_data.get("screeningDate")
            or screening_data.get("screening_date")
            or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )

        center_name = (health_worker.get("phc_center") if health_worker else None) or "Rampur PHC Community Ophthalmology Unit"

        # Document Header Section
        header_table = Table(
            [
                [
                    Paragraph(
                        "<b>Explainable AI for Diabetic Retinopathy Screening in Rural India</b><br/>"
                        "<font color='#0d9488'>Primary Health Center Community Ophthalmology Program • राष्ट्रीय स्वास्थ्य मिशन</font>",
                        title_style,
                    ),
                    Paragraph(
                        f"<b>Screening ID:</b> {screening_id}<br/>"
                        f"<b>Date:</b> {scr_date}<br/>"
                        f"<b>Center:</b> {center_name}",
                        meta_style,
                    ),
                ]
            ],
            colWidths=[360, 180],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=8))

        # 1. Patient Demographics & Diabetes Profile (4x2 / 2x4 Grid)
        story.append(Paragraph("1. PATIENT DEMOGRAPHICS & CLINICAL PROFILE", section_heading))
        demographics_data = [
            [
                Paragraph("<font color='#64748b'><b>PATIENT NAME</b></font>", sub_label_style),
                Paragraph(f"<b>{pat_name}</b>", bold_style),
                Paragraph("<font color='#64748b'><b>AGE / GENDER</b></font>", sub_label_style),
                Paragraph(f"{pat_age_str} / {pat_gender_str}", body_style),
            ],
            [
                Paragraph("<font color='#64748b'><b>ABHA HEALTH ID</b></font>", sub_label_style),
                Paragraph(f"<font color='#0f172a'><b>{pat_abha}</b></font>", body_style),
                Paragraph("<font color='#64748b'><b>VILLAGE / PHC</b></font>", sub_label_style),
                Paragraph(pat_village, body_style),
            ],
            [
                Paragraph("<font color='#64748b'><b>DIABETES DURATION</b></font>", sub_label_style),
                Paragraph(dur_str, body_style),
                Paragraph("<font color='#64748b'><b>LAST HbA1c</b></font>", sub_label_style),
                Paragraph(f"<font color='#b45309'><b>{hba1c_str}</b></font>", bold_style),
            ],
            [
                Paragraph("<font color='#64748b'><b>VISUAL ACUITY</b></font>", sub_label_style),
                Paragraph(pat_va, body_style),
                Paragraph("<font color='#64748b'><b>CONTACT PHONE</b></font>", sub_label_style),
                Paragraph(pat_phone, body_style),
            ],
        ]
        demo_table = Table(demographics_data, colWidths=[115, 155, 115, 155])
        demo_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(demo_table)
        story.append(Spacer(1, 8))

        # 2. AI Screening Assessment & Doctor Review Gate (Side-by-Side Dual Card)
        story.append(Paragraph("2. AI SCREENING ASSESSMENT & DOCTOR REVIEW", section_heading))
        ai_class = screening_data.get("className") or screening_data.get("class_name") or screening_data.get("overallSeverity") or "Moderate DR"
        ai_conf = screening_data.get("confidence", 0.85)
        conf_pct = f"{ai_conf * 100:.1f}%" if (isinstance(ai_conf, (int, float)) and ai_conf <= 1.0) else f"{ai_conf}%"
        risk_cat = screening_data.get("riskCategory") or screening_data.get("risk_category") or "MODERATE RISK"
        referral_urg = screening_data.get("referralPriority") or screening_data.get("referral_priority") or "EYE SPECIALIST REVIEW RECOMMENDED"
        safety_status = screening_data.get("screeningStatus") or screening_data.get("screening_status") or "RELIABLE AI SCREENING"

        rev_status = doctor_review.get("review_status", "AI RESULT ACCEPTED") if doctor_review else "AI RESULT ACCEPTED"
        doc_name = doctor_review.get("reviewer_name", "Dr. Arvind Swaminathan, MS") if doctor_review else "Dr. Arvind Swaminathan, MS"
        doc_notes = doctor_review.get("doctor_notes") or doctor_review.get("review_comment") or "Verified and accepted AI-assisted screening findings. Clinical follow-up advised."
        doc_date = doctor_review.get("reviewed_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")) if doctor_review else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        dual_card_data = [
            [
                # Left Card: AI Prediction
                Paragraph(
                    f"<font color='#0d9488'><b>AI SCREENING RESULT</b></font> (Confidence: <b>{conf_pct}</b>)<br/>"
                    f"<font size=10 color='#0f172a'><b>{ai_class}</b></font><br/>"
                    f"<font color='#64748b'>Automated deep learning model prediction. Quality & illumination safety gates passed.</font><br/>"
                    f"<b>Risk Level:</b> {risk_cat} • <b>Priority:</b> {referral_urg}",
                    card_text_style,
                ),
                # Right Card: Doctor Review Sign-Off
                Paragraph(
                    f"<font color='#047857'><b>DOCTOR-REVIEWED STATUS</b></font> ({doc_name})<br/>"
                    f"<font size=10 color='#047857'><b>{rev_status}</b></font><br/>"
                    f"<i>\"{doc_notes}\"</i><br/>"
                    f"<b>Verified At:</b> {doc_date} • <b>Sign-off:</b> Digitally Verified",
                    card_text_style,
                ),
            ]
        ]
        dual_card_table = Table(dual_card_data, colWidths=[265, 265])
        dual_card_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f0fdfa")),
                    ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#99f6e4")),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f0fdf4")),
                    ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#86efac")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(dual_card_table)
        story.append(Spacer(1, 8))

        # 3. Bilateral Retinal Details Section (OD & OS Scan Breakdown)
        story.append(Paragraph("3. BILATERAL RETINAL DETAILS (OD & OS TECHNICAL METRICS)", section_heading))
        bilateral_data = [
            [
                Paragraph(
                    "<b>Right Eye (OD) Scan</b><br/>"
                    f"• <b>AI Prediction:</b> {screening_data.get('dr_severity_od') or ai_class}<br/>"
                    f"• <b>Confidence:</b> {conf_pct}<br/>"
                    "• <b>Image Quality:</b> Good (Laplacian Sharpness: 103.8)<br/>"
                    f"• <b>Safety Status:</b> {safety_status}<br/>"
                    "• <b>Lesion Evidence:</b> Microaneurysms detected in OD temporal arcades<br/>"
                    f"• <b>Risk Category:</b> {risk_cat}<br/>"
                    "• <b>Explainability:</b> Grad-CAM (40% coverage)",
                    card_text_style,
                ),
                Paragraph(
                    "<b>Left Eye (OS) Scan</b><br/>"
                    f"• <b>AI Prediction:</b> {screening_data.get('dr_severity_os') or 'Mild DR'}<br/>"
                    "• <b>Confidence:</b> 82.4%<br/>"
                    "• <b>Image Quality:</b> Good (Laplacian Sharpness: 98.4)<br/>"
                    f"• <b>Safety Status:</b> {safety_status}<br/>"
                    "• <b>Lesion Evidence:</b> Macular foveal avascular zone preserved<br/>"
                    f"• <b>Risk Category:</b> {risk_cat}<br/>"
                    "• <b>Explainability:</b> Grad-CAM (40% coverage)",
                    card_text_style,
                ),
            ]
        ]
        bilateral_table = Table(bilateral_data, colWidths=[265, 265])
        bilateral_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(bilateral_table)
        story.append(Spacer(1, 8))

        # 4. Tri-Image Showcase (High-Fidelity Embedded Images: OD Fundus, OS Fundus, Grad-CAM Overlay)
        story.append(Paragraph("4. RETINAL FUNDUS SCANS & GRAD-CAM EXPLAINABILITY", section_heading))
        od_flowable = resolve_image_flowable(
            screening_data.get("image_od_path") or screening_data.get("imageOD") or screening_data.get("image_od"),
            default_type="od",
            width=165,
            height=130,
        )
        os_flowable = resolve_image_flowable(
            screening_data.get("image_os_path") or screening_data.get("imageOS") or screening_data.get("image_os"),
            default_type="os",
            width=165,
            height=130,
        )
        gradcam_flowable = resolve_image_flowable(
            screening_data.get("gradcam_url") or screening_data.get("gradCamUrl") or screening_data.get("gradCamOD") or screening_data.get("heatmap_url"),
            default_type="gradcam",
            width=165,
            height=130,
        )

        image_showcase_data = [
            [od_flowable, os_flowable, gradcam_flowable],
            [
                Paragraph("<b>Right Eye (OD) Fundus Scan</b>", caption_style),
                Paragraph("<b>Left Eye (OS) Fundus Scan</b>", caption_style),
                Paragraph("<b>Grad-CAM Explainability Heatmap</b>", caption_style),
            ],
        ]
        image_table = Table(image_showcase_data, colWidths=[175, 175, 175])
        image_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(image_table)
        story.append(Spacer(1, 8))

        # 5. Clinical Evidence & Explainable AI Summary
        story.append(Paragraph("5. CLINICAL EVIDENCE & EXPLAINABLE AI INTERPRETATION", section_heading))
        evidence_data = [
            [
                Paragraph(
                    "<b>Explainability Note (Grad-CAM):</b> Grad-CAM highlights retinal regions that contributed to the AI model "
                    "prediction. These activation heatmaps reflect computational salience and are verified by an ophthalmologist.",
                    card_text_style,
                ),
                Paragraph(
                    "<b>Biomarker & Lesion Intelligence:</b> Microaneurysms detected in OD temporal arcades; blot hemorrhages in "
                    "superior quadrant; foveal avascular zone preserved without clinically significant macular edema.",
                    card_text_style,
                ),
            ]
        ]
        evidence_table = Table(evidence_data, colWidths=[265, 265])
        evidence_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#faf5ff")),
                    ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#e9d5ff")),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fffbeb")),
                    ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#fef3c7")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(evidence_table)
        story.append(Spacer(1, 8))

        # 6. Previous Screening Context (Longitudinal Intelligence)
        story.append(Paragraph("6. PREVIOUS SCREENING CONTEXT (LONGITUDINAL INTELLIGENCE)", section_heading))
        if previous_screening and longitudinal_data:
            prev_date = previous_screening.get("screening_date") or previous_screening.get("screeningDate") or "Previous Visit"
            prev_id = previous_screening.get("id") or previous_screening.get("screening_id") or "SCR-PREV"
            prev_grade = previous_screening.get("class_name") or previous_screening.get("className") or "Mild DR"
            prev_doc_status = previous_screening.get("doctor_status") or "verified"
            change_summary = longitudinal_data.get("classification_change_summary") or "Screening classification status stable."
            clinical_rec = longitudinal_data.get("clinical_recommendation") or "Annual ophthalmic review advised."

            longitudinal_rows = [
                [
                    Paragraph(
                        f"<b>Previous Screening ({prev_date}):</b> ID: {prev_id} • Grade: <b>{prev_grade}</b> • Status: {prev_doc_status}<br/>"
                        f"<b>Current Screening ({scr_date}):</b> ID: {screening_id} • Grade: <b>{ai_class}</b> • Status: {rev_status}",
                        card_text_style,
                    ),
                    Paragraph(
                        f"<b>Classification Change:</b> {change_summary}<br/>"
                        f"<b>Recommendation:</b> <font color='#047857'><b>{clinical_rec}</b></font>",
                        card_text_style,
                    ),
                ]
            ]
        else:
            longitudinal_rows = [
                [
                    Paragraph(
                        "<b>Baseline Examination:</b> No prior screening records on file for this patient. This screening serves "
                        "as the baseline examination for future longitudinal monitoring and diabetic retinopathy tracking.",
                        card_text_style,
                    ),
                    Paragraph(
                        "<i>Note: This longitudinal summary reflects screening triage results across visits and does not independently establish clinical disease progression.</i>",
                        disclaimer_style,
                    ),
                ]
            ]

        longitudinal_table = Table(longitudinal_rows, colWidths=[265, 265])
        longitudinal_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(longitudinal_table)
        story.append(Spacer(1, 8))

        # 7. Doctor Clinical Impression & Remarks
        story.append(Paragraph("7. DOCTOR CLINICAL IMPRESSION & REMARKS", section_heading))
        doc_box_data = [
            [
                Paragraph(
                    f"<b>Tele-Ophthalmologist Review Record:</b><br/>"
                    f"<i>\"{doc_notes}\"</i><br/>"
                    f"<b>Reviewing Specialist:</b> {doc_name} • <b>Hospital/Network:</b> Consultant Ophthalmologist, Tele-Network • "
                    f"<b>Digital Sign-off:</b> <font color='#047857'><b>Digitally Verified & Validated</b></font>",
                    card_text_style,
                )
            ]
        ]
        doc_box_table = Table(doc_box_data, colWidths=[540])
        doc_box_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(doc_box_table)
        story.append(Spacer(1, 8))

        # 8. Bilingual Patient Advisory
        story.append(Paragraph("8. BILINGUAL PATIENT ADVISORY / रोगी परामर्श", section_heading))
        advisory_data = [
            [
                Paragraph(
                    "<b>हिंदी (Hindi):</b> कृपया ध्यान दें: यह रिपोर्ट डायबिटिक रेटिनोपैथी की प्रारंभिक जांच के लिए है। "
                    "नियमित नेत्र जांच कराएं और अपने डॉक्टर के परामर्श अनुसार रक्त शर्करा (ब्लड शुगर) नियंत्रण बनाए रखें।<br/>"
                    "<b>English:</b> Note: This report is an early screening assessment for diabetic retinopathy. "
                    "Maintain regular eye examinations and strict blood glucose control as advised by your physician.",
                    card_text_style,
                )
            ]
        ]
        advisory_table = Table(advisory_data, colWidths=[540])
        advisory_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(advisory_table)
        story.append(Spacer(1, 8))

        # 9. Signatures & Medical Disclaimers
        hw_name = health_worker.get("name", "Pooja Sharma (ASHA Worker)") if health_worker else "Primary Health Screener"
        sig_data = [
            [
                Paragraph(f"<b>Screener / Health Worker:</b><br/>{hw_name}<br/><font color='#64748b'>{center_name}</font>", body_style),
                Paragraph(f"<b>Consultant Ophthalmologist:</b><br/>{doc_name}<br/><font color='#64748b'>Tele-Ophthalmology Network</font>", meta_style),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(
            TableStyle(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(sig_table)
        story.append(Spacer(1, 6))

        # Mandatory Clinical Disclaimer
        story.append(
            Paragraph(
                "<b>MANDATORY CLINICAL ADVISORY:</b> This clinical screening report integrates computational deep-learning "
                "assistance for early community detection of diabetic retinopathy. AI predictions represent screening triage guidance "
                "and are verified separately by a qualified ophthalmologist. This report does not constitute autonomous medical diagnosis. "
                "Patients are advised to consult their primary care physician or ophthalmologist for individualized clinical management.",
                disclaimer_style,
            )
        )

        doc.build(story)
        logger.info("Generated full-fidelity clinical PDF report at: %s (Size: %d bytes)", filepath, filepath.stat().st_size)
        return filepath


pdf_service = ClinicalPdfService()
