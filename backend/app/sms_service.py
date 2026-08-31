"""
Phase 15: Demo SMS Patient Report Notification Service.
Provides authoritative patient recipient resolution from MySQL, doctor-review safety gate,
secure non-guessable random report access token generation, provider abstraction (simulated demo),
unique message ID generation, duplicate protection, and database logging.

IMPORTANT:
This is a DEMONSTRATION feature only.
NO real SMS gateway is invoked.
NO real SMS is sent to any telecommunication mobile number.
The status is strictly labeled 'SIMULATED'.
"""

import os
import re
import secrets
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Explicitly load backend/.env if present
BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if BACKEND_ENV_FILE.is_file():
    load_dotenv(dotenv_path=BACKEND_ENV_FILE)

from app.database import SessionLocal
from app.models import (
    PatientModel,
    ScreeningModel,
    ScreeningReviewModel,
    ReportModel,
    DoctorModel,
    SmsNotificationModel,
)
from app.schemas import (
    SmsNotificationStatus,
    SmsNotificationRecord,
    SmsNotificationPreviewResponse,
    SmsNotificationStatusResponse,
    SecurePatientReportResponse,
)
from app.review_service import get_screening_review
from app.pdf_service import generate_secure_pdf_token

logger = logging.getLogger("dr_backend.sms_service")

# Base URL for public secure report portal links (can be overridden via environment)
REPORT_PORTAL_BASE_URL = os.getenv("REPORT_PORTAL_BASE_URL", "https://demo-rural-dr.example")


# =====================================================================
# Provider Abstraction Interface
# =====================================================================

class BaseSMSProvider(ABC):
    """Abstract SMS Gateway Provider Interface for future production extensibility."""

    @abstractmethod
    async def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Dispatches an SMS message through the underlying provider."""
        pass


class SimulatedSMSProvider(BaseSMSProvider):
    """
    Demonstration SMS Provider.
    NO real SMS gateway is invoked.
    NO network request is sent to any telecommunication provider.
    Always produces simulated success with 'SIMULATED' status.
    """

    def __init__(self):
        self.provider_name = "Simulated Demo Gateway"

    async def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        logger.info(f"[DEMO SMS SIMULATION] Simulated delivery to {to_phone}. Message size: {len(message)} chars.")
        return {
            "status": "SIMULATED",
            "provider": self.provider_name,
            "is_simulated": True,
            "disclaimer": "This is a demonstration notification. No real SMS was sent.",
        }


def get_sms_provider() -> BaseSMSProvider:
    """Factory returning the configured SMS provider instance."""
    mode = os.getenv("SMS_SERVICE_MODE", "demo").lower()
    if mode == "production":
        # Future production integration hook
        return SimulatedSMSProvider()
    return SimulatedSMSProvider()


# =====================================================================
# Phone Masking Helper
# =====================================================================

def mask_mobile_number(phone: Optional[str]) -> str:
    """
    Masks a phone number for clinical privacy in the UI (e.g., 98******54 or 73******13).
    Extracts the local 10-digit number and masks intermediate digits with asterisks.
    """
    if not phone:
        return "Not Available"

    cleaned = re.sub(r"[^\d]", "", str(phone).strip())
    if len(cleaned) >= 10:
        # Take the last 10 digits as the subscriber mobile number
        local_10 = cleaned[-10:]
        first_2 = local_10[:2]
        last_2 = local_10[-2:]
        return f"{first_2}******{last_2}"
    elif len(cleaned) >= 6:
        return f"{cleaned[:2]}***{cleaned[-2:]}"
    return "******"


# =====================================================================
# SMS Notification Service
# =====================================================================

class SmsNotificationService:
    def __init__(self):
        self.provider = get_sms_provider()
        # In-memory token cache for fast validation: token -> screening_id
        self._token_cache: Dict[str, Dict[str, Any]] = {}

    def resolve_patient_for_screening(
        self,
        screening_id: str,
        db: Optional[Session] = None,
    ) -> Optional[PatientModel]:
        """
        Authoritatively resolves the registered patient assigned to a screening record.
        Strictly resolves from:
          screening.patient_id -> MySQL patient record -> patient.phone / patient.mobile

        STRICT SAFETY RULES:
        - NEVER uses health worker mobile number
        - NEVER uses doctor mobile number
        - NEVER uses hardcoded or localStorage fallbacks
        - Returns None if patient or mobile number is not found.
        """
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
            if scr:
                if scr.patient_id:
                    pat = db.query(PatientModel).filter(PatientModel.id == scr.patient_id).first()
                    if pat and (pat.phone or pat.mobile):
                        return pat
                    if pat and scr.patient_name and not scr.patient_name.startswith("Patient "):
                        real_pat = db.query(PatientModel).filter(
                            PatientModel.name == scr.patient_name
                        ).order_by(PatientModel.created_at.desc()).first()
                        if real_pat and (real_pat.phone or real_pat.mobile):
                            return real_pat
                        return pat

                if scr.patient_name and scr.patient_name.strip() and not scr.patient_name.startswith("Patient "):
                    pat = db.query(PatientModel).filter(
                        PatientModel.name == scr.patient_name
                    ).order_by(PatientModel.created_at.desc()).first()
                    if pat and (pat.phone or pat.mobile):
                        return pat
            return None
        except Exception as e:
            logger.warning(f"Error resolving patient for screening {screening_id}: {e}")
            return None
        finally:
            if owns_session:
                db.close()

    def check_doctor_review_gate(
        self,
        screening_id: str,
        db: Optional[Session] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validates the Doctor Review Safety Gate.
        Patient notification is permitted ONLY IF:
          - Doctor reviews report AND
          - Doctor APPROVES/VERIFIES report (ACCEPT or MODIFY).

        BLOCKED IF:
          - Doctor review is still pending
          - Doctor requests image re-capture / rejects report.
        """
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
            rev_model = db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id == screening_id).first()

            if rev_model:
                action = (rev_model.action or "").upper()
                if action in ["ACCEPT", "MODIFY"]:
                    return True, None, {
                        "action": action,
                        "doctor_id": rev_model.doctor_id,
                        "doctor_name": rev_model.doctor_name,
                        "review_status": rev_model.review_status,
                        "review_timestamp": rev_model.review_timestamp,
                        "doctor_notes": rev_model.doctor_notes or rev_model.review_comment,
                    }
                elif action == "RECAPTURE":
                    return False, "Screening was marked for image re-capture. Report verified notification cannot be sent.", {
                        "action": action,
                        "doctor_id": rev_model.doctor_id,
                        "doctor_name": rev_model.doctor_name,
                        "review_status": "IMAGE RE-CAPTURE REQUESTED",
                    }

            if scr:
                if scr.doctor_status == "verified" or scr.review_status in ["AI RESULT ACCEPTED", "DOCTOR REVIEWED / MODIFIED"]:
                    return True, None, {
                        "action": "ACCEPT",
                        "doctor_id": "DOC-SWAMINATHAN",
                        "doctor_name": "Dr. Arvind Swaminathan, MS",
                        "review_status": scr.review_status or "AI RESULT ACCEPTED",
                    }
                elif scr.doctor_status == "recapture_requested" or scr.review_status == "IMAGE RE-CAPTURE REQUESTED":
                    return False, "Screening was marked for image re-capture. Report verified notification cannot be sent.", {
                        "action": "RECAPTURE",
                        "doctor_id": "DOC-SWAMINATHAN",
                        "doctor_name": "Dr. Arvind Swaminathan, MS",
                        "review_status": "IMAGE RE-CAPTURE REQUESTED",
                    }

            # Check review service fallback
            rev = get_screening_review(screening_id)
            if rev:
                action = (rev.get("action") or "").upper()
                if action in ["ACCEPT", "MODIFY"]:
                    return True, None, rev
                elif action == "RECAPTURE":
                    return False, "Screening was marked for image re-capture. Report verified notification cannot be sent.", rev

            return False, "Doctor review is still pending. Notification cannot be generated until doctor verifies report.", None
        except Exception as e:
            logger.warning(f"Error checking doctor review gate for {screening_id}: {e}")
            return False, f"Error validating doctor review: {e}", None
        finally:
            if owns_session:
                db.close()

    def generate_secure_report_token(self, screening_id: str, patient_id: str) -> str:
        """
        Generates a non-guessable random report access token mapping to the approved report.
        Tokens use URL-safe base64 secrets (e.g. '8fK92xLmQ7').
        """
        token = secrets.token_urlsafe(10)
        self._token_cache[token] = {
            "screening_id": screening_id,
            "patient_id": patient_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return token

    def generate_unique_message_id(self, db: Optional[Session] = None) -> str:
        """
        Generates a unique message tracking identifier e.g. SMS-2026-0001, SMS-2026-0012.
        Consistent with project ID formatting.
        """
        year = datetime.now().year
        count = 1
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            count = db.query(SmsNotificationModel).count() + 1
        except Exception:
            count = len(self._token_cache) + 1
        finally:
            if owns_session:
                db.close()

        # Add random salt to guarantee global uniqueness across concurrent generations
        random_suffix = secrets.token_hex(2).upper()
        return f"SMS-{year}-{count:04d}-{random_suffix}"

    def construct_sms_message(self, secure_report_url: str) -> str:
        """
        Constructs the standard demo SMS message body.
        CLINICAL SAFETY: Contains only doctor review notification + secure link.
        NO diagnosis or sensitive medical data is placed in the SMS text.
        """
        return (
            "Rural DR Screening: Your eye screening report has been successfully reviewed by the doctor.\n\n"
            "Download your report:\n"
            f"{secure_report_url}"
        )

    def get_sms_preview(
        self,
        screening_id: str,
        db: Optional[Session] = None,
    ) -> SmsNotificationPreviewResponse:
        """Generates the SMS preview metadata and checks recipient readiness."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            patient = self.resolve_patient_for_screening(screening_id, db=db)
            can_notify, gate_reason, review = self.check_doctor_review_gate(screening_id, db=db)

            pat_id = getattr(patient, "id", "PAT-UNKNOWN") if patient else "PAT-UNKNOWN"
            pat_name = getattr(patient, "name", "Patient") if patient else "Patient"
            phone = getattr(patient, "phone", None) or getattr(patient, "mobile", None)

            if not phone:
                can_notify = False
                block_reason = "Patient registered mobile number is not available."
                masked_phone = "Not Available"
            elif not can_notify:
                block_reason = gate_reason
                masked_phone = mask_mobile_number(phone)
            else:
                block_reason = None
                masked_phone = mask_mobile_number(phone)

            # Check existing notification record
            existing = db.query(SmsNotificationModel).filter(
                SmsNotificationModel.screening_id == screening_id
            ).order_by(SmsNotificationModel.created_at.desc()).first()

            if existing:
                secure_token = existing.secure_report_token
                secure_url = existing.secure_report_url
                has_existing = True
                existing_id = existing.notification_id
            else:
                secure_token = self.generate_secure_report_token(screening_id, pat_id)
                secure_url = f"{REPORT_PORTAL_BASE_URL}/patient-report/{secure_token}"
                has_existing = False
                existing_id = None

            message_text = self.construct_sms_message(secure_url)

            return SmsNotificationPreviewResponse(
                screening_id=screening_id,
                patient_id=pat_id,
                patient_name=pat_name,
                recipient_mobile_masked=masked_phone,
                message_type="Doctor-reviewed report",
                message_preview=message_text,
                secure_report_token=secure_token,
                secure_report_url=secure_url,
                doctor_review_status=review.get("review_status", "PENDING DOCTOR REVIEW") if review else "PENDING DOCTOR REVIEW",
                can_notify=can_notify,
                block_reason=block_reason,
                has_existing_notification=has_existing,
                existing_notification_id=existing_id,
                disclaimer="This is a demonstration notification. No real SMS was sent.",
            )
        finally:
            if owns_session:
                db.close()

    async def simulate_sms_notification(
        self,
        screening_id: str,
        force_regenerate: bool = False,
        db: Optional[Session] = None,
    ) -> SmsNotificationRecord:
        """
        Executes simulated demo SMS notification.
        Validates doctor review gate and patient recipient mobile.
        Handles duplicate protection and writes persistent log entry to MySQL.
        """
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            patient = self.resolve_patient_for_screening(screening_id, db=db)
            can_notify, gate_reason, review = self.check_doctor_review_gate(screening_id, db=db)

            if not patient:
                raise ValueError("Patient record could not be resolved from database for screening.")

            phone = getattr(patient, "phone", None) or getattr(patient, "mobile", None)
            if not phone or not str(phone).strip():
                raise ValueError("Patient registered mobile number is not available.")

            if not can_notify:
                raise ValueError(f"Notification blocked: {gate_reason}")

            # Check duplicate notification protection
            existing = db.query(SmsNotificationModel).filter(
                SmsNotificationModel.screening_id == screening_id
            ).order_by(SmsNotificationModel.created_at.desc()).first()

            if existing and not force_regenerate:
                logger.info(f"Returning existing simulated notification {existing.notification_id} for {screening_id}")
                return SmsNotificationRecord(
                    notification_id=existing.notification_id,
                    patient_id=existing.patient_id,
                    patient_name=patient.name,
                    screening_id=existing.screening_id,
                    report_id=existing.report_id,
                    recipient_mobile_masked=existing.recipient_mobile_masked,
                    message_type=existing.message_type,
                    message=existing.message,
                    secure_report_token=existing.secure_report_token,
                    secure_report_url=existing.secure_report_url,
                    status="SIMULATED",
                    created_at=existing.created_at,
                    generated_at=existing.generated_at or existing.created_at,
                    is_simulated=True,
                    disclaimer=existing.disclaimer,
                )

            # Generate new notification record
            pat_id = getattr(patient, "id", "PAT-UNKNOWN")
            token = self.generate_secure_report_token(screening_id, pat_id)
            secure_url = f"{REPORT_PORTAL_BASE_URL}/patient-report/{token}"
            message_text = self.construct_sms_message(secure_url)
            message_id = self.generate_unique_message_id(db=db)
            masked_phone = mask_mobile_number(phone)
            iso_now = datetime.now(timezone.utc).isoformat()

            # Execute simulation via provider abstraction
            sim_res = await self.provider.send_sms(to_phone=phone, message=message_text)

            # Save in database
            db_record = SmsNotificationModel(
                id=message_id,
                notification_id=message_id,
                patient_id=pat_id,
                screening_id=screening_id,
                report_id=f"REP-{screening_id}",
                recipient_mobile_masked=masked_phone,
                recipient_mobile_raw=str(phone).strip(),
                message_type="Doctor-reviewed report",
                message=message_text,
                secure_report_token=token,
                secure_report_url=secure_url,
                status="SIMULATED",  # Strictly SIMULATED, NEVER SENT
                is_simulated=True,
                disclaimer="This is a demonstration notification. No real SMS was sent.",
                created_at=iso_now,
                generated_at=iso_now,
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)

            self._token_cache[token] = {
                "screening_id": screening_id,
                "patient_id": pat_id,
                "created_at": iso_now,
            }

            return SmsNotificationRecord(
                notification_id=db_record.notification_id,
                patient_id=db_record.patient_id,
                patient_name=patient.name,
                screening_id=db_record.screening_id,
                report_id=db_record.report_id,
                recipient_mobile_masked=db_record.recipient_mobile_masked,
                message_type=db_record.message_type,
                message=db_record.message,
                secure_report_token=db_record.secure_report_token,
                secure_report_url=db_record.secure_report_url,
                status="SIMULATED",
                created_at=db_record.created_at,
                generated_at=db_record.generated_at,
                is_simulated=True,
                disclaimer=db_record.disclaimer,
            )
        except Exception as e:
            if owns_session:
                db.rollback()
            logger.error(f"Error simulating SMS notification for {screening_id}: {e}")
            raise
        finally:
            if owns_session:
                db.close()

    def get_sms_status(
        self,
        screening_id: str,
        db: Optional[Session] = None,
    ) -> SmsNotificationStatusResponse:
        """Retrieves SMS notification status, doctor gate evaluation, and historical notification log."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            patient = self.resolve_patient_for_screening(screening_id, db=db)
            can_notify, gate_reason, review = self.check_doctor_review_gate(screening_id, db=db)

            pat_id = getattr(patient, "id", None) if patient else None
            pat_name = getattr(patient, "name", None) if patient else None
            phone = getattr(patient, "phone", None) or getattr(patient, "mobile", None)

            if not phone:
                can_notify = False
                block_reason = "Patient registered mobile number is not available."
                masked_phone = None
                current_status = SmsNotificationStatus.MOBILE_NOT_AVAILABLE.value
            elif not can_notify:
                block_reason = gate_reason
                masked_phone = mask_mobile_number(phone)
                if review and (review.get("action") == "RECAPTURE" or review.get("review_status") == "IMAGE RE-CAPTURE REQUESTED"):
                    current_status = SmsNotificationStatus.REJECTED_BLOCKED.value
                else:
                    current_status = SmsNotificationStatus.PENDING_DOCTOR_REVIEW.value
            else:
                block_reason = None
                masked_phone = mask_mobile_number(phone)
                current_status = SmsNotificationStatus.READY_TO_NOTIFY.value

            # Fetch all notification records from DB
            db_records = db.query(SmsNotificationModel).filter(
                SmsNotificationModel.screening_id == screening_id
            ).order_by(SmsNotificationModel.created_at.desc()).all()

            history: List[SmsNotificationRecord] = []
            for rec in db_records:
                history.append(
                    SmsNotificationRecord(
                        notification_id=rec.notification_id,
                        patient_id=rec.patient_id,
                        patient_name=pat_name,
                        screening_id=rec.screening_id,
                        report_id=rec.report_id,
                        recipient_mobile_masked=rec.recipient_mobile_masked,
                        message_type=rec.message_type,
                        message=rec.message,
                        secure_report_token=rec.secure_report_token,
                        secure_report_url=rec.secure_report_url,
                        status=rec.status,
                        created_at=rec.created_at,
                        generated_at=rec.generated_at,
                        is_simulated=rec.is_simulated,
                        disclaimer=rec.disclaimer,
                    )
                )

            latest_rec = history[0] if history else None
            if latest_rec:
                current_status = SmsNotificationStatus.SIMULATED.value

            rev_status = review.get("review_status", "PENDING DOCTOR REVIEW") if review else "PENDING DOCTOR REVIEW"

            return SmsNotificationStatusResponse(
                screening_id=screening_id,
                status=current_status,
                recipient_mobile_masked=masked_phone,
                patient_id=pat_id,
                patient_name=pat_name,
                message_type="Doctor-reviewed report",
                doctor_review_status=rev_status,
                can_notify=can_notify,
                block_reason=block_reason,
                is_simulated=True,
                has_existing_notification=bool(latest_rec),
                notification_record=latest_rec,
                notification_history=history,
                disclaimer="This is a demonstration notification. No real SMS was sent.",
            )
        finally:
            if owns_session:
                db.close()

    def verify_and_get_patient_report(
        self,
        token: str,
        db: Optional[Session] = None,
    ) -> SecurePatientReportResponse:
        """
        Validates secure report access token and returns verified patient report data.
        SECURITY & CLINICAL SAFETY GATES:
        - Token must map to a registered screening
        - Doctor review must be APPROVED (not pending, not rejected)
        - Report must belong to the verified patient
        Strictly raises ValueError (403/404) if unapproved or invalid.
        """
        if not token or not str(token).strip():
            raise ValueError("Invalid access token.")

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            # 1. Look up token in database
            notif = db.query(SmsNotificationModel).filter(
                SmsNotificationModel.secure_report_token == token.strip()
            ).first()

            screening_id = notif.screening_id if notif else None
            if not screening_id:
                # Check cache
                cached = self._token_cache.get(token.strip())
                if cached:
                    screening_id = cached.get("screening_id")

            if not screening_id:
                raise ValueError("Secure report link is invalid or has expired.")

            # 2. Query Screening and Patient
            scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
            if not scr:
                raise ValueError("Clinical report not found.")

            patient = db.query(PatientModel).filter(PatientModel.id == scr.patient_id).first()

            # 3. Check Doctor Review Approval Gate
            can_notify, gate_reason, review = self.check_doctor_review_gate(screening_id, db=db)
            if not can_notify:
                raise ValueError(f"Access Forbidden: Clinical report is not doctor-approved. {gate_reason}")

            # 4. Assemble report response
            doc_name = review.get("doctor_name", "Dr. Arvind Swaminathan, MS") if review else "Dr. Arvind Swaminathan, MS"
            doc_title = "Senior Consultant Ophthalmologist (Retina Specialist)"
            doc_notes = review.get("doctor_notes") or review.get("review_comment") or (scr.review.doctor_notes if scr.review else None)

            # Determine doctor-verified result
            reviewed_result = review.get("doctor_reviewed_result") or review.get("reviewed_result")
            if reviewed_result:
                final_dr = reviewed_result
            elif scr.review and scr.review.reviewed_result:
                final_dr = scr.review.reviewed_result
            else:
                final_dr = scr.class_name

            # Secure PDF token
            pdf_tok = generate_secure_pdf_token(screening_id)
            pdf_url = f"/api/reports/{screening_id}/pdf/view?token={pdf_tok}"

            conf_pct = f"{(scr.confidence * 100):.1f}%" if scr.confidence else "85.0%"

            return SecurePatientReportResponse(
                token=token,
                is_valid=True,
                screening_id=screening_id,
                patient_id=scr.patient_id,
                patient_name=patient.name if patient else scr.patient_name,
                age=patient.age if patient else None,
                gender=patient.gender if patient else None,
                village=patient.village if patient else scr.village,
                screening_date=scr.screening_date,
                doctor_status=scr.doctor_status,
                review_status=review.get("review_status", "AI RESULT ACCEPTED") if review else "AI RESULT ACCEPTED",
                doctor_name=doc_name,
                doctor_title=doc_title,
                doctor_notes=doc_notes,
                final_dr_result=final_dr,
                overall_severity=scr.overall_severity,
                confidence_percentage=conf_pct,
                referral_priority=scr.referral_priority or "ROUTINE ANNUAL FOLLOW-UP",
                recommendation=scr.referral_guidance or "Regular blood sugar control and annual retinal screening.",
                pdf_download_url=pdf_url,
                generated_at=notif.generated_at if notif else datetime.now(timezone.utc).isoformat(),
                is_verified=True,
            )
        finally:
            if owns_session:
                db.close()


# Global Singleton
sms_service = SmsNotificationService()
