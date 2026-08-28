import React from 'react';

export const DemoDisclaimer = ({ text = "DEMO DATA — NOT REAL MEDICAL RESULTS", className = "" }) => {
  return (
    <div
      className={`no-print inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-amber-50/80 text-amber-800/90 border border-amber-200/60 text-[11px] font-medium tracking-tight ${className}`}
      role="note"
      aria-label="Demo Data Disclaimer"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
      <span>{text}</span>
    </div>
  );
};
