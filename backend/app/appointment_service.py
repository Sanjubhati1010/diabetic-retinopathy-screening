"""
Tele-Ophthalmology & Doctor Appointment Service
Provides doctor directory, slot availability, appointment lifecycle management,
appointment-scoped messaging, clinical consultation notes, and WebRTC signaling sessions.
"""

import logging
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional, Set
from fastapi import WebSocket

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

# Seeded Demo Doctors (Clearly labeled as Demo Doctor)
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
        "hospital": "Regional Eye Institute & Rural Tele-Link Hub",
        "location": "Bengaluru / Rural Outreach Division",
        "languages": ["English", "Hindi", "Kannada"],
        "experience_years": 11,
        "is_demo": True,
        "status": "Available",
        "avatar_badge": "MN",
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "working_hours_start": "10:00",
        "working_hours_end": "18:00",
        "slot_duration_minutes": 30,
        "rating": 4.8,
        "total_consultations": 218,
    },
    {
        "id": "DOC-RAO",
        "name": "Dr. Rajeshwar Rao, MS",
        "title": "Community Ophthalmology Specialist",
        "specialization": "Diabetic Retinopathy Screening & Low-Resource Tele-Care",
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


class AppointmentService:
    """Singleton service managing appointments, availability, chat, and signaling."""

    def __init__(self):
        self._doctors: Dict[str, Dict[str, Any]] = {d["id"]: d for d in DEMO_DOCTORS}
        self._appointments: Dict[str, Dict[str, Any]] = {}
        self._messages: Dict[str, List[Dict[str, Any]]] = {}  # appointment_id -> [messages]
        self._active_connections: Dict[str, Set[WebSocket]] = {}  # appointment_id -> Set[WebSocket]

        self._seed_initial_appointments()

    def _seed_initial_appointments(self):
        """Seed representative demo appointments across different statuses."""
        initial = [
            {
                "id": "APT-2026-101",
                "doctor_id": "DOC-SWAMINATHAN",
                "doctor_name": "Dr. Arvind Swaminathan, MS",
                "health_worker_id": "HW-RAMPUR-01",
                "health_worker_name": "Pooja Sharma (ASHA Worker)",
                "health_worker_email": "asha.rampur@phc.in",
                "patient_id": "PAT-2026-081",
                "patient_name": "Ramesh Kumar Verma",
                "patient_age": 58,
                "patient_gender": "male",
                "village": "Rampur Gram Panchayat",
                "screening_id": "SCR-2026-0991",
                "screening_summary": "Moderate DR (AI Confidence 85.0%)",
                "date": "2026-08-28",
                "start_time": "10:30",
                "end_time": "11:00",
                "reason": "AI screening indicates progression from Mild to Moderate DR. Blurring reported in right eye.",
                "status": STATUS_CONFIRMED,
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
                "health_worker_id": "HW-RAMPUR-01",
                "health_worker_name": "Pooja Sharma (ASHA Worker)",
                "health_worker_email": "asha.rampur@phc.in",
                "patient_id": "PAT-2026-082",
                "patient_name": "Sunita Devi",
                "patient_age": 52,
                "patient_gender": "female",
                "village": "Shivpuri Taluk",
                "screening_id": "SCR-2026-0992",
                "screening_summary": "Severe DR (Urgent Referral Required)",
                "date": "2026-08-28",
                "start_time": "11:30",
                "end_time": "12:00",
                "reason": "High risk NPDR with macular edema suspicion. Tele-consultation required for urgent tertiary hospital referral.",
                "status": STATUS_PENDING,
                "created_at": "2026-08-27T14:15:00Z",
                "updated_at": "2026-08-27T14:15:00Z",
                "doctor_notes": None,
                "doctor_recommendation": None,
                "follow_up_date": None,
            },
            {
                "id": "APT-2026-103",
                "doctor_id": "DOC-NAMBIAR",
                "doctor_name": "Dr. Meera Nambiar, MD",
                "health_worker_id": "HW-RAMPUR-01",
                "health_worker_name": "Pooja Sharma (ASHA Worker)",
                "health_worker_email": "asha.rampur@phc.in",
                "patient_id": "PAT-2026-083",
                "patient_name": "Balwinder Singh",
                "patient_age": 46,
                "patient_gender": "male",
                "village": "Kolar Rural Block",
                "screening_id": "SCR-2026-0850",
                "screening_summary": "No DR (Routine Follow-up)",
                "date": "2026-08-26",
                "start_time": "09:30",
                "end_time": "10:00",
                "reason": "Baseline diabetic eye review with mild family history concern.",
                "status": STATUS_COMPLETED,
                "created_at": "2026-08-25T09:00:00Z",
                "updated_at": "2026-08-26T10:05:00Z",
                "doctor_notes": "Doctor-entered consultation note: Fundus clear of microaneurysms or exudates. Routine annual DR screening advised.",
                "doctor_recommendation": "Annual follow-up screening in 12 months. Glycemic control counseling given.",
                "follow_up_date": "2027-08-26",
            },
        ]

        for apt in initial:
            self._appointments[apt["id"]] = apt
            self._messages[apt["id"]] = [
                {
                    "id": f"MSG-{apt['id']}-01",
                    "appointment_id": apt["id"],
                    "sender_id": apt["health_worker_id"],
                    "sender_name": apt["health_worker_name"],
                    "sender_role": "health_worker",
                    "message": f"Hello Doctor, screening results and patient history attached for {apt['patient_name']}.",
                    "created_at": apt["created_at"],
                }
            ]

    # -------------------------------------------------------------
    # Doctor Directory & Availability
    # -------------------------------------------------------------
    def get_doctors(self) -> List[Dict[str, Any]]:
        """Return list of verified demo doctors with availability metadata."""
        return list(self._doctors.values())

    def get_doctor_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        return self._doctors.get(doctor_id)

    def get_doctor_availability(self, doctor_id: str, target_date_str: str) -> Dict[str, Any]:
        """
        Generate time slots for a given date and check existing appointment bookings.
        Prevents past slot booking and double booking.
        """
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            raise ValueError(f"Doctor '{doctor_id}' not found.")

        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date format must be YYYY-MM-DD.")

        # Check if day of week is supported
        day_name = target_date.strftime("%A")
        if day_name not in doctor.get("working_days", []):
            return {
                "doctor_id": doctor_id,
                "doctor_name": doctor["name"],
                "date": target_date_str,
                "day_name": day_name,
                "is_working_day": False,
                "slots": [],
                "message": f"{doctor['name']} does not have scheduled hours on {day_name}s.",
            }

        # Check if target date is in the past
        now = datetime.now()
        today = now.date()
        is_past_date = target_date < today

        # Generate standard 30-min slots from start to end
        start_hour, start_min = map(int, doctor["working_hours_start"].split(":"))
        end_hour, end_min = map(int, doctor["working_hours_end"].split(":"))

        slots = []
        curr_hour, curr_min = start_hour, start_min
        slot_duration = doctor.get("slot_duration_minutes", 30)

        # Find existing active bookings for this doctor on target_date
        booked_slots = set()
        for apt in self._appointments.values():
            if (
                apt["doctor_id"] == doctor_id
                and apt["date"] == target_date_str
                and apt["status"] not in [STATUS_CANCELLED, STATUS_DECLINED]
            ):
                booked_slots.add(apt["start_time"])

        while (curr_hour < end_hour) or (curr_hour == end_hour and curr_min < end_min):
            slot_start_time = f"{curr_hour:02d}:{curr_min:02d}"
            
            # calculate end time
            next_min = curr_min + slot_duration
            next_hour = curr_hour + (next_min // 60)
            next_min = next_min % 60
            slot_end_time = f"{next_hour:02d}:{next_min:02d}"

            # Check availability
            is_booked = slot_start_time in booked_slots
            
            # Check if time has already passed today
            is_past_time = False
            if target_date == today:
                slot_datetime = datetime.combine(today, time(curr_hour, curr_min))
                is_past_time = slot_datetime <= now

            available = not is_past_date and not is_past_time and not is_booked

            slots.append({
                "start_time": slot_start_time,
                "end_time": slot_end_time,
                "available": available,
                "reason": (
                    "Slot already booked" if is_booked
                    else "Time has already passed" if (is_past_date or is_past_time)
                    else "Available for consultation"
                )
            })

            curr_hour, curr_min = next_hour, next_min

        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "date": target_date_str,
            "day_name": day_name,
            "is_working_day": True,
            "slots": slots,
            "total_slots": len(slots),
            "available_slots_count": sum(1 for s in slots if s["available"]),
        }

    # -------------------------------------------------------------
    # Appointment CRUD & State Transitions
    # -------------------------------------------------------------
    def create_appointment(
        self,
        doctor_id: str,
        health_worker_id: str,
        health_worker_name: str,
        health_worker_email: str,
        patient_id: str,
        patient_name: str,
        patient_age: Optional[int],
        patient_gender: Optional[str],
        village: Optional[str],
        screening_id: Optional[str],
        screening_summary: Optional[str],
        date_str: str,
        start_time_str: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Create a new appointment after strictly validating doctor existence,
        date/time validity, and double-booking.
        """
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            raise ValueError(f"Doctor '{doctor_id}' does not exist.")

        if not patient_id or not patient_name:
            raise ValueError("Patient ID and Patient Name are required.")

        if not reason or not reason.strip():
            raise ValueError("Reason for consultation must be specified.")

        # Validate slot availability
        availability = self.get_doctor_availability(doctor_id, date_str)
        if not availability["is_working_day"]:
            raise ValueError(availability["message"])

        matching_slot = None
        for slot in availability["slots"]:
            if slot["start_time"] == start_time_str:
                matching_slot = slot
                break

        if not matching_slot:
            raise ValueError(f"Time slot '{start_time_str}' is not within doctor working hours.")

        if not matching_slot["available"]:
            raise ValueError(f"Slot '{start_time_str}' on {date_str} is not available ({matching_slot['reason']}).")

        # Generate appointment ID
        apt_num = len(self._appointments) + 104
        appointment_id = f"APT-2026-{apt_num}"
        now_iso = datetime.utcnow().isoformat() + "Z"

        new_appointment = {
            "id": appointment_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "health_worker_id": health_worker_id,
            "health_worker_name": health_worker_name,
            "health_worker_email": health_worker_email,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "patient_age": patient_age or 45,
            "patient_gender": patient_gender or "unknown",
            "village": village or "PHC Center",
            "screening_id": screening_id,
            "screening_summary": screening_summary,
            "date": date_str,
            "start_time": start_time_str,
            "end_time": matching_slot["end_time"],
            "reason": reason.strip(),
            "status": STATUS_PENDING,
            "created_at": now_iso,
            "updated_at": now_iso,
            "doctor_notes": None,
            "doctor_recommendation": None,
            "follow_up_date": None,
        }

        self._appointments[appointment_id] = new_appointment
        self._messages[appointment_id] = [
            {
                "id": f"MSG-{appointment_id}-01",
                "appointment_id": appointment_id,
                "sender_id": health_worker_id,
                "sender_name": health_worker_name,
                "sender_role": "health_worker",
                "message": f"Appointment requested for patient {patient_name}. Reason: {reason.strip()}",
                "created_at": now_iso,
            }
        ]

        logger.info(f"Created appointment {appointment_id} for Patient {patient_id} with Doctor {doctor_id}")
        return new_appointment

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        return self._appointments.get(appointment_id)

    def list_appointments(
        self,
        doctor_id: Optional[str] = None,
        health_worker_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List appointments with optional filtering."""
        results = []
        for apt in self._appointments.values():
            if doctor_id and apt["doctor_id"] != doctor_id:
                continue
            if health_worker_id and apt["health_worker_id"] != health_worker_id:
                continue
            if patient_id and apt["patient_id"] != patient_id:
                continue
            if status and apt["status"].upper() != status.upper():
                continue
            results.append(apt)

        # Sort by date and start_time descending (newest first)
        results.sort(key=lambda x: f"{x['date']} {x['start_time']}", reverse=True)
        return results

    def update_appointment_status(
        self,
        appointment_id: str,
        new_status: str,
        caller_role: str,
        reason_or_comment: Optional[str] = None,
        proposed_date: Optional[str] = None,
        proposed_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transition appointment status with role-based checks.
        """
        new_status = new_status.upper()
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(sorted(VALID_STATUSES))}")

        apt = self.get_appointment_by_id(appointment_id)
        if not apt:
            raise ValueError(f"Appointment '{appointment_id}' not found.")

        current_status = apt["status"]
        now_iso = datetime.utcnow().isoformat() + "Z"

        # Permission checks
        if new_status in [STATUS_CONFIRMED, STATUS_DECLINED, STATUS_RESCHEDULE_REQUESTED, STATUS_COMPLETED]:
            if caller_role not in ["doctor", "admin"]:
                raise PermissionError(f"Only a doctor or admin can mark appointment as {new_status}.")

        if new_status == STATUS_CANCELLED:
            if caller_role not in ["health_worker", "doctor", "admin"]:
                raise PermissionError("Unauthorized to cancel appointment.")

        apt["status"] = new_status
        apt["updated_at"] = now_iso

        if proposed_date and proposed_time and new_status == STATUS_RESCHEDULE_REQUESTED:
            apt["reschedule_proposed_date"] = proposed_date
            apt["reschedule_proposed_time"] = proposed_time

        # Add system message to appointment chat
        sys_msg = f"Status updated to '{new_status}'."
        if reason_or_comment:
            sys_msg += f" Note: {reason_or_comment}"

        self.add_message(
            appointment_id=appointment_id,
            sender_id="SYSTEM",
            sender_name="System Notification",
            sender_role="system",
            message=sys_msg,
        )

        logger.info(f"Appointment {appointment_id} transitioned from {current_status} -> {new_status}")
        return apt

    def add_consultation_notes(
        self,
        appointment_id: str,
        doctor_id: str,
        doctor_notes: str,
        recommendations: str,
        follow_up_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record doctor clinical consultation notes (clearly labeled)."""
        apt = self.get_appointment_by_id(appointment_id)
        if not apt:
            raise ValueError(f"Appointment '{appointment_id}' not found.")

        if apt["doctor_id"] != doctor_id:
            raise PermissionError(f"Doctor '{doctor_id}' is not assigned to appointment '{appointment_id}'.")

        if not doctor_notes or not doctor_notes.strip():
            raise ValueError("Doctor consultation notes cannot be empty.")

        now_iso = datetime.utcnow().isoformat() + "Z"
        apt["doctor_notes"] = f"Doctor-entered consultation note: {doctor_notes.strip()}"
        apt["doctor_recommendation"] = recommendations.strip() if recommendations else "Continue prescribed care."
        apt["follow_up_date"] = follow_up_date
        apt["status"] = STATUS_COMPLETED
        apt["updated_at"] = now_iso

        self.add_message(
            appointment_id=appointment_id,
            sender_id=doctor_id,
            sender_name=apt["doctor_name"],
            sender_role="doctor",
            message=f"Consultation completed. Clinical note: {doctor_notes.strip()}",
        )

        logger.info(f"Consultation notes added for appointment {appointment_id} by {doctor_id}")
        return apt

    # -------------------------------------------------------------
    # Appointment-Scoped Chat
    # -------------------------------------------------------------
    def get_messages(self, appointment_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a specific appointment."""
        if appointment_id not in self._appointments:
            raise ValueError(f"Appointment '{appointment_id}' not found.")
        return self._messages.get(appointment_id, [])

    def add_message(
        self,
        appointment_id: str,
        sender_id: str,
        sender_name: str,
        sender_role: str,
        message: str,
    ) -> Dict[str, Any]:
        """Add appointment-scoped message."""
        if appointment_id not in self._appointments:
            raise ValueError(f"Appointment '{appointment_id}' not found.")

        if not message or not message.strip():
            raise ValueError("Message text cannot be empty.")

        now_iso = datetime.utcnow().isoformat() + "Z"
        msg_id = f"MSG-{appointment_id}-{len(self._messages.get(appointment_id, [])) + 1:02d}"

        msg = {
            "id": msg_id,
            "appointment_id": appointment_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "sender_role": sender_role,
            "message": message.strip(),
            "created_at": now_iso,
        }

        if appointment_id not in self._messages:
            self._messages[appointment_id] = []

        self._messages[appointment_id].append(msg)
        return msg

    # -------------------------------------------------------------
    # WebRTC Video Signaling Session
    # -------------------------------------------------------------
    def authorize_video_session(self, appointment_id: str, user_id: str, role: str) -> Dict[str, Any]:
        """
        Authorize participant to join the WebRTC video consultation room.
        """
        apt = self.get_appointment_by_id(appointment_id)
        if not apt:
            raise ValueError(f"Appointment '{appointment_id}' not found.")

        # Allow assigned doctor, assigned health worker, or admin
        is_assigned_doctor = apt["doctor_id"] == user_id or role == "doctor"
        is_assigned_hw = apt["health_worker_id"] == user_id or role == "health_worker"
        is_admin = role == "admin"

        if not (is_assigned_doctor or is_assigned_hw or is_admin):
            raise PermissionError(f"User '{user_id}' is not authorized to join appointment '{appointment_id}'.")

        # Generate session token and room ID
        room_id = f"room_{appointment_id.lower().replace('-', '_')}"
        return {
            "appointment_id": appointment_id,
            "room_id": room_id,
            "authorized": True,
            "participant_id": user_id,
            "participant_role": role,
            "doctor_name": apt["doctor_name"],
            "patient_name": apt["patient_name"],
            "screening_id": apt.get("screening_id"),
            "ice_servers": [
                {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}
            ],
        }

    async def register_websocket(self, appointment_id: str, websocket: WebSocket):
        """Register active signaling connection for appointment room."""
        if appointment_id not in self._active_connections:
            self._active_connections[appointment_id] = set()
        self._active_connections[appointment_id].add(websocket)

    async def unregister_websocket(self, appointment_id: str, websocket: WebSocket):
        """Remove signaling connection from appointment room."""
        if appointment_id in self._active_connections:
            self._active_connections[appointment_id].discard(websocket)
            if not self._active_connections[appointment_id]:
                del self._active_connections[appointment_id]

    async def broadcast_signal(self, appointment_id: str, sender_ws: WebSocket, message: Dict[str, Any]):
        """Relay WebRTC signaling message (offer, answer, ICE candidate) to other room peers."""
        connections = self._active_connections.get(appointment_id, set())
        for ws in connections:
            if ws != sender_ws:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Error broadcasting WebRTC signal in {appointment_id}: {e}")


# Singleton instance
appointment_service = AppointmentService()
