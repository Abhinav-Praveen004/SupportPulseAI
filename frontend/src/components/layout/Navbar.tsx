import React, { useState } from 'react';
import { Activity, ChevronDown, LogOut, Moon, Shield, Sun, User as UserIcon, Users } from 'lucide-react';
import { useAuth } from '../../lib/authContext';
import { useSSE } from '../../lib/useSSE';
import { useTheme } from '../../lib/themeContext';

export const Navbar: React.FC = () => {
  const { user, switchRole, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { status: sseStatus } = useSSE();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const roles = [
    { key: 'admin', label: 'Admin (Full Access)', pass: 'admin123', role: 'admin' },
    { key: 'manager', label: 'Manager (Supervisor)', pass: 'manager123', role: 'manager' },
    { key: 'agent', label: 'Agent (Triage/Resolver)', pass: 'agent123', role: 'agent' },
  ] as const;

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

      {/* Right controls: SSE status, Theme Toggle, Role Switcher */}
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

        {/* Role Switcher & User Profile */}
        <div className="relative border-l border-slate-200 dark:border-slate-800 pl-3">
          <button
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
            className="flex items-center gap-2 px-2 py-1 rounded-md text-xs font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Switch Demo Role"
          >
            <div className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-2xs uppercase">
              {user ? user.username.slice(0, 2) : 'AD'}
            </div>
            <div className="text-left hidden md:block">
              <div className="font-semibold text-slate-800 dark:text-slate-200 leading-none">
                {user ? user.full_name : 'System Administrator'}
              </div>
              <div className="text-2xs text-slate-400 capitalize flex items-center gap-1 mt-0.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {user ? user.role : 'admin'} (Click to switch)
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Dropdown Menu */}
          {roleMenuOpen && (
            <div
              className="absolute right-0 mt-2 w-64 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
              onMouseLeave={() => setRoleMenuOpen(false)}
            >
              <div className="px-3 py-1.5 text-2xs uppercase font-bold text-slate-400 tracking-wider">
                Switch Demo Account
              </div>
              {roles.map((r) => {
                const isActive = user?.username === r.key;
                return (
                  <button
                    key={r.key}
                    onClick={async () => {
                      await switchRole(r.key);
                      setRoleMenuOpen(false);
                      window.location.reload();
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors ${
                      isActive ? 'bg-brand-50/50 dark:bg-brand-950/40 text-brand-600 font-semibold' : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-medium">{r.label}</div>
                      <div className="text-2xs text-slate-400 font-mono">user: {r.key} | pass: {r.pass}</div>
                    </div>
                    {isActive && (
                      <span className="text-2xs font-bold text-brand-600 bg-brand-100 dark:bg-brand-900/60 px-1.5 py-0.5 rounded">
                        Active
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
