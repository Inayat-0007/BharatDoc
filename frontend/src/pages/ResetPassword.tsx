import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Password strength indicator
  const getPasswordStrength = (pw: string): { level: number; label: string; color: string } => {
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[a-z]/.test(pw)) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pw)) score++;

    if (score <= 2) return { level: score, label: 'Weak', color: 'bg-red-500' };
    if (score <= 3) return { level: score, label: 'Fair', color: 'bg-amber-500' };
    if (score <= 4) return { level: score, label: 'Good', color: 'bg-blue-500' };
    return { level: score, label: 'Strong', color: 'bg-green-500' };
  };

  const strength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
      return;
    }

    setLoading(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password');
      }

      setSuccess(true);
      // Auto-redirect to login after 3 seconds
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">Invalid Reset Link</h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Link
              to="/forgot-password"
              className="inline-flex items-center justify-center px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold text-sm"
            >
              Request New Reset Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
            Set New Password
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200 dark:border-slate-700 p-8">
          {success ? (
            <div className="text-center animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Password Reset Successful!
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                Your password has been updated. All previous sessions have been invalidated for security.
              </p>
              <p className="text-violet-600 dark:text-violet-400 text-sm font-medium">
                Redirecting to login...
              </p>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Create a new password
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
                Your new password must contain at least 8 characters, including uppercase, lowercase, a number, and a special character.
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    New Password
                  </label>
                  <input
                    id="reset-password"
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={8}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
                    placeholder="••••••••"
                  />
                  {/* Password Strength Meter */}
                  {password && (
                    <div className="mt-2">
                      <div className="flex gap-1 mb-1">
                        {[1, 2, 3, 4, 5].map(i => (
                          <div
                            key={i}
                            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                              i <= strength.level ? strength.color : 'bg-slate-200 dark:bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                      <p className={`text-xs ${
                        strength.level <= 2 ? 'text-red-500' :
                        strength.level <= 3 ? 'text-amber-500' :
                        strength.level <= 4 ? 'text-blue-500' : 'text-green-500'
                      }`}>
                        Strength: {strength.label}
                      </p>
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Confirm Password
                  </label>
                  <input
                    id="reset-confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    required
                    minLength={8}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
                    placeholder="••••••••"
                  />
                  {confirmPassword && password !== confirmPassword && (
                    <p className="mt-1 text-xs text-red-500">Passwords do not match</p>
                  )}
                </div>
                <button
                  id="reset-submit"
                  type="submit"
                  disabled={loading || password !== confirmPassword}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
