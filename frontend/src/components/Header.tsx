import React from 'react';
import { LogIn, LogOut, LayoutDashboard } from 'lucide-react';
import {
  ROLE_DISPLAY_NAMES, ROLE_BADGE_COLORS,
  type UserProfile
} from '@/types/auth';

interface HeaderProps {
  user: UserProfile | null;
  activeView: 'landing' | 'studio' | 'dashboard';
  onOpenAuth: (mode?: 'signin' | 'login') => void;
  onSwitchView: (view: 'landing' | 'studio' | 'dashboard') => void;
  onSignOut: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  activeView,
  onOpenAuth,
  onSwitchView,
  onSignOut,
}) => {
  const isSuperAdmin = user?.role === 'super_admin';
  const badgeStyle = user ? (ROLE_BADGE_COLORS[user.role] || ROLE_BADGE_COLORS.technical_team) : null;

  return (
    <header className="sticky top-0 z-50 border-b border-[#1A2820] bg-[#0A0F0D]/95 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Left: Clean Brand Wordmark */}
        <div className="flex items-center gap-10">
          <button
            type="button"
            onClick={() => onSwitchView(user ? 'studio' : 'landing')}
            className="flex items-center gap-2 group text-left"
          >
            <div className="w-7 h-7 rounded-lg bg-[#143324] border border-[#23533B] flex items-center justify-center text-white font-bold text-sm tracking-tight">
              A
            </div>
            <span className="font-heading text-lg font-bold text-white tracking-tight">
              Avyra
            </span>
          </button>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            <button
              type="button"
              onClick={() => onSwitchView('landing')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                activeView === 'landing'
                  ? 'text-white bg-[#131F19]'
                  : 'text-[#9EB3A8] hover:text-white hover:bg-[#0E1712]'
              }`}
            >
              Product
            </button>

            {user && (
              <button
                type="button"
                onClick={() => onSwitchView('studio')}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  activeView === 'studio'
                    ? 'text-white bg-[#131F19]'
                    : 'text-[#9EB3A8] hover:text-white hover:bg-[#0E1712]'
                }`}
              >
                Workspace
              </button>
            )}

            {user && (
              <button
                type="button"
                onClick={() => onSwitchView('dashboard')}
                className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
                  activeView === 'dashboard'
                    ? 'text-white bg-[#131F19]'
                    : 'text-[#9EB3A8] hover:text-white hover:bg-[#0E1712]'
                }`}
              >
                <LayoutDashboard className="w-4 h-4 text-[#52B788]" />
                <span>{isSuperAdmin ? 'Admin Center' : 'Operations'}</span>
              </button>
            )}
          </nav>
        </div>

        {/* Right: Auth Controls */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3">
              {/* User Pill */}
              <div className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#111A15] border border-[#1E2F26] text-xs">
                <span className="text-[#DCE6E0] truncate max-w-[160px] font-medium">{user.email}</span>
                {badgeStyle && (
                  <span className={`text-[10px] font-medium px-2.5 py-0.5 rounded-full border ${badgeStyle.bg} ${badgeStyle.text} ${badgeStyle.border}`}>
                    {ROLE_DISPLAY_NAMES[user.role]}
                  </span>
                )}
              </div>

              {/* View Switch Button */}
              <button
                type="button"
                onClick={() => onSwitchView(activeView === 'dashboard' ? 'studio' : 'dashboard')}
                className="px-3.5 py-1.5 rounded-full border border-[#23573E] bg-[#111A15] text-[#DCE6E0] text-xs font-medium hover:bg-[#18261F] hover:text-[#52B788] hover:border-[#52B788]/60 transition-all active:scale-[0.98]"
              >
                {activeView === 'dashboard' ? 'Open Workspace' : isSuperAdmin ? 'Admin Center' : 'Dashboard'}
              </button>

              {/* Sign Out */}
              <button
                type="button"
                onClick={onSignOut}
                title="Sign Out"
                className="p-2 rounded-full border border-[#22332A] bg-[#111A15] text-[#9EB3A8] hover:text-red-400 hover:border-red-900/40 hover:bg-red-950/20 transition-all active:scale-[0.98]"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onOpenAuth('signin')}
                className="px-4 py-1.5 rounded-full text-xs font-medium text-[#9EB3A8] hover:text-white transition-colors"
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => onOpenAuth('login')}
                className="steep-btn-filled text-xs py-1.5 px-4"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Log In</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
