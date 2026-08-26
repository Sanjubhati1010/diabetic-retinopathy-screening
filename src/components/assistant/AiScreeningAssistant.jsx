import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import { queryAssistant } from '../../services/api';
import {
  Sparkles,
  MessageSquare,
  X,
  Send,
  HelpCircle,
  ShieldCheck,
  Eye,
  AlertTriangle,
  RotateCcw,
  ChevronRight,
  ChevronDown,
  Info,
  CheckCircle2,
  Minimize2,
  Maximize2,
  Bot,
  Compass,
} from 'lucide-react';

export const AiScreeningAssistant = () => {
  const { t, language: appLang } = useLanguage();
  const { activeScreening, screenings, voiceGuidanceEnabled, speakPrompt } = useApp();
  const location = useLocation();

  const [isOpen, setIsOpen] = useState(false);
  const [assistantLang, setAssistantLang] = useState(appLang === 'hi' ? 'hi' : 'en');
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [guidedModeOpen, setGuidedModeOpen] = useState(false);
  const messagesEndRef = useRef(null);

  // Sync assistant language if app language changes
  useEffect(() => {
    setAssistantLang(appLang === 'hi' ? 'hi' : 'en');
  }, [appLang]);

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          sender: 'assistant',
          text:
            assistantLang === 'hi'
              ? 'नमस्ते! मैं मैडॉक्स (MADOCS) स्क्रीनिंग सहायक हूँ। मैं स्क्रीनिंग सिस्टम का उपयोग करने और एआई परिणामों को समझने में आपकी मदद कर सकता हूँ।'
              : "Hi! I'm the MADOCS Screening Assistant. I can help you use the screening system and understand your AI-assisted results.",
          contextUsed: false,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  }, [assistantLang]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, loading]);

  // Extract active screening context safely
  const getSanitizedScreeningContext = () => {
    const latest = screenings.find((s) => s.isRealPrediction || s.confidence !== null) || activeScreening;
    if (!latest) return null;

    return {
      eye: latest.selectedEyeForAnalysis || 'Bilateral',
      prediction: latest.className || (latest.overallSeverity ? t(latest.overallSeverity) : null),
      confidence: latest.confidence,
      safety_status: latest.safetyStatus || 'READY_FOR_AI',
      risk_category: latest.riskCategory || 'MODERATE',
      referral_priority: latest.referralPriority || 'EYE SPECIALIST REVIEW RECOMMENDED',
      explainability_available: Boolean(latest.gradCamUrl || latest.gradCamOD || latest.gradCamOS),
      is_low_confidence: Boolean(latest.isLowConfidence),
      next_step: latest.nextStep,
    };
  };

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setLoading(true);

    try {
      const context = getSanitizedScreeningContext();
      const response = await queryAssistant(text, assistantLang, context, location.pathname);

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.reply,
        contextUsed: response.context_used,
        suggestedActions: response.suggested_actions,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Assistant response failed:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text:
            assistantLang === 'hi'
              ? 'सहायक सेवा अस्थायी रूप से अनुपलब्ध है। आप त्वरित सहायता विकल्पों का उपयोग कर सकते हैं।'
              : 'The assistant service is temporarily unavailable. You can use the quick help options below.',
          contextUsed: false,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      label: assistantLang === 'hi' ? 'एआई ने यह परिणाम क्यों दिया?' : 'Why this result?',
      query: assistantLang === 'hi' ? 'एआई ने यह परिणाम क्यों दिया?' : 'Why did AI give this result?',
      icon: Sparkles,
    },
    {
      label: assistantLang === 'hi' ? 'कॉन्फिडेंस का क्या अर्थ है?' : 'What is confidence?',
      query: assistantLang === 'hi' ? 'कॉन्फिडेंस का क्या अर्थ है?' : 'What does confidence mean?',
      icon: Info,
    },
    {
      label: assistantLang === 'hi' ? 'डॉक्टर समीक्षा क्यों जरूरी?' : 'Why doctor review?',
      query: assistantLang === 'hi' ? 'डॉक्टर समीक्षा की सिफारिश क्यों की गई है?' : 'Why is doctor review recommended?',
      icon: ShieldCheck,
    },
    {
      label: assistantLang === 'hi' ? 'Grad-CAM क्या दिखाता है?' : 'What Grad-CAM shows?',
      query: assistantLang === 'hi' ? 'Grad-CAM क्या दिखाता है?' : 'What does Grad-CAM show?',
      icon: Eye,
    },
    {
      label: assistantLang === 'hi' ? 'री-कैप्चर के बाद क्या होगा?' : 'After re-capture?',
      query: assistantLang === 'hi' ? 'दोबारा फोटो लेने के बाद क्या होता है?' : 'What happens after re-capture?',
      icon: RotateCcw,
    },
    {
      label: assistantLang === 'hi' ? 'इमेज कैसे अपलोड करें?' : 'How to Upload?',
      query: assistantLang === 'hi' ? 'इमेज कैसे अपलोड करें?' : 'How do I upload fundus images?',
      icon: HelpCircle,
    },
  ];

  const guidedSteps = [
    { id: 1, text: t('guidedStep1') || 'Step 1: Register patient & prepare camera' },
    { id: 2, text: t('guidedStep2') || 'Step 2: Capture & upload Right Eye (OD) scan' },
    { id: 3, text: t('guidedStep3') || 'Step 3: Capture & upload Left Eye (OS) scan' },
    { id: 4, text: t('guidedStep4') || 'Step 4: Verify AI Safety Gate quality check' },
    { id: 5, text: t('guidedStep5') || 'Step 5: Run AI Screening & review confidence' },
    { id: 6, text: t('guidedStep6') || 'Step 6: Inspect Grad-CAM attention heatmap' },
    { id: 7, text: t('guidedStep7') || 'Step 7: Check referral recommendation & report' },
  ];

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-reset',
        sender: 'assistant',
        text:
          assistantLang === 'hi'
            ? 'चैट साफ़ कर दी गई है। मैं आपकी क्या सहायता कर सकता हूँ?'
            : 'Chat cleared. How can I assist you with your screening workflow?',
        contextUsed: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return (
    <>
      {/* Floating Trigger Button (Bottom Right) */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 p-3.5 sm:px-5 sm:py-3.5 rounded-full bg-gradient-to-r from-brand-600 to-teal-600 text-white font-bold text-xs shadow-glow hover:shadow-xl transition-all transform hover:scale-105 flex items-center gap-2.5 group focus:outline-none focus:ring-4 focus:ring-brand-500/30"
          aria-label="Open AI Screening Assistant"
        >
          <div className="relative">
            <Bot className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping"></span>
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full"></span>
          </div>
          <span className="hidden sm:inline tracking-wide font-extrabold">{t('assistantTitle') || 'AI Assistant'}</span>
        </button>
      )}

      {/* Floating Collapsible Assistant Drawer Panel */}
      {isOpen && (
        <div className="fixed bottom-0 sm:bottom-6 right-0 sm:right-6 z-50 w-full sm:w-96 max-h-[92vh] sm:max-h-[640px] h-[92vh] sm:h-[620px] bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl border border-slate-200/90 flex flex-col overflow-hidden animate-slide-up sm:animate-fade-in font-sans">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white p-4 flex items-center justify-between border-b border-slate-700/70 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand-500/20 border border-brand-400/40 flex items-center justify-center text-brand-400">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xs font-extrabold tracking-tight flex items-center gap-1.5">
                  <span>{t('assistantTitle') || 'AI Screening Assistant'}</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                </h3>
                <p className="text-[10px] text-slate-400 font-medium">
                  {t('assistantSubtitle') || 'Clinical Screening Companion'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {/* Language Switcher Pill */}
              <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700 text-[10px] font-bold">
                <button
                  type="button"
                  onClick={() => setAssistantLang('en')}
                  className={`px-2 py-0.5 rounded-md transition ${
                    assistantLang === 'en' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  EN
                </button>
                <button
                  type="button"
                  onClick={() => setAssistantLang('hi')}
                  className={`px-2 py-0.5 rounded-md transition font-hindi ${
                    assistantLang === 'hi' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  हिन्दी
                </button>
              </div>

              {/* Close Button */}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                aria-label="Close Assistant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick-Action Chips Ribbon */}
          <div className="bg-slate-50/90 border-b border-slate-200 px-3 py-2 shrink-0">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Quick Actions</span>
              <button
                type="button"
                onClick={() => setGuidedModeOpen(!guidedModeOpen)}
                className="text-[10px] font-bold text-brand-700 hover:text-brand-800 flex items-center gap-0.5"
              >
                <Compass className="w-3 h-3" />
                <span>{guidedModeOpen ? 'Hide Workflow' : t('guidedModeTitle') || 'Guided Workflow'}</span>
              </button>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
              {quickActions.map((qa, idx) => {
                const Icon = qa.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(qa.query)}
                    className="whitespace-nowrap inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-brand-50 border border-slate-200 hover:border-brand-300 text-[11px] font-bold text-slate-700 hover:text-brand-700 transition shadow-xs shrink-0"
                  >
                    <Icon className="w-3 h-3 text-brand-600" />
                    <span>{qa.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Collapsible Guided Workflow Accordion */}
            {guidedModeOpen && (
              <div className="mt-2 p-2.5 rounded-xl bg-white border border-brand-200 text-[11px] space-y-1 animate-fade-in shadow-inner">
                <div className="flex items-center justify-between font-bold text-brand-900 pb-1 border-b border-brand-100">
                  <span>{t('guidedModeTitle') || 'Guided Screening Workflow'}</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-brand-50 text-brand-700">7 Steps</span>
                </div>
                <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                  {guidedSteps.map((step) => (
                    <div key={step.id} className="flex items-start gap-1.5 text-slate-600 py-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-brand-600 shrink-0 mt-0.5" />
                      <span className="text-[10px] leading-tight">{step.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Conversation Stream Area */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 bg-gradient-to-b from-slate-50/50 to-white text-xs">
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-3 shadow-xs leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-br from-brand-600 to-teal-600 text-white rounded-br-xs'
                        : 'bg-white border border-slate-200 text-slate-800 rounded-bl-xs'
                    }`}
                  >
                    <p className="text-[11px] whitespace-pre-line">{msg.text}</p>
                  </div>

                  <div className="flex items-center gap-1.5 text-[9px] text-slate-400 px-1">
                    <span>{msg.time}</span>
                    {msg.contextUsed && (
                      <span className="text-emerald-700 font-bold bg-emerald-50 px-1 rounded border border-emerald-200">
                        • Screening Context Active
                      </span>
                    )}
                  </div>

                  {/* Follow-up Action Suggestions */}
                  {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {msg.suggestedActions.map((act, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleSendMessage(act)}
                          className="px-2 py-0.5 rounded-full bg-slate-100 hover:bg-brand-50 text-slate-600 hover:text-brand-700 border border-slate-200 text-[10px] font-semibold transition"
                        >
                          {act}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Loading Typing Indicator */}
            {loading && (
              <div className="flex items-center gap-2 text-slate-500 text-[11px] p-2 bg-white border border-slate-200 rounded-2xl max-w-[50%] shadow-xs animate-pulse">
                <Sparkles className="w-3.5 h-3.5 text-brand-600 animate-spin" />
                <span>Generating explanation...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input Area */}
          <div className="p-3 bg-white border-t border-slate-200 space-y-2 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={t('assistantPlaceholder') || 'Ask a question in English or Hindi...'}
                className="flex-1 px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 text-xs text-slate-800 placeholder-slate-400"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || loading}
                className="p-2 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white transition flex items-center justify-center shrink-0 shadow-sm"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>

            <div className="flex items-center justify-between text-[9px] text-slate-400">
              <span className="italic">{t('assistantDisclaimer') || 'AI screening support • Not a diagnostician'}</span>
              <button
                type="button"
                onClick={handleClearChat}
                className="hover:text-slate-600 transition"
              >
                {t('btnClearChat') || 'Clear'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
