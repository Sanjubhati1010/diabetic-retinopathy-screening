/**
 * Safe LocalStorage Utility with QuotaExceededError Resilience
 * Guarantees that LocalStorage operations never crash the application or pop up browser alerts.
 * MySQL remains the true persistent source of truth for all clinical data.
 */

export function safeLocalStorageSet(key, value) {
  try {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    localStorage.setItem(key, serialized);
  } catch (err) {
    if (
      err.name === 'QuotaExceededError' ||
      err.name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
      err.code === 22 ||
      err.code === 1014 ||
      (err.number && err.number === -2147024882)
    ) {
      console.warn(
        `[LocalStorage] QuotaExceededError while saving key "${key}". Skipping local cache persistence to preserve system stability.`
      );
    } else {
      console.warn(`[LocalStorage] Failed to set item for key "${key}":`, err);
    }
  }
}

export function safeLocalStorageGet(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`[LocalStorage] Failed to parse key "${key}":`, err);
    return fallback;
  }
}

export function safeLocalStorageRemove(key) {
  try {
    localStorage.removeItem(key);
  } catch (err) {
    console.warn(`[LocalStorage] Failed to remove key "${key}":`, err);
  }
}

/**
 * Persists ONLY lightweight review state to localStorage.
 * Clinical and full audit details are maintained in MySQL/FastAPI backend.
 */
export function persistLightweightReview(screeningId, reviewData) {
  if (!screeningId || !reviewData) return;
  const lightweightPayload = {
    screeningId: reviewData.screeningId || reviewData.screening_id || screeningId,
    reviewStatus: reviewData.reviewStatus || reviewData.review_status || 'PENDING DOCTOR REVIEW',
    doctorDecision: reviewData.doctorDecision || reviewData.review_action || reviewData.action || null,
    doctorReviewedResult: reviewData.doctorReviewedResult || reviewData.doctor_reviewed_result || null,
    updatedAt: reviewData.updatedAt || reviewData.review_timestamp || new Date().toISOString(),
  };
  safeLocalStorageSet(`madocs_review_${screeningId}`, lightweightPayload);
}

export function getLightweightReview(screeningId) {
  if (!screeningId) return null;
  return safeLocalStorageGet(`madocs_review_${screeningId}`, null);
}

/**
 * Sanitizes screening objects before caching in LocalStorage:
 * - Strips heavy Base64 image data strings (> 500 chars or data URLs)
 * - Strips raw File objects
 * - Keeps lightweight IDs, dates, and severity metadata
 */
export function sanitizeScreeningsForStorage(screeningsList) {
  if (!Array.isArray(screeningsList)) return [];
  return screeningsList.map((s) => {
    const sanitized = { ...s };
    // Strip file instances
    delete sanitized.fileOD;
    delete sanitized.fileOS;

    // Sanitize imageOD / imageOS if they contain base64 payloads
    if (typeof sanitized.imageOD === 'string' && (sanitized.imageOD.startsWith('data:') || sanitized.imageOD.length > 500)) {
      sanitized.imageOD = '/samples/eyes.png';
    }
    if (typeof sanitized.imageOS === 'string' && (sanitized.imageOS.startsWith('data:') || sanitized.imageOS.length > 500)) {
      sanitized.imageOS = '/samples/eyes_os.png';
    }
    return sanitized;
  });
}

/**
 * Sanitizes patient objects before caching in LocalStorage
 */
export function sanitizePatientsForStorage(patientsList) {
  if (!Array.isArray(patientsList)) return [];
  return patientsList.map((p) => {
    const sanitized = { ...p };
    if (typeof sanitized.imageOD === 'string' && (sanitized.imageOD.startsWith('data:') || sanitized.imageOD.length > 500)) {
      sanitized.imageOD = '/samples/eyes.png';
    }
    if (typeof sanitized.imageOS === 'string' && (sanitized.imageOS.startsWith('data:') || sanitized.imageOS.length > 500)) {
      sanitized.imageOS = '/samples/eyes_os.png';
    }
    return sanitized;
  });
}
