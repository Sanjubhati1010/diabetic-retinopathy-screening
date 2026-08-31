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
import { getFullResultUrl } from '../../services/api';

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
  const [opacity, setOpacity] = useState(40);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showLandmarks, setShowLandmarks] = useState(false);
  const [imageError, setImageError] = useState(false);

  const stageRef = React.useRef(null);
  const [stageSize, setStageSize] = useState({ width: 640, height: 380 });
  const [imgDimensions, setImgDimensions] = useState({ naturalWidth: 1009, naturalHeight: 857 });

  useEffect(() => {
    setImageError(false);
  }, [heatmapImage, heatmapUrl, selectedEye]);

  const handleImageLoad = (e) => {
    if (e.target.naturalWidth && e.target.naturalHeight) {
      setImgDimensions({
        naturalWidth: e.target.naturalWidth,
        naturalHeight: e.target.naturalHeight,
      });
    }
  };

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(Number((prev + 0.25).toFixed(2)), 2.5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(Number((prev - 0.25).toFixed(2)), 0.75));
  const handleReset = () => {
    setZoomLevel(1);
    setOpacity(40);
    setViewMode('overlay');
  };

  // Pure Heatmap URL (JET heatmap without base image blend) normalized with getFullResultUrl
  const rawHeatmap = heatmapUrl || heatmapImage;
  const rawOverlay = heatmapImage || heatmapUrl;

  const pureHeatmap = rawHeatmap ? (rawHeatmap.startsWith('blob:') || rawHeatmap.startsWith('data:') ? rawHeatmap : getFullResultUrl(rawHeatmap)) : null;
  const blendedOverlay = rawOverlay ? (rawOverlay.startsWith('blob:') || rawOverlay.startsWith('data:') ? rawOverlay : getFullResultUrl(rawOverlay)) : null;
  const displayOriginal = originalImage ? (originalImage.startsWith('blob:') || originalImage.startsWith('data:') || originalImage.startsWith('/samples/') ? originalImage : getFullResultUrl(originalImage)) : null;

  const hasValidHeatmap = Boolean((pureHeatmap || blendedOverlay) && !imageError && !safetyBlocked);

  const naturalW = imgDimensions.naturalWidth || 1009;
  const naturalH = imgDimensions.naturalHeight || 857;

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

      {/* Main Canvas / Image Viewport - Stable Viewport with Native Aspect Ratio Containment */}
      <div className="relative bg-slate-950 p-6 sm:p-8 h-[360px] sm:h-[400px] md:h-[430px] w-full flex items-center justify-center overflow-hidden select-none">
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
          /* Split View: Side-by-Side Contained Frame */
          <div
            className="relative transition-transform duration-150 ease-out select-none flex flex-col sm:flex-row items-center justify-center gap-4 w-full h-full max-w-full max-h-full"
            style={{
              transform: `scale(${zoomLevel})`,
              transformOrigin: 'center center',
            }}
          >
            {/* Split Left: Original Fundus */}
            <div
              className="relative bg-black rounded-xl border border-slate-800 shadow-2xl overflow-hidden flex items-center justify-center select-none"
              style={{
                aspectRatio: `${naturalW} / ${naturalH}`,
                maxHeight: '100%',
                maxWidth: 'calc(50% - 12px)',
                height: 'auto',
                width: 'auto',
              }}
            >
              <img
                src={displayOriginal}
                alt="Original Retinal Fundus Scan"
                onLoad={handleImageLoad}
                className="w-full h-full object-contain block select-none"
              />
              <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/75 text-[10px] font-bold text-white border border-white/10 pointer-events-none z-10">
                {t('modeOriginal') || 'Original'} ({selectedEye})
              </span>
              {/* Independent UI A Marker */}
              <div
                className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-white/95 text-slate-900 font-extrabold text-[11px] border border-slate-300 shadow-sm pointer-events-none select-none z-10 flex items-center justify-center leading-none"
                title="Anatomical Reference Marker A"
              >
                A
              </div>
            </div>

            {/* Split Right: Grad-CAM Overlay */}
            <div
              className="relative bg-black rounded-xl border border-slate-800 shadow-2xl overflow-hidden flex items-center justify-center select-none"
              style={{
                aspectRatio: `${naturalW} / ${naturalH}`,
                maxHeight: '100%',
                maxWidth: 'calc(50% - 12px)',
                height: 'auto',
                width: 'auto',
              }}
            >
              {hasValidHeatmap ? (
                <>
                  {/* Layer 1: Base Retinal Scan */}
                  <img
                    src={displayOriginal}
                    alt="Base Fundus Scan"
                    className="w-full h-full object-contain block select-none"
                  />
                  {/* Layer 2: Grad-CAM Layer */}
                  <img
                    src={pureHeatmap || blendedOverlay}
                    alt="Grad-CAM Overlay"
                    onError={() => setImageError(true)}
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150 select-none"
                    style={{
                      opacity: opacity / 100,
                      mixBlendMode: pureHeatmap && pureHeatmap !== blendedOverlay ? 'screen' : 'normal',
                    }}
                  />
                  {/* Layer 3: Independent UI A Marker (Above heatmap) */}
                  <div
                    className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-white/95 text-slate-900 font-extrabold text-[11px] border border-slate-300 shadow-sm pointer-events-none select-none z-10 flex items-center justify-center leading-none"
                    title="Anatomical Reference Marker A"
                  >
                    A
                  </div>
                  {/* Layer 3B: Independent Tag */}
                  <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/75 text-[10px] font-bold text-purple-300 border border-white/10 pointer-events-none z-10">
                    Grad-CAM Overlay ({selectedEye})
                  </span>
                </>
              ) : imageError ? (
                <div className="p-4 text-center text-rose-300 space-y-1">
                  <AlertTriangle className="w-5 h-5 text-rose-500 mx-auto" />
                  <p className="text-[11px] font-bold">{t('explanationTempUnavailable') || 'Visualization unavailable.'}</p>
                </div>
              ) : (
                <div className="p-4 text-center text-slate-400 space-y-1">
                  <Sparkles className="w-5 h-5 text-brand-400 mx-auto" />
                  <p className="text-[11px] font-bold text-slate-200">No Heatmap Available</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Single View Modes (Original, Heatmap, Overlay) - 100% Shared Aspect-Ratio Frame */
          <div
            className="relative transition-transform duration-150 ease-out select-none flex items-center justify-center w-full h-full max-w-full max-h-full"
            style={{
              transform: `scale(${zoomLevel})`,
              transformOrigin: 'center center',
            }}
          >
            <div
              className="relative bg-black rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex items-center justify-center select-none"
              style={{
                aspectRatio: `${naturalW} / ${naturalH}`,
                maxHeight: '100%',
                maxWidth: '100%',
                height: 'auto',
                width: 'auto',
              }}
            >
              {/* Layer 1: Base Retinal Fundus Scan (always present for geometric truth) */}
              <img
                src={displayOriginal}
                alt="Retinal Fundus Image"
                onLoad={handleImageLoad}
                className={`w-full h-full object-contain block select-none transition-opacity duration-150 ${
                  viewMode === 'heatmap' ? 'opacity-40' : 'opacity-100'
                }`}
              />

              {/* Layer 2: Grad-CAM Heatmap Layer (Overlay & Heatmap Modes) */}
              {hasValidHeatmap && (viewMode === 'heatmap' || viewMode === 'overlay') && (
                <img
                  src={pureHeatmap || blendedOverlay}
                  alt="Grad-CAM Heatmap Layer"
                  onError={() => setImageError(true)}
                  className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150 select-none"
                  style={{
                    opacity: viewMode === 'heatmap' ? 0.88 : opacity / 100,
                    mixBlendMode: viewMode === 'heatmap' ? 'screen' : (pureHeatmap && pureHeatmap !== blendedOverlay ? 'screen' : 'normal'),
                  }}
                />
              )}

              {/* Layer 3A: Independent Anatomical "A" Reference Marker (z-10 on top of heatmap, never tinted) */}
              <div
                className="absolute bottom-2.5 right-2.5 px-1.5 py-0.5 rounded bg-white/95 text-slate-900 font-extrabold text-[11px] border border-slate-300 shadow-sm pointer-events-none select-none z-10 flex items-center justify-center leading-none"
                title="Anatomical Reference Marker A"
              >
                A
              </div>

              {/* Layer 3B: Independent Anatomical Landmark Overlays (Optic Disc & Macula) */}
              {showLandmarks && (
                <div className="absolute inset-0 pointer-events-none z-10">
                  {/* Optic Disc Marker */}
                  <div
                    className={`absolute ${
                      selectedEye === 'OD' ? 'left-[26%]' : 'right-[26%]'
                    } top-[46%] -translate-x-1/2 -translate-y-1/2 w-14 h-14 rounded-full border-2 border-dashed border-amber-400/90 flex items-center justify-center shadow-sm`}
                  >
                    <span className="absolute -top-5 text-[9px] font-bold text-amber-300 bg-black/85 px-1.5 py-0.5 rounded border border-amber-400/30">
                      Optic Disc
                    </span>
                  </div>

                  {/* Macula Zone */}
                  <div
                    className={`absolute ${
                      selectedEye === 'OD' ? 'left-[62%]' : 'left-[38%]'
                    } top-[48%] -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full border-2 border-emerald-400/80 flex items-center justify-center shadow-sm`}
                  >
                    <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                    <span className="absolute -bottom-5 text-[9px] font-bold text-emerald-300 bg-black/85 px-1.5 py-0.5 rounded border border-emerald-400/30">
                      Macula / FAZ
                    </span>
                  </div>
                </div>
              )}

              {/* Layer 4: Error Notice */}
              {imageError && (
                <div className="absolute bottom-3 inset-x-3 bg-slate-900/90 backdrop-blur-md rounded-xl p-3 border border-rose-800 text-center text-xs text-rose-300 shadow-lg space-y-1 z-20">
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

              {/* Layer 5: Mode & Eye Status Badge */}
              <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/80 backdrop-blur-sm border border-white/10 text-[10px] font-bold text-white pointer-events-none z-20">
                <div
                  className={`w-2 h-2 rounded-full ${
                    viewMode === 'original'
                      ? 'bg-blue-400'
                      : viewMode === 'heatmap'
                      ? 'bg-orange-400 animate-pulse'
                      : hasValidHeatmap
                      ? 'bg-purple-400 animate-pulse'
                      : 'bg-brand-400'
                  }`}
                ></div>
                <span>{selectedEye === 'OD' ? 'OD (Right Eye)' : 'OS (Left Eye)'}</span>
                <span className="text-slate-300">
                  • {viewMode === 'original' ? (t('modeOriginal') || 'Original Fundus') : viewMode === 'heatmap' ? (t('modeHeatmap') || 'Grad-CAM Heatmap') : (t('modeOverlay') || 'Overlay')}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Viewport Zoom & Pan Floating Controls */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white shadow-xl">
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
          {/* Opacity Slider for Overlay & Split Modes */}
          {(viewMode === 'overlay' || viewMode === 'split') && (
            <div className="space-y-2.5 p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold text-slate-700">
                <div className="flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-brand-600" />
                  <span className="font-bold text-slate-900">
                    {t('heatmapOpacity') || 'Overlay Opacity'}: <span className="font-mono text-brand-700 font-extrabold">{opacity}%</span>
                  </span>
                </div>
                
                {/* Quick Opacity Presets */}
                <div className="flex items-center gap-1">
                  {[20, 30, 40, 50, 60, 70].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setOpacity(val)}
                      className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition border ${
                        opacity === val
                          ? 'bg-brand-600 text-white border-brand-500 shadow-xs'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {val === 40 ? '40% (Default)' : `${val}%`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Slider Track (20% to 70%) */}
              <div className="flex items-center gap-3 pt-1">
                <span className="text-[11px] font-bold text-slate-500">20%</span>
                <input
                  type="range"
                  min="20"
                  max="70"
                  step="1"
                  value={opacity}
                  onChange={(e) => setOpacity(Number(e.target.value))}
                  className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600 focus:outline-none"
                  aria-label="Adjust Overlay Opacity"
                />
                <span className="text-[11px] font-bold text-slate-500">70%</span>
              </div>

              <p className="text-[11px] text-slate-500 font-medium">
                Grad-CAM highlights regions that contributed to the model prediction.
              </p>
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
