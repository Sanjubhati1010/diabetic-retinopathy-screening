/**
 * Image Optimization & Upload Management Service for Rural & Low-Bandwidth Screening
 *
 * Provides:
 * - Client-side file size detection and user-friendly formatting
 * - Lightweight canvas-based thumbnail generation for responsive UI rendering in Low-Bandwidth Mode
 * - Safe image preservation: ALWAYS preserves the clinical-grade source image Blob for backend AI inference
 */

export function formatFileSize(bytes) {
  if (bytes === 0 || !bytes) return '0 KB';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function detectImageMeta(file) {
  if (!file) return { sizeFormatted: '0 KB', sizeBytes: 0, type: 'unknown' };
  return {
    sizeBytes: file.size || 0,
    sizeFormatted: formatFileSize(file.size || 0),
    type: file.type || 'image/jpeg',
    name: file.name || 'fundus_image.jpg',
  };
}

/**
 * Creates an optimized lightweight client-side preview for UI display without altering the original Blob.
 */
export async function createOptimizedPreview(fileOrUrl, maxWidth = 480, maxHeight = 400) {
  if (!fileOrUrl) return null;

  // If already a string URL and not a Blob/File, return as is
  if (typeof fileOrUrl === 'string' && !fileOrUrl.startsWith('blob:') && !fileOrUrl.startsWith('data:')) {
    return fileOrUrl;
  }

  return new Promise((resolve) => {
    try {
      const img = new Image();
      const objectUrl = typeof fileOrUrl === 'string' ? fileOrUrl : URL.createObjectURL(fileOrUrl);

      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          if (width > height) {
            if (width > maxWidth) {
              height = Math.round((height * maxWidth) / width);
              width = maxWidth;
            }
          } else {
            if (height > maxHeight) {
              width = Math.round((width * maxHeight) / height);
              height = maxHeight;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          const previewDataUrl = canvas.toDataURL('image/jpeg', 0.85);
          if (typeof fileOrUrl !== 'string') {
            URL.revokeObjectURL(objectUrl);
          }
          resolve(previewDataUrl);
        } catch {
          resolve(objectUrl);
        }
      };

      img.onerror = () => {
        resolve(objectUrl);
      };

      img.src = objectUrl;
    } catch {
      resolve(null);
    }
  });
}
