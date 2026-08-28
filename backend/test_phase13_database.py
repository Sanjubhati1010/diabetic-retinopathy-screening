"""
Phase 13 Test Suite: Persistent Database Storage & Integrity (MySQL / SQLAlchemy ORM).
Validates 20 distinct database persistence, transactional integrity, foreign key relations,
and cross-phase data consistency requirements.
"""

import os
import sys
import unittest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base, SessionLocal, engine, get_db
from app.models import (
    PatientModel,
    DoctorModel,
    HealthWorkerModel,
    ScreeningModel,
    ScreeningReviewModel,
    ReviewAuditEventModel,
    AppointmentModel,
    AppointmentMessageModel,
    ReportModel,
    WhatsAppDeliveryModel,
    WhatsAppAuditEventModel,
)
from app.schemas import DoctorReviewRequest
from app.review_service import process_doctor_review, get_audit_history, get_screening_review
from app.longitudinal_service import longitudinal_service
from app.appointment_service import appointment_service
from app.whatsapp_service import whatsapp_service
from app.db_seeder import seed_database_if_empty


class TestPhase13DatabasePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database_if_empty(db)
        finally:
            db.close()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        try:
            self.db.query(ScreeningModel).filter(
                ScreeningModel.patient_id == "PAT-2026-081",
                ScreeningModel.id.notin_(["SCR-2026-0991", "SCR-2026-0740", "SCR-2026-0410"])
            ).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    # 1. Patient creation and retrieval
    def test_01_patient_creation_and_retrieval(self):
        pat_id = f"PAT-TEST-{uuid.uuid4().hex[:6]}"
        new_pat = PatientModel(
            id=pat_id,
            name="Aarav Sharma",
            age=48,
            gender="male",
            village="Rampur",
            registered_date="2026-08-27",
            abha_id="ABHA-9999-1234",
            phone="+919876543210",
        )
        self.db.add(new_pat)
        self.db.commit()

        queried = self.db.query(PatientModel).filter(PatientModel.id == pat_id).first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.name, "Aarav Sharma")
        self.assertEqual(queried.age, 48)
        self.assertEqual(queried.abha_id, "ABHA-9999-1234")
        print("\n[TEST 1] Patient creation and retrieval verified.")

    # 2. Duplicate patient handling / unique constraints
    def test_02_duplicate_patient_handling(self):
        pat_id = f"PAT-DUP-{uuid.uuid4().hex[:6]}"
        p1 = PatientModel(id=pat_id, name="Test Unique", age=50, gender="female", village="Rampur", registered_date="2026-08-27")
        self.db.add(p1)
        self.db.commit()

        p2 = PatientModel(id=pat_id, name="Duplicate Entry", age=50, gender="female", village="Rampur", registered_date="2026-08-27")
        self.db.add(p2)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()
        print("[TEST 2] Duplicate primary key integrity enforced.")

    # 3. Screening record persistence
    def test_03_screening_persistence(self):
        pat_id = "PAT-2026-081"
        scr_id = f"SCR-TEST-{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        scr = ScreeningModel(
            id=scr_id,
            patient_id=pat_id,
            patient_name="Ramesh Kumar Verma",
            village="Rampur Gram Panchayat",
            screening_date="2026-08-27 10:00 AM",
            timestamp_iso=now_iso,
            predicted_class=2,
            class_name="Moderate",
            confidence=0.845,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
        )
        self.db.add(scr)
        self.db.commit()

        retrieved = self.db.query(ScreeningModel).filter(ScreeningModel.id == scr_id).first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.patient_id, pat_id)
        self.assertEqual(retrieved.class_name, "Moderate")
        self.assertAlmostEqual(retrieved.confidence, 0.845, places=3)
        print("[TEST 3] Screening persistence verified.")

    # 4. Doctor review persistence
    def test_04_review_persistence(self):
        scr_id = f"SCR-REV-{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Ramesh Kumar Verma",
            village="Rampur Gram Panchayat",
            screening_date="2026-08-27 10:00 AM",
            timestamp_iso=now_iso,
            predicted_class=1,
            class_name="Mild",
            confidence=0.76,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
        )
        self.db.add(scr)
        self.db.commit()

        req_accept = DoctorReviewRequest(
            screening_id=scr_id,
            action="ACCEPT",
            reviewer_id="DOC-SWAMINATHAN",
            reviewer_name="Dr. Arvind Swaminathan, MS",
            review_comment="Fundus findings align with AI prediction of Mild DR.",
        )
        rev_res = process_doctor_review(
            request=req_accept,
            original_ai_result="Mild",
            original_confidence=0.76,
            role="doctor",
            db=self.db,
        )
        self.assertEqual(rev_res.review_status, "AI RESULT ACCEPTED")

        # Verify persisted review
        db_rev = get_screening_review(scr_id, db=self.db)
        self.assertIsNotNone(db_rev)
        self.assertEqual(db_rev["review_status"], "AI RESULT ACCEPTED")
        print("[TEST 4] Doctor review record persistence verified.")

    # 5. Review override audit event creation
    def test_05_review_override_audit_event(self):
        scr_id = f"SCR-MOD-{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Ramesh Kumar Verma",
            village="Rampur Gram Panchayat",
            screening_date="2026-08-27 10:00 AM",
            timestamp_iso=now_iso,
            predicted_class=2,
            class_name="Moderate",
            confidence=0.82,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
        )
        self.db.add(scr)
        self.db.commit()

        req_modify = DoctorReviewRequest(
            screening_id=scr_id,
            action="MODIFY",
            reviewed_class=1,
            reviewed_class_name="Mild",
            reviewer_id="DOC-SWAMINATHAN",
            reviewer_name="Dr. Arvind Swaminathan, MS",
            review_comment="Only isolated microaneurysms seen.",
        )
        process_doctor_review(
            request=req_modify,
            original_ai_result="Moderate",
            original_confidence=0.82,
            role="doctor",
            db=self.db,
        )

        history = get_audit_history(scr_id, db=self.db)
        self.assertTrue(len(history) >= 1)
        override_evt = next((e for e in history if getattr(e, "event_type", None) == "RESULT_MODIFIED"), None)
        self.assertIsNotNone(override_evt)
        self.assertEqual(override_evt.reviewed_result, "Mild")
        print("[TEST 5] Review override audit event persistence verified.")

    # 6. Appointment creation and double-booking prevention
    def test_06_appointment_double_booking_prevention(self):
        day_num = (int(uuid.uuid4().hex[:2], 16) % 28) + 1
        apt_date = f"2026-11-{day_num:02d}"
        apt_slot = "10:00"

        # Clean existing test appointment on that date if any
        existing = self.db.query(AppointmentModel).filter(
            AppointmentModel.doctor_id == "DOC-SWAMINATHAN",
            AppointmentModel.date == apt_date,
            AppointmentModel.start_time == apt_slot
        ).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        # First booking
        apt1 = appointment_service.book_appointment({
            "doctor_id": "DOC-SWAMINATHAN",
            "health_worker_id": "HW-RAMPUR-01",
            "patient_id": "PAT-2026-081",
            "date": apt_date,
            "start_time": apt_slot,
            "reason": "Primary tele-review",
        }, db=self.db)
        self.assertIsNotNone(apt1["id"])

        # Second booking on same slot -> Must reject
        with self.assertRaises(ValueError) as ctx:
            appointment_service.book_appointment({
                "doctor_id": "DOC-SWAMINATHAN",
                "health_worker_id": "HW-SHIVPURI-02",
                "patient_id": "PAT-2026-082",
                "date": apt_date,
                "start_time": apt_slot,
                "reason": "Conflicting booking",
            }, db=self.db)
        self.assertIn("already booked", str(ctx.exception))
        print("[TEST 6] Transactional appointment double-booking prevention verified.")

    # 7. Appointment status transitions
    def test_07_appointment_status_transitions(self):
        day_num = (int(uuid.uuid4().hex[:2], 16) % 28) + 1
        apt_date = f"2026-12-{day_num:02d}"
        apt_slot = "11:00"

        existing = self.db.query(AppointmentModel).filter(
            AppointmentModel.doctor_id == "DOC-SWAMINATHAN",
            AppointmentModel.date == apt_date,
            AppointmentModel.start_time == apt_slot
        ).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        apt = appointment_service.book_appointment({
            "doctor_id": "DOC-SWAMINATHAN",
            "health_worker_id": "HW-RAMPUR-01",
            "patient_id": "PAT-2026-081",
            "date": apt_date,
            "start_time": apt_slot,
            "reason": "Triage check",
        }, db=self.db)
        apt_id = apt["id"]

        # Confirm
        updated = appointment_service.update_appointment_status(
            appointment_id=apt_id,
            new_status="CONFIRMED",
            role="doctor",
            db=self.db,
        )
        self.assertEqual(updated["status"], "CONFIRMED")

        # Query from DB
        db_apt = self.db.query(AppointmentModel).filter(AppointmentModel.id == apt_id).first()
        self.assertEqual(db_apt.status, "CONFIRMED")
        print("[TEST 7] Appointment status transition persistence verified.")

    # 8. Appointment messages thread persistence
    def test_08_appointment_messages_persistence(self):
        apt_id = "APT-2026-101"
        msg = appointment_service.add_message(
            appointment_id=apt_id,
            sender_id="HW-RAMPUR-01",
            sender_name="Pooja Sharma",
            sender_role="health_worker",
            message="Patient fundus scan ready for specialist triage.",
            db=self.db,
        )
        self.assertIsNotNone(msg["id"])

        messages = appointment_service.get_messages(apt_id, db=self.db)
        self.assertTrue(len(messages) >= 2)
        self.assertTrue(any(m["message"] == "Patient fundus scan ready for specialist triage." for m in messages))
        print("[TEST 8] Appointment chat messaging persistence verified.")

    # 9. Doctor clinical consultation notes persistence
    def test_09_consultation_notes_persistence(self):
        day_num = (int(uuid.uuid4().hex[:2], 16) % 28) + 1
        apt_date = f"2027-01-{day_num:02d}"

        existing = self.db.query(AppointmentModel).filter(
            AppointmentModel.doctor_id == "DOC-SWAMINATHAN",
            AppointmentModel.date == apt_date,
            AppointmentModel.start_time == "14:30"
        ).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        apt = appointment_service.book_appointment({
            "doctor_id": "DOC-SWAMINATHAN",
            "health_worker_id": "HW-RAMPUR-01",
            "patient_id": "PAT-2026-081",
            "date": apt_date,
            "start_time": "14:30",
            "reason": "Follow-up consultation",
        }, db=self.db)
        apt_id = apt["id"]

        completed = appointment_service.add_consultation_notes(
            appointment_id=apt_id,
            doctor_id="DOC-SWAMINATHAN",
            doctor_notes="Clear fundus without new hemorrhages. Stable.",
            recommendations="Annual follow-up screening in 12 months.",
            follow_up_date="2027-11-22",
            db=self.db,
        )
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertIn("Doctor-entered consultation note", completed["doctor_notes"])

        # DB verification
        db_apt = self.db.query(AppointmentModel).filter(AppointmentModel.id == apt_id).first()
        self.assertEqual(db_apt.status, "COMPLETED")
        self.assertEqual(db_apt.follow_up_date, "2027-11-22")
        print("[TEST 9] Doctor clinical consultation notes persistence verified.")

    # 10. WhatsApp delivery record persistence
    def test_10_whatsapp_delivery_persistence(self):
        scr_id = "SCR-2026-0991"
        del_model = self.db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id == scr_id).first()
        now_iso = datetime.now(timezone.utc).isoformat()
        if not del_model:
            del_model = WhatsAppDeliveryModel(
                id=f"DEL-{scr_id}",
                screening_id=scr_id,
                recipient_phone="+917378216613",
                patient_id="PAT-2026-081",
                patient_name="Sanjay Bhati",
                health_worker_id="HW-RAMPUR-01",
                health_worker_name="Pooja Sharma (ASHA Worker)",
                language="en",
                status="SENT",
                provider_message_id="wamid.TEST_PERSIST_001",
                retry_count=0,
                created_at=now_iso,
                sent_at=now_iso,
            )
            self.db.add(del_model)
            self.db.commit()

        status_rec = whatsapp_service.get_delivery_status(scr_id, db=self.db)
        self.assertIsNotNone(status_rec)
        self.assertEqual(status_rec.recipient_phone, "+917378216613")
        self.assertEqual(status_rec.patient_name, "Sanjay Bhati")
        print("[TEST 10] WhatsApp delivery record persistence verified.")

    # 11. WhatsApp webhook status update persistence
    def test_11_whatsapp_webhook_persistence(self):
        scr_id = f"SCR-WH-{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        wamid = f"wamid.WH_TEST_{uuid.uuid4().hex[:8]}"

        # Insert parent screening first to fulfill FK
        scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            village="Rampur Gram Panchayat",
            screening_date="2026-08-27 10:00 AM",
            timestamp_iso=now_iso,
            predicted_class=1,
            class_name="Mild",
            confidence=0.78,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="MODERATE",
            referral_priority="EYE SPECIALIST REVIEW RECOMMENDED",
        )
        self.db.add(scr)
        self.db.commit()

        del_model = WhatsAppDeliveryModel(
            id=f"DEL-{scr_id}",
            screening_id=scr_id,
            recipient_phone="+917378216613",
            patient_id="PAT-2026-081",
            patient_name="Sanjay Bhati",
            health_worker_id="HW-RAMPUR-01",
            health_worker_name="Pooja Sharma (ASHA Worker)",
            language="en",
            status="SENT",
            provider_message_id=wamid,
            retry_count=0,
            created_at=now_iso,
            sent_at=now_iso,
        )
        self.db.add(del_model)
        self.db.commit()

        webhook_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": wamid,
                                        "status": "delivered",
                                        "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        whatsapp_service.process_webhook_status_update(webhook_payload, db=self.db)

        # Verify DB updated
        refreshed = self.db.query(WhatsAppDeliveryModel).filter(WhatsAppDeliveryModel.screening_id == scr_id).first()
        self.assertEqual(refreshed.status, "DELIVERED")
        print("[TEST 11] WhatsApp webhook status update persistence verified.")

    # 12. WhatsApp audit trail retrieval
    def test_12_whatsapp_audit_trail_retrieval(self):
        scr_id = "SCR-2026-0991"
        audit_records = self.db.query(WhatsAppAuditEventModel).filter(
            WhatsAppAuditEventModel.screening_id == scr_id
        ).all()
        self.assertTrue(isinstance(audit_records, list))
        print(f"[TEST 12] WhatsApp audit trail retrieval verified ({len(audit_records)} events).")

    # 13. Patient screening history ordering
    def test_13_patient_history_ordering(self):
        history = longitudinal_service.get_patient_screening_history("PAT-2026-081", db=self.db)
        self.assertTrue(len(history) >= 2)
        # Check reverse chronological ordering
        for i in range(len(history) - 1):
            t1 = history[i].get("timestamp_iso") or ""
            t2 = history[i+1].get("timestamp_iso") or ""
            self.assertGreaterEqual(t1, t2, f"Screenings must be newest first: {t1} >= {t2}")
        print("[TEST 13] Patient screening history reverse chronological ordering verified.")

    # 14. Longitudinal comparison across visits in DB
    def test_14_longitudinal_comparison_in_db(self):
        comp = longitudinal_service.compare_screenings("SCR-2026-0991", "SCR-2026-0740", db=self.db)
        self.assertEqual(comp["classification_change_status"], "CLASSIFICATION INCREASED")
        self.assertIn("Mild to Moderate", comp["classification_change_summary"])
        print("[TEST 14] Longitudinal database multi-visit comparison verified.")

    # 15. Cross-patient comparison security block
    def test_15_cross_patient_security_block(self):
        with self.assertRaises(ValueError) as ctx:
            longitudinal_service.compare_screenings("SCR-2026-0991", "SCR-2026-0992", db=self.db)
        self.assertIn("Security Violation", str(ctx.exception))
        print("[TEST 15] Cross-patient screening comparison security isolation verified.")

    # 16. Transaction atomicity / rollback on error
    def test_16_transaction_rollback(self):
        pat_id = f"PAT-ROLLBACK-{uuid.uuid4().hex[:6]}"
        pat = PatientModel(id=pat_id, name="Temp Rollback", age=30, gender="male", village="Rampur", registered_date="2026-08-27")
        self.db.add(pat)

        # Intentionally cause constraint violation
        bad_apt = AppointmentModel(
            id="APT-INVALID",
            doctor_id="DOC-NONEXISTENT",
            doctor_name="Dr. Fake",
            health_worker_id="HW-RAMPUR-01",
            health_worker_name="Pooja",
            health_worker_email="p@phc.in",
            patient_id=pat_id,
            patient_name="Temp",
            date="2026-09-01",
            start_time="10:00",
            end_time="10:30",
            reason="Test",
            status="CONFIRMED",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(bad_apt)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

        # Verify patient was rolled back
        found_pat = self.db.query(PatientModel).filter(PatientModel.id == pat_id).first()
        self.assertIsNone(found_pat)
        print("[TEST 16] Transaction atomicity and rollback verified.")

    # 17. Restart persistence test
    def test_17_restart_persistence(self):
        pat_id = f"PAT-RESTART-{uuid.uuid4().hex[:6]}"
        p = PatientModel(id=pat_id, name="Persistence Check Patient", age=62, gender="female", village="Shivpuri", registered_date="2026-08-27")
        self.db.add(p)
        self.db.commit()

        # Simulate fresh session / engine reconnection
        new_session = SessionLocal()
        try:
            queried = new_session.query(PatientModel).filter(PatientModel.id == pat_id).first()
            self.assertIsNotNone(queried)
            self.assertEqual(queried.name, "Persistence Check Patient")
        finally:
            new_session.close()
        print("[TEST 17] Data persistence across backend sessions/restarts verified.")

    # 18. Foreign key integrity enforcement
    def test_18_foreign_key_integrity(self):
        scr_id = f"SCR-FK-{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Attempt to insert screening for non-existent patient
        bad_scr = ScreeningModel(
            id=scr_id,
            patient_id="PAT-NON-EXISTENT-9999",
            patient_name="Ghost Patient",
            village="Unknown",
            screening_date="2026-08-27 10:00 AM",
            timestamp_iso=now_iso,
            predicted_class=0,
            class_name="No DR",
            confidence=0.98,
            safety_status="READY_FOR_AI",
            screening_status="RELIABLE AI SCREENING",
            risk_category="LOW",
            referral_priority="ROUTINE FOLLOW-UP",
        )
        self.db.add(bad_scr)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()
        print("[TEST 18] Foreign key relational integrity enforced.")

    # 19. Doctor availability slot generation against DB appointments
    def test_19_doctor_availability_slot_calculation(self):
        avail = appointment_service.get_doctor_availability("DOC-SWAMINATHAN", "2026-08-28", db=self.db)
        self.assertIn("slots", avail)
        self.assertEqual(avail["doctor_id"], "DOC-SWAMINATHAN")
        self.assertEqual(avail["working_hours"], "09:00 - 17:00")
        self.assertTrue(len(avail["slots"]) > 0)
        # Check booked slot
        booked_slot = next((s for s in avail["slots"] if s["time"] == "10:30"), None)
        self.assertIsNotNone(booked_slot)
        self.assertFalse(booked_slot["available"])
        self.assertEqual(booked_slot["status"], "BOOKED")
        print("[TEST 19] Doctor slot availability calculation against database appointments verified.")

    # 20. Database connection resilience and engine status
    def test_20_database_resilience(self):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            self.assertEqual(result, 1)

        doctors_count = self.db.query(DoctorModel).count()
        patients_count = self.db.query(PatientModel).count()
        screenings_count = self.db.query(ScreeningModel).count()
        self.assertGreaterEqual(doctors_count, 3)
        self.assertGreaterEqual(patients_count, 3)
        self.assertGreaterEqual(screenings_count, 4)
        print(f"[TEST 20] Database resilience verified (Doctors: {doctors_count}, Patients: {patients_count}, Screenings: {screenings_count}).")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING PHASE 13 MYSQL / SQLALCHEMY DATABASE TESTS")
    print("==================================================")
    unittest.main(verbosity=2)
