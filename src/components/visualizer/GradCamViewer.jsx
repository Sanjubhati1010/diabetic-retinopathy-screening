import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import {
  Layers,
  Eye,
  Sliders,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  Info,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';

export const GradCamViewer = ({
  originalImage,
  heatmapImage,
  title = 'Retinal Fundus & Grad-CAM Heatmap',
  confidence = null,
  severity = 'drUncertain',
  selectedEye = 'OD',
  onEyeChange,
  showControls = true,
}) => {
  const { t } = useLanguage();
  const [opacity, setOpacity] = useState(65);
  const [viewMode, setViewMode] = useState('blend'); // 'blend' | 'split' | 'original'
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    setImageError(false);
  }, [heatmapImage, selectedEye]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75));
  const handleReset = () => {
    setZoomLevel(1);
    setOpacity(65);
    setViewMode('blend');
  };

  const hasValidHeatmap = Boolean(heatmapImage && !imageError);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden transition-all">
      {/* Top Bar with Eye Switcher & Mode Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-slate-100 bg-slate-50/70">
        <div className="flex items-center gap-3">
          {/* Eye Switcher */}
          {onEyeChange && (
            <div className="inline-flex rounded-xl p-1 bg-slate-200/70 border border-slate-200">
              <button
                type="button"
                onClick={() => onEyeChange('OD')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  selectedEye === 'OD'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                OD (Right Eye)
              </button>
              <button
                type="button"
                onClick={() => onEyeChange('OS')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  selectedEye === 'OS'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                OS (Left Eye)
              </button>
            </div>
          )}

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            <span>Grad-CAM Explainability Interface</span>
          </div>
        </div>

        {/* View Mode Pills */}
        <div className="flex items-center gap-1 bg-slate-200/60 p-1 rounded-xl text-xs font-semibold">
          <button
            type="button"
            onClick={() => setViewMode('blend')}
            className={`px-2.5 py-1 rounded-lg transition ${
              viewMode === 'blend'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {t('blendedView')}
          </button>
          <button
            type="button"
            onClick={() => setViewMode('split')}
            className={`px-2.5 py-1 rounded-lg transition ${
              viewMode === 'split'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Split Side-by-Side
          </button>
          <button
            type="button"
            onClick={() => setViewMode('original')}
            className={`px-2.5 py-1 rounded-lg transition ${
              viewMode === 'original'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {t('originalScan')}
          </button>
        </div>
      </div>

      {/* Main Canvas / Image Viewport */}
      <div className="relative bg-slate-950 p-4 sm:p-6 flex items-center justify-center min-h-[380px] sm:min-h-[440px] overflow-hidden select-none">
        <div
          className="relative transition-transform duration-150 ease-out max-w-full flex items-center justify-center"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          {viewMode === 'split' ? (
            /* Split View */
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black">
                <img
                  src={originalImage}
                  alt="Original Retinal Fundus Scan"
                  className="w-full h-full object-contain"
                />
                <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white border border-white/10">
                  {t('originalScan')} ({selectedEye})
                </span>
              </div>
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
                {hasValidHeatmap ? (
                  <>
                    <img
                      src={heatmapImage}
                      alt="Grad-CAM Heatmap"
                      onError={() => setImageError(true)}
                      className="w-full h-full object-contain"
                    />
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-emerald-300 border border-white/10">
                      Grad-CAM Heatmap ({selectedEye})
                    </span>
                  </>
                ) : imageError ? (
                  <div className="p-4 text-center text-rose-300 space-y-1">
                    <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto" />
                    <p className="text-xs font-bold">Unable to load Grad-CAM image</p>
                    <p className="text-[10px] text-slate-400">Please verify backend service is running</p>
                  </div>
                ) : (
                  <div className="p-4 text-center text-slate-400 space-y-1">
                    <Sparkles className="w-6 h-6 text-brand-400 mx-auto" />
                    <p className="text-xs font-bold text-slate-200">No Heatmap Available</p>
                    <p className="text-[10px] text-slate-400">Run AI analysis to generate Grad-CAM</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Blended / Overlay View */
            <div className="relative w-72 h-72 sm:w-96 sm:h-96 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
              {/* Base Fundus Image */}
              <img
                src={originalImage}
                alt="Retinal Fundus Image"
                className="w-full h-full object-contain"
              />

              {/* Real Grad-CAM Heatmap Overlay Layer */}
              {viewMode !== 'original' && hasValidHeatmap && (
                <div
                  className="absolute inset-0 pointer-events-none transition-opacity duration-150 flex items-center justify-center"
                  style={{ opacity: opacity / 100 }}
                >
                  <img
                    src={heatmapImage}
                    alt="Grad-CAM Heatmap Layer"
                    onError={() => setImageError(true)}
                    className="w-full h-full object-contain"
                  />
                </div>
              )}

              {/* Anatomical Landmark Overlays */}
              {showLandmarks && (
                <div className="absolute inset-0 pointer-events-none">
                  {/* Optic Disc Marker */}
                  <div
                    className={`absolute ${
                      selectedEye === 'OD' ? 'left-[26%]' : 'right-[26%]'
                    } top-[46%] -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full border-2 border-dashed border-amber-400/80 flex items-center justify-center`}
                  >
                    <span className="absolute -top-5 text-[9px] font-bold text-amber-300 bg-black/70 px-1 rounded">
                      Optic Disc
                    </span>
                  </div>

                  {/* Macula Zone */}
                  <div
                    className={`absolute ${
                      selectedEye === 'OD' ? 'left-[62%]' : 'left-[38%]'
                    } top-[48%] -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full border-2 border-emerald-400/70 flex items-center justify-center`}
                  >
                    <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                    <span className="absolute -bottom-5 text-[9px] font-bold text-emerald-300 bg-black/70 px-1 rounded">
                      Macula / FAZ
                    </span>
                  </div>
                </div>
              )}

              {/* Error Notice */}
              {imageError && (
                <div className="absolute bottom-3 inset-x-3 bg-slate-900/90 backdrop-blur-md rounded-xl p-2.5 border border-rose-800 text-center text-[11px] text-rose-300 shadow-lg pointer-events-none">
                  <span className="font-bold block">
                    Unable to load Grad-CAM visualization from server.
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Verify FastAPI backend results endpoint
                  </span>
                </div>
              )}

              {/* View Status Tag */}
              <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] font-bold text-white">
                <div
                  className={`w-2 h-2 rounded-full ${
                    hasValidHeatmap ? 'bg-emerald-400 animate-pulse' : 'bg-brand-400'
                  }`}
                ></div>
                <span>{selectedEye === 'OD' ? 'OD (Right Eye)' : 'OS (Left Eye)'}</span>
                <span className="text-slate-400">
                  • {hasValidHeatmap ? 'Grad-CAM Active' : 'Fundus Scan'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Viewport Zoom & Pan Floating Controls */}
        <div className="absolute bottom-4 right-4 flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white shadow-xl">
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Bottom Interactive Controls */}
      {showControls && (
        <div className="p-4 sm:p-5 bg-white border-t border-slate-100 space-y-4">
          {/* Opacity Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <div className="flex items-center gap-1.5">
                <Sliders className="w-4 h-4 text-brand-600" />
                <span>{t('gradCamOpacity')}</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-bold border border-brand-200">
                {opacity}%
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[11px] text-slate-400 font-medium">{t('originalScan')} (0%)</span>
              <input
                type="range"
                min="0"
                max="100"
                value={opacity}
                onChange={(e) => setOpacity(Number(e.target.value))}
                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600 focus:outline-none"
              />
              <span className="text-[11px] text-slate-400 font-medium">100% Grad-CAM</span>
            </div>
          </div>

          {/* Overlays & Landmark Toggles */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showLandmarks}
                  onChange={(e) => setShowLandmarks(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
                />
                <span className="text-slate-700 font-medium">{t('anatomicalLandmarks')}</span>
              </label>
            </div>

            <div className="flex items-center gap-2 text-slate-500 text-[11px]">
              <Info className="w-3.5 h-3.5 text-brand-600" />
              <span>
                {hasValidHeatmap
                  ? 'EfficientNet-B0 Convolutional Layer Grad-CAM Loaded'
                  : 'Grad-CAM Visualization Layer Ready'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
