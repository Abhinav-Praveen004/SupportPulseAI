import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  AlertTriangle,
  Beaker,
  Compass,
  Cpu,
  Frown,
  Inbox,
  LayoutDashboard,
  Settings as SettingsIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Command Center', icon: LayoutDashboard },
  { to: '/triage', label: 'Triage Queue', icon: Inbox },
  { to: '/sla-risk', label: 'SLA Risk Forecast', icon: AlertTriangle },
  { to: '/friction', label: 'Friction Monitor', icon: Frown },
  { to: '/themes', label: 'Theme Explorer', icon: Compass },
  { to: '/playground', label: 'Playground', icon: Beaker },
  { to: '/models', label: 'Model Lab', icon: Cpu },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 flex flex-col shrink-0">
      <div className="p-4 flex-1">
        <div className="text-2xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-3 mb-2">
          Service Desk Intelligence
        </div>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 font-semibold border-l-2 border-brand-600'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Local deployment pill */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-2xs text-slate-500 dark:text-slate-400">
          <div className="font-semibold text-slate-700 dark:text-slate-300 mb-0.5">
            Single-Laptop Local
          </div>
          <div>CPU Inference | Zero Data Leakage</div>
        </div>
      </div>
    </aside>
  );
};
