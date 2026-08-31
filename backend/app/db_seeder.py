"""
Initial Database Seeder for MADOCS DR Screening System.
Populates normalized initial demo records for Doctors, Health Workers, Patients,
and Canonical Longitudinal Screenings if the database tables are empty.
"""

import json
import logging
from sqlalchemy.orm import Session
from app.models import (
    PatientModel,
    DoctorModel,
    HealthWorkerModel,
    ScreeningModel,
    ScreeningReviewModel,
    ReviewAuditEventModel,
    AppointmentModel,
    AppointmentMessageModel,
)

logger = logging.getLogger("dr_backend.db_seeder")

DEMO_DOCTORS = [
    {
        "id": "DOC-SWAMINATHAN",
        "name": "Dr. Arvind Swaminathan, MS",
        "title": "Senior Consultant Ophthalmologist",
        "specialization": "Retina & Vitreous Specialist",
        "hospital": "District Hospital Tele-Ophthalmology Center",
        "location": "Varanasi, Uttar Pradesh",
        "languages_json": json.dumps(["English", "Hindi", "Tamil"]),
        "experience_years": 16,
        "is_demo": True,
        "status": "Available",
        "avatar_badge": "AS",
        "working_days_json": json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
        "working_hours_start": "09:00",
        "working_hours_end": "17:00",
        "slot_duration_minutes": 30,
        "rating": 4.9,
        "total_consultations": 342,
    },
    {
        "id": "DOC-NAMBIAR",
        "name": "Dr. Meera Nambiar, MD",
        "title": "Consultant Tele-Ophthalmologist",
        "specialization": "Comprehensive Ophthalmology & Diabetic Retinopathy Triage",
        "hospital": "Regional Institute of Ophthalmology",
        "location": "Prayagraj, Uttar Pradesh",
        "languages_json": json.dumps(["English", "Hindi", "Malayalam"]),
        "experience_years": 11,
        "is_demo": True,
        "status": "Available",
        "avatar_badge": "MN",
        "working_days_json": json.dumps(["Monday", "Wednesday", "Thursday", "Friday"]),
        "working_hours_start": "10:00",
        "working_hours_end": "16:00",
        "slot_duration_minutes": 30,
        "rating": 4.8,
        "total_consultations": 215,
    },
    {
        "id": "DOC-RAO",
        "name": "Dr. Rajeshwar Rao, MS",
        "title": "Community Ophthalmology Specialist",
        "specialization": "Diabetic Retinopathy Screening & Low-Resource Tele-Care",
        "hospital": "State Mobile Ophthalmology Health Mission",
        "location": "Lucknow, Uttar Pradesh",
        "languages_json": json.dumps(["English", "Hindi"]),
        "experience_years": 14,
        "is_demo": True,
        "status": "Busy",
        "avatar_badge": "RR",
        "working_days_json": json.dumps(["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
        "working_hours_start": "09:30",
        "working_hours_end": "16:30",
        "slot_duration_minutes": 30,
        "rating": 4.7,
        "total_consultations": 189,
    },
]

DEMO_HEALTH_WORKERS = [
    {
        "id": "HW-RAMPUR-01",
        "name": "Pooja Sharma (ASHA Worker)",
        "role": "health_worker",
        "phone": "+919876543210",
        "email": "asha.rampur@phc.in",
        "village": "Rampur Gram Panchayat",
        "phc_center": "Primary Health Center Rampur",
        "whatsapp_opt_in": True,
        "whatsapp_opt_in_date": "2026-08-01T09:00:00Z",
    },
    {
        "id": "HW-SHIVPURI-02",
        "name": "Sarita Devi (Vision Tech)",
        "role": "health_worker",
        "phone": "+919412388990",
        "email": "sarita.vision@phc.in",
        "village": "Shivpuri Taluk",
        "phc_center": "Sub-Center Shivpuri",
        "whatsapp_opt_in": True,
        "whatsapp_opt_in_date": "2026-08-05T10:00:00Z",
    },
    {
        "id": "HW-KOLAR-03",
        "name": "Sunil Gowda (Vision Tech)",
        "role": "health_worker",
        "phone": "+919789012345",
        "email": "sunil.gowda@phc.in",
        "village": "Kolar Rural Block",
        "phc_center": "Kolar Rural PHC",
        "whatsapp_opt_in": False,
        "whatsapp_opt_in_date": None,
    },
]

DEMO_PATIENTS = [
    {
        "id": "PAT-2026-081",
        "abha_id": "91-4829-1029-4821",
        "name": "Sanjay Bhati",
        "age": 58,
        "gender": "male",
        "phone": "+91 73782 16613",
        "email": "sanjay.bhati@example.com",
        "village": "Rampur Gram Panchayat",
        "district": "Varanasi",
        "diabetes_duration": 8,
        "last_hba1c": 8.6,
        "insulin_use": True,
        "visual_acuity_od": "6/12",
        "visual_acuity_os": "6/18",
        "symptoms_json": json.dumps(["blurredVision", "floaters"]),
        "registered_date": "2026-08-14",
        "last_screened": "2026-08-22",
        "latest_status": "dr2",
        "referral_urgency": "moderate",
        "doctor_verified": True,
    },
    {
        "id": "PAT-2026-082",
        "abha_id": "91-7712-3904-1182",
        "name": "Sunita Devi",
        "age": 52,
        "gender": "female",
        "phone": "+91 94123 88990",
        "email": "sunita.devi@example.com",
        "village": "Shivpuri Taluk",
        "district": "Varanasi",
        "diabetes_duration": 12,
        "last_hba1c": 9.8,
        "insulin_use": True,
        "visual_acuity_od": "6/18",
        "visual_acuity_os": "6/24",
        "symptoms_json": json.dumps(["blurredVision", "nightBlindness"]),
        "registered_date": "2026-08-18",
        "last_screened": "2026-08-22",
        "latest_status": "dr3",
        "referral_urgency": "urgent",
        "doctor_verified": True,
    },
    {
        "id": "PAT-2026-083",
        "abha_id": "91-3349-8012-9901",
        "name": "Balwinder Singh",
        "age": 46,
        "gender": "male",
        "phone": "+91 97890 12345",
        "email": None,
        "village": "Kolar Rural Block",
        "district": "Kolar",
        "diabetes_duration": 3,
        "last_hba1c": 6.8,
        "insulin_use": False,
        "visual_acuity_od": "6/6",
        "visual_acuity_os": "6/6",
        "symptoms_json": json.dumps(["noneSymptoms"]),
        "registered_date": "2026-08-10",
        "last_screened": "2026-08-21",
        "latest_status": "dr0",
        "referral_urgency": "routine",
        "doctor_verified": True,
    },
    {
        "id": "PAT-2026-084",
        "abha_id": "91-8890-2134-5567",
        "name": "Lakshmi Patel",
        "age": 64,
        "gender": "female",
        "phone": "+91 91234 56780",
        "email": "lakshmi.patel@example.com",
        "village": "Mandya East Sector",
        "district": "Mandya",
        "diabetes_duration": 15,
        "last_hba1c": 10.2,
        "insulin_use": True,
        "visual_acuity_od": "6/24",
        "visual_acuity_os": "6/36",
        "symptoms_json": json.dumps(["blurredVision", "distortedVision", "floaters"]),
        "registered_date": "2026-08-05",
        "last_screened": "2026-08-19",
        "latest_status": "dr4",
        "referral_urgency": "critical",
        "doctor_verified": False,
    },
]

DEMO_SCREENINGS = [
    # Patient PAT-2026-081 (Sanjay Bhati) - 3 Visits
    {
        "id": "SCR-2026-0991",
        "patient_id": "PAT-2026-081",
        "patient_name": "Sanjay Bhati",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-08-22 10:45 AM",
        "timestamp_iso": "2026-08-22T10:45:00Z",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.85,
        "probabilities_json": json.dumps({"No DR": 0.02, "Mild": 0.08, "Moderate": 0.85, "Severe": 0.04, "Proliferative DR": 0.01}),
        "dr_severity_od": "dr2",
        "dr_severity_os": "dr1",
        "overall_severity": "dr2",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "risk_explanation": "Features consistent with moderate diabetic retinopathy detected.",
        "referral_guidance": "Eye specialist review is recommended within 2-4 weeks.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
    {
        "id": "SCR-2026-0740",
        "patient_id": "PAT-2026-081",
        "patient_name": "Sanjay Bhati",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-06-15 11:20 AM",
        "timestamp_iso": "2026-06-15T11:20:00Z",
        "predicted_class": 1,
        "class_name": "Mild",
        "confidence": 0.78,
        "probabilities_json": json.dumps({"No DR": 0.12, "Mild": 0.78, "Moderate": 0.08, "Severe": 0.01, "Proliferative DR": 0.01}),
        "dr_severity_od": "dr1",
        "dr_severity_os": "dr0",
        "overall_severity": "dr1",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "risk_explanation": "Features consistent with mild diabetic retinopathy detected.",
        "referral_guidance": "Annual follow-up screening recommended.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
    {
        "id": "SCR-2026-0410",
        "patient_id": "PAT-2026-081",
        "patient_name": "Sanjay Bhati",
        "village": "Rampur Gram Panchayat",
        "screening_date": "2026-03-20 09:30 AM",
        "timestamp_iso": "2026-03-20T09:30:00Z",
        "predicted_class": 1,
        "class_name": "Mild",
        "confidence": 0.82,
        "probabilities_json": json.dumps({"No DR": 0.08, "Mild": 0.82, "Moderate": 0.08, "Severe": 0.01, "Proliferative DR": 0.01}),
        "dr_severity_od": "dr1",
        "dr_severity_os": "dr0",
        "overall_severity": "dr1",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "risk_explanation": "No diabetic retinopathy detected.",
        "referral_guidance": "Annual follow-up screening recommended.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
    # Patient PAT-2026-082 (Sunita Devi) - 2 Visits
    {
        "id": "SCR-2026-0992",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "village": "Shivpuri Taluk",
        "screening_date": "2026-08-22 02:30 PM",
        "timestamp_iso": "2026-08-22T14:30:00Z",
        "predicted_class": 3,
        "class_name": "Severe",
        "confidence": 0.89,
        "probabilities_json": json.dumps({"No DR": 0.01, "Mild": 0.02, "Moderate": 0.05, "Severe": 0.89, "Proliferative DR": 0.03}),
        "dr_severity_od": "dr3",
        "dr_severity_os": "dr2",
        "overall_severity": "dr3",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "HIGH",
        "referral_priority": "PRIORITY SPECIALIST REVIEW",
        "risk_explanation": "Severe NPDR features detected with multiple retinal hemorrhages.",
        "referral_guidance": "Urgent ophthalmology referral required within 1-2 weeks.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
    {
        "id": "SCR-2026-0612",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "village": "Shivpuri Taluk",
        "screening_date": "2026-05-10 10:00 AM",
        "timestamp_iso": "2026-05-10T10:00:00Z",
        "predicted_class": 2,
        "class_name": "Moderate",
        "confidence": 0.82,
        "probabilities_json": json.dumps({"No DR": 0.03, "Mild": 0.10, "Moderate": 0.82, "Severe": 0.04, "Proliferative DR": 0.01}),
        "dr_severity_od": "dr2",
        "dr_severity_os": "dr1",
        "overall_severity": "dr2",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "risk_explanation": "Moderate diabetic retinopathy features present.",
        "referral_guidance": "Specialist referral recommended.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
    # Patient PAT-2026-083 (Balwinder Singh) - 1 Visit
    {
        "id": "SCR-2026-0993",
        "patient_id": "PAT-2026-083",
        "patient_name": "Balwinder Singh",
        "village": "Kolar Rural Block",
        "screening_date": "2026-08-21 03:45 PM",
        "timestamp_iso": "2026-08-21T15:45:00Z",
        "predicted_class": 0,
        "class_name": "No DR",
        "confidence": 0.96,
        "probabilities_json": json.dumps({"No DR": 0.96, "Mild": 0.03, "Moderate": 0.005, "Severe": 0.003, "Proliferative DR": 0.002}),
        "dr_severity_od": "dr0",
        "dr_severity_os": "dr0",
        "overall_severity": "dr0",
        "safety_status": "READY_FOR_AI",
        "screening_status": "RELIABLE AI SCREENING",
        "risk_category": "LOW",
        "referral_priority": "ROUTINE FOLLOW-UP",
        "risk_explanation": "Healthy retinal background observed.",
        "referral_guidance": "Routine annual screening recommended.",
        "safety_message": "AI Safety Gate cleared.",
        "gradcam_url": "/samples/gradcam_od.png",
        "heatmap_url": "/samples/heatmap_od.png",
        "image_od_path": "/samples/eyes.png",
        "image_os_path": "/samples/eyes_os.png",
        "doctor_status": "verified",
        "review_status": "AI RESULT ACCEPTED",
    },
]

DEMO_APPOINTMENTS = [
    {
        "id": "APT-2026-101",
        "doctor_id": "DOC-SWAMINATHAN",
        "doctor_name": "Dr. Arvind Swaminathan, MS",
        "health_worker_id": "HW-RAMPUR-01",
        "health_worker_name": "Pooja Sharma (ASHA Worker)",
        "health_worker_email": "asha.rampur@phc.in",
        "patient_id": "PAT-2026-081",
        "patient_name": "Sanjay Bhati",
        "patient_age": 58,
        "patient_gender": "male",
        "village": "Rampur Gram Panchayat",
        "screening_id": "SCR-2026-0991",
        "screening_summary": "Moderate NPDR (AI Confidence 85.00%)",
        "date": "2026-09-01",
        "start_time": "10:30",
        "end_time": "11:00",
        "reason": "AI screening indicates increase from Mild NPDR to Moderate NPDR. Blurring reported in right eye.",
        "status": "CONFIRMED",
        "created_at": "2026-08-27T10:00:00Z",
        "updated_at": "2026-08-27T11:30:00Z",
        "doctor_notes": None,
        "doctor_recommendation": None,
        "follow_up_date": None,
    },
    {
        "id": "APT-2026-102",
        "doctor_id": "DOC-SWAMINATHAN",
        "doctor_name": "Dr. Arvind Swaminathan, MS",
        "health_worker_id": "HW-SHIVPURI-02",
        "health_worker_name": "Sarita Devi (Vision Tech)",
        "health_worker_email": "sarita.vision@phc.in",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "patient_age": 52,
        "patient_gender": "female",
        "village": "Shivpuri Taluk",
        "screening_id": "SCR-2026-0992",
        "screening_summary": "Severe NPDR (Urgent Specialist Review Recommended)",
        "date": "2026-09-01",
        "start_time": "11:15",
        "end_time": "11:45",
        "reason": "Severe NPDR detected with retinal hemorrhages. Urgent specialist consultation required.",
        "status": "CONFIRMED",
        "created_at": "2026-08-27T14:30:00Z",
        "updated_at": "2026-08-27T15:00:00Z",
        "doctor_notes": None,
        "doctor_recommendation": None,
        "follow_up_date": None,
    },
    {
        "id": "APT-2026-103",
        "doctor_id": "DOC-NAMBIAR",
        "doctor_name": "Dr. Meera Nambiar, MD",
        "health_worker_id": "HW-KOLAR-03",
        "health_worker_name": "Sunil Gowda (Vision Tech)",
        "health_worker_email": "sunil.gowda@phc.in",
        "patient_id": "PAT-2026-083",
        "patient_name": "Balwinder Singh",
        "patient_age": 46,
        "patient_gender": "male",
        "village": "Kolar Rural Block",
        "screening_id": "SCR-2026-0993",
        "screening_summary": "No DR (Routine Follow-up)",
        "date": "2026-08-26",
        "start_time": "09:30",
        "end_time": "10:00",
        "reason": "Baseline diabetic eye review with mild family history concern.",
        "status": "COMPLETED",
        "created_at": "2026-08-25T09:00:00Z",
        "updated_at": "2026-08-26T10:05:00Z",
        "doctor_notes": "Doctor-entered consultation note: Fundus clear of microaneurysms or exudates. Routine annual DR screening advised.",
        "doctor_recommendation": "Maintain HbA1c < 7.0 and repeat fundus examination in 12 months.",
        "follow_up_date": "2027-08-26",
    },
]


def seed_database_if_empty(db: Session):
    """
    Initializes database tables with baseline demo records if empty.
    Preserves all modified or dynamically created records across restarts.
    """
    # 0. Schema Migration for WhatsApp Delivery & Patient Email & Email Delivery Tables
    try:
        from sqlalchemy import text
        from app.database import Base
        Base.metadata.create_all(bind=db.bind)

        with db.bind.connect() as conn:
            # 0.1 Check patients.email column
            try:
                conn.execute(text("SELECT email FROM patients LIMIT 1"))
            except Exception:
                logger.info("Migrating patients table: adding email column...")
                conn.execute(text("ALTER TABLE patients ADD COLUMN email VARCHAR(128)"))
                conn.commit()

            # 0.2 Check whatsapp_deliveries columns
            try:
                conn.execute(text("SELECT patient_id FROM whatsapp_deliveries LIMIT 1"))
            except Exception:
                logger.info("Migrating whatsapp_deliveries table: adding patient_id and patient_name columns...")
                conn.execute(text("ALTER TABLE whatsapp_deliveries ADD COLUMN patient_id VARCHAR(64)"))
                conn.execute(text("ALTER TABLE whatsapp_deliveries ADD COLUMN patient_name VARCHAR(128)"))
                conn.commit()

        # Migrate existing WhatsApp delivery records to patient recipient
        from app.models import WhatsAppDeliveryModel
        legacy_deliveries = db.query(WhatsAppDeliveryModel).all()
        for del_row in legacy_deliveries:
            if del_row.recipient_phone == "+919876543210" or del_row.patient_name is None:
                if del_row.screening_id in ["SCR-2026-0991", "SCR-2026-1024", "SCR-2026-0740", "SCR-2026-0410", "SCR-WH-d24ca6", "SCR-PHASE12-ACCEPTED", "SCR-FAILED-001"]:
                    del_row.patient_id = "PAT-2026-081"
                    del_row.patient_name = "Sanjay Bhati"
                    del_row.recipient_phone = "+917378216613"
                elif del_row.screening_id in ["SCR-2026-0992", "SCR-2026-0612"]:
                    del_row.patient_id = "PAT-2026-082"
                    del_row.patient_name = "Sunita Devi"
                    del_row.recipient_phone = "+919412388990"
                elif del_row.screening_id in ["SCR-2026-0993", "SCR-2026-0850"]:
                    del_row.patient_id = "PAT-2026-083"
                    del_row.patient_name = "Balwinder Singh"
                    del_row.recipient_phone = "+919789012345"
        db.commit()
    except Exception as e:
        logger.debug(f"Schema migration note: {e}")

    # 1. Seed Doctors
    if db.query(DoctorModel).count() == 0:
        logger.info("Seeding initial Doctor records into database...")
        for doc in DEMO_DOCTORS:
            db.add(DoctorModel(**doc))
        db.commit()
    else:
        for doc_data in DEMO_DOCTORS:
            if not db.query(DoctorModel).filter(DoctorModel.id == doc_data["id"]).first():
                db.add(DoctorModel(**doc_data))
        db.commit()

    # 2. Seed Health Workers
    if db.query(HealthWorkerModel).count() == 0:
        logger.info("Seeding initial Health Worker records into database...")
        for hw in DEMO_HEALTH_WORKERS:
            db.add(HealthWorkerModel(**hw))
        db.commit()
    else:
        for hw_data in DEMO_HEALTH_WORKERS:
            hw_rec = db.query(HealthWorkerModel).filter(HealthWorkerModel.id == hw_data["id"]).first()
            if not hw_rec:
                db.add(HealthWorkerModel(**hw_data))
            else:
                hw_rec.name = hw_data["name"]
                hw_rec.phone = hw_data["phone"]
                hw_rec.village = hw_data.get("village", hw_rec.village)
        db.commit()

    # 3. Seed / Sync Patients
    if db.query(PatientModel).count() == 0:
        logger.info("Seeding initial Patient records into database...")
        for pat in DEMO_PATIENTS:
            db.add(PatientModel(**pat))
        db.commit()
    else:
        for pat_data in DEMO_PATIENTS:
            p = db.query(PatientModel).filter(PatientModel.id == pat_data["id"]).first()
            if not p:
                db.add(PatientModel(**pat_data))
            else:
                p.name = pat_data["name"]
                p.phone = pat_data["phone"]
                p.email = pat_data.get("email", p.email)
                p.village = pat_data["village"]
                p.district = pat_data.get("district", p.district)
        db.commit()

    # 4. Seed / Sync Screenings
    if db.query(ScreeningModel).count() == 0:
        logger.info("Seeding initial Screening records into database...")
        for scr in DEMO_SCREENINGS:
            db.add(ScreeningModel(**scr))
        db.commit()
    else:
        # Sync canonical baseline screenings if updated
        for scr_data in DEMO_SCREENINGS:
            existing = db.query(ScreeningModel).filter(ScreeningModel.id == scr_data["id"]).first()
            if not existing:
                db.add(ScreeningModel(**scr_data))
            else:
                existing.patient_id = scr_data.get("patient_id", existing.patient_id)
                existing.patient_name = scr_data.get("patient_name", existing.patient_name)
                existing.village = scr_data.get("village", existing.village)
                existing.predicted_class = scr_data["predicted_class"]
                existing.class_name = scr_data["class_name"]
                existing.confidence = scr_data["confidence"]
                existing.dr_severity_od = scr_data["dr_severity_od"]
                existing.dr_severity_os = scr_data["dr_severity_os"]
                existing.overall_severity = scr_data["overall_severity"]
        db.commit()

        # Seed baseline reviews & audit events for accepted demo screenings
        for scr in DEMO_SCREENINGS:
            if scr.get("review_status") == "AI RESULT ACCEPTED":
                rev_id = f"REV-{scr['id']}"
                if not db.query(ScreeningReviewModel).filter((ScreeningReviewModel.id == rev_id) | (ScreeningReviewModel.screening_id == scr["id"])).first():
                    review_rec = ScreeningReviewModel(
                        id=rev_id,
                        screening_id=scr["id"],
                        action="ACCEPT",
                        doctor_id="DOC-SWAMINATHAN",
                        doctor_name="Dr. Arvind Swaminathan, MS",
                        original_ai_result=scr["class_name"],
                        original_confidence=scr["confidence"],
                        reviewed_result=scr["class_name"],
                        review_comment="AI screening prediction accepted during clinical review.",
                        doctor_notes="Clinical findings confirmed by specialist.",
                        review_status="AI RESULT ACCEPTED",
                        review_timestamp=scr["timestamp_iso"],
                    )
                    db.add(review_rec)

                # Baseline audit events
                ai_evt_id = f"evt-ai-{scr['id']}"
                if not db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.id == ai_evt_id).first():
                    db.add(
                        ReviewAuditEventModel(
                            id=ai_evt_id,
                            screening_id=scr["id"],
                            event_type="AI_SCREENING_COMPLETED",
                            description=f"AI model screening inference completed ({scr['class_name']}, Confidence: {scr['confidence']*100:.1f}%).",
                            actor_id="SYSTEM_AI",
                            actor_role="ai_screening_engine",
                            original_ai_result=scr["class_name"],
                            original_confidence=scr["confidence"],
                            timestamp=scr["timestamp_iso"],
                        )
                    )
                doc_evt_id = f"evt-doc-{scr['id']}"
                if not db.query(ReviewAuditEventModel).filter(ReviewAuditEventModel.id == doc_evt_id).first():
                    db.add(
                        ReviewAuditEventModel(
                            id=doc_evt_id,
                            screening_id=scr["id"],
                            event_type="DOCTOR_REVIEW_COMPLETED",
                            description="Doctor accepted AI screening prediction as accurate.",
                            actor_id="DOC-SWAMINATHAN",
                            actor_role="doctor",
                            original_ai_result=scr["class_name"],
                            original_confidence=scr["confidence"],
                            reviewed_result=scr["class_name"],
                            review_comment="AI screening prediction accepted during clinical review.",
                            timestamp=scr["timestamp_iso"],
                        )
                    )
        db.commit()

    # 5. Seed Appointments
    if db.query(AppointmentModel).count() == 0:
        logger.info("Seeding initial Appointment records into database...")
        for apt in DEMO_APPOINTMENTS:
            db.add(AppointmentModel(**apt))
        db.commit()
    else:
        for apt_data in DEMO_APPOINTMENTS:
            existing = db.query(AppointmentModel).filter(AppointmentModel.id == apt_data["id"]).first()
            if not existing:
                db.add(AppointmentModel(**apt_data))
            else:
                existing.health_worker_id = apt_data["health_worker_id"]
                existing.health_worker_name = apt_data["health_worker_name"]
                existing.health_worker_email = apt_data.get("health_worker_email")
                existing.date = apt_data["date"]
                existing.start_time = apt_data["start_time"]
                existing.end_time = apt_data["end_time"]
                existing.status = apt_data["status"]
        db.commit()

    # 6. Seed Initial Appointment Messages
    for apt in DEMO_APPOINTMENTS:
        msg_id = f"MSG-{apt['id']}-01"
        if not db.query(AppointmentMessageModel).filter(AppointmentMessageModel.id == msg_id).first():
            db.add(
                AppointmentMessageModel(
                    id=msg_id,
                    appointment_id=apt["id"],
                    sender_id=apt["health_worker_id"],
                    sender_name=apt["health_worker_name"],
                    sender_role="health_worker",
                    content=f"Hello Doctor, screening results and patient history attached for {apt['patient_name']}.",
                    timestamp=apt["created_at"],
                    is_system=False,
                )
            )
    db.commit()

    logger.info("Database seeding check completed successfully.")
