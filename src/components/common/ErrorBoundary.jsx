import React from 'react';
import { AlertOctagon, RotateCcw, ArrowLeft } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onRetry) {
      this.props.onRetry();
    } else {
      window.location.reload();
    }
  };

  handleBack = () => {
    if (this.props.onBack) {
      this.props.onBack();
    } else {
      window.history.back();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-3xl border border-slate-200 shadow-card max-w-xl mx-auto my-8 space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 shadow-sm">
            <AlertOctagon className="w-7 h-7" />
          </div>

          <div className="space-y-1.5">
            <h3 className="text-base font-extrabold text-slate-900">
              Something went wrong while displaying the report.
            </h3>
            <p className="text-xs text-slate-500 max-w-md leading-relaxed">
              An unexpected display issue occurred. You can retry loading the report or return to the screening overview.
            </p>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={this.handleBack}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition shadow-xs"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Screening</span>
            </button>

            <button
              type="button"
              onClick={this.handleRetry}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold transition shadow-md"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
