import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided. Please check your email for the correct link.');
      return;
    }

    const verifyEmail = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || '/api';
        const response = await fetch(`${apiUrl}/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage(data.message || 'Email verified successfully!');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed. The link may have expired.');
        }
      } catch {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verifyEmail();
  }, [token]);

  const handleResend = async () => {
    // This is a simplified resend — in reality, the user would need to provide their email.
    // For UX, we show a link to the login page where they can request a new verification.
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-700 mb-4 shadow-lg shadow-violet-500/25">
            <span className="text-2xl text-white font-bold">B</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            BharatDoc
          </h1>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200 dark:border-slate-700 p-8 text-center">
          {status === 'loading' && (
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-violet-100 dark:bg-violet-900/30 mb-4">
                <svg className="w-8 h-8 text-violet-600 dark:text-violet-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Verifying your email...
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                Please wait while we confirm your email address.
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Email Verified! ✅
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                {message}
              </p>
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-8 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all duration-200"
              >
                Sign In Now →
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
                <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Verification Failed
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                {message}
              </p>
              <div className="space-y-3">
                <Link
                  to="/login"
                  className="block w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold shadow-lg shadow-violet-500/25 transition-all duration-200 text-center"
                >
                  Go to Login
                </Link>
                <p className="text-xs text-slate-400">
                  You can request a new verification email from the login page.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
