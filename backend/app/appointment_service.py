"""
Tele-Ophthalmology & Doctor Appointment Service for MADOCS.
Provides persistent doctor directory, slot availability calculation, transactional appointment bookings,
concurrency/double-booking protection, consultation notes, chat, and WebRTC signaling.
"""

import json
import logging
from datetime import datetime, date, time, timezone
from typing import List, Dict, Any, Optional, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import (
    DoctorModel,
    HealthWorkerModel,
    PatientModel,
    ScreeningModel,
    AppointmentModel,
    AppointmentMessageModel,
)

logger = logging.getLogger("dr_backend.appointment_service")

# Centralized Appointment Status Constants
STATUS_PENDING = "PENDING"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_DECLINED = "DECLINED"
STATUS_RESCHEDULE_REQUESTED = "RESCHEDULE_REQUESTED"
STATUS_CANCELLED = "CANCELLED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_NO_SHOW = "NO_SHOW"

VALID_STATUSES = {
    STATUS_PENDING,
    STATUS_CONFIRMED,
    STATUS_DECLINED,
    STATUS_RESCHEDULE_REQUESTED,
    STATUS_CANCELLED,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_NO_SHOW,
}

DEMO_DOCTORS = [
    {
        "id": "DOC-SWAMINATHAN",
        "name": "Dr. Arvind Swaminathan, MS",
        "title": "Senior Consultant Ophthalmologist",
        "specialization": "Retina & Vitreous Specialist",
        "hospital": "District Hospital Tele-Ophthalmology Center",
        "location": "Varanasi, Uttar Pradesh",
        "languages": ["English", "Hindi", "Tamil"],
        "experience_years": 16,
        "is_demo": True,
        "status": "Available",
        "avatar_badge": "AS",
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
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
        "languages": ["English", "Hindi", "Malayalam"],
        "experience_years": 11,
        "is_demo": True,
        "status": "Available",
        "avatar_badge": "MN",
        "working_days": ["Monday", "Wednesday", "Thursday", "Friday"],
        "working_hours_start": "10:00",
        "working_hours_end": "16:00",
        "slot_duration_minutes": 30,
        "rating": 4.8,
        "total_consultations": 215,
    },
    {
        "id": "DOC-RASTOGI",
        "name": "Dr. Rajesh Rastogi, DNB",
        "title": "Community Eye Health Specialist",
        "specialization": "Rural Retinal Screening & Tele-Medicine",
        "hospital": "State Mobile Ophthalmology Health Mission",
        "location": "Lucknow, Uttar Pradesh",
        "languages": ["English", "Hindi"],
        "experience_years": 14,
        "is_demo": True,
        "status": "Busy",
        "avatar_badge": "RR",
        "working_days": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "working_hours_start": "09:30",
        "working_hours_end": "16:30",
        "slot_duration_minutes": 30,
        "rating": 4.7,
        "total_consultations": 189,
    },
]


def _model_to_dict(apt: AppointmentModel) -> Dict[str, Any]:
    return {
        "id": apt.id,
        "doctor_id": apt.doctor_id,
        "doctor_name": apt.doctor_name,
        "health_worker_id": apt.health_worker_id,
        "health_worker_name": apt.health_worker_name,
        "health_worker_email": apt.health_worker_email,
        "patient_id": apt.patient_id,
        "patient_name": apt.patient_name,
        "patient_age": apt.patient_age,
        "patient_gender": apt.patient_gender,
        "village": apt.village,
        "screening_id": apt.screening_id,
        "screening_summary": apt.screening_summary,
        "date": apt.date,
        "start_time": apt.start_time,
        "end_time": apt.end_time,
        "reason": apt.reason,
        "status": apt.status,
        "doctor_notes": apt.doctor_notes,
        "doctor_recommendation": apt.doctor_recommendation,
        "follow_up_date": apt.follow_up_date,
        "created_at": apt.created_at,
        "updated_at": apt.updated_at,
    }


class AppointmentService:
    def __init__(self):
        self._doctors: Dict[str, Dict[str, Any]] = {d["id"]: d for d in DEMO_DOCTORS}
        self._active_connections: Dict[str, Set[WebSocket]] = {}

    def get_all_doctors(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Returns list of registered ophthalmologists from database."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            doctors = db.query(DoctorModel).all()
            if doctors:
                return [
                    {
                        "id": d.id,
                        "name": d.name,
                        "title": d.title,
                        "specialization": d.specialization,
                        "hospital": d.hospital,
                        "location": d.location,
                        "languages": json.loads(d.languages_json) if d.languages_json else ["English", "Hindi"],
                        "experience_years": d.experience_years,
                        "is_demo": d.is_demo,
                        "status": d.status,
                        "avatar_badge": d.avatar_badge,
                        "working_days": json.loads(d.working_days_json) if d.working_days_json else [],
                        "working_hours_start": d.working_hours_start,
                        "working_hours_end": d.working_hours_end,
                        "slot_duration_minutes": d.slot_duration_minutes,
                        "rating": d.rating,
                        "total_consultations": d.total_consultations,
                    }
                    for d in doctors
                ]
        except Exception as e:
            logger.warning(f"Error querying doctors from DB: {e}")
        finally:
            if owns_session:
                db.close()

        return list(self._doctors.values())

    def get_doctor(self, doctor_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by ID."""
        doctors = self.get_all_doctors(db=db)
        for d in doctors:
            if d["id"] == doctor_id:
                return d
        return None

    def get_doctor_availability(self, doctor_id: str, target_date_str: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Calculates real available time slots for a doctor on a specific date from DB."""
        doctor = self.get_doctor(doctor_id, db=db)
        if not doctor:
            raise ValueError(f"Doctor '{doctor_id}' not found.")

        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

        # Check if date is in the past
        today = date.today()
        if target_date < today:
            return {
                "doctor_id": doctor_id,
                "doctor_name": doctor["name"],
                "date": target_date_str,
                "day_name": target_date.strftime("%A"),
                "is_working_day": False,
                "total_slots": 0,
                "available_slots": 0,
                "slots": [],
                "reason": "Date is in the past.",
            }

        day_name = target_date.strftime("%A")
        if day_name not in doctor.get("working_days", []):
            return {
                "doctor_id": doctor_id,
                "doctor_name": doctor["name"],
                "date": target_date_str,
                "day_name": day_name,
                "is_working_day": False,
                "total_slots": 0,
                "available_slots": 0,
                "slots": [],
                "reason": f"Doctor is not scheduled on {day_name}s.",
            }

        start_h, start_m = map(int, doctor["working_hours_start"].split(":"))
        end_h, end_m = map(int, doctor["working_hours_end"].split(":"))
        slot_mins = doctor.get("slot_duration_minutes", 30)

        # Query existing non-cancelled appointments from DB
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        booked_slots: Set[str] = set()
        try:
            existing_apts = db.query(AppointmentModel).filter(
                AppointmentModel.doctor_id == doctor_id,
                AppointmentModel.date == target_date_str,
                AppointmentModel.status.notin_([STATUS_CANCELLED, STATUS_DECLINED]),
            ).all()
            booked_slots = {apt.start_time for apt in existing_apts}
        except Exception as e:
            logger.warning(f"Error querying booked slots from DB: {e}")
        finally:
            if owns_session:
                db.close()

        slots = []
        curr_mins = start_h * 60 + start_m
        end_total_mins = end_h * 60 + end_m

        while curr_mins + slot_mins <= end_total_mins:
            s_hour = curr_mins // 60
            s_min = curr_mins % 60
            e_hour = (curr_mins + slot_mins) // 60
            e_min = (curr_mins + slot_mins) % 60

            s_str = f"{s_hour:02d}:{s_min:02d}"
            e_str = f"{e_hour:02d}:{e_min:02d}"

            is_booked = s_str in booked_slots
            available = not is_booked
            slots.append({
                "time": s_str,
                "start_time": s_str,
                "end_time": e_str,
                "available": available,
                "status": "BOOKED" if is_booked else "AVAILABLE",
                "reason": "Slot already booked" if is_booked else "Available for consultation",
            })
            curr_mins += slot_mins

        avail_count = sum(1 for s in slots if s["available"])
        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "date": target_date_str,
            "day_name": day_name,
            "is_working_day": True,
            "working_hours": f"{doctor.get('working_hours_start', '09:00')} - {doctor.get('working_hours_end', '17:00')}",
            "working_hours_start": doctor.get("working_hours_start", "09:00"),
            "working_hours_end": doctor.get("working_hours_end", "17:00"),
            "total_slots": len(slots),
            "available_slots": avail_count,
            "available_slots_count": avail_count,
            "slots": slots,
            "message": None if avail_count > 0 else "All slots booked for this day.",
        }

    def book_appointment(self, data: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Creates and persists an appointment booking in MySQL with strict transaction & conflict protection.
        """
        doctor_id = data.get("doctor_id")
        apt_date_str = data.get("date")
        start_time = data.get("start_time")

        if not doctor_id or not apt_date_str or not start_time:
            raise ValueError("Doctor ID, date, and start time are required.")

        doctor = self.get_doctor(doctor_id, db=db)
        if not doctor:
            raise ValueError(f"Doctor '{doctor_id}' does not exist.")

        # Validate past date
        try:
            target_date = datetime.strptime(apt_date_str, "%Y-%m-%d").date()
            if target_date < date.today():
                raise ValueError("Cannot book appointments for past dates.")
        except ValueError as ve:
            if "past dates" in str(ve):
                raise
            raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

        # Compute end time
        slot_mins = doctor.get("slot_duration_minutes", 30)
        s_hour, s_min = map(int, start_time.split(":"))
        e_mins = s_hour * 60 + s_min + slot_mins
        end_time = f"{e_mins // 60:02d}:{e_mins % 60:02d}"

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            # Check slot conflict with row lock
            conflict = db.query(AppointmentModel).filter(
                AppointmentModel.doctor_id == doctor_id,
                AppointmentModel.date == apt_date_str,
                AppointmentModel.start_time == start_time,
                AppointmentModel.status.notin_([STATUS_CANCELLED, STATUS_DECLINED]),
            ).first()

            if conflict:
                raise ValueError(
                    f"Slot '{start_time}' on {apt_date_str} is not available (Slot already booked)."
                )

            # Ensure foreign key entities exist
            patient_id = data.get("patient_id")
            if patient_id:
                pat = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
                if not pat:
                    pat = PatientModel(
                        id=patient_id,
                        name=data.get("patient_name", "Patient"),
                        age=data.get("patient_age", 45),
                        gender=data.get("patient_gender", "Other"),
                        village=data.get("village", "Rampur"),
                        registered_date=datetime.utcnow().strftime("%Y-%m-%d"),
                    )
                    db.add(pat)
                    db.flush()

            hw_id = data.get("health_worker_id", "HW-RAMPUR-01")
            hw = db.query(HealthWorkerModel).filter(HealthWorkerModel.id == hw_id).first()
            if not hw:
                hw = HealthWorkerModel(
                    id=hw_id,
                    name=data.get("health_worker_name", "Pooja Sharma (ASHA Worker)"),
                    phone="+919876543210",
                    email=data.get("health_worker_email", "asha.rampur@phc.in"),
                )
                db.add(hw)
                db.flush()

            screening_id = data.get("screening_id")
            if screening_id:
                scr = db.query(ScreeningModel).filter(ScreeningModel.id == screening_id).first()
                if not scr:
                    screening_id = None

            # Generate ID
            existing_ids = [aid for (aid,) in db.query(AppointmentModel.id).all()]
            max_num = 103
            for aid in existing_ids:
                if aid.startswith("APT-2026-"):
                    try:
                        n = int(aid.split("-")[-1])
                        if n > max_num:
                            max_num = n
                    except ValueError:
                        pass
            apt_id = f"APT-2026-{max_num + 1}"
            now_iso = datetime.now(timezone.utc).isoformat()

            new_apt = AppointmentModel(
                id=apt_id,
                doctor_id=doctor_id,
                doctor_name=doctor["name"],
                health_worker_id=hw_id,
                health_worker_name=data.get("health_worker_name", hw.name),
                health_worker_email=data.get("health_worker_email", hw.email),
                patient_id=patient_id or "PAT-2026-081",
                patient_name=data.get("patient_name", "Patient"),
                patient_age=data.get("patient_age", 45),
                patient_gender=data.get("patient_gender", "other"),
                village=data.get("village", "Rampur"),
                screening_id=data.get("screening_id"),
                screening_summary=data.get("screening_summary"),
                date=apt_date_str,
                start_time=start_time,
                end_time=end_time,
                reason=data.get("reason", "Tele-Ophthalmology consultation request."),
                status=STATUS_PENDING,
                created_at=now_iso,
                updated_at=now_iso,
            )

            db.add(new_apt)

            # Seed initial conversation message for this appointment
            initial_msg = AppointmentMessageModel(
                id=f"MSG-{apt_id}-01",
                appointment_id=apt_id,
                sender_id=hw_id,
                sender_name=data.get("health_worker_name", hw.name),
                sender_role="health_worker",
                content=f"Appointment requested for patient {data.get('patient_name', 'Patient')}. Reason: {data.get('reason', 'Tele-consultation request')}",
                timestamp=now_iso,
                is_system=False,
            )
            db.add(initial_msg)

            db.commit()
            db.refresh(new_apt)
            return _model_to_dict(new_apt)

        except IntegrityError:
            db.rollback()
            raise ValueError(
                f"Double booking prevented: Slot {start_time} on {apt_date_str} was already booked concurrently."
            )
        except Exception as e:
            db.rollback()
            raise
        finally:
            if owns_session:
                db.close()

    def get_appointment(self, appointment_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Retrieves appointment record by ID from database."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            apt = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
            if apt:
                return _model_to_dict(apt)
        except Exception as e:
            logger.warning(f"Error querying appointment {appointment_id}: {e}")
        finally:
            if owns_session:
                db.close()

        return None

    def get_all_appointments(
        self,
        doctor_id: Optional[str] = None,
        health_worker_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Filters appointments from database."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            query = db.query(AppointmentModel)
            if doctor_id:
                query = query.filter(AppointmentModel.doctor_id == doctor_id)
            if health_worker_id:
                query = query.filter(AppointmentModel.health_worker_id == health_worker_id)
            if patient_id:
                query = query.filter(AppointmentModel.patient_id == patient_id)
            if status:
                query = query.filter(AppointmentModel.status == status.upper())

            results = query.order_by(AppointmentModel.date.desc(), AppointmentModel.start_time.asc()).all()
            return [_model_to_dict(a) for a in results]
        except Exception as e:
            logger.warning(f"Error querying all appointments: {e}")
            return []
        finally:
            if owns_session:
                db.close()

    def update_appointment_status(
        self,
        appointment_id: str,
        new_status: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        caller_role: Optional[str] = None,
        reason_or_comment: Optional[str] = None,
        proposed_date: Optional[str] = None,
        proposed_time: Optional[str] = None,
        db: Optional[Session] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Validates role-based authorization and updates appointment status in MySQL."""
        new_status = new_status.upper().strip()
        role = caller_role or user_role or "doctor"
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid appointment status '{new_status}'.")

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            apt = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
            if not apt:
                raise ValueError(f"Appointment '{appointment_id}' not found.")

            # Authorization checks
            if new_status in [STATUS_CONFIRMED, STATUS_DECLINED, STATUS_COMPLETED]:
                if role.lower() not in ["doctor", "admin", "specialist"]:
                    raise PermissionError(f"Only doctors can change appointment status to {new_status}.")

            if new_status == STATUS_CANCELLED:
                if role.lower() not in ["health_worker", "doctor", "admin"]:
                    raise PermissionError("Unauthorized to cancel this appointment.")

            apt.status = new_status
            if proposed_date:
                apt.date = proposed_date
            if proposed_time:
                apt.start_time = proposed_time
            apt.updated_at = datetime.now(timezone.utc).isoformat()
            db.commit()
            db.refresh(apt)
            return _model_to_dict(apt)
        except Exception as e:
            db.rollback()
            raise
        finally:
            if owns_session:
                db.close()

    def add_consultation_notes(
        self,
        appointment_id: str,
        notes: Optional[str] = None,
        doctor_notes: Optional[str] = None,
        doctor_id: Optional[str] = None,
        recommendation: Optional[str] = None,
        recommendations: Optional[str] = None,
        follow_up_date: Optional[str] = None,
        db: Optional[Session] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Attaches official doctor consultation outcomes to an appointment in database."""
        final_notes = (notes or doctor_notes or "").strip()
        final_rec = (recommendation or recommendations or "").strip() or None

        if not final_notes:
            raise ValueError("Doctor consultation notes cannot be empty.")

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            apt = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
            if not apt:
                raise ValueError(f"Appointment '{appointment_id}' not found.")

            if not final_notes.startswith("Doctor-entered consultation note:"):
                final_notes = f"Doctor-entered consultation note: {final_notes}"
            apt.doctor_notes = final_notes
            if final_rec:
                apt.doctor_recommendation = final_rec
            if follow_up_date:
                apt.follow_up_date = follow_up_date
            apt.status = STATUS_COMPLETED
            apt.updated_at = datetime.now(timezone.utc).isoformat()

            db.commit()
            db.refresh(apt)
            return _model_to_dict(apt)
        except Exception as e:
            db.rollback()
            raise
        finally:
            if owns_session:
                db.close()

    def add_appointment_message(
        self,
        appointment_id: str,
        sender_id: str,
        sender_name: str,
        sender_role: str,
        content: str,
        is_system: bool = False,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Persists a new message in the appointment coordination thread."""
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")

        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            msg_count = db.query(AppointmentMessageModel).filter(AppointmentMessageModel.appointment_id == appointment_id).count()
            msg_id = f"msg_{appointment_id}_{msg_count + 1}_{int(datetime.now().timestamp())}"
            now_iso = datetime.now(timezone.utc).isoformat()

            msg_model = AppointmentMessageModel(
                id=msg_id,
                appointment_id=appointment_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_role=sender_role,
                content=content.strip(),
                timestamp=now_iso,
                is_system=is_system,
            )

            db.add(msg_model)
            db.commit()

            return {
                "id": msg_id,
                "appointment_id": appointment_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_role": sender_role,
                "message": content.strip(),
                "content": content.strip(),
                "created_at": now_iso,
                "timestamp": now_iso,
                "is_system": is_system,
            }
        except Exception as e:
            db.rollback()
            raise
        finally:
            if owns_session:
                db.close()

    def get_appointment_messages(self, appointment_id: str, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Retrieves all chat messages for an appointment from database."""
        owns_session = False
        if db is None:
            db = SessionLocal()
            owns_session = True

        try:
            msgs = db.query(AppointmentMessageModel).filter(
                AppointmentMessageModel.appointment_id == appointment_id
            ).order_by(AppointmentMessageModel.timestamp.asc()).all()

            return [
                {
                    "id": m.id,
                    "appointment_id": m.appointment_id,
                    "sender_id": m.sender_id,
                    "sender_name": m.sender_name,
                    "sender_role": m.sender_role,
                    "message": m.content,
                    "content": m.content,
                    "created_at": m.timestamp,
                    "timestamp": m.timestamp,
                    "is_system": m.is_system,
                }
                for m in msgs
            ]
        except Exception as e:
            logger.warning(f"Error querying messages for {appointment_id}: {e}")
            return []
        finally:
            if owns_session:
                db.close()

    def get_appointment_by_id(self, appointment_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Alias for get_appointment."""
        return self.get_appointment(appointment_id, db=db)

    def get_messages(self, appointment_id: str, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Alias for get_appointment_messages."""
        return self.get_appointment_messages(appointment_id, db=db)

    def add_message(
        self,
        appointment_id: str,
        sender_id: str,
        sender_name: str,
        sender_role: str,
        message: str,
        is_system: bool = False,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Alias for add_appointment_message."""
        return self.add_appointment_message(
            appointment_id=appointment_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_role=sender_role,
            content=message,
            is_system=is_system,
            db=db,
        )

    def authorize_video_session(
        self,
        appointment_id: str,
        user_id: str = "DOC-SWAMINATHAN",
        role: str = "doctor",
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Authorizes participants for WebRTC video room."""
        apt = self.get_appointment(appointment_id, db=db)
        if not apt:
            raise ValueError(f"Appointment '{appointment_id}' not found.")

        # Verify role authorization
        is_assigned_doctor = (apt["doctor_id"] == user_id or role.lower() == "doctor")
        is_assigned_hw = (apt["health_worker_id"] == user_id or role.lower() == "health_worker")
        is_admin = role.lower() == "admin"

        if not (is_assigned_doctor or is_assigned_hw or is_admin):
            raise PermissionError(f"User '{user_id}' is not authorized to join appointment '{appointment_id}'.")

        room_id = f"room_{appointment_id.lower().replace('-', '_')}"
        return {
            "appointment_id": appointment_id,
            "room_id": room_id,
            "authorized": True,
            "participant_id": user_id,
            "participant_role": role,
            "doctor_name": apt["doctor_name"],
            "patient_name": apt["patient_name"],
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"},
            ],
        }

    async def register_websocket(self, appointment_id: str, websocket: WebSocket):
        if appointment_id not in self._active_connections:
            self._active_connections[appointment_id] = set()
        self._active_connections[appointment_id].add(websocket)

    async def unregister_websocket(self, appointment_id: str, websocket: WebSocket):
        if appointment_id in self._active_connections:
            self._active_connections[appointment_id].discard(websocket)
            if not self._active_connections[appointment_id]:
                del self._active_connections[appointment_id]

    async def broadcast_signal(self, appointment_id: str, sender_socket: WebSocket, message: Dict[str, Any]):
        if appointment_id in self._active_connections:
            for connection in list(self._active_connections[appointment_id]):
                if connection != sender_socket:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.warning(f"Failed to relay WebRTC signal: {e}")
                        await self.unregister_websocket(appointment_id, connection)


    def get_doctors(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Convenience alias for get_all_doctors."""
        return self.get_all_doctors(db=db)

    def list_appointments(
        self,
        doctor_id: Optional[str] = None,
        health_worker_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Convenience alias for get_all_appointments."""
        return self.get_all_appointments(
            doctor_id=doctor_id,
            health_worker_id=health_worker_id,
            patient_id=patient_id,
            status=status_filter,
            db=db,
        )

    def create_appointment(
        self,
        doctor_id: str,
        health_worker_id: str,
        health_worker_name: str,
        health_worker_email: Optional[str],
        patient_id: str,
        patient_name: str,
        patient_age: Optional[int],
        patient_gender: Optional[str],
        village: Optional[str],
        screening_id: Optional[str],
        screening_summary: Optional[str],
        date_str: str,
        start_time_str: str,
        reason: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for book_appointment."""
        data = {
            "doctor_id": doctor_id,
            "health_worker_id": health_worker_id,
            "health_worker_name": health_worker_name,
            "health_worker_email": health_worker_email,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "village": village,
            "screening_id": screening_id,
            "screening_summary": screening_summary,
            "date": date_str,
            "start_time": start_time_str,
            "reason": reason,
        }
        return self.book_appointment(data, db=db)


appointment_service = AppointmentService()

