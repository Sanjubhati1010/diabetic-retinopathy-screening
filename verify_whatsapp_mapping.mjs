// End-to-end verification script for WhatsApp recipient mapping & authorization
import http from 'http';

const API_BASE = 'http://127.0.0.1:8000';

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const json = await res.json().catch(() => ({}));
  return { status: res.status, data: json };
}

async function runVerification() {
  console.log('====================================================');
  console.log('VERIFYING AUTHORITATIVE PATIENT WHATSAPP RECIPIENT DATA FLOW');
  console.log('====================================================\n');

  // Test 1: SCR-2026-1024 (Rampur Gram Panchayat / Sanjay Bhati)
  console.log('[TEST 1] Querying WhatsApp status for SCR-2026-1024 (Sanjay Bhati)...');
  const t1 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-1024/whatsapp/status`);
  console.log('Status Response:', t1.data);
  if (
    t1.status === 200 &&
    t1.data.patient_name === 'Sanjay Bhati' &&
    t1.data.recipient_phone === '+917378216613' &&
    t1.data.recipient_phone !== '+919876543210' &&
    t1.data.health_worker_name === 'Pooja Sharma (ASHA Worker)'
  ) {
    console.log('✅ TEST 1 PASSED: SCR-2026-1024 accurately mapped to Patient Sanjay Bhati (+917378216613) and NOT Health Worker Pooja Sharma (+919876543210).\n');
  } else {
    console.error('❌ TEST 1 FAILED:', t1);
    process.exit(1);
  }

  // Test 2: SCR-2026-0992 (Shivpuri Taluk / Sunita Devi)
  console.log('[TEST 2] Querying WhatsApp status for SCR-2026-0992 (Sunita Devi)...');
  const t2 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-0992/whatsapp/status`);
  console.log('Status Response:', t2.data);
  if (
    t2.status === 200 &&
    t2.data.patient_name === 'Sunita Devi' &&
    t2.data.recipient_phone === '+919412388990' &&
    t2.data.recipient_phone !== '+919876543210' &&
    t2.data.recipient_phone !== '+917378216613' &&
    t2.data.health_worker_name === 'Sarita Devi (Vision Tech)'
  ) {
    console.log('✅ TEST 2 PASSED: SCR-2026-0992 accurately mapped to Patient Sunita Devi (+919412388990) and NOT Pooja Sharma.\n');
  } else {
    console.error('❌ TEST 2 FAILED:', t2);
    process.exit(1);
  }

  // Test 3: SCR-2026-0850 (Kolar Rural Block / Balwinder Singh)
  console.log('[TEST 3] Querying WhatsApp status for SCR-2026-0850 (Balwinder Singh)...');
  const t3 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-0850/whatsapp/status`);
  console.log('Status Response:', t3.data);
  if (
    t3.status === 200 &&
    t3.data.patient_name === 'Balwinder Singh' &&
    t3.data.recipient_phone === '+919789012345' &&
    t3.data.recipient_phone !== '+919876543210' &&
    t3.data.health_worker_name === 'Sunil Gowda (Vision Tech)'
  ) {
    console.log('✅ TEST 3 PASSED: SCR-2026-0850 accurately mapped to Patient Balwinder Singh (+919789012345).\n');
  } else {
    console.error('❌ TEST 3 FAILED:', t3);
    process.exit(1);
  }

  // Test 4: Unassigned Screening Safety Gate
  console.log('[TEST 4] Querying WhatsApp status for SCR-UNKNOWN-VILLAGE-999 (Unassigned)...');
  const t4 = await fetchJson(`${API_BASE}/api/reports/SCR-UNKNOWN-VILLAGE-999/whatsapp/status`);
  console.log('Status Response:', t4.data);
  if (
    t4.status === 200 &&
    t4.data.can_send === false &&
    t4.data.recipient_phone === null &&
    t4.data.block_reason === 'Patient mobile number not available/verified.'
  ) {
    console.log('✅ TEST 4 PASSED: Unassigned patient safely blocks dispatch and displays "Patient mobile number not available/verified.".\n');
  } else {
    console.error('❌ TEST 4 FAILED:', t4);
    process.exit(1);
  }

  // Test 5: Mismatched Phone Number Rejection
  console.log('[TEST 5] Attempting to send report with mismatched patient and phone number...');
  const t5 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-0992/whatsapp/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      screening_id: 'SCR-2026-0992',
      recipient_phone: '+919876543210', // Health worker number instead of Sunita Devi's number
      health_worker_id: 'HW-SHIVPURI-02',
      language: 'en',
      opt_in_confirmed: true,
    }),
  });
  console.log('Mismatched Send Response (Status:', t5.status, '):', t5.data);
  if (t5.status === 400 && t5.data.detail && t5.data.detail.includes('Unauthorized recipient phone')) {
    console.log('✅ TEST 5 PASSED: Mismatched phone numbers strictly blocked by backend security gate.\n');
  } else {
    console.error('❌ TEST 5 FAILED:', t5);
    process.exit(1);
  }

  console.log('====================================================');
  console.log('ALL VERIFICATION CHECKS PASSED WITH 100% SUCCESS!');
  console.log('====================================================');
}

runVerification().catch((err) => {
  console.error('Fatal error during verification:', err);
  process.exit(1);
});

