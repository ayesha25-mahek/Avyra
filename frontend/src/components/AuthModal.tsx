import React, { useState } from 'react';
import { X, Lock, Mail, Eye, EyeOff, Loader2, AlertCircle, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { loginUser } from '@/lib/authApi';
import type { UserProfile } from '@/types/auth';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
  initialMode?: 'signin' | 'login';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialMode = 'login',
}) => {
  const [mode, setMode] = useState<'signin' | 'login'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError('Please enter your authorized email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setIsLoading(true);
    try {
      const resp = await loginUser(email, password);
      setIsLoading(false);
      onSuccess(resp.user);
      onClose();
    } catch (err: unknown) {
      setIsLoading(false);
      const message = err instanceof Error ? err.message : 'Invalid email or password.';
      setError(message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-md rounded-md border border-[#1E2F26] bg-[#0E1712] p-6 shadow-2xl font-serif text-gray-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-sm text-gray-400 hover:text-white hover:bg-[#0c1e14] transition-colors"
          title="Close authentication modal"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="space-y-2 text-center pb-5 border-b border-[#142B1F]">
          <div className="w-10 h-10 rounded-md bg-[#00D084]/15 border border-[#00D084]/30 flex items-center justify-center mx-auto">
            <ShieldCheck className="w-5 h-5 text-[#00D084]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-wide font-serif">
              Avyra Autonomous Workspace
            </h2>
            <p className="text-xs text-gray-400 font-serif mt-1">
              Role-Gated Access Control & Intelligence Portal
            </p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex rounded-sm bg-[#06110A] border border-[#142B1F] p-1 mt-4">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-sm transition-all ${
                mode === 'login'
                  ? 'bg-[#00D084] text-black shadow-sm font-bold'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Log In
            </button>
            <button
              type="button"
              onClick={() => { setMode('signin'); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-sm transition-all ${
                mode === 'signin'
                  ? 'bg-[#00D084] text-black shadow-sm font-bold'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mt-4 p-3 rounded-sm bg-red-950/40 border border-red-800/40 flex items-start gap-2.5 text-xs text-red-300 font-serif">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{error}</p>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4 font-serif">
          {/* Email Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-[#00D084]" />
              Authorized Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. ayeshamahek2509@gmail.com"
              required
              disabled={isLoading}
              className="w-full px-3.5 py-2.5 rounded-sm bg-[#06110A] border-[#1E2F26] text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#00D084] transition-colors"
            />
          </div>

          {/* Password Input (Masked) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#00D084]" />
                Password
              </span>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-[11px] text-gray-400 hover:text-[#00D084] flex items-center gap-1 focus:outline-none"
              >
                {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter authorized password"
                required
                disabled={isLoading}
                className="w-full px-3.5 py-2.5 rounded-sm bg-[#06110A] border-[#1E2F26] text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#00D084] transition-colors pr-10"
              />
            </div>
            <div className="mt-2 text-xs"><a href="/reset-password" className="text-gray-400 hover:text-[#00E599]">Forgot password?</a></div>

            {/* 1-Click Role Login Shortcuts for Demo/Evaluation */}
            <div className="pt-2">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block mb-1.5 font-bold">
                1-Click Industrial Role Login:
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[11px] font-mono">
                <button
                  type="button"
                  onClick={() => { setEmail('admin@avyara.internal'); setPassword('adminpass'); }}
                  className="px-2 py-1 rounded bg-[#143324] hover:bg-[#1E4D36] text-[#00E599] border border-[#23573E] truncate text-left"
                >
                  Admin (All)
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('engineer@avyara.internal'); setPassword('engineerpass'); }}
                  className="px-2 py-1 rounded bg-[#0F293D] hover:bg-[#163D5C] text-[#38BDF8] border border-[#1E4E6D] truncate text-left"
                >
                  Plant Engineer
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('inspector@avyara.internal'); setPassword('inspectorpass'); }}
                  className="px-2 py-1 rounded bg-[#33220A] hover:bg-[#4D330F] text-[#FBBF24] border border-[#61451B] truncate text-left"
                >
                  Field Inspector
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('analyst@avyara.internal'); setPassword('analystpass'); }}
                  className="px-2 py-1 rounded bg-[#271533] hover:bg-[#3D2150] text-[#C084FC] border border-[#4D2863] truncate text-left"
                >
                  Data Analyst
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('manager@avyara.internal'); setPassword('managerpass'); }}
                  className="px-2 py-1 rounded bg-[#163827] hover:bg-[#1E4D36] text-[#74C69D] border border-[#1E4D36] truncate text-left"
                >
                  Asset Manager
                </button>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 mt-2 rounded-sm bg-[#00D084] hover:bg-[#05E594] text-black font-bold text-sm tracking-wide transition-all font-serif flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                Verifying Credentials…
              </>
            ) : mode === 'login' ? (
              'Log In to Avyra'
            ) : (
              'Sign In with Authorized Account'
            )}
          </Button>
        </form>

        {/* Security / Role Notice */}
        <div className="mt-5 pt-4 border-t border-[#142B1F] text-center">
          <p className="text-[11px] text-gray-500 leading-relaxed font-serif">
            Protected by Supabase PBKDF2/SHA-256 Authentication & Role-Level Security (RLS).
            Access is provisioned exclusively to designated Super Admin, Technical Lead, PR Lead, and Team members.
          </p>
        </div>
      </div>
    </div>
  );
};
