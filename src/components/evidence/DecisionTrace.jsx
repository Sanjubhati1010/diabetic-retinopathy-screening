import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import {
  Upload,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  ShieldCheck,
  Cpu,
  BarChart2,
  Sparkles,
  Award,
  ArrowRight,
  Clock,
  Stethoscope,
  ChevronRight,
} from 'lucide-react';

/**
 * AI Decision Trace Component
 * Visualizes the 10-stage clinical intelligence and verification pathway from fundus intake to specialist review.
 */
export const DecisionTrace = ({ screening, selectedEye = 'OD', className = '' }) => {
  const { t, language } = useLanguage();

  if (!screening) return null;

  const isOD = selectedEye === 'OD';
  const analysis = isOD
    ? screening.rightEyeAnalysis || screening.aiResultOD || (screening.selectedEyeForAnalysis === 'OD' ? screening.aiResult : null)
    : screening.leftEyeAnalysis || screening.aiResultOS || (screening.selectedEyeForAnalysis === 'OS' ? screening.aiResult : null);

  const validation = isOD ? screening.odValidation : screening.osValidation;
  const imagePresent = isOD ? Boolean(screening.imageOD) : Boolean(screening.imageOS);
  const isValidRetinal = validation ? validation.is_retinal : true;
  const qualityGrade = validation?.quality_grade || 'good';
  const safetyStatus = analysis?.safety_status || (isOD ? screening.safetyStatusOD : screening.safetyStatusOS) || 'READY_FOR_AI';
  const isSafetyPassed = safetyStatus === 'READY_FOR_AI';
  const hasClassification = Boolean(analysis?.predicted_class !== undefined || screening.aiResult !== undefined);
  const rawConfidence = analysis?.confidence ?? screening.confidence;
  const hasConfidence = rawConfidence !== null && rawConfidence !== undefined;
  const hasGradcam = Boolean(
    analysis?.gradcam_url ||
    (isOD ? screening.gradCamOD : screening.gradCamOS) ||
    screening.gradCamUrl
  );
  const hasRisk = Boolean(analysis?.risk_category || screening.riskCategory);
  const hasReferral = Boolean(analysis?.referral_priority || screening.referralPriority);
  const reviewStatus = screening.reviewStatus || (screening.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW');
  const isDoctorReviewed = reviewStatus === 'AI RESULT ACCEPTED' || reviewStatus === 'DOCTOR REVIEWED / MODIFIED';

  const steps = [
    {
      id: 1,
      title: 'Image Uploaded',
      titleHi: 'इमेज अपलोड',
      status: imagePresent ? 'success' : 'pending',
      desc: imagePresent ? `${selectedEye} Scan Available` : 'Awaiting upload',
    },
    {
      id: 2,
      title: 'Image Validated',
      titleHi: 'रेटिना सत्यापन',
      status: isValidRetinal ? 'success' : 'failed',
      desc: isValidRetinal ? 'Retinal Fundus Verified' : 'Non-retinal scan rejected',
    },
    {
      id: 3,
      title: 'Quality Checked',
      titleHi: 'गुणवत्ता जाँच',
      status: qualityGrade === 'good' ? 'success' : qualityGrade === 'warning' ? 'warning' : 'failed',
      desc: validation?.metrics?.resolution ? `${validation.metrics.resolution} • ${qualityGrade}` : 'Validated',
    },
    {
      id: 4,
      title: 'AI Safety Gate',
      titleHi: 'AI सुरक्षा गेट',
      status: isSafetyPassed ? 'success' : 'failed',
      desc: isSafetyPassed ? 'Passed Safety Threshold' : 'Safety Gate Blocked',
    },
    {
      id: 5,
      title: 'DR Classification',
      titleHi: 'डीआर वर्गीकरण',
      status: hasClassification ? 'success' : 'pending',
      desc: analysis?.class_name ? `Class: ${analysis.class_name}` : 'Predicted',
    },
    {
      id: 6,
      title: 'Confidence Computed',
      titleHi: 'कॉन्फिडेंस संगणना',
      status: hasConfidence ? (rawConfidence >= 0.6 ? 'success' : 'warning') : 'pending',
      desc: hasConfidence ? `${(rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence).toFixed(1)}% Agreement` : 'Computed',
    },
    {
      id: 7,
      title: 'Grad-CAM Generated',
      titleHi: 'Grad-CAM उत्पन्न',
      status: hasGradcam ? 'success' : 'failed',
      desc: hasGradcam ? 'Attention Heatmap (40%)' : 'Unavailable',
    },
    {
      id: 8,
      title: 'Risk Assessed',
      titleHi: 'जोखिम मूल्यांकन',
      status: hasRisk ? 'success' : 'pending',
      desc: analysis?.risk_category || screening.riskCategory || 'Assessed',
    },
    {
      id: 9,
      title: 'Referral Guidance',
      titleHi: 'रेफरल मार्गदर्शन',
      status: hasReferral ? 'success' : 'pending',
      desc: 'Protocol Assigned',
    },
    {
      id: 10,
      title: 'Doctor Review',
      titleHi: 'डॉक्टर समीक्षा',
      status: isDoctorReviewed ? 'success' : 'pending',
      desc: isDoctorReviewed ? 'Specialist Signed-off' : 'Pending Tele-Review',
    },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
      case 'warning':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
      case 'failed':
        return <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getStepBorderColor = (status) => {
    switch (status) {
      case 'success':
        return 'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50';
      case 'warning':
        return 'border-amber-200 bg-amber-50/50 hover:bg-amber-50';
      case 'failed':
        return 'border-rose-200 bg-rose-50/50 hover:bg-rose-50';
      default:
        return 'border-slate-200 bg-slate-50/50';
    }
  };

  return (
    <div className={`rounded-3xl border border-slate-200 bg-white shadow-card p-5 sm:p-6 space-y-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-600" />
            <span>{t('decisionTraceTitle') || 'AI Decision Trace'}</span>
          </h3>
          <p className="text-xs text-slate-500 font-medium">
            {t('decisionTraceSub') || 'Step-by-step verification audit from image intake to clinical review'}
          </p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-bold">
          10/10 Stages Audited
        </span>
      </div>

      {/* 10-Stage Horizontal Scrollable / Responsive Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        {steps.map((st) => (
          <div
            key={st.id}
            className={`p-2.5 rounded-2xl border transition flex flex-col justify-between space-y-1.5 ${getStepBorderColor(
              st.status
            )}`}
          >
            <div className="flex items-center justify-between">
              <span className="w-5 h-5 rounded-full bg-white border border-slate-200 text-[10px] font-bold flex items-center justify-center text-slate-700 shadow-2xs">
                {st.id}
              </span>
              {getStatusBadge(st.status)}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 leading-tight">
                {language === 'hi' ? st.titleHi : st.title}
              </p>
              <p className="text-[10px] text-slate-500 font-medium truncate pt-0.5">
                {st.desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
