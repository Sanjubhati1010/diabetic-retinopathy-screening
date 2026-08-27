"""
Comprehensive Master Test Runner for Rural DR Screening System (Phases 1 - 13).
Executes each phase test suite, captures output, and verifies 100% test passing baseline.
"""

import os
import sys
import subprocess
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

TEST_SUITES = [
    ("Phase 1: Input Validation & Image Quality", "test_phase1_validation.py"),
    ("Phase 2: AI Safety Gate & Confidence", "test_phase2_safety.py"),
    ("Phase 3: Explainability & Grad-CAM", "test_phase3_explainability.py"),
    ("Phase 4: Risk Categorization & Referral", "test_phase4_risk.py"),
    ("Phase 5: Conversational AI Assistant", "test_phase5_assistant.py"),
    ("Phase 6: Human-in-the-Loop Doctor Review", "test_phase6_doctor_review.py"),
    ("Phase 10: Longitudinal Patient Tracking", "test_phase10_longitudinal.py"),
    ("Phase 11: Tele-Ophthalmology & Appointments", "test_phase11_appointments.py"),
    ("Phase 12: WhatsApp Clinical Report Delivery", "test_phase12_whatsapp.py"),
    ("Phase 13: MySQL / SQLAlchemy Database Persistence", "test_phase13_database.py"),
    ("End-to-End API Integration", "test_e2e_api.py"),
    ("DR Classification Model Inference", "test_inference.py"),
]

def run_suite(name, filename):
    print(f"\n=======================================================")
    print(f"RUNNING: {name} ({filename})")
    print(f"=======================================================")
    start_t = time.time()
    
    python_exe = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    res = subprocess.run(
        [python_exe, filename],
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - start_t
    
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
        
    if res.returncode == 0:
        print(f"[PASSED] {name} ({elapsed:.2f}s)")
        return True, elapsed
    else:
        print(f"[FAILED] {name} (Exit code {res.returncode}, {elapsed:.2f}s)")
        return False, elapsed

def main():
    print("==================================================================")
    print("MADOCS AI RETINAL SCREENING — COMPREHENSIVE TEST SUITE EXECUTION")
    print("==================================================================")
    
    results = []
    total_start = time.time()
    
    for name, filename in TEST_SUITES:
        passed, elapsed = run_suite(name, filename)
        results.append((name, filename, passed, elapsed))
        
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY REPORT OF ALL TEST SUITES")
    print("=" * 70)
    
    all_passed = True
    for name, filename, passed, elapsed in results:
        status_str = "PASS [OK]" if passed else "FAIL [ERROR]"
        print(f"{status_str:<12} | {elapsed:>5.2f}s | {name} ({filename})")
        if not passed:
            all_passed = False
            
    print("=" * 70)
    if all_passed:
        print(f"SUCCESS: ALL {len(TEST_SUITES)} TEST SUITES PASSED IN {total_elapsed:.2f}s!")
        sys.exit(0)
    else:
        print(f"FAILURE: One or more test suites failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
