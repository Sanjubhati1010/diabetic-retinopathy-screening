const API_BASE = 'http://127.0.0.1:8000';

async function runEndToEndVerification() {
  console.log('================================================================');
  console.log('STARTING END-TO-END PATIENT CONTACT PERSISTENCE VERIFICATION');
  console.log('================================================================\n');

  // 1. Check SCR-2026-1025 WhatsApp Status
  console.log('1. Checking WhatsApp Recipient Resolution for SCR-2026-1025...');
  const waRes = await fetch(`${API_BASE}/api/reports/SCR-2026-1025/whatsapp/status`);
  const waData = await waRes.json();
  console.log('   Status Code:', waRes.status);
  console.log('   Patient Name:', waData.patient_name);
  console.log('   Recipient Phone:', waData.recipient_phone);
  console.log('   Doctor Review Status:', waData.doctor_review_status);
  console.log('   Can Send:', waData.can_send);
  if (waData.patient_name === 'Devendra Mehra' && waData.recipient_phone === '+919877766554') {
    console.log('   ✅ WhatsApp Resolution PASSED for Devendra Mehra (+91 98777 66554)\n');
  } else {
    console.error('   ❌ WhatsApp Resolution FAILED:', waData);
    process.exit(1);
  }

  // 2. Check SCR-2026-1025 Email Status
  console.log('2. Checking Email Recipient Resolution for SCR-2026-1025...');
  const emRes = await fetch(`${API_BASE}/api/reports/SCR-2026-1025/email/status`);
  const emData = await emRes.json();
  console.log('   Status Code:', emRes.status);
  console.log('   Patient Name:', emData.patient_name);
  console.log('   Recipient Email:', emData.recipient_email);
  console.log('   Doctor Review Status:', emData.doctor_review_status);
  console.log('   Can Send:', emData.can_send);
  if (emData.patient_name === 'Devendra Mehra' && emData.recipient_email === 'devendra.mehra@ruralcare.org') {
    console.log('   ✅ Email Resolution PASSED for Devendra Mehra (devendra.mehra@ruralcare.org)\n');
  } else {
    console.error('   ❌ Email Resolution FAILED:', emData);
    process.exit(1);
  }

  // 3. Check SCR-2026-1025 Screening Record & Linked Patient in Database
  console.log('3. Checking Database Screening & Patient Record for SCR-2026-1025...');
  const scrRes = await fetch(`${API_BASE}/api/screenings/SCR-2026-1025`);
  const scrData = await scrRes.json();
  console.log('   Screening ID:', scrData.id);
  console.log('   Patient ID in Screening:', scrData.patient_id);
  console.log('   Patient Name in Screening:', scrData.patient_name);

  const patRes = await fetch(`${API_BASE}/api/patients/${scrData.patient_id}`);
  const patData = await patRes.json();
  console.log('   Resolved Patient ID:', patData.id);
  console.log('   Resolved Patient Name:', patData.name);
  console.log('   Resolved Patient Phone/Mobile:', patData.phone, '/', patData.mobile);
  console.log('   Resolved Patient Email:', patData.email);
  if (patData.name === 'Devendra Mehra' && patData.phone === '+91 98777 66554' && patData.email === 'devendra.mehra@ruralcare.org') {
    console.log('   ✅ Authoritative Database Linkage PASSED for SCR-2026-1025 -> Patient Devendra Mehra\n');
  } else {
    console.error('   ❌ Authoritative Database Linkage FAILED:', patData);
    process.exit(1);
  }

  // 4. Register New Dynamic Patient & Screening to Verify Full End-to-End Persistence
  console.log('4. Registering New Patient with Mobile + Email & creating new screening...');
  const newPatPayload = {
    name: 'Ananya Sharma',
    age: 46,
    gender: 'female',
    mobile: '+91 98123 45678',
    email: 'ananya.sharma@visioncare.org',
    village: 'Shivpur Gram',
    district: 'Varanasi',
    diabetesDuration: 4,
    lastHba1c: 7.2,
    insulinUse: false,
  };
  const regRes = await fetch(`${API_BASE}/api/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newPatPayload),
  });
  const regData = await regRes.json();
  console.log('   Created Patient ID:', regData.id);
  console.log('   Created Patient Phone:', regData.phone);
  console.log('   Created Patient Email:', regData.email);

  const newScrPayload = {
    id: `SCR-${Date.now()}`,
    patientId: regData.id,
    patientName: regData.name,
    predictedClass: 1,
    className: 'Mild DR',
    confidence: 0.91,
    overallSeverity: 'dr1',
  };
  const newScrRes = await fetch(`${API_BASE}/api/screenings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newScrPayload),
  });
  const newScrData = await newScrRes.json();
  console.log('   Created Screening ID:', newScrData.id);

  // Check WhatsApp & Email resolution for new dynamic screening
  const newWaRes = await fetch(`${API_BASE}/api/reports/${newScrData.id}/whatsapp/status`);
  const newWaData = await newWaRes.json();
  console.log('   New Screening WhatsApp Recipient Phone:', newWaData.recipient_phone);

  const newEmRes = await fetch(`${API_BASE}/api/reports/${newScrData.id}/email/status`);
  const newEmData = await newEmRes.json();
  console.log('   New Screening Email Recipient Email:', newEmData.recipient_email);

  if (newWaData.recipient_phone === '+919812345678' && newEmData.recipient_email === 'ananya.sharma@visioncare.org') {
    console.log('   ✅ Dynamic Patient Registration & Contact Persistence Flow PASSED!\n');
  } else {
    console.error('   ❌ Dynamic Flow FAILED:', newWaData, newEmData);
    process.exit(1);
  }

  console.log('================================================================');
  console.log('🎉 ALL END-TO-END CONTACT PERSISTENCE CHECKS PASSED (100%)');
  console.log('================================================================');
}

runEndToEndVerification().catch((err) => {
  console.error('Unhandled error during verification:', err);
  process.exit(1);
});
