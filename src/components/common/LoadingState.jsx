import React from 'react';
import { Loader2, Eye, Sparkles } from 'lucide-react';

export const LoadingState = ({ message = 'Loading Clinical Data...', fullScreen = false }) => {
  const content = (
    <div className="flex flex-col items-center justify-center p-8 space-y-4 text-center">
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600 shadow-glow">
          <Eye className="w-8 h-8 animate-pulse" />
        </div>
        <div className="absolute -inset-1 rounded-2xl bg-brand-500/20 blur-sm -z-10 animate-ping opacity-50" />
      </div>
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-slate-800 flex items-center justify-center gap-1.5">
          <Loader2 className="w-4 h-4 text-brand-600 animate-spin" />
          <span>{message}</span>
        </h4>
        <p className="text-xs text-slate-400">Diabetic Retinopathy Screening System</p>
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
};
