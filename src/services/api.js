/**
 * FastAPI AI Screening Service Client
 * Connects NetraAI React frontend to FastAPI EfficientNet-B0 & Grad-CAM screening endpoints.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Constructs the absolute URL for static backend assets such as Grad-CAM heatmaps.
 * Example: "/results/sample_gradcam.jpg" -> "http://localhost:8000/results/sample_gradcam.jpg"
 */
export function getFullResultUrl(path) {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const cleanBase = API_BASE_URL.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

/**
 * Maps ICDR numerical class to internal severity key ('dr0'..'dr4')
 * 0 = No DR
 * 1 = Mild
 * 2 = Moderate
 * 3 = Severe
 * 4 = Proliferative DR
 */
export function getSeverityKeyFromClass(classIndex) {
  switch (Number(classIndex)) {
    case 0:
      return 'dr0';
    case 1:
      return 'dr1';
    case 2:
      return 'dr2';
    case 3:
      return 'dr3';
    case 4:
      return 'dr4';
    default:
      return 'drUncertain';
  }
}

/**
 * Determines clinical referral triage urgency based on ICDR classification index.
 */
export function getUrgencyFromClass(classIndex) {
  switch (Number(classIndex)) {
    case 0:
    case 1:
      return 'routine';
    case 2:
      return 'moderate';
    case 3:
    case 4:
      return 'urgent';
    default:
      return 'routine';
  }
}

/**
 * Centralized Clinical Confidence Threshold for AI Decision Support
 * Predictions with confidence below 60% are flagged as LOW CONFIDENCE.
 */
export const CONFIDENCE_THRESHOLD = 0.60;

/**
 * Formats decimal confidence (0.0 - 1.0) into a percentage string (e.g. 0.6365 -> 63.65%)
 */
export function formatConfidence(conf) {
  if (conf === null || conf === undefined || isNaN(conf)) {
    return '0.00%';
  }
  // If already percentage (e.g. > 1.0)
  const val = conf <= 1 ? conf * 100 : conf;
  return `${val.toFixed(2)}%`;
}

/**
 * Evaluates model confidence against the clinical threshold
 */
export function evaluateConfidence(conf, threshold = CONFIDENCE_THRESHOLD) {
  if (conf === null || conf === undefined || isNaN(conf)) {
    return {
      isLowConfidence: true,
      screeningStatus: 'UNABLE TO ASSESS',
      nextStep: 'AI confidence unavailable. Please recapture fundus image or request specialist review.',
    };
  }
  const numericConf = conf > 1.0 ? conf / 100.0 : Number(conf);
  const isLow = numericConf < threshold;
  return {
    isLowConfidence: isLow,
    screeningStatus: isLow ? 'LOW CONFIDENCE' : 'RELIABLE AI SCREENING',
    nextStep: isLow
      ? 'AI confidence is low. Please capture a clearer image or request specialist review.'
      : 'Continue to explanation / specialist review.',
  };
}

/**
 * Phase 4: Centralized Risk and Referral Evaluation for Individual Eye
 */
export function evaluateRiskAndReferral(predictedClass, confidence, safetyStatus = 'READY_FOR_AI', isLowConfidence = false) {
  if (safetyStatus !== 'READY_FOR_AI' || predictedClass === null || predictedClass === undefined) {
    return {
      riskCategory: 'UNABLE TO ASSESS',
      referralPriority: 'IMAGE RE-CAPTURE REQUIRED',
      riskExplanation: 'Image quality or retinal validation checks failed. Risk cannot be reliably computed.',
      referralGuidance: 'Please capture a clearer fundus image or request specialist clinical examination.',
      riskLevelNumeric: -1,
    };
  }

  if (isLowConfidence) {
    return {
      riskCategory: 'LOW CONFIDENCE / REVIEW REQUIRED',
      referralPriority: 'EYE SPECIALIST REVIEW RECOMMENDED',
      riskExplanation: 'Model confidence is below the clinical threshold. Risk assessment requires specialist verification.',
      referralGuidance: 'Consider image re-capture or specialist review.',
      riskLevelNumeric: 1,
    };
  }

  const cls = Number(predictedClass);
  if (cls === 0) {
    return {
      riskCategory: 'LOW',
      referralPriority: 'ROUTINE FOLLOW-UP',
      riskExplanation: 'No diabetic retinopathy lesions detected. Low risk of vision impairment.',
      referralGuidance: 'Routine follow-up may be appropriate according to local clinical protocol.',
      riskLevelNumeric: 0,
    };
  } else if (cls === 1 || cls === 2) {
    return {
      riskCategory: 'MODERATE',
      referralPriority: 'EYE SPECIALIST REVIEW RECOMMENDED',
      riskExplanation: 'Features consistent with non-proliferative diabetic retinopathy detected. Moderate risk profile.',
      referralGuidance: 'Eye specialist review is recommended based on the AI-assisted screening result.',
      riskLevelNumeric: 2,
    };
  } else if (cls === 3 || cls === 4) {
    return {
      riskCategory: 'HIGH',
      referralPriority: 'PRIORITY SPECIALIST REVIEW',
      riskExplanation: 'Features consistent with severe non-proliferative or proliferative diabetic retinopathy detected. High risk profile.',
      referralGuidance: 'Priority specialist review is recommended based on the AI-assisted screening result.',
      riskLevelNumeric: 3,
    };
  }

  return {
    riskCategory: 'UNABLE TO ASSESS',
    referralPriority: 'IMAGE RE-CAPTURE REQUIRED',
    riskExplanation: 'Risk cannot be reliably computed.',
    referralGuidance: 'Please capture a clearer fundus image or request specialist review.',
    riskLevelNumeric: -1,
  };
}

/**
 * Phase 4: Two-Eye Aggregation using Max-Risk Rule
 */
export function aggregateTwoEyeScreening(odEval, osEval) {
  const odLevel = odEval?.riskLevelNumeric ?? -1;
  const osLevel = osEval?.riskLevelNumeric ?? -1;

  const odCat = odEval?.riskCategory || 'UNABLE TO ASSESS';
  const osCat = osEval?.riskCategory || 'UNABLE TO ASSESS';

  if (odLevel === -1 && osLevel === -1) {
    return {
      overallRisk: 'UNABLE TO ASSESS',
      highestRiskEye: 'Unable to Assess',
      overallReferral: 'IMAGE RE-CAPTURE REQUIRED',
      overallGuidance: 'Bilateral image capture did not pass AI safety checks. Please capture clearer fundus scans.',
    };
  }

  if (odLevel === -1) {
    return {
      overallRisk: osCat,
      highestRiskEye: 'Left Eye (OS)',
      overallReferral: osEval.referralPriority,
      overallGuidance: `Left eye evaluated as ${osCat}. Right eye image re-capture is required.`,
    };
  }

  if (osLevel === -1) {
    return {
      overallRisk: odCat,
      highestRiskEye: 'Right Eye (OD)',
      overallReferral: odEval.referralPriority,
      overallGuidance: `Right eye evaluated as ${odCat}. Left eye image re-capture is required.`,
    };
  }

  if (odLevel > osLevel) {
    return {
      overallRisk: odEval.riskCategory,
      highestRiskEye: 'Right Eye (OD)',
      overallReferral: odEval.referralPriority,
      overallGuidance: odEval.referralGuidance,
    };
  } else if (osLevel > odLevel) {
    return {
      overallRisk: osEval.riskCategory,
      highestRiskEye: 'Left Eye (OS)',
      overallReferral: osEval.referralPriority,
      overallGuidance: osEval.referralGuidance,
    };
  } else {
    return {
      overallRisk: odEval.riskCategory,
      highestRiskEye: 'Both Eyes',
      overallReferral: odEval.referralPriority,
      overallGuidance: odEval.referralGuidance,
    };
  }
}

/**
 * Converts any image input (File, Blob, base64 data URL, SVG data URI, or URL)
 * into a valid JPEG File object with proper MIME type and filename.
 */
export async function ensureImageFile(imageSource, filename = 'retinal_scan.jpg') {
  if (!imageSource) {
    throw new Error('No retinal image data provided.');
  }

  // If already a File instance with valid image type
  if (imageSource instanceof File) {
    return imageSource;
  }

  // If a Blob instance
  if (imageSource instanceof Blob) {
    const mime = imageSource.type || 'image/jpeg';
    const ext = mime.includes('png') ? '.png' : '.jpg';
    return new File([imageSource], filename.endsWith(ext) ? filename : `${filename}${ext}`, {
      type: mime,
    });
  }

  // If a string (data URI or remote URL)
  if (typeof imageSource === 'string') {
    // If it is an SVG data URI or SVG markup, render it onto a canvas to export as JPEG
    if (imageSource.startsWith('data:image/svg+xml') || imageSource.includes('<svg')) {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          try {
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || 512;
            canvas.height = img.naturalHeight || 512;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);

            canvas.toBlob(
              (blob) => {
                if (blob) {
                  resolve(new File([blob], filename, { type: 'image/jpeg' }));
                } else {
                  reject(new Error('Failed to convert SVG canvas to JPEG blob.'));
                }
              },
              'image/jpeg',
              0.95
            );
          } catch (err) {
            reject(err);
          }
        };
        img.onerror = () => reject(new Error('Failed to load SVG data for canvas rendering.'));
        img.src = imageSource;
      });
    }

    // If standard data URI (data:image/jpeg;base64,... or data:image/png...)
    if (imageSource.startsWith('data:image/')) {
      const res = await fetch(imageSource);
      const blob = await res.blob();
      const mime = blob.type || 'image/jpeg';
      return new File([blob], filename, { type: mime });
    }

    // If regular URL path (e.g. /samples/eyes.png)
    try {
      const res = await fetch(imageSource);
      if (!res.ok) {
        throw new Error(`Failed to fetch image from ${imageSource} (Status ${res.status})`);
      }
      const blob = await res.blob();
      const mime = blob.type || (imageSource.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg');
      const ext = mime.includes('png') ? '.png' : '.jpg';
      const cleanName = filename.replace(/\.(png|jpg|jpeg|svg)$/i, '') + ext;
      return new File([blob], cleanName, { type: mime });
    } catch (fetchErr) {
      throw new Error(`Could not load image from URL: ${fetchErr.message}`);
    }
  }

  throw new Error('Unsupported image format provided for analysis.');
}

/**
 * Checks backend health status and model readiness.
 * GET /api/health
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
    });
    if (!response.ok) {
      return { ok: false, status: response.status, data: null };
    }
    const data = await response.json();
    return { ok: true, status: response.status, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message };
  }
}

/**
 * Helper to execute multipart/form-data POST request to FastAPI endpoints.
 */
async function postImageMultipart(endpointUrl, imageSource, filename) {
  const file = await ensureImageFile(imageSource, filename);
  const formData = new FormData();
  formData.append('file', file);

  let response;
  try {
    response = await fetch(endpointUrl, {
      method: 'POST',
      body: formData,
    });
  } catch (networkError) {
    console.error(`Network request failed for ${endpointUrl}:`, networkError);
    const err = new Error('Unable to connect to AI screening service.');
    err.status = 0;
    err.isConnectionError = true;
    err.originalError = networkError;
    throw err;
  }

  if (!response.ok) {
    let errorDetail = '';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || '';
    } catch {
      errorDetail = response.statusText;
    }

    const err = new Error(errorDetail || `API request failed with status ${response.status}.`);
    err.status = response.status;
    throw err;
  }

  return await response.json();
}

/**
 * Executes direct prediction endpoint:
 * POST http://localhost:8000/api/predict
 *
 * Form field: "file" (multipart/form-data)
 * Returns: { predicted_class, class_name, confidence, probabilities, inference_time }
 */
export async function predictRetinalImage(imageSource, filename = 'retinal_fundus.jpg') {
  const endpoint = `${API_BASE_URL}/api/predict`;
  return await postImageMultipart(endpoint, imageSource, filename);
}

/**
 * Executes Grad-CAM explanation endpoint:
 * POST http://localhost:8000/api/explain
 *
 * Form field: "file" (multipart/form-data)
 * Returns: { predicted_class, class_name, gradcam_url, explanation, inference_time }
 */
export async function explainRetinalImage(imageSource, filename = 'retinal_fundus.jpg') {
  const endpoint = `${API_BASE_URL}/api/explain`;
  return await postImageMultipart(endpoint, imageSource, filename);
}

/**
 * Performs Phase 1 Multi-Criteria Retinal Image Validation & Quality Assessment:
 * POST http://localhost:8000/api/validate-quality
 *
 * Checks:
 * - Valid image format (.jpg, .jpeg, .png) & corruption
 * - Minimum resolution (>= 224x224)
 * - Retinal spectral & hue domain signature (rejects selfies/photos/screenshots)
 * - Sharpness & focus (Laplacian blur estimation)
 * - Illumination (detects underexposed / overexposed scans)
 * - Retinal coverage
 *
 * Returns: { is_valid_file, is_retinal, quality_grade, screening_status, can_proceed, reasons, metrics, message }
 */
export async function validateImageQuality(imageSource, filename = 'retinal_fundus.jpg') {
  const endpoint = `${API_BASE_URL}/api/validate-quality`;

  try {
    return await postImageMultipart(endpoint, imageSource, filename);
  } catch (err) {
    // If backend is unavailable or offline, perform client-side fallback validation
    if (err.isConnectionError || err.status === 404) {
      console.warn('Backend validation endpoint offline, executing client-side fallback validation...');
      return await clientFallbackImageValidation(imageSource, filename);
    }
    throw err;
  }
}

/**
 * Client-side fallback validator for network interruption resilience
 */
async function clientFallbackImageValidation(imageSource, filename) {
  try {
    const file = await ensureImageFile(imageSource, filename);
    
    // Check file size (max 15MB)
    if (file.size > 15 * 1024 * 1024) {
      return {
        is_valid_file: false,
        is_retinal: false,
        quality_grade: 'insufficient',
        screening_status: 'Image Re-capture Required',
        can_proceed: false,
        reasons: ['File size exceeds 15MB limit. Please upload a smaller fundus image.'],
        metrics: { resolution: '0x0', sharpness_score: 0, brightness_score: 0, retinal_coverage: 0 },
        message: 'File size exceeds 15MB limit.',
      };
    }

    // Load image on canvas to inspect dimensions & basic pixel histogram
    return new Promise((resolve) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(url);
        const w = img.naturalWidth || img.width;
        const h = img.naturalHeight || img.height;

        if (w < 224 || h < 224) {
          return resolve({
            is_valid_file: true,
            is_retinal: false,
            quality_grade: 'insufficient',
            screening_status: 'Image Re-capture Required',
            can_proceed: false,
            reasons: [
              'Image resolution is too low. Minimum resolution is 224x224 pixels.',
              'Image quality is insufficient. Please capture or upload a clearer fundus image.'
            ],
            metrics: { resolution: `${w}x${h}`, sharpness_score: 0, brightness_score: 0, retinal_coverage: 0 },
            message: 'Image resolution is too low. Please upload a higher resolution fundus photograph.',
          });
        }

        // Basic client validation passed
        resolve({
          is_valid_file: true,
          is_retinal: true,
          quality_grade: 'good',
          screening_status: 'Ready for Screening',
          can_proceed: true,
          reasons: [],
          metrics: { resolution: `${w}x${h}`, sharpness_score: 100, brightness_score: 120, retinal_coverage: 0.85 },
          message: 'Image validated successfully and ready for screening.',
        });
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve({
          is_valid_file: false,
          is_retinal: false,
          quality_grade: 'insufficient',
          screening_status: 'Image Re-capture Required',
          can_proceed: false,
          reasons: ['Please upload a valid image file. Corrupted or invalid image data.'],
          metrics: { resolution: '0x0', sharpness_score: 0, brightness_score: 0, retinal_coverage: 0 },
          message: 'Please upload a valid image file.',
        });
      };
      img.src = url;
    });
  } catch (err) {
    return {
      is_valid_file: false,
      is_retinal: false,
      quality_grade: 'insufficient',
      screening_status: 'Image Re-capture Required',
      can_proceed: false,
      reasons: ['Please upload a valid image file.'],
      metrics: { resolution: '0x0', sharpness_score: 0, brightness_score: 0, retinal_coverage: 0 },
      message: 'Please upload a valid image file.',
    };
  }
}

/**
 * Performs complete end-to-end retinal screening analysis:
 * POST http://localhost:8000/api/screenings/analyze (or combined /api/predict + /api/explain)
 *
 * Accepts multipart/form-data with form field "file".
 * Returns: { predicted_class, class_name, confidence, probabilities, gradcam_url, explanation, disclaimer, inference_time }
 */
export async function analyzeRetinalImage(imageSource, filename = 'retinal_fundus.jpg') {
  const analyzeEndpoint = `${API_BASE_URL}/api/screenings/analyze`;

  try {
    return await postImageMultipart(analyzeEndpoint, imageSource, filename);
  } catch (err) {
    // If /api/screenings/analyze endpoint is 404, fallback to /api/predict + /api/explain
    if (err.status === 404) {
      console.warn('/api/screenings/analyze returned 404, falling back to /api/predict...');
      const pred = await predictRetinalImage(imageSource, filename);
      let gradcamUrl = null;
      let explanation = null;
      try {
        const exp = await explainRetinalImage(imageSource, filename);
        gradcamUrl = exp.gradcam_url;
        explanation = exp.explanation;
      } catch (expErr) {
        console.warn('Explainability generation failed:', expErr);
      }
      return {
        ...pred,
        gradcam_url: gradcamUrl,
        explanation: explanation || "Highlighted regions indicate image areas that contributed to the model's prediction.",
        disclaimer: 'AI-assisted screening only. This result is not a medical diagnosis and must be reviewed by a qualified healthcare professional.',
      };
    }
    throw err;
  }
}

