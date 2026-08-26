import React, { useState } from 'react';
import { AlertTriangle, AlertCircle, X, CheckCircle2, Info } from 'lucide-react';

export const AlertBanner = ({ type = 'info', title, message, dismissible = true, onDismiss }) => {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  const handleDismiss = () => {
    setVisible(false);
    if (onDismiss) onDismiss();
  };

  const getAlertStyles = () => {
    switch (type) {
      case 'error':
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          icon: AlertCircle,
          iconColor: 'text-rose-600',
        };
      case 'warning':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          icon: AlertTriangle,
          iconColor: 'text-amber-600',
        };
      case 'success':
        return {
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          icon: CheckCircle2,
          iconColor: 'text-emerald-600',
        };
      default:
        return {
          bg: 'bg-blue-50 border-blue-200 text-blue-800',
          icon: Info,
          iconColor: 'text-blue-600',
        };
    }
  };

  const config = getAlertStyles();
  const Icon = config.icon;

  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl border ${config.bg} shadow-sm transition-all`}>
      <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${config.iconColor}`} />
      <div className="flex-1 min-w-0">
        {title && <h5 className="text-xs font-bold uppercase tracking-wider">{title}</h5>}
        <p className="text-xs mt-0.5 leading-relaxed">{message}</p>
      </div>
      {dismissible && (
        <button
          onClick={handleDismiss}
          className="p-1 rounded-lg hover:bg-black/5 text-current shrink-0 transition"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
