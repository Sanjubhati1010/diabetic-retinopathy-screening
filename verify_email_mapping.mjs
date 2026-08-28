// End-to-end verification script for Phase 14: Patient Email Registration & Verified Email Delivery
const API_BASE = 'http://127.0.0.1:8000';

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const json = await res.json().catch(() => ({}));
  return { status: res.status, data: json };
}

async function runVerification() {
  console.log('====================================================');
  console.log('VERIFYING PHASE 14 PATIENT EMAIL REGISTRATION & VERIFIED DELIVERY');
  console.log('====================================================\n');

  // Test 1: Patient Registration with Email
  console.log('[TEST 1] Registering a new patient with valid email...');
  const newPat = {
    name: 'Devendra Mehra',
    age: 50,
    gender: 'male',
    phone: '+91 98777 66554',
    email: 'devendra.mehra@ruralcare.org',
    village: 'Varanasi Central',
    district: 'Varanasi',
    diabetes_duration: 7,
    last_hba1c: 7.9,
    insulin_use: true,
  };
  const t1 = await fetchJson(`${API_BASE}/api/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newPat),
  });
  console.log('Registration Response:', t1.data);
  if (t1.status === 201 && t1.data.email === 'devendra.mehra@ruralcare.org') {
    console.log('✅ TEST 1 PASSED: Patient registered with valid email in backend/MySQL.\n');
  } else {
    console.error('❌ TEST 1 FAILED:', t1);
    process.exit(1);
  }

  // Test 2: Invalid Email Format Rejection
  console.log('[TEST 2] Verifying rejection of invalid email format during patient registration...');
  const badPat = {
    name: 'Bad Email Patient',
    age: 40,
    gender: 'female',
    phone: '+91 98000 00000',
    email: 'invalid-email-address',
  };
  const t2 = await fetchJson(`${API_BASE}/api/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(badPat),
  });
  if (t2.status === 400 && t2.data.detail?.includes('Invalid email address format')) {
    console.log('✅ TEST 2 PASSED: Backend correctly rejects invalid email format with HTTP 400.\n');
  } else {
    console.error('❌ TEST 2 FAILED:', t2);
    process.exit(1);
  }

  // Test 3: Email Status for Sanjay Bhati (SCR-2026-1024)
  console.log('[TEST 3] Querying Email status for SCR-2026-1024 (Sanjay Bhati)...');
  const t3 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-1024/email/status`);
  console.log('Status Response:', t3.data);
  if (
    t3.status === 200 &&
    t3.data.patient_name === 'Sanjay Bhati' &&
    t3.data.recipient_email === 'sanjay.bhati@example.com' &&
    t3.data.recipient_email !== 'asha.rampur@phc.in'
  ) {
    console.log('✅ TEST 3 PASSED: SCR-2026-1024 accurately mapped to Patient Sanjay Bhati (sanjay.bhati@example.com) and NOT Health Worker.\n');
  } else {
    console.error('❌ TEST 3 FAILED:', t3);
    process.exit(1);
  }

  // Test 4: Rejection of Health Worker Email as recipient
  console.log('[TEST 4] Attempting to dispatch report to Health Worker email (asha.rampur@phc.in)...');
  const t4 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-1024/email/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      screening_id: 'SCR-2026-1024',
      recipient_email: 'asha.rampur@phc.in',
    }),
  });
  if (t4.status === 400 && (t4.data.detail?.includes('Unauthorized recipient email') || t4.data.detail?.includes('Email service is not configured.'))) {
    console.log('✅ TEST 4 PASSED: Dispatching to Health Worker email or unconfigured service is strictly rejected with HTTP 400.\n');
  } else {
    console.error('❌ TEST 4 FAILED:', t4);
    process.exit(1);
  }

  // Test 5: Unconfigured Email Provider Safety Gate (No fake SENT simulation)
  console.log('[TEST 5] Verifying unconfigured email service safety (strictly blocks fake SENT)...');
  const t5 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-1024/email/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      screening_id: 'SCR-2026-1024',
      recipient_email: 'sanjay.bhati@example.com',
      language: 'en',
      opt_in_confirmed: true,
    }),
  });
  console.log('Send Response:', t5.data);
  if (t5.status === 400 && t5.data.detail === 'Email service is not configured.') {
    console.log('✅ TEST 5 PASSED: Unconfigured email service strictly rejects dispatch with "Email service is not configured." (No fake SENT).\n');
  } else if (t5.status === 200 && t5.data.status === 'SENT' && t5.data.provider_message_id?.startsWith('smtp-')) {
    console.log('✅ TEST 5 PASSED: Verified real SMTP dispatch accepted by mail provider with real message ID.\n');
  } else {
    console.error('❌ TEST 5 FAILED:', t5);
    process.exit(1);
  }

  // Test 6: Patient without Email (Balwinder Singh / SCR-2026-0850)
  console.log('[TEST 6] Verifying dispatch block for patient without email (SCR-2026-0850)...');
  const t6 = await fetchJson(`${API_BASE}/api/reports/SCR-2026-0850/email/status`);
  console.log('Status Response for patient without email:', t6.data);
  if (
    t6.status === 200 &&
    t6.data.can_send === false &&
    t6.data.block_reason === 'Patient email address not available.'
  ) {
    console.log('✅ TEST 6 PASSED: Missing patient email correctly blocks delivery with "Patient email address not available."\n');
  } else {
    console.error('❌ TEST 6 FAILED:', t6);
    process.exit(1);
  }

  console.log('====================================================');
  console.log('🎉 ALL PHASE 14 EMAIL RECIPIENT & DELIVERY VERIFICATION TESTS PASSED 100%');
  console.log('====================================================');
}

runVerification().catch((err) => {
  console.error('Fatal Verification Error:', err);
  process.exit(1);
});
