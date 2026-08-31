import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import {
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  AlertOctagon,
  HelpCircle,
  Clock,
  CheckCircle,
  UserCheck,
} from 'lucide-react';

export const SeverityBadge = ({ severity, showIcon = true, size = 'md' }) => {
  const { t } = useLanguage();

  const getBadgeConfig = () => {
    switch (severity) {
      case 'dr0':
        return {
          label: t('dr0'),
          shortLabel: 'DR 0 (No DR)',
          bgColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dotColor: 'bg-emerald-500',
          icon: ShieldCheck,
        };
      case 'dr1':
        return {
          label: t('dr1'),
          shortLabel: 'DR 1 (Mild NPDR)',
          bgColor: 'bg-blue-50 text-blue-700 border-blue-200',
          dotColor: 'bg-blue-500',
          icon: AlertCircle,
        };
      case 'dr2':
        return {
          label: t('dr2'),
          shortLabel: 'DR 2 (Moderate NPDR)',
          bgColor: 'bg-amber-50 text-amber-700 border-amber-200',
          dotColor: 'bg-amber-500',
          icon: AlertTriangle,
        };
      case 'dr3':
        return {
          label: t('dr3'),
          shortLabel: 'DR 3 (Severe NPDR)',
          bgColor: 'bg-orange-50 text-orange-700 border-orange-200',
          dotColor: 'bg-orange-600',
          icon: AlertOctagon,
        };
      case 'dr4':
        return {
          label: t('dr4'),
          shortLabel: 'DR 4 (Proliferative DR)',
          bgColor: 'bg-rose-50 text-rose-700 border-rose-200',
          dotColor: 'bg-rose-600',
          icon: AlertOctagon,
        };
      default:
        return {
          label: t('drUncertain'),
          shortLabel: 'Pending',
          bgColor: 'bg-slate-100 text-slate-700 border-slate-200',
          dotColor: 'bg-slate-400',
          icon: HelpCircle,
        };
    }
  };

  const config = getBadgeConfig();
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-medium',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1.5 text-sm font-bold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${sizeClasses[size] || sizeClasses.md}`}
    >
      {showIcon && <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />}
      <span>{size === 'sm' ? config.shortLabel : config.label}</span>
    </span>
  );
};

export const SafetyBadge = ({ status = 'READY_FOR_AI', size = 'md' }) => {
  const { t } = useLanguage();
  const normalized = (status || '').toUpperCase().trim();

  let config = {
    label: t('safetyReady') || 'READY FOR AI',
    bgColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    dotColor: 'bg-emerald-500',
    icon: ShieldCheck,
  };

  if (normalized.includes('INVALID')) {
    config = {
      label: t('safetyInvalid') || 'IMAGE INVALID',
      bgColor: 'bg-rose-50 text-rose-800 border-rose-200',
      dotColor: 'bg-rose-500',
      icon: AlertOctagon,
    };
  } else if (normalized.includes('INSUFFICIENT') || normalized.includes('QUALITY')) {
    config = {
      label: t('safetyQualityLow') || 'QUALITY INSUFFICIENT',
      bgColor: 'bg-amber-50 text-amber-800 border-amber-200',
      dotColor: 'bg-amber-500',
      icon: AlertTriangle,
    };
  } else if (normalized.includes('BLOCKED')) {
    config = {
      label: t('safetyBlocked') || 'AI ANALYSIS BLOCKED',
      bgColor: 'bg-slate-100 text-slate-800 border-slate-300',
      dotColor: 'bg-slate-500',
      icon: AlertCircle,
    };
  }

  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px] font-bold',
    md: 'px-2.5 py-1 text-xs font-bold',
    lg: 'px-3.5 py-1.5 text-sm font-extrabold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${
        sizeClasses[size] || sizeClasses.md
      }`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};

export const ScreeningStatusBadge = ({ status = 'RELIABLE AI SCREENING', size = 'md' }) => {
  const { t } = useLanguage();
  const normalized = (status || '').toUpperCase().trim();

  let config = {
    label: t('statusReliable') || 'Reliable AI Screening',
    bgColor: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    icon: ShieldCheck,
  };

  if (normalized.includes('LOW')) {
    config = {
      label: t('statusLowConfidence') || 'Low Confidence',
      bgColor: 'bg-amber-50 text-amber-800 border-amber-300',
      icon: AlertTriangle,
    };
  } else if (normalized.includes('UNABLE') || normalized.includes('ASSESS') || normalized.includes('RECAPTURE')) {
    config = {
      label: t('statusUnableToAssess') || 'Unable to Assess',
      bgColor: 'bg-rose-50 text-rose-800 border-rose-300',
      icon: AlertOctagon,
    };
  }

  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-xs font-bold',
    md: 'px-3 py-1 text-xs font-bold',
    lg: 'px-4 py-1.5 text-sm font-extrabold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${
        sizeClasses[size] || sizeClasses.md
      }`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};

export const UrgencyBadge = ({ urgency }) => {
  const { t } = useLanguage();

  switch (urgency) {
    case 'urgent':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300 animate-pulse-subtle">
          <AlertOctagon className="w-3.5 h-3.5 text-red-600" />
          {t('referralUrgent')}
        </span>
      );
    case 'moderate':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          {t('referralModerate')}
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          {t('referralRoutine')}
        </span>
      );
  }
};

export const RiskBadge = ({ risk = 'MODERATE', size = 'md' }) => {
  const { t } = useLanguage();
  const normalized = (risk || '').toUpperCase().trim();

  let config = {
    label: t('riskModerate') || 'MODERATE',
    bgColor: 'bg-amber-50 text-amber-800 border-amber-200',
    icon: AlertTriangle,
  };

  if (normalized === 'LOW') {
    config = {
      label: t('riskLow') || 'LOW',
      bgColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      icon: ShieldCheck,
    };
  } else if (normalized === 'HIGH') {
    config = {
      label: t('riskHigh') || 'HIGH',
      bgColor: 'bg-rose-50 text-rose-800 border-rose-200',
      icon: AlertOctagon,
    };
  } else if (normalized.includes('LOW CONFIDENCE') || normalized.includes('REVIEW')) {
    config = {
      label: t('riskLowConf') || 'LOW CONFIDENCE / REVIEW REQUIRED',
      bgColor: 'bg-amber-100 text-amber-900 border-amber-300',
      icon: AlertTriangle,
    };
  } else if (normalized.includes('UNABLE') || normalized.includes('ASSESS')) {
    config = {
      label: t('riskUnable') || 'UNABLE TO ASSESS',
      bgColor: 'bg-slate-100 text-slate-800 border-slate-300',
      icon: HelpCircle,
    };
  }

  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-xs font-bold',
    md: 'px-3 py-1 text-xs font-bold',
    lg: 'px-4 py-1.5 text-sm font-extrabold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${
        sizeClasses[size] || sizeClasses.md
      }`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};

export const ReferralBadge = ({ priority = 'EYE SPECIALIST REVIEW RECOMMENDED', size = 'md' }) => {
  const { t } = useLanguage();
  const normalized = (priority || '').toUpperCase().trim();

  let config = {
    label: t('referralSpecialist') || 'EYE SPECIALIST REVIEW RECOMMENDED',
    bgColor: 'bg-amber-50 text-amber-800 border-amber-200',
    icon: AlertTriangle,
  };

  if (normalized.includes('ROUTINE')) {
    config = {
      label: t('referralRoutine') || 'ROUTINE FOLLOW-UP',
      bgColor: 'bg-blue-50 text-blue-800 border-blue-200',
      icon: ShieldCheck,
    };
  } else if (normalized.includes('PRIORITY')) {
    config = {
      label: t('referralPrioritySpecialist') || 'PRIORITY SPECIALIST REVIEW',
      bgColor: 'bg-rose-50 text-rose-800 border-rose-300 animate-pulse-subtle',
      icon: AlertOctagon,
    };
  } else if (normalized.includes('RECAPTURE') || normalized.includes('RE-CAPTURE')) {
    config = {
      label: t('referralRecapture') || 'IMAGE RE-CAPTURE REQUIRED',
      bgColor: 'bg-orange-50 text-orange-800 border-orange-200',
      icon: AlertTriangle,
    };
  }

  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-xs font-bold',
    md: 'px-3 py-1 text-xs font-bold',
    lg: 'px-4 py-1.5 text-sm font-extrabold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${
        sizeClasses[size] || sizeClasses.md
      }`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};

export const DoctorReviewStatusBadge = ({ status = 'PENDING DOCTOR REVIEW', size = 'md' }) => {
  const { t } = useLanguage();
  const normalized = (status || '').toUpperCase().trim();

  let config = {
    label: t('statusPendingDoctorReview') || 'PENDING SPECIALIST REVIEW',
    bgColor: 'bg-amber-50 text-amber-800 border-amber-300',
    icon: Clock,
  };

  if (normalized.includes('ACCEPTED')) {
    config = {
      label: t('statusAiResultAccepted') || 'AI RESULT ACCEPTED',
      bgColor: 'bg-emerald-50 text-emerald-800 border-emerald-300',
      icon: CheckCircle,
    };
  } else if (normalized.includes('RECAPTURE') || normalized.includes('RE-CAPTURE')) {
    config = {
      label: t('statusImageRecaptureRequested') || 'IMAGE RE-CAPTURE REQUESTED',
      bgColor: 'bg-rose-50 text-rose-800 border-rose-300',
      icon: AlertTriangle,
    };
  } else if (normalized.includes('MODIFIED') || normalized.includes('OVERRID')) {
    config = {
      label: t('statusDoctorReviewedModified') || 'DOCTOR REVIEWED / MODIFIED',
      bgColor: 'bg-blue-50 text-blue-800 border-blue-300',
      icon: UserCheck,
    };
  } else if (normalized.includes('PENDING') || normalized.includes('SPECIALIST') || normalized.includes('DOCTOR REVIEW')) {
    config = {
      label: t('statusPendingDoctorReview') || 'PENDING SPECIALIST REVIEW',
      bgColor: 'bg-amber-50 text-amber-800 border-amber-300',
      icon: Clock,
    };
  } else if (normalized.includes('UNABLE')) {
    config = {
      label: t('statusUnableToAssess') || 'UNABLE TO ASSESS',
      bgColor: 'bg-slate-100 text-slate-800 border-slate-300',
      icon: AlertCircle,
    };
  }

  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-[10px] font-bold',
    md: 'px-3 py-1 text-xs font-bold',
    lg: 'px-4 py-1.5 text-sm font-extrabold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bgColor} ${
        sizeClasses[size] || sizeClasses.md
      }`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};

