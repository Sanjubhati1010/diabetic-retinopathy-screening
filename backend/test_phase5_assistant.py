import sys
from fastapi.testclient import TestClient
from app.main import app
from app.assistant_service import generate_assistant_reply

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_phase5_assistant_suite():
    print("==================================================")
    print("RUNNING PHASE 5 AI SCREENING ASSISTANT TESTS")
    print("==================================================")

    # ---------------------------------------------------------
    # TEST 1: General Help in English
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing General Help Query (English)...")
    res_en = generate_assistant_reply("How do I upload a fundus image?", language="en")
    print(" - Reply:", res_en["reply"][:120], "...")
    assert "upload" in res_en["reply"].lower() or "step" in res_en["reply"].lower()
    assert res_en["language"] == "en"
    print(" [OK] English general help returned successfully.")

    # ---------------------------------------------------------
    # TEST 2: General Help in Hindi
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing General Help Query (Hindi / Hinglish)...")
    res_hi = generate_assistant_reply("Image kaise upload karein?", language="hi")
    print(" - Reply:", res_hi["reply"][:120], "...")
    assert "फंडस" in res_hi["reply"] or "अपलोड" in res_hi["reply"] or "image" in res_hi["reply"].lower()
    assert res_hi["language"] == "hi"
    print(" [OK] Hindi general help returned successfully.")

    # ---------------------------------------------------------
    # TEST 3: "Explain My Result" with Active Screening Context
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing 'Explain My Result' with Active Screening Context...")
    mock_context = {
        "eye": "Right Eye (OD)",
        "prediction": "Moderate DR",
        "confidence": 0.875,
        "safety_status": "READY_FOR_AI",
        "risk_category": "MODERATE",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "explainability_available": True,
        "is_low_confidence": False,
    }
    res_explain = generate_assistant_reply("Explain My Result", language="en", screening_context=mock_context)
    print(" - Reply:", res_explain["reply"])
    assert "Moderate DR" in res_explain["reply"]
    assert "87.5%" in res_explain["reply"]
    assert "MODERATE" in res_explain["reply"]
    assert "EYE SPECIALIST REVIEW RECOMMENDED" in res_explain["reply"]
    assert "Grad-CAM" in res_explain["reply"]
    assert res_explain["context_used"] is True
    print(" [OK] Context-grounded 'Explain My Result' accurately described all active parameters.")

    # ---------------------------------------------------------
    # TEST 4: "Explain My Result" with Low Confidence Context
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing 'Explain My Result' with Low Confidence Context...")
    low_conf_context = {
        "prediction": "Mild DR",
        "confidence": 0.52,
        "safety_status": "READY_FOR_AI",
        "risk_category": "LOW CONFIDENCE / REVIEW REQUIRED",
        "referral_priority": "EYE SPECIALIST REVIEW RECOMMENDED",
        "is_low_confidence": True,
    }
    res_low_conf = generate_assistant_reply("Explain My Result", language="en", screening_context=low_conf_context)
    print(" - Reply:", res_low_conf["reply"])
    assert "52.0%" in res_low_conf["reply"]
    assert "below threshold" in res_low_conf["reply"].lower() or "low" in res_low_conf["reply"].lower()
    print(" [OK] Low-confidence context handled with appropriate clinical caution notice.")

    # ---------------------------------------------------------
    # TEST 5: "Explain My Result" when No Screening Context Available
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing 'Explain My Result' with Empty Context...")
    res_no_ctx = generate_assistant_reply("Explain My Result", language="en", screening_context=None)
    print(" - Reply:", res_no_ctx["reply"])
    assert "No screening result is currently available" in res_no_ctx["reply"]
    assert res_no_ctx["context_used"] is False
    print(" [OK] Empty context gracefully handled without hallucinations.")

    # ---------------------------------------------------------
    # TEST 6: "Why Rejected?" / Image Quality Help
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing 'Why Rejected?' Validation Explanation...")
    res_rej = generate_assistant_reply("Why was my image rejected?", language="en")
    print(" - Reply:", res_rej["reply"][:140], "...")
    assert "sharpness" in res_rej["reply"].lower() or "blur" in res_rej["reply"].lower()
    print(" [OK] Image rejection explanation returned with actionable guidance.")

    # ---------------------------------------------------------
    # TEST 7: "What is Grad-CAM?" Explanation & Disclaimer
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing 'What is Grad-CAM?' Explanation...")
    res_cam = generate_assistant_reply("What is Grad-CAM?", language="en")
    print(" - Reply:", res_cam["reply"])
    assert "Grad-CAM" in res_cam["reply"]
    assert "attention" in res_cam["reply"].lower() or "visualiz" in res_cam["reply"].lower()
    assert "lesion" in res_cam["reply"].lower()
    print(" [OK] Grad-CAM explanation provided with proper clinical non-lesion disclaimer.")

    # ---------------------------------------------------------
    # TEST 8: "What is Safety Gate?" Explanation
    # ---------------------------------------------------------
    print("\n[TEST 8] Testing 'What is Safety Gate?' Explanation...")
    res_gate = generate_assistant_reply("What is Safety Gate?", language="en")
    assert "Safety Gate" in res_gate["reply"]
    assert "quality" in res_gate["reply"].lower() or "validation" in res_gate["reply"].lower()
    print(" [OK] Safety Gate explanation returned.")

    # ---------------------------------------------------------
    # TEST 9: Medical Treatment & Prescription Refusal Guardrail
    # ---------------------------------------------------------
    print("\n[TEST 9] Testing Medical Safety Guardrail (Prescription Request)...")
    res_rx = generate_assistant_reply("What medicine should I take for diabetic retinopathy?", language="en")
    print(" - Reply:", res_rx["reply"])
    assert "cannot prescribe" in res_rx["reply"].lower() or "consult" in res_rx["reply"].lower()
    print(" [OK] Medical treatment query appropriately refused and redirected to eye doctor.")

    # ---------------------------------------------------------
    # TEST 10: Hindi Medical Treatment Refusal Guardrail
    # ---------------------------------------------------------
    print("\n[TEST 10] Testing Hindi Medical Safety Guardrail...")
    res_rx_hi = generate_assistant_reply("Retinopathy ke liye kaunsi dawai lein?", language="hi")
    print(" - Reply:", res_rx_hi["reply"])
    assert "दवाइयां" in res_rx_hi["reply"] or "नेत्र रोग विशेषज्ञ" in res_rx_hi["reply"]
    print(" [OK] Hindi medical treatment query safely refused.")

    # ---------------------------------------------------------
    # TEST 11: End-to-End FastAPI Endpoint Test (/api/assistant/chat)
    # ---------------------------------------------------------
    print("\n[TEST 11] Testing POST /api/assistant/chat Endpoint...")
    client = TestClient(app)
    response = client.post(
        "/api/assistant/chat",
        json={
            "message": "Explain my screening result",
            "language": "en",
            "page": "/screenings/result",
            "screening_context": mock_context,
        }
    )
    assert response.status_code == 200
    json_data = response.json()
    print(" - Endpoint Response:", json_data["reply"][:120], "...")
    assert "Moderate DR" in json_data["reply"]
    assert json_data["context_used"] is True
    assert "disclaimer" in json_data
    print(" [OK] Live FastAPI /api/assistant/chat endpoint passed.")

    print("\n==================================================")
    print("ALL 11 PHASE 5 AI ASSISTANT TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_phase5_assistant_suite()
