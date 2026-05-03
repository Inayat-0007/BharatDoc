import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to send reset email');
      }

      setSubmitted(true);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
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
          <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
            Password Recovery
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200 dark:border-slate-700 p-8">
          {submitted ? (
            /* Success State */
            <div className="text-center animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Check Your Email
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mb-6">
                If an account with <strong className="text-slate-700 dark:text-slate-300">{email}</strong> exists,
                we've sent a password reset link. The link expires in <strong>15 minutes</strong>.
              </p>
              <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 text-xs mb-6">
                <strong>🔐 Security Tip:</strong> Don't share the reset link with anyone. BharatDoc staff will never ask for it.
              </div>
              <Link
                to="/login"
                className="inline-flex items-center text-violet-600 dark:text-violet-400 hover:underline font-medium text-sm"
              >
                ← Back to Login
              </Link>
            </div>
          ) : (
            /* Form State */
            <>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Forgot your password?
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                Enter the email address you registered with and we'll send you a secure reset link.
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Email Address
                  </label>
                  <input
                    id="forgot-email"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
                    placeholder="you@example.com"
                  />
                </div>
                <button
                  id="forgot-submit"
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center mt-6 text-sm text-slate-500 dark:text-slate-400">
          Remember your password?{' '}
          <Link to="/login" className="text-violet-600 dark:text-violet-400 hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;
