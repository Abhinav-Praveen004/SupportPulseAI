import React from 'react';
import { Activity, LogOut, Moon, Sun, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../lib/authContext';
import { useSSE } from '../../lib/useSSE';
import { useTheme } from '../../lib/themeContext';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { status: sseStatus } = useSSE();

  return (
    <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between px-6">
      {/* Brand logo & title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white font-bold shadow-sm">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-slate-900 dark:text-slate-100 tracking-tight text-base">
            SupportPulse
          </span>
          <span className="ml-1.5 text-xs font-semibold px-1.5 py-0.5 rounded bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
            AI
          </span>
        </div>
      </div>

      {/* Right controls: SSE status, Theme Toggle, User Profile */}
      <div className="flex items-center gap-4">
        {/* Real-time SSE indicator */}
        <div
          className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-400 select-none"
          title={`Real-time SSE updates: ${sseStatus}`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              sseStatus === 'connected'
                ? 'bg-emerald-500 animate-pulse'
                : sseStatus === 'connecting'
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
          />
          <span className="capitalize hidden sm:inline">{sseStatus}</span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label="Toggle color theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* User profile & logout */}
        {user ? (
          <div className="flex items-center gap-3 pl-2 border-l border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200 text-xs font-semibold">
                {user.username.slice(0, 2).toUpperCase()}
              </div>
              <div className="hidden md:block text-left">
                <div className="text-xs font-medium text-slate-900 dark:text-slate-100 leading-tight">
                  {user.full_name}
                </div>
                <div className="text-2xs text-slate-500 dark:text-slate-400 capitalize">
                  {user.role}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Sign out"
              aria-label="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center text-xs text-slate-500">
            <UserIcon className="w-4 h-4 mr-1" />
            Demo Mode
          </div>
        )}
      </div>
    </header>
  );
};
