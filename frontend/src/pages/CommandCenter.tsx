import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Flame,
  Frown,
  Inbox,
  ShieldCheck,
  TrendingUp,
  UserCheck,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { RiskBadge } from '../components/common/RiskBadge';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { Skeleton } from '../components/common/Skeleton';
import { Drawer } from '../components/common/Drawer';
import { Button } from '../components/common/Button';
import { Ticket } from '../lib/types';
import { TicketDetailContent } from './TicketDetail';

export const CommandCenter: React.FC = () => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);

  const { data: summary, isLoading, refetch } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => api.getDashboardSummary(),
    refetchInterval: 15000,
  });

  const { data: selectedTicket, isLoading: isLoadingTicket } = useQuery({
    queryKey: ['ticket', selectedTicketId],
    queryFn: () => (selectedTicketId ? api.getTicket(selectedTicketId) : null),
    enabled: !!selectedTicketId,
  });

  const handleAckAlert = async (alertId: number) => {
    try {
      await api.acknowledgeAlert(alertId);
      refetch();
    } catch {
      // Ignore
    }
  };

  if (isLoading || !summary) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Skeleton className="h-24 w-full" count={5} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-80 w-full" count={3} />
        </div>
      </div>
    );
  }

  const kpis = [
    {
      label: 'Open Backlog',
      value: summary.open_tickets,
      total: summary.total_tickets,
      icon: Inbox,
      color: 'text-blue-500',
      desc: 'Active tickets in queue',
    },
    {
      label: 'High & Critical Risk',
      value: summary.high_critical_risk_count,
      icon: Flame,
      color: 'text-rose-500',
      desc: 'At imminent breach risk',
    },
    {
      label: 'Breaches in Next 4h',
      value: summary.predicted_breaches_next_4h,
      icon: Clock,
      color: 'text-orange-500',
      desc: 'Predicted SLA expirations',
    },
    {
      label: 'Average Friction',
      value: summary.avg_friction_score.toFixed(1),
      suffix: '/100',
      icon: Frown,
      color: 'text-amber-500',
      desc: 'Requester agitation index',
    },
    {
      label: 'Auto-Triaged',
      value: `${summary.auto_triaged_share_pct.toFixed(0)}%`,
      icon: UserCheck,
      color: 'text-emerald-500',
      desc: 'Confidence >= threshold',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Command Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time proactive IT service desk telemetry and early warning radar.
          </p>
        </div>
      </div>

      {/* KPI Metric Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <Card key={idx} className="relative overflow-hidden">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {kpi.label}
                </span>
                <Icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 tabular-nums font-mono">
                  {kpi.value}
                </span>
                {kpi.suffix && (
                  <span className="text-xs text-slate-400 font-mono">{kpi.suffix}</span>
                )}
              </div>
              <p className="text-2xs text-slate-400 dark:text-slate-500 mt-1">
                {kpi.desc}
              </p>
            </Card>
          );
        })}
      </div>

      {/* Main Grid: Live Risk Queue & Volume Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live At-Risk Queue */}
        <Card
          className="lg:col-span-2"
          title="Live High-Risk Queue"
          subtitle="Top open tickets ranked by proactive ML breach probability"
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => (window.location.href = '/sla-risk')}
            >
              Full Forecast <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          }
        >
          {summary.top_at_risk_tickets.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No tickets currently at high SLA risk.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-medium">
                    <th className="pb-3 pl-2">Ticket ID</th>
                    <th className="pb-3">Subject</th>
                    <th className="pb-3">Priority</th>
                    <th className="pb-3">Risk Level</th>
                    <th className="pb-3">Friction</th>
                    <th className="pb-3 pr-2 text-right">Est. Time Remaining</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                  {summary.top_at_risk_tickets.map((t) => (
                    <tr
                      key={t.ticket_id}
                      onClick={() => setSelectedTicketId(t.ticket_id)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 pl-2 font-mono font-medium text-brand-600 dark:text-brand-400">
                        {t.ticket_id}
                      </td>
                      <td className="py-3 font-medium text-slate-900 dark:text-slate-100 max-w-xs truncate">
                        {t.subject}
                      </td>
                      <td className="py-3">
                        <PriorityBadge priority={t.priority as any} />
                      </td>
                      <td className="py-3">
                        <RiskBadge band={t.risk_band as any} probability={t.probability} size="sm" />
                      </td>
                      <td className="py-3">
                        <FrictionBadge band="Uneasy" score={t.friction_score} size="sm" />
                      </td>
                      <td className="py-3 pr-2 text-right font-mono tabular-nums text-slate-600 dark:text-slate-400">
                        {t.estimated_minutes > 0 ? `${t.estimated_minutes.toFixed(0)}m` : 'Overtime'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Live Alerts Feed */}
        <Card
          title="Proactive Alerts Feed"
          subtitle="Real-time notifications on risk escalation"
          className="flex flex-col"
        >
          {summary.recent_alerts.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No recent alerts raised.
            </div>
          ) : (
            <div className="space-y-3 overflow-y-auto max-h-[340px] pr-1">
              {summary.recent_alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border text-xs transition-colors ${
                    alert.acknowledged
                      ? 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 opacity-60'
                      : 'bg-rose-50/60 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                      {alert.ticket_id}
                    </span>
                    <span className="text-2xs text-slate-400">{alert.created_at.slice(11, 19)}</span>
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-snug mb-2">
                    {alert.message}
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <RiskBadge band={alert.current_band as any} size="sm" showProbability={false} />
                    {!alert.acknowledged ? (
                      <button
                        onClick={() => handleAckAlert(alert.id)}
                        className="text-2xs font-medium text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" /> Acknowledge
                      </button>
                    ) : (
                      <span className="text-2xs text-slate-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Acknowledged
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Secondary Grid: Volume Trend and Category Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 14-Day Ticket Volume Chart */}
        <Card
          className="lg:col-span-2"
          title="Daily Ticket Volume & Breach Trajectory (Last 14 Days)"
          subtitle="Total ingest vs breached tickets"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary.volume_by_day} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorBreached" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Area type="monotone" dataKey="tickets" stroke="#3b82f6" fillOpacity={1} fill="url(#colorTickets)" name="Total Tickets" />
                <Area type="monotone" dataKey="breached" stroke="#ef4444" fillOpacity={1} fill="url(#colorBreached)" name="Breached" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Category Breakdown */}
        <Card
          title="Open Tickets by Category"
          subtitle="Distribution of current active workload"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={summary.category_distribution.slice(0, 6)}
                margin={{ top: 5, right: 15, left: 35, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis dataKey="category" type="category" tick={{ fontSize: 10, fill: '#94a3b8' }} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Tickets" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Ticket Detail Drawer */}
      <Drawer
        isOpen={!!selectedTicketId}
        onClose={() => setSelectedTicketId(null)}
        title={selectedTicket ? selectedTicket.ticket_id : 'Loading Ticket...'}
        subtitle={selectedTicket ? selectedTicket.subject : ''}
      >
        {isLoadingTicket || !selectedTicket ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" count={4} />
          </div>
        ) : (
          <TicketDetailContent ticket={selectedTicket} onUpdated={refetch} />
        )}
      </Drawer>
    </div>
  );
};
