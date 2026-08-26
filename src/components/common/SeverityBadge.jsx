import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { ShieldCheck, AlertCircle, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react';

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
          shortLabel: 'DR 1 (Mild)',
          bgColor: 'bg-blue-50 text-blue-700 border-blue-200',
          dotColor: 'bg-blue-500',
          icon: AlertCircle,
        };
      case 'dr2':
        return {
          label: t('dr2'),
          shortLabel: 'DR 2 (Moderate)',
          bgColor: 'bg-amber-50 text-amber-700 border-amber-200',
          dotColor: 'bg-amber-500',
          icon: AlertTriangle,
        };
      case 'dr3':
        return {
          label: t('dr3'),
          shortLabel: 'DR 3 (Severe)',
          bgColor: 'bg-orange-50 text-orange-700 border-orange-200',
          dotColor: 'bg-orange-600',
          icon: AlertOctagon,
        };
      case 'dr4':
        return {
          label: t('dr4'),
          shortLabel: 'PDR 4 (Proliferative)',
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
