"""
SQLAlchemy 2.0 ORM Models for MADOCS Persistent Relational Storage.
Defines normalized schemas with primary keys, foreign keys, unique constraints, and indexes.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True, index=True)  # e.g., PAT-2026-081
    abha_id = Column(String(64), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(32), nullable=False)
    phone = Column(String(32), nullable=True, index=True)
    email = Column(String(128), nullable=True, index=True)
    village = Column(String(128), nullable=True)
    district = Column(String(128), nullable=True)
    diabetes_duration = Column(Integer, nullable=True)
    last_hba1c = Column(Float, nullable=True)
    insulin_use = Column(Boolean, default=False)
    visual_acuity_od = Column(String(32), default="6/6")
    visual_acuity_os = Column(String(32), default="6/6")
    symptoms_json = Column(Text, nullable=True)  # JSON array string
    registered_date = Column(String(32), nullable=False)
    last_screened = Column(String(32), default="-")
    latest_status = Column(String(64), default="drUncertain")
    referral_urgency = Column(String(64), default="routine")
    doctor_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    screenings = relationship("ScreeningModel", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("AppointmentModel", back_populates="patient")
    sms_notifications = relationship("SmsNotificationModel", back_populates="patient")

    @property
    def mobile(self) -> Optional[str]:
        return self.phone

    @mobile.setter
    def mobile(self, val: Optional[str]):
        self.phone = val


class DoctorModel(Base):
    __tablename__ = "doctors"

    id = Column(String(64), primary_key=True, index=True)  # e.g., DOC-SWAMINATHAN
    name = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    specialization = Column(String(256), nullable=False)
    hospital = Column(String(256), nullable=False)
    location = Column(String(128), nullable=False)
    languages_json = Column(Text, nullable=False)  # JSON array of languages
    experience_years = Column(Integer, default=10)
    is_demo = Column(Boolean, default=True)
    status = Column(String(32), default="Available")
    avatar_badge = Column(String(16), default="DR")
    working_days_json = Column(Text, nullable=False)  # JSON array of day names
    working_hours_start = Column(String(16), default="09:00")
    working_hours_end = Column(String(16), default="17:00")
    slot_duration_minutes = Column(Integer, default=30)
    rating = Column(Float, default=4.9)
    total_consultations = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_utc_now)

    appointments = relationship("AppointmentModel", back_populates="doctor")


class HealthWorkerModel(Base):
    __tablename__ = "health_workers"

    id = Column(String(64), primary_key=True, index=True)  # e.g., HW-RAMPUR-01
    name = Column(String(128), nullable=False)
    role = Column(String(64), default="health_worker")
    phone = Column(String(32), nullable=False, unique=True, index=True)
    email = Column(String(128), nullable=True)
    village = Column(String(128), nullable=True)
    phc_center = Column(String(128), nullable=True)
    whatsapp_opt_in = Column(Boolean, default=True)
    whatsapp_opt_in_date = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    appointments = relationship("AppointmentModel", back_populates="health_worker")


class ScreeningModel(Base):
    __tablename__ = "screenings"

    id = Column(String(64), primary_key=True, index=True)  # e.g., SCR-2026-0991
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    patient_name = Column(String(128), nullable=False)
    village = Column(String(128), nullable=True)
    screening_date = Column(String(64), nullable=False)
    timestamp_iso = Column(String(64), nullable=False)
    predicted_class = Column(Integer, nullable=False)
    class_name = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities_json = Column(Text, nullable=True)  # JSON dictionary
    dr_severity_od = Column(String(32), default="drUncertain")
    dr_severity_os = Column(String(32), default="drUncertain")
    overall_severity = Column(String(32), default="drUncertain")
    safety_status = Column(String(64), default="READY_FOR_AI")
    screening_status = Column(String(64), default="RELIABLE AI SCREENING")
    risk_category = Column(String(64), default="MODERATE")
    referral_priority = Column(String(128), default="EYE SPECIALIST REVIEW RECOMMENDED")
    risk_explanation = Column(Text, nullable=True)
    referral_guidance = Column(Text, nullable=True)
    safety_message = Column(Text, nullable=True)
    gradcam_url = Column(String(256), nullable=True)
    heatmap_url = Column(String(256), nullable=True)
    image_od_path = Column(String(256), nullable=True)
    image_os_path = Column(String(256), nullable=True)
    doctor_status = Column(String(64), default="pending")  # 'pending', 'verified', 'recapture_requested'
    review_status = Column(String(64), default="PENDING DOCTOR REVIEW")
    created_at = Column(DateTime, default=get_utc_now)

    patient = relationship("PatientModel", back_populates="screenings")
    review = relationship("ScreeningReviewModel", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    audit_events = relationship("ReviewAuditEventModel", back_populates="screening", cascade="all, delete-orphan")
    appointments = relationship("AppointmentModel", back_populates="screening")
    whatsapp_delivery = relationship("WhatsAppDeliveryModel", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    email_delivery = relationship("EmailDeliveryModel", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    sms_notifications = relationship("SmsNotificationModel", back_populates="screening", cascade="all, delete-orphan")
    report = relationship("ReportModel", back_populates="screening", uselist=False, cascade="all, delete-orphan")


class ScreeningReviewModel(Base):
    __tablename__ = "screening_reviews"

    id = Column(String(64), primary_key=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, unique=True, index=True)
    action = Column(String(32), nullable=False)  # 'ACCEPT', 'MODIFY', 'RECAPTURE'
    doctor_id = Column(String(64), ForeignKey("doctors.id"), nullable=False)
    doctor_name = Column(String(128), nullable=False)
    original_ai_result = Column(String(64), nullable=False)
    original_confidence = Column(Float, nullable=True)
    reviewed_result = Column(String(64), nullable=True)
    review_comment = Column(Text, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    review_status = Column(String(64), nullable=False)
    review_timestamp = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    screening = relationship("ScreeningModel", back_populates="review")


class ReviewAuditEventModel(Base):
    __tablename__ = "review_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    actor_id = Column(String(64), nullable=False)
    actor_role = Column(String(64), nullable=False)
    original_ai_result = Column(String(64), nullable=True)
    original_confidence = Column(Float, nullable=True)
    reviewed_result = Column(String(64), nullable=True)
    review_comment = Column(Text, nullable=True)
    timestamp = Column(String(64), nullable=False)

    screening = relationship("ScreeningModel", back_populates="audit_events")


class AppointmentModel(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_slot_appointment"),
        Index("idx_doctor_date", "doctor_id", "date"),
        Index("idx_patient_appointment", "patient_id"),
    )

    id = Column(String(64), primary_key=True, index=True)  # e.g., APT-2026-101
    doctor_id = Column(String(64), ForeignKey("doctors.id"), nullable=False, index=True)
    doctor_name = Column(String(128), nullable=False)
    health_worker_id = Column(String(64), ForeignKey("health_workers.id"), nullable=False, index=True)
    health_worker_name = Column(String(128), nullable=False)
    health_worker_email = Column(String(128), nullable=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    patient_name = Column(String(128), nullable=False)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(32), nullable=True)
    village = Column(String(128), nullable=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=True, index=True)
    screening_summary = Column(String(256), nullable=True)
    date = Column(String(32), nullable=False)  # YYYY-MM-DD
    start_time = Column(String(16), nullable=False)  # HH:MM
    end_time = Column(String(16), nullable=False)  # HH:MM
    reason = Column(Text, nullable=True)
    status = Column(String(32), default="PENDING", index=True)
    doctor_notes = Column(Text, nullable=True)
    doctor_recommendation = Column(Text, nullable=True)
    follow_up_date = Column(String(32), nullable=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    doctor = relationship("DoctorModel", back_populates="appointments")
    health_worker = relationship("HealthWorkerModel", back_populates="appointments")
    patient = relationship("PatientModel", back_populates="appointments")
    screening = relationship("ScreeningModel", back_populates="appointments")
    messages = relationship("AppointmentMessageModel", back_populates="appointment", cascade="all, delete-orphan")


class AppointmentMessageModel(Base):
    __tablename__ = "appointment_messages"

    id = Column(String(64), primary_key=True, index=True)
    appointment_id = Column(String(64), ForeignKey("appointments.id"), nullable=False, index=True)
    sender_id = Column(String(64), nullable=False)
    sender_name = Column(String(128), nullable=False)
    sender_role = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(String(64), nullable=False)
    is_system = Column(Boolean, default=False)

    appointment = relationship("AppointmentModel", back_populates="messages")


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, unique=True, index=True)
    pdf_filename = Column(String(256), nullable=False)
    pdf_relative_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    is_final_doctor_approved = Column(Boolean, default=True)
    token_hash = Column(String(256), nullable=True)
    generated_at = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    screening = relationship("ScreeningModel", back_populates="report")


class WhatsAppDeliveryModel(Base):
    __tablename__ = "whatsapp_deliveries"

    id = Column(String(64), primary_key=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, unique=True, index=True)
    recipient_phone = Column(String(32), nullable=False, index=True)
    patient_id = Column(String(64), nullable=True, index=True)
    patient_name = Column(String(128), nullable=True)
    health_worker_id = Column(String(64), ForeignKey("health_workers.id"), nullable=False, index=True)
    health_worker_name = Column(String(128), nullable=False)
    language = Column(String(16), default="en")
    status = Column(String(32), default="NOT_REQUESTED", index=True)
    provider_message_id = Column(String(128), nullable=True, unique=True, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    is_demo = Column(Boolean, default=True)
    created_at = Column(String(64), nullable=False)
    sent_at = Column(String(64), nullable=True)
    delivered_at = Column(String(64), nullable=True)
    read_at = Column(String(64), nullable=True)

    screening = relationship("ScreeningModel", back_populates="whatsapp_delivery")
    audit_events = relationship("WhatsAppAuditEventModel", back_populates="delivery", cascade="all, delete-orphan")


class WhatsAppAuditEventModel(Base):
    __tablename__ = "whatsapp_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    delivery_id = Column(String(64), ForeignKey("whatsapp_deliveries.id"), nullable=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    actor_id = Column(String(64), nullable=False)
    timestamp = Column(String(64), nullable=False)

    delivery = relationship("WhatsAppDeliveryModel", back_populates="audit_events")


class EmailDeliveryModel(Base):
    __tablename__ = "email_deliveries"

    id = Column(String(64), primary_key=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, unique=True, index=True)
    patient_id = Column(String(64), nullable=True, index=True)
    patient_name = Column(String(128), nullable=True)
    recipient_email = Column(String(128), nullable=False, index=True)
    subject = Column(String(256), nullable=False)
    status = Column(String(32), default="NOT_REQUESTED", index=True)  # NOT_REQUESTED, PENDING, SENT, FAILED
    provider_message_id = Column(String(128), nullable=True, unique=True, index=True)
    error_message = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    pdf_filename = Column(String(256), nullable=True)
    is_demo = Column(Boolean, default=True)
    created_at = Column(String(64), nullable=False)
    sent_at = Column(String(64), nullable=True)

    screening = relationship("ScreeningModel", back_populates="email_delivery")
    audit_events = relationship("EmailAuditEventModel", back_populates="delivery", cascade="all, delete-orphan")


class EmailAuditEventModel(Base):
    __tablename__ = "email_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    delivery_id = Column(String(64), ForeignKey("email_deliveries.id"), nullable=True, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    actor_id = Column(String(64), nullable=False)
    timestamp = Column(String(64), nullable=False)

    delivery = relationship("EmailDeliveryModel", back_populates="audit_events")


class SmsNotificationModel(Base):
    __tablename__ = "sms_notifications"

    id = Column(String(64), primary_key=True, index=True)  # e.g., SMS-2026-0001
    notification_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    screening_id = Column(String(64), ForeignKey("screenings.id"), nullable=False, index=True)
    report_id = Column(String(64), nullable=True)
    recipient_mobile_masked = Column(String(32), nullable=False)
    recipient_mobile_raw = Column(String(32), nullable=True)
    message_type = Column(String(64), default="Doctor-reviewed report")
    message = Column(Text, nullable=False)
    secure_report_token = Column(String(128), unique=True, index=True, nullable=False)
    secure_report_url = Column(String(256), nullable=False)
    status = Column(String(32), default="SIMULATED", index=True)  # Strictly "SIMULATED", NEVER fake "SENT"
    is_simulated = Column(Boolean, default=True)
    disclaimer = Column(String(256), default="This is a demonstration notification. No real SMS was sent.")
    created_at = Column(String(64), nullable=False)
    generated_at = Column(String(64), nullable=True)

    patient = relationship("PatientModel", back_populates="sms_notifications")
    screening = relationship("ScreeningModel", back_populates="sms_notifications")


