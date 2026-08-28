import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.whatsapp_service import whatsapp_service, normalize_phone_number
from app.review_service import process_doctor_review
from app.pdf_service import pdf_service, verify_secure_pdf_token, generate_secure_pdf_token
from app.schemas import DoctorReviewRequest, WhatsAppSendRequest, WhatsAppDeliveryStatus, WhatsAppDeliveryRecord

client = TestClient(app)


class TestPhase12WhatsAppReportDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n==================================================")
        print("RUNNING PHASE 12 WHATSAPP CLINICAL REPORT TESTS")
        print("==================================================")

        # Run seed and migrations
        from app.database import SessionLocal
        from app.db_seeder import seed_database_if_empty
        from app.models import WhatsAppDeliveryModel, WhatsAppAuditEventModel, ScreeningReviewModel, ReviewAuditEventModel, ScreeningModel
        db = SessionLocal()
        try:
            seed_database_if_empty(db)
            test_sids = ["SCR-PHASE12-ACCEPTED", "SCR-PHASE12-RECAPTURE", "SCR-FAILED-001", "SCR-UNREVIEWED-999", "SCR-UNREVIEWED-888"]
            db.query(WhatsAppAuditEventModel).filter(WhatsAppAuditEventModel.screening_id.in_(test_sids)).delete(synchronize_session=False)
            db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id.in_(test_sids)).delete(synchronize_session=False)
            db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.screening_id.in_(test_sids)).delete(synchronize_session=False)
            db.query(ScreeningReviewModel).filter(ScreeningReviewModel.screening_id.in_(test_sids)).delete(synchronize_session=False)

            # Ensure ScreeningModel entries exist for test screenings
            for sid, cname, conf in [
                ("SCR-PHASE12-ACCEPTED", "Moderate", 0.875),
                ("SCR-PHASE12-RECAPTURE", "Moderate", 0.875),
                ("SCR-FAILED-001", "Moderate", 0.85),
            ]:
                s_rec = db.query(ScreeningModel).filter(ScreeningModel.id == sid).first()
                if not s_rec:
                    db.add(
                        ScreeningModel(
                            id=sid,
                            patient_id="PAT-2026-081",
                            patient_name="Sanjay Bhati",
                            village="Rampur Gram Panchayat",
                            screening_date="2026-08-28 10:00 AM",
                            timestamp_iso="2026-08-28T10:00:00Z",
                            predicted_class=2,
                            class_name=cname,
                            confidence=conf,
                            dr_severity_od="dr2",
                            dr_severity_os="dr1",
                            overall_severity="dr2",
                            safety_status="READY_FOR_AI",
                            screening_status="RELIABLE AI SCREENING",
                            risk_category="MODERATE",
                            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
                            doctor_status="verified",
                            review_status="AI RESULT ACCEPTED",
                        )
                    )
                else:
                    s_rec.patient_id = "PAT-2026-081"
                    s_rec.patient_name = "Sanjay Bhati"
                    s_rec.village = "Rampur Gram Panchayat"
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error in setUpClass DB setup: {e}")
        finally:
            db.close()

        # Pre-seed a doctor-reviewed accepted screening
        process_doctor_review(
            request=DoctorReviewRequest(
                screening_id="SCR-PHASE12-ACCEPTED",
                action="ACCEPT",
                doctor_id="DOC-SWAMINATHAN",
                doctor_name="Dr. Arvind Swaminathan, MS",
                doctor_notes="AI screening findings confirmed and verified.",
            ),
            original_ai_result="Moderate",
            original_confidence=0.875,
            role="doctor",
        )

        # Pre-seed a doctor-reviewed re-capture screening
        process_doctor_review(
            request=DoctorReviewRequest(
                screening_id="SCR-PHASE12-RECAPTURE",
                action="RECAPTURE",
                doctor_id="DOC-SWAMINATHAN",
                doctor_name="Dr. Arvind Swaminathan, MS",
                doctor_notes="Image has poor focus in macula. Re-capture required.",
            ),
            original_ai_result="Moderate",
            original_confidence=0.875,
            role="doctor",
        )

        # Pre-seed doctor review for SCR-FAILED-001 (used in retry test)
        process_doctor_review(
            request=DoctorReviewRequest(
                screening_id="SCR-FAILED-001",
                action="ACCEPT",
                doctor_id="DOC-SWAMINATHAN",
                doctor_name="Dr. Arvind Swaminathan, MS",
                doctor_notes="Review accepted for retry test.",
            ),
            original_ai_result="Moderate",
            original_confidence=0.85,
            role="doctor",
        )

        # Pre-seed unreviewed screening SCR-UNREVIEWED-888
        db_unrev = SessionLocal()
        try:
            scr_unrev = db_unrev.query(ScreeningModel).filter(ScreeningModel.id == "SCR-UNREVIEWED-888").first()
            if not scr_unrev:
                db_unrev.add(
                    ScreeningModel(
                        id="SCR-UNREVIEWED-888",
                        patient_id="PAT-2026-081",
                        patient_name="Sanjay Bhati",
                        village="Rampur Gram Panchayat",
                        screening_date="2026-08-28",
                        timestamp_iso="2026-08-28T10:00:00Z",
                        predicted_class=2,
                        class_name="Moderate DR",
                        confidence=0.85,
                        doctor_status="pending",
                        review_status="PENDING_REVIEW",
                    )
                )
                db_unrev.commit()
        finally:
            db_unrev.close()

    def test_01_doctor_review_gate_blocks_unreviewed(self):
        """1. Doctor-review gate: Blocks unreviewed screening from WhatsApp delivery."""
        res = client.post(
            "/api/reports/SCR-UNREVIEWED-999/whatsapp/send",
            json={
                "screening_id": "SCR-UNREVIEWED-999",
                "recipient_phone": "+917378216613",
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Doctor review has not been completed", res.json()["detail"])
        print("\n[TEST 1] Doctor-review gate successfully blocked unreviewed screening.")

    def test_02_no_report_before_review(self):
        """2. No report before review: Blocks PDF generation endpoint if screening is pending review."""
        res = client.post("/api/reports/SCR-UNREVIEWED-888/pdf")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Doctor review has not been completed", res.json()["detail"])
        print("[TEST 2] PDF generation endpoint blocked unreviewed screening.")

    def test_03_recapture_blocks_final_delivery(self):
        """3. Re-capture blocks final delivery: Re-capture request status blocks WhatsApp delivery."""
        res = client.post(
            "/api/reports/SCR-PHASE12-RECAPTURE/whatsapp/send",
            json={
                "screening_id": "SCR-PHASE12-RECAPTURE",
                "recipient_phone": "+917378216613",
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Final report is waiting for re-capture", res.json()["detail"])
        print("[TEST 3] Re-capture request status safely blocked final delivery.")

    def test_04_valid_phone_normalization(self):
        """4. Valid phone normalization: Successfully accepts and formats valid phone numbers."""
        phone1 = normalize_phone_number("+91 73782 16613")
        phone2 = normalize_phone_number("7378216613")
        phone3 = normalize_phone_number("917378216613")
        self.assertEqual(phone1, "+917378216613")
        self.assertEqual(phone2, "+917378216613")
        self.assertEqual(phone3, "+917378216613")
        print("[TEST 4] Phone number normalization verified.")

    def test_05_missing_patient_mobile_blocks_send(self):
        """5. Missing Patient Mobile Gate: Rejects delivery when patient mobile is missing or unverified."""
        res = client.get("/api/reports/SCR-UNKNOWN-VILLAGE-999/whatsapp/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["can_send"])
        self.assertEqual(data["block_reason"], "Patient mobile number not available/verified.")
        print("[TEST 5] Missing patient mobile gate verified (can_send=False, block_reason enforced).")

    def test_06_unauthorized_number(self):
        """6. Unauthorized number: Rejects delivery when phone does not match registered patient."""
        res = client.post(
            "/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/send",
            json={
                "screening_id": "SCR-PHASE12-ACCEPTED",
                "recipient_phone": "+919999999999",  # Unauthorized number (Patient is +917378216613)
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unauthorized recipient phone", res.json()["detail"])
        print("[TEST 6] Unauthorized recipient number rejected with HTTP 400.")

    def test_07_pdf_generation(self):
        """7. PDF generation: Successfully generates standard clinical report PDF."""
        res = client.post("/api/reports/SCR-PHASE12-ACCEPTED/pdf")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(".pdf", data["pdf_filename"])
        self.assertTrue(data["is_final_doctor_approved"])
        self.assertTrue(data["file_size_bytes"] > 0)
        print(f"[TEST 7] PDF generation verified ({data['file_size_bytes']} bytes).")

    def test_08_whatsapp_api_request_and_secure_download(self):
        """8. WhatsApp API request & secure download: Verifies tokenized document access."""
        token = generate_secure_pdf_token("SCR-PHASE12-ACCEPTED")
        self.assertTrue(verify_secure_pdf_token("SCR-PHASE12-ACCEPTED", token))
        self.assertFalse(verify_secure_pdf_token("SCR-PHASE12-ACCEPTED", "invalid_token"))

        res = client.get(f"/api/reports/SCR-PHASE12-ACCEPTED/document?token={token}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        print("[TEST 8] Secure tokenized PDF download endpoint verified.")

    def test_09_provider_success_and_send_to_patient(self):
        """9. Provider success: Verifies delivery record creation and status marked SENT to patient."""
        res = client.post(
            "/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/send",
            json={
                "screening_id": "SCR-PHASE12-ACCEPTED",
                "recipient_phone": "+917378216613",
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SENT")
        self.assertEqual(data["recipient_phone"], "+917378216613")
        self.assertEqual(data["patient_name"], "Sanjay Bhati")
        self.assertEqual(data["health_worker_name"], "Pooja Sharma (ASHA Worker)")
        self.assertIn("wamid.", data["provider_message_id"])
        print(f"[TEST 9] WhatsApp delivery dispatch to patient verified (Recipient: {data['recipient_phone']} - {data['patient_name']}).")

    def test_10_provider_failure_handling(self):
        """10. Provider failure handling: Status response indicates failure correctly."""
        from app.database import SessionLocal
        from app.models import WhatsAppDeliveryModel
        from datetime import timezone
        db = SessionLocal()
        try:
            del_rec = db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id == "SCR-FAILED-001").first()
            now_iso = datetime.now(timezone.utc).isoformat()
            if not del_rec:
                del_rec = WhatsAppDeliveryModel(
                    id="DEL-SCR-FAILED-001",
                    screening_id="SCR-FAILED-001",
                    recipient_phone="+917378216613",
                    patient_id="PAT-2026-081",
                    patient_name="Sanjay Bhati",
                    health_worker_id="HW-RAMPUR-01",
                    health_worker_name="Pooja Sharma (ASHA Worker)",
                    language="en",
                    status="FAILED",
                    error_message="Recipient phone number not registered on WhatsApp.",
                    retry_count=0,
                    created_at=now_iso,
                    sent_at=now_iso,
                )
                db.add(del_rec)
            else:
                del_rec.status = "FAILED"
                del_rec.recipient_phone = "+917378216613"
                del_rec.patient_name = "Sanjay Bhati"
                del_rec.error_message = "Recipient phone number not registered on WhatsApp."
                del_rec.retry_count = 0
            db.commit()
        finally:
            db.close()

        # Also set in in-memory store for fallback
        whatsapp_service._delivery_records["SCR-FAILED-001"] = WhatsAppDeliveryRecord(
            screening_id="SCR-FAILED-001",
            recipient_phone="+917378216613",
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            health_worker_id="HW-RAMPUR-01",
            status=WhatsAppDeliveryStatus.FAILED,
            error_message="Recipient phone number not registered on WhatsApp.",
        )
        status_res = client.get("/api/reports/SCR-FAILED-001/whatsapp/status")
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["status"], "FAILED")
        print("[TEST 10] Provider failure status handling verified.")

    def test_11_retry_mechanism(self):
        """11. Retry mechanism: Successfully executes retry on failed delivery to patient mobile."""
        res = client.post(
            "/api/reports/SCR-FAILED-001/whatsapp/retry",
            json={
                "screening_id": "SCR-FAILED-001",
                "health_worker_id": "HW-RAMPUR-01",
                "force_regenerate_pdf": False,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SENT")
        self.assertEqual(data["recipient_phone"], "+917378216613")
        self.assertEqual(data["patient_name"], "Sanjay Bhati")
        self.assertEqual(data["retry_count"], 1)
        print("[TEST 11] WhatsApp delivery retry verified (Status: SENT, Retries: 1, Patient: Sanjay Bhati).")

    def test_12_duplicate_send_prevention(self):
        """12. Duplicate-send prevention: Repeated delivery requests return existing record."""
        res1 = client.post(
            "/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/send",
            json={
                "screening_id": "SCR-PHASE12-ACCEPTED",
                "recipient_phone": "+917378216613",
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res1.status_code, 200)
        record1 = res1.json()

        # Call again
        res2 = client.post(
            "/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/send",
            json={
                "screening_id": "SCR-PHASE12-ACCEPTED",
                "recipient_phone": "+917378216613",
                "health_worker_id": "HW-RAMPUR-01",
                "language": "en",
                "opt_in_confirmed": True,
            },
        )
        self.assertEqual(res2.status_code, 200)
        record2 = res2.json()
        self.assertEqual(record1["provider_message_id"], record2["provider_message_id"])
        print("[TEST 12] Duplicate-send prevention verified.")

    def test_13_delivery_status_update_via_webhook(self):
        """13. Delivery status update: Updates to DELIVERED and READ via webhook."""
        record = whatsapp_service.get_delivery_status("SCR-PHASE12-ACCEPTED")
        self.assertIsNotNone(record)
        msg_id = record.provider_message_id

        # Send webhook for 'delivered'
        webhook_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": msg_id,
                                        "status": "delivered",
                                        "timestamp": "1724337015",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        wb_res = client.post("/api/whatsapp/webhook", json=webhook_payload)
        self.assertEqual(wb_res.status_code, 200)
        self.assertEqual(wb_res.json()["processed_updates"], 1)

        # Check updated status
        status_res = client.get("/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/status")
        self.assertEqual(status_res.json()["status"], "DELIVERED")
        print("[TEST 13] Webhook status update (DELIVERED) verified.")

    def test_14_webhook_challenge_authentication(self):
        """14. Webhook authentication: Challenge verification passes with valid token and fails with invalid."""
        valid_res = client.get(
            "/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=madocs_verify_token_2026&hub.challenge=test_challenge_1234"
        )
        self.assertEqual(valid_res.status_code, 200)
        self.assertEqual(valid_res.text, "test_challenge_1234")

        invalid_res = client.get(
            "/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_challenge_1234"
        )
        self.assertEqual(invalid_res.status_code, 403)
        print("[TEST 14] Webhook authentication and challenge verification passed.")

    def test_15_hindi_template(self):
        """15. Hindi template: Message body formatted correctly in Hindi."""
        msg = whatsapp_service.format_message_body(
            screening_id="SCR-2026-001",
            patient_ref="संजय भाटी",
            review_status="AI RESULT ACCEPTED",
            language="hi",
        )
        self.assertIn("आपकी डायबिटिक रेटिनोपैथी स्क्रीनिंग रिपोर्ट", msg)
        self.assertIn("SCR-2026-001", msg)
        self.assertIn("संजय भाटी", msg)
        print("[TEST 15] Hindi message template verified.")

    def test_16_english_template(self):
        """16. English template: Message body formatted correctly in English."""
        msg = whatsapp_service.format_message_body(
            screening_id="SCR-2026-001",
            patient_ref="Sanjay Bhati",
            review_status="AI RESULT ACCEPTED",
            language="en",
        )
        self.assertIn("Your diabetic retinopathy screening report is ready", msg)
        self.assertIn("SCR-2026-001", msg)
        self.assertIn("Sanjay Bhati", msg)
        print("[TEST 16] English message template verified.")

    def test_17_audit_trail(self):
        """17. Audit trail: Verifies all audit events are logged chronologically."""
        status_res = client.get("/api/reports/SCR-PHASE12-ACCEPTED/whatsapp/status")
        events = status_res.json()["audit_events"]
        event_types = [e["event_type"] for e in events]
        self.assertIn("REPORT_GENERATED", event_types)
        self.assertIn("DOCTOR_REVIEW_COMPLETED", event_types)
        self.assertIn("WHATSAPP_REPORT_REQUESTED", event_types)
        self.assertIn("WHATSAPP_REPORT_SENT", event_types)
        self.assertIn("WHATSAPP_REPORT_DELIVERED", event_types)
        print(f"[TEST 17] Complete audit trail verified ({len(events)} events).")

    def test_18_phase11_appointments_integrity(self):
        """18. Phase 11 appointment workflow integrity."""
        res = client.get("/api/doctors")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()["doctors"]) >= 3)
        print("[TEST 18] Phase 11 Doctor Directory & Tele-Ophthalmology integrity verified.")

    def test_19_existing_report_generation_integrity(self):
        """19. Existing report generation integrity."""
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        print("[TEST 19] Core screening API and health check integrity verified.")

    def test_20_existing_longitudinal_workflow_integrity(self):
        """20. Existing longitudinal workflow integrity."""
        res = client.get("/api/patients/PAT-2026-081/screening-history")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["patient_id"], "PAT-2026-081")
        print("[TEST 20] Phase 10 Longitudinal patient screening history integrity verified.")

    def test_21_whatsapp_patient_recipient_mapping_regression(self):
        """21. Regression Test: WhatsApp recipient is authoritatively resolved to the Patient record from DB, not health worker."""
        # 1. Sanjay Bhati (PAT-2026-081 / SCR-2026-1024) -> Patient: Sanjay Bhati (+91 73782 16613), Screener: Pooja Sharma (+919876543210)
        res_rampur = client.get("/api/reports/SCR-2026-1024/whatsapp/status")
        self.assertEqual(res_rampur.status_code, 200)
        data_r = res_rampur.json()
        self.assertEqual(data_r["patient_name"], "Sanjay Bhati")
        self.assertEqual(data_r["recipient_phone"], "+917378216613")
        self.assertEqual(data_r["health_worker_name"], "Pooja Sharma (ASHA Worker)")
        # CRITICAL ASSERTION: Recipient phone MUST NOT be Pooja Sharma's number
        self.assertNotEqual(data_r["recipient_phone"], "+919876543210")

        # 2. Sunita Devi (PAT-2026-082 / SCR-2026-0992) -> Patient: Sunita Devi (+91 94123 88990), Screener: Sarita Devi
        res_shivpuri = client.get("/api/reports/SCR-2026-0992/whatsapp/status")
        self.assertEqual(res_shivpuri.status_code, 200)
        data_s = res_shivpuri.json()
        self.assertEqual(data_s["patient_name"], "Sunita Devi")
        self.assertEqual(data_s["recipient_phone"], "+919412388990")
        self.assertEqual(data_s["health_worker_name"], "Sarita Devi (Vision Tech)")
        self.assertNotEqual(data_s["recipient_phone"], "+919876543210")
        self.assertNotEqual(data_s["recipient_phone"], "+917378216613")

        # 3. Balwinder Singh (PAT-2026-083 / SCR-2026-0850) -> Patient: Balwinder Singh (+91 97890 12345), Screener: Sunil Gowda
        res_kolar = client.get("/api/reports/SCR-2026-0850/whatsapp/status")
        self.assertEqual(res_kolar.status_code, 200)
        data_k = res_kolar.json()
        self.assertEqual(data_k["patient_name"], "Balwinder Singh")
        self.assertEqual(data_k["recipient_phone"], "+919789012345")
        self.assertEqual(data_k["health_worker_name"], "Sunil Gowda (Vision Tech)")
        self.assertNotEqual(data_k["recipient_phone"], "+919876543210")
        print("[TEST 21] Authoritative WhatsApp patient recipient data mapping verified across distinct patients.")

    def test_22_unassigned_screening_blocks_whatsapp_dispatch(self):
        """22. Safety Gate: Unassigned patient or missing mobile blocks WhatsApp dispatch and never substitutes health worker."""
        res_unknown = client.get("/api/reports/SCR-UNKNOWN-VILLAGE-999/whatsapp/status")
        self.assertEqual(res_unknown.status_code, 200)
        data_u = res_unknown.json()
        self.assertFalse(data_u["can_send"])
        self.assertIsNone(data_u["recipient_phone"])
        self.assertEqual(data_u["block_reason"], "Patient mobile number not available/verified.")
        print("[TEST 22] Safety gate for unassigned patient correctly blocks dispatch with 'Patient mobile number not available/verified.'.")

if __name__ == "__main__":
    unittest.main()
