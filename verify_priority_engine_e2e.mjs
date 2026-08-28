/**
 * End-to-end verification of Rural Care Priority Engine against live backend.
 */
const API_BASE = 'http://127.0.0.1:8000';

async function verifyPriorityEngine() {
  console.log('================================================================');
  console.log('STARTING RURAL CARE PRIORITY ENGINE E2E VERIFICATION');
  console.log('================================================================\n');

  // 1. Check Priority Stats
  console.log('1. Fetching /api/priority/stats...');
  const statsRes = await fetch(`${API_BASE}/api/priority/stats`);
  if (!statsRes.ok) {
    console.error('❌ Stats endpoint failed:', statsRes.status, await statsRes.text());
    process.exit(1);
  }
  const stats = await statsRes.json();
  console.log('   Total Screened:', stats.total_screened);
  console.log('   Urgent (P1):', stats.urgent_count);
  console.log('   Priority (P2):', stats.priority_count);
  console.log('   Routine (P3):', stats.routine_count);
  console.log('   Verification Required (AI Uncertainty):', stats.verification_required_count);
  console.log('   Re-capture Required:', stats.recapture_required_count);
  console.log('   Algorithm Version:', stats.algorithm_version);

  if (stats.total_screened > 0 && stats.algorithm_version === 'RCP-1.0') {
    console.log('   ✅ /api/priority/stats PASSED\n');
  } else {
    console.error('   ❌ Invalid stats payload:', stats);
    process.exit(1);
  }

  // 2. Check Priority Queue
  console.log('2. Fetching /api/priority/queue...');
  const queueRes = await fetch(`${API_BASE}/api/priority/queue`);
  if (!queueRes.ok) {
    console.error('❌ Queue endpoint failed:', queueRes.status, await queueRes.text());
    process.exit(1);
  }
  const qData = await queueRes.json();
  console.log(`   Fetched ${qData.queue.length} priority queue items.`);

  if (qData.queue.length === 0) {
    console.error('   ❌ Queue is empty!');
    process.exit(1);
  }

  const topItem = qData.queue[0];
  console.log('   Top Priority Item:');
  console.log('     Patient:', topItem.patient_name, `(${topItem.patient_id})`);
  console.log('     DR Result:', topItem.dr_result);
  console.log('     AI Confidence:', topItem.confidence_percentage);
  console.log('     Priority Level:', topItem.priority_level, `(${topItem.priority_label})`);
  console.log('     Priority Score:', topItem.priority_score);
  console.log('     Primary Reason:', topItem.primary_reason);
  console.log('     Recommended Action:', topItem.recommended_action);

  // Validate evidence checklist
  const chk = topItem.evidence_checklist;
  if (chk && chk.current_dr && chk.ai_confidence && chk.image_quality && chk.visual_acuity) {
    console.log('   ✅ Evidence Checklist Complete for top item.');
  } else {
    console.error('   ❌ Incomplete evidence checklist:', chk);
    process.exit(1);
  }
  console.log('   ✅ /api/priority/queue PASSED\n');

  // 3. Check Filter /api/priority/queue?filter=P1
  console.log('3. Testing P1 Filter (/api/priority/queue?filter=P1)...');
  const p1Res = await fetch(`${API_BASE}/api/priority/queue?filter=P1`);
  const p1Data = await p1Res.json();
  console.log(`   Found ${p1Data.queue.length} P1 Urgent cases.`);
  for (const item of p1Data.queue) {
    if (item.priority_level !== 'P1') {
      console.error('   ❌ Non-P1 item found in P1 filter:', item);
      process.exit(1);
    }
  }
  console.log('   ✅ P1 Urgent Filter PASSED\n');

  // 4. Check Detail for specific screening
  const sid = topItem.screening_id;
  console.log(`4. Fetching /api/priority/screening/${sid}...`);
  const detailRes = await fetch(`${API_BASE}/api/priority/screening/${sid}`);
  if (!detailRes.ok) {
    console.error('❌ Detail endpoint failed:', detailRes.status, await detailRes.text());
    process.exit(1);
  }
  const detail = await detailRes.json();
  const detItem = detail.priority_item;
  console.log('   Screening ID:', detItem.screening_id);
  console.log('   Detailed Reasons Count:', detItem.detailed_reasons.length);
  console.log('   Disclaimer:', detItem.disclaimer);

  if (detItem.screening_id === sid && detItem.algorithm_version === 'RCP-1.0') {
    console.log('   ✅ /api/priority/screening/{id} PASSED\n');
  } else {
    console.error('   ❌ Invalid detail item:', detItem);
    process.exit(1);
  }

  console.log('================================================================');
  console.log('ALL RURAL CARE PRIORITY ENGINE LIVE E2E CHECKS PASSED (100%)');
  console.log('================================================================\n');
}

verifyPriorityEngine().catch((err) => {
  console.error('Fatal E2E error:', err);
  process.exit(1);
});
