"""
Verification of Database Failure Handling and Resilience for Phase 13.
Validates transactional rollback on errors, connection timeouts, and graceful error handling.
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError

from app.database import Base, SessionLocal, engine
from app.models import PatientModel, ScreeningModel, AppointmentModel
from app.appointment_service import appointment_service

def test_transaction_rollback_on_failure():
    print("==================================================================")
    print("PHASE 13: DATABASE FAILURE RESILIENCE — TEST 1: TRANSACTION ROLLBACK")
    print("==================================================================")
    db = SessionLocal()
    pat_id = "PAT-FAIL-TEST-001"
    try:
        # Create a patient
        patient = PatientModel(
            id=pat_id,
            name="Rollback Test Patient",
            age=50,
            gender="female",
            registered_date="2026-08-27",
        )
        db.add(patient)
        
        # Intentionally cause a foreign key constraint violation within the same transaction
        bad_appointment = AppointmentModel(
            id="APT-INVALID-001",
            doctor_id="DOC-NONEXISTENT",
            doctor_name="Non Existent",
            health_worker_id="HW-NONEXISTENT",
            health_worker_name="Non Existent",
            patient_id="PAT-NONEXISTENT",
            date="2026-08-28",
            start_time="09:00",
            end_time="09:30",
            created_at="2026-08-27T00:00:00Z",
            updated_at="2026-08-27T00:00:00Z",
        )
        db.add(bad_appointment)
        
        try:
            db.commit()
            raise AssertionError("Transaction should have failed on FK violation")
        except IntegrityError:
            print(" [*] Caught expected IntegrityError constraint violation.")
            db.rollback()
            print(" [*] Transaction rollback executed successfully.")
            
        # Verify that patient was rolled back and does not exist
        found = db.query(PatientModel).filter(PatientModel.id == pat_id).first()
        assert found is None, "Patient must not be persisted after transaction rollback"
        print(" [OK] Transaction atomicity confirmed: Zero partial/dirty writes.")
        
    finally:
        db.close()

def test_unreachable_db_handling():
    print("\n==================================================================")
    print("PHASE 13: DATABASE FAILURE RESILIENCE — TEST 2: DISCONNECTED ENGINE")
    print("==================================================================")
    # Instantiate an unreachable database engine with small timeout
    bad_engine = create_engine("mysql+pymysql://invalid_user:invalid_pass@127.0.0.1:9999/non_existent?connect_timeout=1")
    BadSession = sessionmaker(bind=bad_engine)
    bad_session = BadSession()
    
    try:
        bad_session.execute(text("SELECT 1"))
        raise AssertionError("Connection to invalid port should have failed")
    except OperationalError as e:
        print(" [*] Caught expected OperationalError for unreachable database.")
        print(f" [OK] Error successfully caught and handled: {type(e).__name__}")
    finally:
        bad_session.close()
        bad_engine.dispose()

def main():
    test_transaction_rollback_on_failure()
    test_unreachable_db_handling()
    print("\n==================================================================")
    print("DATABASE FAILURE RESILIENCE VERIFICATION: 100% PASSED!")
    print("==================================================================")

if __name__ == "__main__":
    main()
