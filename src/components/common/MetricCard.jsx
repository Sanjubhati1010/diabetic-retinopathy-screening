import React from 'react';

export const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive = true,
  variant = 'default',
  onClick,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'emerald':
        return {
          cardBg: 'bg-emerald-50/70 border-emerald-200 hover:border-emerald-300',
          iconBg: 'bg-emerald-600 text-white shadow-glow',
          textVal: 'text-emerald-900',
        };
      case 'teal':
        return {
          cardBg: 'bg-teal-50/70 border-teal-200 hover:border-teal-300',
          iconBg: 'bg-teal-600 text-white shadow-glow-teal',
          textVal: 'text-teal-900',
        };
      case 'amber':
        return {
          cardBg: 'bg-amber-50/70 border-amber-200 hover:border-amber-300',
          iconBg: 'bg-amber-500 text-white shadow-sm',
          textVal: 'text-amber-900',
        };
      case 'rose':
        return {
          cardBg: 'bg-rose-50/70 border-rose-200 hover:border-rose-300',
          iconBg: 'bg-rose-600 text-white shadow-glow-red',
          textVal: 'text-rose-900',
        };
      case 'indigo':
        return {
          cardBg: 'bg-indigo-50/70 border-indigo-200 hover:border-indigo-300',
          iconBg: 'bg-indigo-600 text-white shadow-sm',
          textVal: 'text-indigo-900',
        };
      default:
        return {
          cardBg: 'bg-white border-slate-200/80 hover:border-slate-300',
          iconBg: 'bg-brand-600 text-white shadow-sm',
          textVal: 'text-slate-900',
        };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl p-5 border transition-all duration-200 shadow-card ${vStyles.cardBg} ${
        onClick ? 'cursor-pointer hover:-translate-y-0.5 hover:shadow-md' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className={`text-2xl sm:text-3xl font-extrabold ${vStyles.textVal}`}>{value}</h3>
            {trend && (
              <span
                className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                  trendPositive ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                }`}
              >
                {trend}
              </span>
            )}
          </div>
        </div>
        {Icon && (
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${vStyles.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      {subtitle && <p className="mt-3 text-xs text-slate-500 leading-relaxed">{subtitle}</p>}
    </div>
  );
};
