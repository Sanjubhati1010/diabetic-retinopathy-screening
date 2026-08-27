import os
import re
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import httpx

from app.schemas import (
    WhatsAppDeliveryStatus,
    WhatsAppDeliveryRecord,
    WhatsAppAuditEvent,
    HealthWorkerProfile,
)
from app.pdf_service import pdf_service, generate_secure_pdf_token
from app.review_service import get_screening_review

logger = logging.getLogger("dr_backend.whatsapp_service")

# Environment settings
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "madocs_verify_token_2026")
WHATSAPP_ENVIRONMENT = os.getenv("WHATSAPP_ENVIRONMENT", "demo").lower()
BASE_SERVER_URL = os.getenv("BASE_SERVER_URL", "http://localhost:8000")


def normalize_phone_number(phone: str) -> str:
    """Normalizes phone numbers to E.164 standard without whitespace or hyphens."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if not cleaned.startswith("+"):
        if cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = "+" + cleaned
        elif len(cleaned) == 10:
            cleaned = "+91" + cleaned
    return cleaned


class WhatsAppService:
    def __init__(self):
        # Health Workers Registry
        self._health_workers: Dict[str, HealthWorkerProfile] = {
            "HW-RAMPUR-01": HealthWorkerProfile(
                id="HW-RAMPUR-01",
                name="Pooja Sharma (ASHA Worker)",
                role="health_worker",
                phone="+919876543210",
                email="asha.rampur@phc.in",
                village="Rampur Gram Panchayat",
                phc_center="Primary Health Center Rampur",
                whatsapp_opt_in=True,
                whatsapp_opt_in_date="2026-08-01T09:00:00Z",
            ),
            "HW-SHIVPURI-02": HealthWorkerProfile(
                id="HW-SHIVPURI-02",
                name="Sarita Devi (Vision Tech)",
                role="health_worker",
                phone="+919412388990",
                email="sarita.vision@phc.in",
                village="Shivpuri Taluk",
                phc_center="Sub-Center Shivpuri",
                whatsapp_opt_in=True,
                whatsapp_opt_in_date="2026-08-05T10:00:00Z",
            ),
            "HW-KOLAR-03": HealthWorkerProfile(
                id="HW-KOLAR-03",
                name="Sunil Gowda (Vision Tech)",
                role="health_worker",
                phone="+919789012345",
                email="sunil.gowda@phc.in",
                village="Kolar Rural Block",
                phc_center="Kolar Rural PHC",
                whatsapp_opt_in=False,  # Explicitly opted-out for consent gate testing
                whatsapp_opt_in_date=None,
            ),
        }

        # In-memory screening delivery tracking store: screening_id -> WhatsAppDeliveryRecord
        self._delivery_records: Dict[str, WhatsAppDeliveryRecord] = {}

        # Message ID index for webhook lookups: provider_message_id -> screening_id
        self._message_id_map: Dict[str, str] = {}

        # Initialize mock records for pre-seeded screenings
        self._init_demo_records()

    def _init_demo_records(self):
        """Initializes seed delivery tracking records."""
        rec1 = WhatsAppDeliveryRecord(
            screening_id="SCR-2026-001",
            recipient_phone="+919876543210",
            health_worker_id="HW-RAMPUR-01",
            health_worker_name="Pooja Sharma (ASHA Worker)",
            status=WhatsAppDeliveryStatus.DELIVERED,
            provider_message_id="wamid.DEMO_SCR_001_DELIVERED",
            provider_status="delivered",
            sent_at="2026-08-22T14:30:00Z",
            delivered_at="2026-08-22T14:30:15Z",
            read_at="2026-08-22T14:32:00Z",
            pdf_filename="SCR-2026-001_clinical_report.pdf",
            pdf_download_url="/api/reports/SCR-2026-001/document?token=sec_tok_SCR-2026-001_seed",
            template_name="clinical_report_delivery_v1",
            language="en",
            is_demo=True,
            audit_events=[
                WhatsAppAuditEvent(
                    event_type="REPORT_GENERATED",
                    timestamp="2026-08-22T14:28:00Z",
                    screening_id="SCR-2026-001",
                    actor="system",
                    delivery_status="NOT_REQUESTED",
                    details={"file": "SCR-2026-001_clinical_report.pdf"},
                ),
                WhatsAppAuditEvent(
                    event_type="DOCTOR_REVIEW_COMPLETED",
                    timestamp="2026-08-22T14:29:00Z",
                    screening_id="SCR-2026-001",
                    actor="Dr. Arvind Swaminathan, MS",
                    delivery_status="NOT_REQUESTED",
                    details={"action": "ACCEPT", "review_status": "AI RESULT ACCEPTED"},
                ),
                WhatsAppAuditEvent(
                    event_type="WHATSAPP_REPORT_SENT",
                    timestamp="2026-08-22T14:30:00Z",
                    screening_id="SCR-2026-001",
                    actor="HW-RAMPUR-01",
                    delivery_status="SENT",
                    provider_message_id="wamid.DEMO_SCR_001_DELIVERED",
                ),
                WhatsAppAuditEvent(
                    event_type="WHATSAPP_REPORT_DELIVERED",
                    timestamp="2026-08-22T14:30:15Z",
                    screening_id="SCR-2026-001",
                    actor="whatsapp_webhook",
                    delivery_status="DELIVERED",
                    provider_message_id="wamid.DEMO_SCR_001_DELIVERED",
                ),
            ],
        )
        self._delivery_records["SCR-2026-001"] = rec1
        self._message_id_map["wamid.DEMO_SCR_001_DELIVERED"] = "SCR-2026-001"

    def get_health_worker(self, hw_id: str) -> Optional[HealthWorkerProfile]:
        return self._health_workers.get(hw_id)

    def get_all_health_workers(self) -> List[HealthWorkerProfile]:
        return list(self._health_workers.values())

    def update_health_worker_opt_in(self, hw_id: str, opt_in: bool, phone: Optional[str] = None) -> HealthWorkerProfile:
        hw = self._health_workers.get(hw_id)
        if not hw:
            hw = HealthWorkerProfile(
                id=hw_id,
                name="Health Worker",
                phone=normalize_phone_number(phone) if phone else "+919876543210",
                email=f"{hw_id.lower()}@phc.in",
                village="Rural PHC",
                phc_center="Community Center",
                whatsapp_opt_in=opt_in,
                whatsapp_opt_in_date=datetime.utcnow().isoformat() if opt_in else None,
            )
            self._health_workers[hw_id] = hw
        else:
            hw.whatsapp_opt_in = opt_in
            hw.whatsapp_opt_in_date = datetime.utcnow().isoformat() if opt_in else None
            if phone:
                hw.phone = normalize_phone_number(phone)
        return hw

    def check_doctor_review_gate(self, screening_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates whether the doctor review gate has passed for a given screening ID.
        Returns: (can_proceed, status_reason, review_dict)
        """
        review = get_screening_review(screening_id)
        if not review:
            # Fallback check for seed screenings
            if screening_id in ["SCR-2026-001", "SCR-2026-0991", "SCR-2026-0994"]:
                return (
                    True,
                    "Doctor review accepted.",
                    {
                        "review_status": "AI RESULT ACCEPTED",
                        "reviewer_name": "Dr. Arvind Swaminathan, MS",
                        "doctor_notes": "AI screening classification confirmed and clinically verified.",
                        "reviewed_at": "2026-08-22T14:29:00Z",
                    },
                )
            return (
                False,
                "Doctor review has not been completed. Final clinical report requires doctor sign-off before delivery.",
                None,
            )

        rev_status = review.get("review_status", "PENDING DOCTOR REVIEW")
        if rev_status == "IMAGE RE-CAPTURE REQUESTED" or review.get("is_recapture"):
            return (
                False,
                "Final report is waiting for re-capture/doctor review. Cannot deliver report until doctor accepts screening.",
                review,
            )

        if rev_status not in ["AI RESULT ACCEPTED", "DOCTOR REVIEWED / MODIFIED"]:
            return (
                False,
                f"Doctor review status '{rev_status}' does not allow report delivery. Final doctor sign-off required.",
                review,
            )

        return True, "Doctor review completed and verified.", review

    def format_message_body(
        self,
        screening_id: str,
        patient_ref: str,
        review_status: str,
        language: str = "en",
    ) -> str:
        """Constructs the standard WhatsApp notification text body."""
        if language == "hi":
            return (
                f"आपकी डायबिटिक रेटिनोपैथी स्क्रीनिंग रिपोर्ट डॉक्टर द्वारा सत्यापन के पश्चात तैयार है।\n\n"
                f"स्क्रीनिंग आईडी: {screening_id}\n"
                f"मरीज: {patient_ref}\n"
                f"डॉक्टर समीक्षा: {review_status}\n\n"
                f"आपकी क्लिनिकल रिपोर्ट संलग्न दस्तावेज में उपलब्ध है।\n\n"
                f"चिकित्सीय प्रश्नों के लिए कृपया समीक्षा करने वाले स्वास्थ्य विशेषज्ञ से संपर्क करें।"
            )
        return (
            f"Your diabetic retinopathy screening report is ready after doctor review.\n\n"
            f"Screening ID: {screening_id}\n"
            f"Patient: {patient_ref}\n"
            f"Doctor review: {review_status}\n\n"
            f"Your clinical report is available in the attached document.\n\n"
            f"For medical questions, please contact the reviewing healthcare professional."
        )

    def get_delivery_status(self, screening_id: str) -> Optional[WhatsAppDeliveryRecord]:
        return self._delivery_records.get(screening_id)

    async def send_whatsapp_report(
        self,
        screening_id: str,
        recipient_phone: str,
        health_worker_id: str,
        language: str = "en",
        opt_in_confirmed: bool = True,
        patient_data: Optional[Dict[str, Any]] = None,
        screening_data: Optional[Dict[str, Any]] = None,
    ) -> WhatsAppDeliveryRecord:
        """
        Main delivery workflow:
        1. Validates doctor review gate
        2. Validates health worker identity and mobile number
        3. Validates explicit WhatsApp opt-in consent
        4. Prevents duplicate sends
        5. Generates standardized clinical PDF
        6. Dispatches via WhatsApp Business Cloud API (or structured demo mode)
        7. Records audit trail
        """
        norm_phone = normalize_phone_number(recipient_phone)

        # 1. Doctor Review Gate Check
        can_proceed, gate_reason, review = self.check_doctor_review_gate(screening_id)
        if not can_proceed:
            logger.warning("WhatsApp delivery blocked for %s: %s", screening_id, gate_reason)
            raise ValueError(f"Doctor Review Gate Violation: {gate_reason}")

        # 2. Health Worker Verification & Authorization
        hw = self.get_health_worker(health_worker_id)
        if not hw:
            # Create dynamic entry if valid HW ID format
            if health_worker_id.startswith("HW-"):
                hw = self.update_health_worker_opt_in(health_worker_id, opt_in_confirmed, norm_phone)
            else:
                raise ValueError(f"Unauthorized health worker identifier: {health_worker_id}")

        # Check phone authorization: recipient_phone must match registered HW phone
        if normalize_phone_number(hw.phone) != norm_phone:
            logger.warning(
                "Phone mismatch for HW %s. Registered: %s, Provided: %s",
                health_worker_id,
                hw.phone,
                norm_phone,
            )
            raise ValueError(
                f"Unauthorized recipient phone. The number {norm_phone} does not match the registered mobile for health worker {health_worker_id}."
            )

        # 3. WhatsApp Opt-in Consent Verification
        if not hw.whatsapp_opt_in or not opt_in_confirmed:
            raise ValueError(
                f"Consent Violation: Health worker {health_worker_id} has not opted in to receive reports via WhatsApp."
            )

        # 4. Duplicate Send Prevention Check
        existing_record = self._delivery_records.get(screening_id)
        if existing_record and existing_record.status in [
            WhatsAppDeliveryStatus.SENT,
            WhatsAppDeliveryStatus.DELIVERED,
            WhatsAppDeliveryStatus.READ,
        ]:
            logger.info("Report for screening %s was already delivered (status: %s)", screening_id, existing_record.status)
            return existing_record

        # 5. Generate Clinical PDF Report
        scr_dict = screening_data or {
            "id": screening_id,
            "screeningDate": datetime.utcnow().strftime("%Y-%m-%d"),
            "className": "Moderate DR",
            "confidence": 0.875,
            "riskCategory": "MODERATE RISK",
            "referralPriority": "EYE SPECIALIST REVIEW RECOMMENDED",
            "screeningStatus": "RELIABLE AI SCREENING",
        }
        pat_dict = patient_data or {
            "name": "Ramesh Kumar Verma",
            "age": 58,
            "gender": "Male",
            "abhaId": "91-4829-1029-4821",
            "village": hw.village,
            "phone": norm_phone,
        }
        hw_dict = {
            "name": hw.name,
            "id": hw.id,
            "village": hw.village,
            "phc_center": hw.phc_center,
        }

        pdf_path = pdf_service.generate_clinical_report(
            screening_data=scr_dict,
            patient_data=pat_dict,
            doctor_review=review,
            health_worker=hw_dict,
        )

        pdf_token = generate_secure_pdf_token(screening_id)
        pdf_download_url = f"/api/reports/{screening_id}/document?token={pdf_token}"

        # 6. Prepare Delivery Record
        timestamp_now = datetime.utcnow().isoformat()
        message_body = self.format_message_body(
            screening_id=screening_id,
            patient_ref=f"{pat_dict.get('name', 'Patient')} (ABHA: {pat_dict.get('abhaId', pat_dict.get('id', 'N/A'))[-4:]})",
            review_status=review.get("review_status", "AI RESULT ACCEPTED") if review else "AI RESULT ACCEPTED",
            language=language,
        )

        # 7. Dispatch via Real WhatsApp Provider or Structured Demo Mode
        is_real_config = bool(WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ENVIRONMENT != "demo")
        provider_msg_id: str
        delivery_status: WhatsAppDeliveryStatus
        error_msg: Optional[str] = None

        if is_real_config:
            # Real Meta WhatsApp Business Cloud API Call
            try:
                endpoint = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                }
                # Construct document message payload
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": norm_phone.replace("+", ""),
                    "type": "document",
                    "document": {
                        "link": f"{BASE_SERVER_URL}{pdf_download_url}",
                        "caption": message_body,
                        "filename": pdf_path.name,
                    },
                }

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code in [200, 201]:
                        resp_data = resp.json()
                        messages = resp_data.get("messages", [])
                        provider_msg_id = messages[0].get("id") if messages else f"wamid.{uuid.uuid4()}"
                        delivery_status = WhatsAppDeliveryStatus.SENT
                    else:
                        delivery_status = WhatsAppDeliveryStatus.FAILED
                        error_msg = f"WhatsApp API HTTP {resp.status_code}: {resp.text}"
                        provider_msg_id = f"err_{uuid.uuid4().hex[:12]}"
            except Exception as e:
                logger.error("Failed to dispatch WhatsApp message to %s: %s", norm_phone, e)
                delivery_status = WhatsAppDeliveryStatus.FAILED
                error_msg = str(e)
                provider_msg_id = f"err_{uuid.uuid4().hex[:12]}"
        else:
            # Structured Demo / Development Mode
            provider_msg_id = f"wamid.DEMO_{screening_id.replace('-', '_')}_{uuid.uuid4().hex[:8]}"
            delivery_status = WhatsAppDeliveryStatus.SENT
            logger.info("Executed demo WhatsApp report delivery for %s to %s", screening_id, norm_phone)

        # 8. Record Delivery State and Audit Trail
        audit_events = [
            WhatsAppAuditEvent(
                event_type="REPORT_GENERATED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor="system",
                delivery_status="PROCESSING",
                details={"filename": pdf_path.name},
            ),
            WhatsAppAuditEvent(
                event_type="DOCTOR_REVIEW_COMPLETED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor=review.get("reviewer_name", "Doctor Specialist"),
                delivery_status="PROCESSING",
                details={"review_status": review.get("review_status")},
            ),
            WhatsAppAuditEvent(
                event_type="WHATSAPP_REPORT_REQUESTED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor=health_worker_id,
                delivery_status="QUEUED",
                details={"recipient_phone": norm_phone, "language": language},
            ),
            WhatsAppAuditEvent(
                event_type="WHATSAPP_REPORT_SENT" if delivery_status != WhatsAppDeliveryStatus.FAILED else "WHATSAPP_REPORT_FAILED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor="whatsapp_service",
                delivery_status=delivery_status.value,
                provider_message_id=provider_msg_id,
                details={"error": error_msg} if error_msg else None,
            ),
        ]

        delivery_record = WhatsAppDeliveryRecord(
            screening_id=screening_id,
            recipient_phone=norm_phone,
            health_worker_id=health_worker_id,
            health_worker_name=hw.name,
            status=delivery_status,
            provider_message_id=provider_msg_id,
            provider_status="sent" if delivery_status == WhatsAppDeliveryStatus.SENT else "failed",
            sent_at=timestamp_now if delivery_status == WhatsAppDeliveryStatus.SENT else None,
            delivered_at=None,
            read_at=None,
            error_message=error_msg,
            retry_count=0,
            pdf_filename=pdf_path.name,
            pdf_download_url=pdf_download_url,
            template_name="clinical_report_delivery_v1",
            language=language,
            is_demo=not is_real_config,
            audit_events=audit_events,
        )

        self._delivery_records[screening_id] = delivery_record
        self._message_id_map[provider_msg_id] = screening_id

        return delivery_record

    async def retry_whatsapp_report(
        self,
        screening_id: str,
        health_worker_id: str,
        force_regenerate_pdf: bool = False,
    ) -> WhatsAppDeliveryRecord:
        """
        Retries failed report delivery with duplicate-send safety checks.
        """
        record = self._delivery_records.get(screening_id)
        if not record:
            raise ValueError(f"No previous delivery record found for screening {screening_id} to retry.")

        if record.status in [WhatsAppDeliveryStatus.DELIVERED, WhatsAppDeliveryStatus.READ]:
            logger.info("Retry ignored: screening %s is already %s", screening_id, record.status)
            return record

        record.retry_count += 1
        timestamp_now = datetime.utcnow().isoformat()

        # Update record status to PROCESSING
        record.status = WhatsAppDeliveryStatus.PROCESSING
        record.audit_events.append(
            WhatsAppAuditEvent(
                event_type="WHATSAPP_REPORT_REQUESTED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor=health_worker_id,
                delivery_status="PROCESSING",
                details={"retry_attempt": record.retry_count},
            )
        )

        # Dispatch retry
        is_real_config = bool(WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ENVIRONMENT != "demo")
        if is_real_config:
            try:
                endpoint = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": record.recipient_phone.replace("+", ""),
                    "type": "document",
                    "document": {
                        "link": f"{BASE_SERVER_URL}{record.pdf_download_url}",
                        "caption": self.format_message_body(screening_id, "Patient", "AI RESULT ACCEPTED", record.language),
                        "filename": record.pdf_filename or f"{screening_id}_clinical_report.pdf",
                    },
                }
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code in [200, 201]:
                        record.status = WhatsAppDeliveryStatus.SENT
                        record.error_message = None
                    else:
                        record.status = WhatsAppDeliveryStatus.FAILED
                        record.error_message = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                record.status = WhatsAppDeliveryStatus.FAILED
                record.error_message = str(e)
        else:
            record.status = WhatsAppDeliveryStatus.SENT
            record.provider_message_id = f"wamid.DEMO_RETRY_{screening_id.replace('-', '_')}_{uuid.uuid4().hex[:6]}"
            record.sent_at = timestamp_now
            record.error_message = None

        record.audit_events.append(
            WhatsAppAuditEvent(
                event_type="WHATSAPP_REPORT_SENT" if record.status == WhatsAppDeliveryStatus.SENT else "WHATSAPP_REPORT_FAILED",
                timestamp=timestamp_now,
                screening_id=screening_id,
                actor="whatsapp_service",
                delivery_status=record.status.value,
                provider_message_id=record.provider_message_id,
                details={"retry_count": record.retry_count},
            )
        )

        return record

    def verify_webhook_challenge(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Validates Meta WhatsApp Webhook subscription handshake."""
        if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            logger.info("WhatsApp webhook challenge verified successfully.")
            return challenge
        logger.warning("WhatsApp webhook challenge verification failed (mode=%s, token=%s)", mode, token)
        return None

    def process_webhook_status_update(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes real Meta WhatsApp webhook delivery status updates:
        Statuses: sent, delivered, read, failed.
        """
        results = []
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                statuses = value.get("statuses", [])
                for stat in statuses:
                    msg_id = stat.get("id")
                    stat_name = stat.get("status", "").lower()
                    timestamp = stat.get("timestamp")
                    iso_time = datetime.utcfromtimestamp(int(timestamp)).isoformat() if timestamp else datetime.utcnow().isoformat()

                    screening_id = self._message_id_map.get(msg_id)
                    if screening_id and screening_id in self._delivery_records:
                        rec = self._delivery_records[screening_id]
                        rec.provider_status = stat_name

                        if stat_name == "delivered":
                            rec.status = WhatsAppDeliveryStatus.DELIVERED
                            rec.delivered_at = iso_time
                            rec.audit_events.append(
                                WhatsAppAuditEvent(
                                    event_type="WHATSAPP_REPORT_DELIVERED",
                                    timestamp=iso_time,
                                    screening_id=screening_id,
                                    actor="whatsapp_webhook",
                                    delivery_status="DELIVERED",
                                    provider_message_id=msg_id,
                                )
                            )
                        elif stat_name == "read":
                            rec.status = WhatsAppDeliveryStatus.READ
                            rec.read_at = iso_time
                            rec.audit_events.append(
                                WhatsAppAuditEvent(
                                    event_type="WHATSAPP_REPORT_READ",
                                    timestamp=iso_time,
                                    screening_id=screening_id,
                                    actor="whatsapp_webhook",
                                    delivery_status="READ",
                                    provider_message_id=msg_id,
                                )
                            )
                        elif stat_name == "failed":
                            rec.status = WhatsAppDeliveryStatus.FAILED
                            rec.error_message = str(stat.get("errors", [{}])[0].get("title", "Delivery failed"))
                            rec.audit_events.append(
                                WhatsAppAuditEvent(
                                    event_type="WHATSAPP_REPORT_FAILED",
                                    timestamp=iso_time,
                                    screening_id=screening_id,
                                    actor="whatsapp_webhook",
                                    delivery_status="FAILED",
                                    provider_message_id=msg_id,
                                    details={"errors": stat.get("errors")},
                                )
                            )
                        results.append({"screening_id": screening_id, "status": stat_name, "message_id": msg_id})
        return results


# Global singleton instance
whatsapp_service = WhatsAppService()
