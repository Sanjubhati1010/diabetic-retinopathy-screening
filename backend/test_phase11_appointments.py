"""
Phase 11 Doctor Appointment & Tele-Ophthalmology Test Suite
Tests:
- Doctor directory with demo labeling
- Working hours & slot availability
- Past slot and double-booking prevention
- Appointment creation and state machine transitions
- Role authorization & security validation
- Appointment-scoped messaging
- Doctor consultation notes
- WebRTC video session authorization
- AI Assistant contextual tele-ophthalmology Q&A
"""

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_01_doctor_directory():
    """Verify demo doctor directory with proper specialization and demo flags."""
    response = client.get("/api/doctors")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["total_count"] >= 3, "Expected at least 3 doctors"
    
    # Check Dr. Swaminathan
    doc1 = next((d for d in data["doctors"] if d["id"] == "DOC-SWAMINATHAN"), None)
    assert doc1 is not None, "DOC-SWAMINATHAN must be present"
    assert doc1["is_demo"] is True, "Doctor must be labeled as is_demo: True"
    assert "Retina" in doc1["specialization"], "Specialization should mention Retina"
    print("\n[TEST 1] Doctor directory verified with Demo Doctor flags.")


def test_02_doctor_availability_working_day():
    """Verify time slot generation for a valid future working day."""
    # Find next Friday (known working day for all demo doctors)
    today = datetime.now().date()
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    future_friday = today + timedelta(days=days_ahead)
    date_str = future_friday.strftime("%Y-%m-%d")

    response = client.get(f"/api/doctors/DOC-SWAMINATHAN/availability?date={date_str}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["is_working_day"] is True
    assert data["total_slots"] > 0
    assert data["available_slots_count"] > 0
    
    first_slot = data["slots"][0]
    assert first_slot["start_time"] == "09:00"
    assert first_slot["available"] is True
    print(f"\n[TEST 2] Doctor availability on {date_str} generated {data['total_slots']} slots.")


def test_03_create_appointment_success():
    """Verify booking a valid appointment."""
    today = datetime.now().date()
    days_ahead = (3 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    future_thursday = today + timedelta(days=days_ahead)
    date_str = future_thursday.strftime("%Y-%m-%d")

    payload = {
        "doctor_id": "DOC-SWAMINATHAN",
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
        "date": date_str,
        "start_time": "14:00",
        "reason": "AI screening indicates moderate DR. Specialist review requested for rural patient.",
    }

    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"].startswith("APT-")
    assert data["status"] == "PENDING"
    assert data["doctor_name"] == "Dr. Arvind Swaminathan, MS"
    assert data["patient_name"] == "Ramesh Kumar Verma"
    assert data["start_time"] == "14:00"
    print(f"\n[TEST 3] Created appointment {data['id']} successfully.")
    return data["id"], date_str


def test_04_double_booking_prevention():
    """Verify server rejects duplicate appointment booking for same doctor, date, and slot."""
    today = datetime.now().date()
    days_ahead = (3 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    future_thursday = today + timedelta(days=days_ahead)
    date_str = future_thursday.strftime("%Y-%m-%d")

    # Attempt to book same 14:00 slot that was booked in test_03
    payload = {
        "doctor_id": "DOC-SWAMINATHAN",
        "health_worker_id": "HW-RAMPUR-02",
        "health_worker_name": "Sunil Gowda",
        "health_worker_email": "sunil@phc.in",
        "patient_id": "PAT-2026-082",
        "patient_name": "Sunita Devi",
        "patient_age": 52,
        "patient_gender": "female",
        "village": "Shivpuri Taluk",
        "date": date_str,
        "start_time": "14:00",
        "reason": "Trying to book already occupied slot.",
    }

    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 400, "Double-booking identical slot must return HTTP 400"
    assert "not available" in response.json()["detail"].lower()
    print("\n[TEST 4] Double-booking prevention verified.")


def test_05_past_date_booking_prevention():
    """Verify server rejects appointment bookings for past dates."""
    past_date_str = "2024-01-15"
    payload = {
        "doctor_id": "DOC-SWAMINATHAN",
        "health_worker_id": "HW-RAMPUR-01",
        "health_worker_name": "Pooja Sharma",
        "health_worker_email": "asha.rampur@phc.in",
        "patient_id": "PAT-2026-081",
        "patient_name": "Ramesh Kumar Verma",
        "date": past_date_str,
        "start_time": "10:00",
        "reason": "Past date test",
    }

    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 400, "Booking past date must return HTTP 400"
    print("\n[TEST 5] Past-date booking prevention verified.")


def test_06_doctor_accept_appointment():
    """Verify doctor accepts appointment transition PENDING -> CONFIRMED."""
    # Using seeded appointment APT-2026-102 (currently PENDING)
    payload = {
        "status": "CONFIRMED",
        "caller_role": "doctor",
        "reason_or_comment": "Screening review confirmed. Tele-consultation scheduled.",
    }
    response = client.patch("/api/appointments/APT-2026-102/status", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "CONFIRMED"
    print("\n[TEST 6] Doctor confirmed appointment APT-2026-102.")


def test_07_doctor_decline_appointment():
    """Verify doctor declines appointment transition."""
    # First create a new pending appointment to decline on a guaranteed working weekday
    today = datetime.now().date()
    days_ahead = (1 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    future_tuesday = today + timedelta(days=days_ahead + 7)  # next next tuesday
    date_str = future_tuesday.strftime("%Y-%m-%d")

    create_payload = {
        "doctor_id": "DOC-NAMBIAR",
        "health_worker_id": "HW-RAMPUR-01",
        "health_worker_name": "Pooja Sharma",
        "health_worker_email": "asha.rampur@phc.in",
        "patient_id": "PAT-2026-084",
        "patient_name": "Lakshmi Patel",
        "date": date_str,
        "start_time": "11:00",
        "reason": "Check for NPDR",
    }
    create_res = client.post("/api/appointments", json=create_payload)
    assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
    created = create_res.json()
    apt_id = created["id"]

    decline_payload = {
        "status": "DECLINED",
        "caller_role": "doctor",
        "reason_or_comment": "Doctor emergency surgery duty at base hospital.",
    }
    response = client.patch(f"/api/appointments/{apt_id}/status", json=decline_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "DECLINED"
    print(f"\n[TEST 7] Doctor declined appointment {apt_id}.")


def test_08_health_worker_cancellation():
    """Verify health worker can cancel an appointment."""
    today = datetime.now().date()
    days_ahead = (2 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    future_wednesday = today + timedelta(days=days_ahead + 7)
    date_str = future_wednesday.strftime("%Y-%m-%d")

    create_payload = {
        "doctor_id": "DOC-RAO",
        "health_worker_id": "HW-RAMPUR-01",
        "health_worker_name": "Pooja Sharma",
        "health_worker_email": "asha.rampur@phc.in",
        "patient_id": "PAT-2026-083",
        "patient_name": "Balwinder Singh",
        "date": date_str,
        "start_time": "10:00",
        "reason": "Routine checkup",
    }
    create_res = client.post("/api/appointments", json=create_payload)
    assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
    created = create_res.json()
    apt_id = created["id"]

    cancel_payload = {
        "status": "CANCELLED",
        "caller_role": "health_worker",
        "reason_or_comment": "Patient unable to travel to PHC center on scheduled date.",
    }
    response = client.patch(f"/api/appointments/{apt_id}/status", json=cancel_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    print(f"\n[TEST 8] Health worker cancelled appointment {apt_id}.")


def test_09_unauthorized_completion_attempt():
    """Verify health worker cannot mark an appointment COMPLETED (only doctor can)."""
    payload = {
        "status": "COMPLETED",
        "caller_role": "health_worker",
        "reason_or_comment": "Attempting unauthorized completion.",
    }
    response = client.patch("/api/appointments/APT-2026-101/status", json=payload)
    assert response.status_code == 403, "Health worker completing appointment must return HTTP 403"
    print("\n[TEST 9] Unauthorized status transition blocked successfully.")


def test_10_doctor_clinical_notes():
    """Verify doctor adds clinical consultation notes and recommendation."""
    payload = {
        "doctor_id": "DOC-SWAMINATHAN",
        "doctor_notes": "Bilateral fundus examined via tele-consultation. Right eye exhibits microaneurysms and hard exudates consistent with Moderate NPDR.",
        "doctor_recommendation": "Advised tighter glycemic control and follow-up tele-screening in 6 months.",
        "follow_up_date": "2027-02-28",
    }
    response = client.post("/api/appointments/APT-2026-101/notes", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "Doctor-entered consultation note" in data["doctor_notes"], "Notes must clearly indicate doctor-entered origin"
    assert data["status"] == "COMPLETED"
    print("\n[TEST 10] Doctor consultation notes recorded with proper clinical attribution.")


def test_11_appointment_chat_messaging():
    """Verify appointment-scoped chat messaging."""
    # Send message as health worker
    msg_payload = {
        "sender_id": "HW-RAMPUR-01",
        "sender_name": "Pooja Sharma",
        "sender_role": "health_worker",
        "message": "Doctor, patient is present in Rampur PHC and vitals are stable.",
    }
    response = client.post("/api/appointments/APT-2026-101/messages", json=msg_payload)
    assert response.status_code == 201
    msg_data = response.json()
    assert msg_data["message"] == msg_payload["message"]
    assert msg_data["sender_role"] == "health_worker"

    # Fetch chat history
    get_res = client.get("/api/appointments/APT-2026-101/messages")
    assert get_res.status_code == 200
    msgs = get_res.json()["messages"]
    assert len(msgs) >= 2
    assert any(m["message"] == msg_payload["message"] for m in msgs)
    print("\n[TEST 11] Appointment-scoped messaging verified.")


def test_12_video_session_authorization():
    """Verify WebRTC video room session authorization and STUN servers."""
    # Authorized Doctor
    res_doc = client.get("/api/appointments/APT-2026-101/video/session?user_id=DOC-SWAMINATHAN&role=doctor")
    assert res_doc.status_code == 200
    data = res_doc.json()
    assert data["authorized"] is True
    assert data["room_id"] == "room_apt_2026_101"
    assert len(data["ice_servers"]) > 0

    # Authorized Health Worker
    res_hw = client.get("/api/appointments/APT-2026-101/video/session?user_id=HW-RAMPUR-01&role=health_worker")
    assert res_hw.status_code == 200
    assert res_hw.json()["authorized"] is True

    # Unauthorized User
    res_unauth = client.get("/api/appointments/APT-2026-101/video/session?user_id=UNKNOWN-USER&role=guest")
    assert res_unauth.status_code == 403
    print("\n[TEST 12] WebRTC video room authorization and security verified.")


def test_13_ai_assistant_appointment_qa_en():
    """Verify AI Assistant explains how to book doctor appointments in English."""
    payload = {
        "message": "How do I book a doctor appointment?",
        "language": "en",
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "Tele-Ophthalmology" in reply or "appointment" in reply.lower()
    assert "Book Appointment" in reply
    print("\n[TEST 13] Assistant English appointment guidance verified.")


def test_14_ai_assistant_video_call_qa_en():
    """Verify AI Assistant explains how to join video consultations."""
    payload = {
        "message": "How do I start the video consultation?",
        "language": "en",
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "Join Video Consultation" in reply or "camera" in reply.lower()
    print("\n[TEST 14] Assistant video consultation guidance verified.")


def test_15_ai_assistant_appointment_qa_hi():
    """Verify AI Assistant Hindi guidance for doctor appointment booking."""
    payload = {
        "message": "डॉक्टर अपॉइंटमेंट कैसे बुक करें?",
        "language": "hi",
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "टेली-परामर्श" in reply or "अपॉइंटमेंट" in reply
    print("\n[TEST 15] Assistant Hindi appointment guidance verified.")


def test_16_ai_assistant_unavailable_doctor_qa():
    """Verify AI Assistant guidance when doctor is unavailable."""
    payload = {
        "message": "What happens if the doctor is unavailable?",
        "language": "en",
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "Reschedule" in reply or "alternate" in reply.lower() or "Hospital" in reply
    print("\n[TEST 16] Assistant doctor unavailability guidance verified.")


def test_17_ai_assistant_screening_sharing_qa():
    """Verify AI Assistant guidance on sharing fundus scans during consultation."""
    payload = {
        "message": "Can I share a screening with the doctor?",
        "language": "en",
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "share" in reply.lower()
    assert "fundus" in reply.lower() or "screening" in reply.lower()
    print("\n[TEST 17] Assistant screening sharing guidance verified.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING PHASE 11 TELE-OPHTHALMOLOGY TESTS")
    print("==================================================")
    test_01_doctor_directory()
    test_02_doctor_availability_working_day()
    test_03_create_appointment_success()
    test_04_double_booking_prevention()
    test_05_past_date_booking_prevention()
    test_06_doctor_accept_appointment()
    test_07_doctor_decline_appointment()
    test_08_health_worker_cancellation()
    test_09_unauthorized_completion_attempt()
    test_10_doctor_clinical_notes()
    test_11_appointment_chat_messaging()
    test_12_video_session_authorization()
    test_13_ai_assistant_appointment_qa_en()
    test_14_ai_assistant_video_call_qa_en()
    test_15_ai_assistant_appointment_qa_hi()
    test_16_ai_assistant_unavailable_doctor_qa()
    test_17_ai_assistant_screening_sharing_qa()
    print("\n==================================================")
    print("ALL 17 PHASE 11 TELE-OPHTHALMOLOGY TESTS PASSED!")
    print("==================================================")
