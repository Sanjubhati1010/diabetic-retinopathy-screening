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
  Image as ImageIcon,
  Flame,
} from 'lucide-react';

export const GradCamViewer = ({
  originalImage,
  heatmapImage,
  heatmapUrl,
  title = 'Retinal Fundus & Grad-CAM Heatmap',
  confidence = null,
  severity = 'drUncertain',
  selectedEye = 'OD',
  onEyeChange,
  showControls = true,
  onRetry,
  isLowConfidence = false,
  safetyBlocked = false,
}) => {
  const { t } = useLanguage();
  // Modes: 'overlay' | 'heatmap' | 'original' | 'split'
  const [viewMode, setViewMode] = useState('overlay');
  const [opacity, setOpacity] = useState(70);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showLandmarks, setShowLandmarks] = useState(false);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    setImageError(false);
  }, [heatmapImage, heatmapUrl, selectedEye]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75));
  const handleReset = () => {
    setZoomLevel(1);
    setOpacity(70);
    setViewMode('overlay');
  };

  const pureHeatmap = heatmapUrl || heatmapImage;
  const overlayImage = heatmapImage || heatmapUrl;
  const hasValidHeatmap = Boolean(overlayImage && !imageError && !safetyBlocked);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-card overflow-hidden transition-all">
      {/* Top Bar with Eye Switcher & Mode Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-slate-100 bg-slate-50/80">
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

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-semibold">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>Grad-CAM Explainability Tri-View</span>
          </div>
        </div>

        {/* 3 Primary View Mode Pills: Original | Heatmap | Overlay (Plus Split) */}
        <div className="flex flex-wrap items-center gap-1 bg-slate-200/70 p-1 rounded-xl text-xs font-bold">
          <button
            type="button"
            onClick={() => setViewMode('original')}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg transition ${
              viewMode === 'original'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>{t('modeOriginal') || 'Original'}</span>
          </button>

          <button
            type="button"
            onClick={() => setViewMode('heatmap')}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg transition ${
              viewMode === 'heatmap'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-orange-500" />
            <span>{t('modeHeatmap') || 'Heatmap'}</span>
          </button>

          <button
            type="button"
            onClick={() => setViewMode('overlay')}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg transition ${
              viewMode === 'overlay'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-brand-600" />
            <span>{t('modeOverlay') || 'Overlay'}</span>
          </button>

          <button
            type="button"
            onClick={() => setViewMode('split')}
            className={`px-2.5 py-1 rounded-lg transition text-[11px] ${
              viewMode === 'split'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Split
          </button>
        </div>
      </div>

      {/* Main Canvas / Image Viewport */}
      <div className="relative bg-slate-950 p-4 sm:p-6 flex items-center justify-center min-h-[380px] sm:min-h-[440px] overflow-hidden select-none">
        <div
          className="relative transition-transform duration-150 ease-out max-w-full flex items-center justify-center"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          {safetyBlocked ? (
            /* Safety Blocked State */
            <div className="p-8 text-center text-rose-300 space-y-3 max-w-md bg-slate-900/90 rounded-2xl border border-rose-800 shadow-2xl">
              <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
              <h4 className="text-sm font-bold text-white">Explainability Unavailable</h4>
              <p className="text-xs text-rose-200 leading-relaxed">
                {t('explanationUnavailable') || 'Explainability is unavailable because the image did not pass the AI safety checks.'}
              </p>
            </div>
          ) : viewMode === 'split' ? (
            /* Split View */
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black">
                <img
                  src={originalImage}
                  alt="Original Retinal Fundus Scan"
                  className="w-full h-full object-contain"
                />
                <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white border border-white/10">
                  {t('modeOriginal') || 'Original'} ({selectedEye})
                </span>
              </div>
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
                {hasValidHeatmap ? (
                  <>
                    <img
                      src={overlayImage}
                      alt="Grad-CAM Visualization"
                      onError={() => setImageError(true)}
                      className="w-full h-full object-contain"
                    />
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-purple-300 border border-white/10">
                      Grad-CAM Overlay ({selectedEye})
                    </span>
                  </>
                ) : imageError ? (
                  <div className="p-4 text-center text-rose-300 space-y-2">
                    <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto" />
                    <p className="text-xs font-bold">{t('explanationTempUnavailable') || 'Explanation visualization is temporarily unavailable.'}</p>
                    {onRetry && (
                      <button
                        type="button"
                        onClick={onRetry}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>{t('btnRetryExplanation') || 'Retry Explanation'}</span>
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-slate-400 space-y-1">
                    <Sparkles className="w-6 h-6 text-brand-400 mx-auto" />
                    <p className="text-xs font-bold text-slate-200">No Heatmap Available</p>
                  </div>
                )}
              </div>
            </div>
          ) : viewMode === 'original' ? (
            /* Original Fundus Mode */
            <div className="relative w-72 h-72 sm:w-96 sm:h-96 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
              <img
                src={originalImage}
                alt="Retinal Fundus Image"
                className="w-full h-full object-contain"
              />
              <div className="absolute top-2 left-2 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm border border-white/10 text-[10px] font-bold text-white flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                <span>{selectedEye} • {t('modeOriginal') || 'Original Fundus'}</span>
              </div>
            </div>
          ) : viewMode === 'heatmap' ? (
            /* Pure Heatmap Mode */
            <div className="relative w-72 h-72 sm:w-96 sm:h-96 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
              {hasValidHeatmap ? (
                <>
                  <img
                    src={pureHeatmap}
                    alt="Grad-CAM Pure Heatmap"
                    onError={() => setImageError(true)}
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-2 left-2 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm border border-white/10 text-[10px] font-bold text-orange-300 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse"></span>
                    <span>{selectedEye} • {t('modeHeatmap') || 'Grad-CAM Heatmap (JET)'}</span>
                  </div>
                </>
              ) : imageError ? (
                <div className="p-6 text-center text-rose-300 space-y-2">
                  <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto" />
                  <p className="text-xs font-bold">{t('explanationTempUnavailable') || 'Explanation visualization is temporarily unavailable.'}</p>
                  {onRetry && (
                    <button
                      type="button"
                      onClick={onRetry}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>{t('btnRetryExplanation') || 'Retry Explanation'}</span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-slate-400 space-y-1">
                  <Sparkles className="w-6 h-6 text-brand-400 mx-auto" />
                  <p className="text-xs font-bold text-slate-200">No Heatmap Available</p>
                </div>
              )}
            </div>
          ) : (
            /* Blended / Overlay Mode */
            <div className="relative w-72 h-72 sm:w-96 sm:h-96 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl bg-black flex items-center justify-center">
              {/* Base Fundus Image */}
              <img
                src={originalImage}
                alt="Retinal Fundus Image"
                className="w-full h-full object-contain"
              />

              {/* Heatmap Overlay Layer with Dynamic Opacity */}
              {hasValidHeatmap && (
                <div
                  className="absolute inset-0 pointer-events-none transition-opacity duration-150 flex items-center justify-center"
                  style={{ opacity: opacity / 100 }}
                >
                  <img
                    src={overlayImage}
                    alt="Grad-CAM Overlay Layer"
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
                <div className="absolute bottom-3 inset-x-3 bg-slate-900/90 backdrop-blur-md rounded-xl p-3 border border-rose-800 text-center text-xs text-rose-300 shadow-lg space-y-1">
                  <span className="font-bold block">
                    {t('explanationTempUnavailable') || 'Explanation visualization is temporarily unavailable.'}
                  </span>
                  {onRetry && (
                    <button
                      type="button"
                      onClick={onRetry}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>{t('btnRetryExplanation') || 'Retry Explanation'}</span>
                    </button>
                  )}
                </div>
              )}

              {/* View Status Tag */}
              <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] font-bold text-white">
                <div
                  className={`w-2 h-2 rounded-full ${
                    hasValidHeatmap ? 'bg-purple-400 animate-pulse' : 'bg-brand-400'
                  }`}
                ></div>
                <span>{selectedEye === 'OD' ? 'OD (Right Eye)' : 'OS (Left Eye)'}</span>
                <span className="text-slate-400">
                  • {hasValidHeatmap ? (t('modeOverlay') || 'Overlay') : 'Fundus Scan'}
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
          {/* Opacity Slider for Overlay Mode */}
          {viewMode === 'overlay' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                <div className="flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-brand-600" />
                  <span>{t('heatmapOpacity') || 'Overlay Opacity'}</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-bold border border-brand-200">
                  {opacity}%
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-slate-400 font-medium">{t('modeOriginal') || 'Original'} (0%)</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={opacity}
                  onChange={(e) => setOpacity(Number(e.target.value))}
                  className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600 focus:outline-none"
                />
                <span className="text-[11px] text-slate-400 font-medium">100% Overlay</span>
              </div>
            </div>
          )}

          {/* Overlays & Landmark Toggles */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100 text-xs">
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
              <Info className="w-3.5 h-3.5 text-purple-600" />
              <span>
                {hasValidHeatmap
                  ? 'Grad-CAM computed over EfficientNet-B0 conv_head'
                  : 'Grad-CAM Visualization Layer Ready'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
