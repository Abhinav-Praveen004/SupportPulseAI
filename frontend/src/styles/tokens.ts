/**
 * SupportPulse AI - Design Tokens
 * Follows Section 9 fallback design principles:
 * - Restrained palette with single primary brand accent
 * - Clear type scale with two font families (Inter for UI, JetBrains Mono for metrics/code)
 * - 4/8px consistent spacing grid
 * - WCAG AA compliant contrast ratios
 * - Multi-modal indicators (shape/icon + text + color) so risk/friction are never conveyed by color alone
 */

export const tokens = {
  typography: {
    fontSans: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontMono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    scale: {
      '2xs': '0.65rem', // 10.4px - badges, labels
      xs: '0.75rem',    // 12px - metadata, captions
      sm: '0.875rem',   // 14px - table data, secondary text
      base: '1rem',      // 16px - body text, inputs
      lg: '1.125rem',   // 18px - card titles, subtitles
      xl: '1.25rem',    // 20px - section headers
      '2xl': '1.5rem',  // 24px - page titles
      '3xl': '1.875rem',// 30px - KPI numbers
      '4xl': '2.25rem', // 36px - hero metrics
    },
  },
  spacing: {
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    8: '32px',
    10: '40px',
    12: '48px',
    16: '64px',
  },
  radii: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
    full: '9999px',
  },
  risk: {
    Low: {
      label: 'Low Risk',
      shortLabel: 'LOW',
      bgLight: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      bgDark: 'dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60',
      color: '#10b981',
      icon: 'ShieldCheck',
      description: 'Standard SLA trajectory; breach unlikely.',
    },
    Medium: {
      label: 'Medium Risk',
      shortLabel: 'MED',
      bgLight: 'bg-amber-50 text-amber-700 border-amber-200',
      bgDark: 'dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
      color: '#f59e0b',
      icon: 'AlertCircle',
      description: 'Moderate delay indicators; proactive check advised.',
    },
    High: {
      label: 'High Risk',
      shortLabel: 'HIGH',
      bgLight: 'bg-orange-50 text-orange-700 border-orange-200',
      bgDark: 'dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800/60',
      color: '#f97316',
      icon: 'AlertTriangle',
      description: 'Imminent breach trajectory; queue reprioritization needed.',
    },
    Critical: {
      label: 'Critical Risk',
      shortLabel: 'CRIT',
      bgLight: 'bg-rose-50 text-rose-700 border-rose-200',
      bgDark: 'dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60',
      color: '#ef4444',
      icon: 'Flame',
      description: 'Severe breach risk or already in overtime; immediate escalation required.',
    },
  },
  friction: {
    Calm: {
      label: 'Calm',
      range: '0-25',
      bgLight: 'bg-slate-100 text-slate-700 border-slate-200',
      bgDark: 'dark:bg-slate-800/60 dark:text-slate-300 dark:border-slate-700',
      color: '#94a3b8',
      icon: 'Smile',
      description: 'Polite, standard routine communication.',
    },
    Uneasy: {
      label: 'Uneasy',
      range: '26-50',
      bgLight: 'bg-amber-50 text-amber-700 border-amber-200',
      bgDark: 'dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
      color: '#f59e0b',
      icon: 'Meh',
      description: 'Mild impatience or initial repeated query.',
    },
    Frustrated: {
      label: 'Frustrated',
      range: '51-75',
      bgLight: 'bg-orange-50 text-orange-700 border-orange-200',
      bgDark: 'dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800/60',
      color: '#f97316',
      icon: 'Frown',
      description: 'Strong agitation, repeated contacts, blocking workflow.',
    },
    Critical: {
      label: 'Critical Friction',
      range: '76-100',
      bgLight: 'bg-rose-50 text-rose-700 border-rose-200',
      bgDark: 'dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60',
      color: '#ef4444',
      icon: 'AlertOctagon',
      description: 'Explicit escalation threats, aggressive language, business halt.',
    },
  },
  priorities: {
    P1: { label: 'P1 - Critical', targetHours: 4, badge: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
    P2: { label: 'P2 - High', targetHours: 8, badge: 'bg-orange-500/10 text-orange-500 border-orange-500/20' },
    P3: { label: 'P3 - Medium', targetHours: 24, badge: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
    P4: { label: 'P4 - Low', targetHours: 72, badge: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
  },
  categories: [
    'Password/Access',
    'Network/VPN',
    'Email',
    'Hardware',
    'Software Install',
    'Application Error',
    'Security Incident',
    'Printer',
    'Cloud/Infrastructure',
    'Service Request',
  ] as const,
  motion: {
    transitionFast: 'transition-all duration-150 ease-out motion-reduce:transition-none',
    transitionBase: 'transition-all duration-200 ease-out motion-reduce:transition-none',
  },
} as const;

export type RiskBand = keyof typeof tokens.risk;
export type FrictionBand = keyof typeof tokens.friction;
export type TicketPriority = keyof typeof tokens.priorities;
export type TicketCategory = (typeof tokens.categories)[number];
