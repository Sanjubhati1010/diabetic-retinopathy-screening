import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  Eye,
  UserCheck,
  Stethoscope,
  ArrowRight,
  Sparkles,
  Lock,
  Mail,
  Languages,
  AlertCircle,
  Shield,
} from 'lucide-react';

const DEMO_CREDENTIALS = {
  health_worker: {
    email: 'asha.rampur@phc.in',
    password: 'asha@rampur2026',
    role: 'health_worker',
    redirect: '/dashboard',
    name: 'Pooja Sharma (ASHA Worker)',
  },
  doctor: {
    email: 'dr.swaminathan@districthospital.gov.in',
    password: 'doctor@teleophth2026',
    role: 'doctor',
    redirect: '/doctor',
    name: 'Dr. Arvind Swaminathan, MS',
  },
};

export const LoginPage = () => {
  const { t, language, toggleLanguage } = useLanguage();
  const { login } = useApp();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState('health_worker');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');

    const trimmedEmail = email.trim();
    const trimmedPassword = password.trim();

    if (!trimmedEmail) {
      setError('Please enter your PHC ID or email.');
      return;
    }

    if (!trimmedPassword) {
      setError('Please enter your password.');
      return;
    }

    setLoading(true);

    setTimeout(() => {
      const healthWorkerDemo = DEMO_CREDENTIALS.health_worker;
      const doctorDemo = DEMO_CREDENTIALS.doctor;

      let authenticatedUser = null;

      if (
        trimmedEmail.toLowerCase() === healthWorkerDemo.email.toLowerCase() &&
        password === healthWorkerDemo.password
      ) {
        authenticatedUser = healthWorkerDemo;
      } else if (
        trimmedEmail.toLowerCase() === doctorDemo.email.toLowerCase() &&
        password === doctorDemo.password
      ) {
        authenticatedUser = doctorDemo;
      }

      if (authenticatedUser) {
        login(authenticatedUser.role, authenticatedUser);
        setLoading(false);
        navigate(authenticatedUser.redirect);
      } else {
        setLoading(false);
        setError('Invalid PHC ID/email or password.');
      }
    }, 350);
  };

  const handleRoleTabChange = (role) => {
    setSelectedRole(role);
    setError('');
  };

  const handleDemoProfileClick = (role) => {
    setError('');
    setSelectedRole(role);
    if (role === 'doctor') {
      setEmail(DEMO_CREDENTIALS.doctor.email);
      setPassword(DEMO_CREDENTIALS.doctor.password);
    } else {
      setEmail(DEMO_CREDENTIALS.health_worker.email);
      setPassword(DEMO_CREDENTIALS.health_worker.password);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50/70 via-slate-50 to-teal-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Top Header Controls */}
      <div className="absolute top-6 right-6 flex items-center gap-3">
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white/80 backdrop-blur shadow-sm text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
        >
          <Languages className="w-4 h-4 text-brand-600" />
          <span>{language === 'en' ? 'हिन्दी' : 'English'}</span>
        </button>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-2">
        <div className="inline-flex w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-teal-500 items-center justify-center text-white shadow-glow mb-2">
          <Eye className="w-7 h-7" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Netra<span className="text-brand-600">AI</span> Portal Sign In
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Diabetic Retinopathy Screening for Primary Health Centers
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-10 rounded-3xl shadow-xl border border-slate-200/80 space-y-6">
          {/* Role Selection Tabs */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Select Your Operational Role
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-2xl">
              <button
                type="button"
                onClick={() => handleRoleTabChange('health_worker')}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl text-xs font-bold transition ${
                  selectedRole === 'health_worker'
                    ? 'bg-white text-brand-700 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <UserCheck className="w-3.5 h-3.5" />
                <span>Health Worker</span>
              </button>
              <button
                type="button"
                onClick={() => handleRoleTabChange('doctor')}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl text-xs font-bold transition ${
                  selectedRole === 'doctor'
                    ? 'bg-white text-teal-700 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Stethoscope className="w-3.5 h-3.5" />
                <span>Doctor / Specialist</span>
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="flex items-center gap-2 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} noValidate className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                PHC Identifier or Email
              </label>
              <div className="mt-1 relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError('');
                  }}
                  className="block w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 placeholder-slate-400"
                  placeholder={
                    selectedRole === 'doctor'
                      ? 'e.g. dr.swaminathan@districthospital.gov.in'
                      : 'e.g. asha.rampur@phc.in'
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700">Security PIN / Password</label>
              <div className="mt-1 relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError('');
                  }}
                  className="block w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 placeholder-slate-400"
                  placeholder="Enter your security PIN or password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-glow transition disabled:opacity-50"
            >
              {loading ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <span>
                    {selectedRole === 'doctor'
                      ? 'Sign In to Tele-Ophthalmology'
                      : 'Sign In to Screening Desk'}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Explicit Demo Profiles */}
          <div className="pt-4 border-t border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 text-center mb-3">
              Demo Credentials (Click to load)
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDemoProfileClick('health_worker')}
                className="p-2.5 rounded-xl border border-brand-200 bg-brand-50/70 hover:bg-brand-100 text-left transition group"
              >
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-brand-900">ASHA Screener</p>
                  <span className="text-[10px] text-brand-600 font-semibold opacity-0 group-hover:opacity-100 transition">
                    Fill
                  </span>
                </div>
                <p className="text-[10px] text-brand-700">Rampur Rural PHC</p>
              </button>

              <button
                type="button"
                onClick={() => handleDemoProfileClick('doctor')}
                className="p-2.5 rounded-xl border border-teal-200 bg-teal-50/70 hover:bg-teal-100 text-left transition group"
              >
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-teal-900">Dr. Swaminathan</p>
                  <span className="text-[10px] text-teal-600 font-semibold opacity-0 group-hover:opacity-100 transition">
                    Fill
                  </span>
                </div>
                <p className="text-[10px] text-teal-700">Tele-Ophthalmologist</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
