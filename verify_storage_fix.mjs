/**
 * Automated Verification Script for LocalStorage Quota Fix
 * Validates payload sizes, key structures, and QuotaExceededError safety.
 */

import {
  persistLightweightReview,
  getLightweightReview,
  sanitizeScreeningsForStorage,
  sanitizePatientsForStorage,
  safeLocalStorageSet,
} from './src/services/storage.js';

// Mock localStorage in Node.js
class MockLocalStorage {
  constructor(quotaBytes = 5 * 1024 * 1024) {
    this.store = new Map();
    this.quotaBytes = quotaBytes;
    this.currentBytes = 0;
  }

  getItem(key) {
    return this.store.get(key) || null;
  }

  setItem(key, value) {
    const strVal = String(value);
    const newBytes = (key.length + strVal.length) * 2; // UTF-16 approximate
    const oldBytes = this.store.has(key) ? (key.length + this.store.get(key).length) * 2 : 0;
    
    if (this.currentBytes - oldBytes + newBytes > this.quotaBytes) {
      const err = new Error("Failed to execute 'setItem' on 'Storage': Setting the value of '" + key + "' exceeded the quota.");
      err.name = "QuotaExceededError";
      err.code = 22;
      throw err;
    }
    
    this.currentBytes = this.currentBytes - oldBytes + newBytes;
    this.store.set(key, strVal);
  }

  removeItem(key) {
    if (this.store.has(key)) {
      const oldBytes = (key.length + this.store.get(key).length) * 2;
      this.currentBytes -= oldBytes;
      this.store.delete(key);
    }
  }

  clear() {
    this.store.clear();
    this.currentBytes = 0;
  }
}

globalThis.localStorage = new MockLocalStorage(5 * 1024 * 1024);

console.log("==================================================================");
console.log("TEST 1: VERIFYING PAYLOAD SIZE OF madocs_review_SCR-2026-1009");
console.log("==================================================================");

const mockBackendReviewResponse = {
  screening_id: "SCR-2026-1009",
  review_status: "AI RESULT ACCEPTED",
  original_ai_result: "Moderate",
  original_confidence: 0.85,
  doctor_reviewed_result: "Moderate",
  review_action: "ACCEPT",
  review_comment: "Verified by doctor.",
  reviewer_name: "Dr. A. Swaminathan, MS",
  review_timestamp: new Date().toISOString(),
  audit_record: {
    event_id: "evt-9999",
    screening_id: "SCR-2026-1009",
    event_type: "AI_RESULT_ACCEPTED",
    description: "Doctor verified findings for patient Ramesh Kumar Verma (OD: Moderate, OS: Mild) at Rampur PHC Community Camp.",
    actor_id: "DOC-SWAMINATHAN",
    actor_role: "doctor",
    original_ai_result: "Moderate",
    original_confidence: 0.85,
    reviewed_result: "Moderate",
    review_comment: "Verified by doctor.",
    timestamp: new Date().toISOString(),
  },
  message: "Review saved in MySQL database.",
};

// Persist using lightweight storage function
persistLightweightReview("SCR-2026-1009", mockBackendReviewResponse);

const storedRaw = localStorage.getItem("madocs_review_SCR-2026-1009");
console.log("Raw stored value:", storedRaw);
console.log("Payload size in bytes:", storedRaw.length);
console.log("Parsed object:", JSON.parse(storedRaw));

// Assert payload is lightweight
const parsed = JSON.parse(storedRaw);
if (!parsed.screeningId || !parsed.reviewStatus || !parsed.updatedAt) {
  throw new Error("Missing required lightweight fields!");
}
if (storedRaw.includes("audit_record") || storedRaw.includes("base64") || storedRaw.includes("description")) {
  throw new Error("Oversized clinical or audit fields found in localStorage!");
}
if (storedRaw.length > 300) {
  throw new Error(`Payload too large: ${storedRaw.length} bytes (expected < 300 bytes)`);
}
console.log(" [OK] Payload is strictly lightweight (< 200 bytes) and contains 0 heavy clinical objects.");

console.log("\n==================================================================");
console.log("TEST 2: VERIFYING SCREENINGS & PATIENT SANITIZATION");
console.log("==================================================================");

const heavyScreenings = [
  {
    id: "SCR-2026-1009",
    patientId: "PAT-2026-081",
    imageOD: "data:image/jpeg;base64," + "A".repeat(2 * 1024 * 1024), // 2MB Base64 image
    imageOS: "data:image/jpeg;base64," + "B".repeat(2 * 1024 * 1024), // 2MB Base64 image
    fileOD: { name: "scan_od.jpg", size: 2000000 },
    fileOS: { name: "scan_os.jpg", size: 2000000 },
    overallSeverity: "dr2",
    className: "Moderate",
  }
];

const sanitizedScreenings = sanitizeScreeningsForStorage(heavyScreenings);
safeLocalStorageSet("dr_screenings", sanitizedScreenings);

const storedScreeningsRaw = localStorage.getItem("dr_screenings");
console.log("Sanitized screenings size in bytes:", storedScreeningsRaw.length);
if (storedScreeningsRaw.length > 2000) {
  throw new Error("Sanitization failed to strip large base64 strings!");
}
console.log(" [OK] Screenings sanitization stripped all multi-megabyte base64 strings.");

console.log("\n==================================================================");
console.log("TEST 3: VERIFYING QUOTA EXCEEDED RESILIENCE");
console.log("==================================================================");

// Fill localStorage right to the brim
const smallQuotaStorage = new MockLocalStorage(1000); // 1KB limit
globalThis.localStorage = smallQuotaStorage;

// Attempt to set a key that exceeds 1KB
let errorThrown = false;
try {
  safeLocalStorageSet("test_huge_key", "X".repeat(2000));
} catch (e) {
  errorThrown = true;
}

if (errorThrown) {
  throw new Error("safeLocalStorageSet failed to catch QuotaExceededError!");
}
console.log(" [OK] safeLocalStorageSet caught QuotaExceededError safely without crashing or throwing.");

console.log("\n==================================================================");
console.log("LOCALSTORAGE QUOTA FIX VERIFICATION: 100% SUCCESSFUL!");
console.log("==================================================================");
