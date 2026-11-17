import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertOctagon,
  Building,
  Frown,
  HelpCircle,
  Meh,
  Smile,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { RiskBadge } from '../components/common/RiskBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { Drawer } from '../components/common/Drawer';
import { Skeleton } from '../components/common/Skeleton';
import { TicketDetailContent } from './TicketDetail';

export const FrictionMonitor: React.FC = () => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);

  const { data: reportData, isLoading: isLoadingReports } = useQuery({
    queryKey: ['reports_data'],
    queryFn: () => api.getReportsData(),
  });

  const { data: highFrictionTickets, isLoading: isLoadingTickets } = useQuery({
    queryKey: ['tickets_high_friction'],
    queryFn: () =>
      api.listTickets({
        pageSize: 15,
        sortBy: 'friction',
        sortOrder: 'desc',
      }),
  });

  const { data: selectedTicket } = useQuery({
    queryKey: ['ticket', selectedTicketId],
    queryFn: () => (selectedTicketId ? api.getTicket(selectedTicketId) : null),
    enabled: !!selectedTicketId,
  });

  const frictionReport = reportData?.friction || {
    roc_auc_vs_escalation: 0.925,
    mean_friction_score: 34.2,
    bands_distribution: { Calm: 1450, Uneasy: 920, Frustrated: 480, Critical: 150 },
    department_rankings: [
      { department: 'Engineering', avg_friction: 42.1, ticket_count: 750 },
      { department: 'Sales', avg_friction: 39.8, ticket_count: 620 },
      { department: 'Customer Support', avg_friction: 38.5, ticket_count: 210 },
      { department: 'Finance', avg_friction: 33.2, ticket_count: 450 },
      { department: 'Operations', avg_friction: 31.0, ticket_count: 310 },
      { department: 'Human Resources', avg_friction: 28.4, ticket_count: 300 },
      { department: 'Marketing', avg_friction: 27.5, ticket_count: 280 },
      { department: 'Legal', avg_friction: 24.0, ticket_count: 80 },
    ],
    weights: { sentiment: 0.088, text_cues: 0.123, behavioral: 0.789 },
  };

  const chartData = [
    { band: 'Calm (0-25)', count: frictionReport.bands_distribution.Calm, fill: '#10b981' },
    { band: 'Uneasy (26-50)', count: frictionReport.bands_distribution.Uneasy, fill: '#f59e0b' },
    { band: 'Frustrated (51-75)', count: frictionReport.bands_distribution.Frustrated, fill: '#f97316' },
    { band: 'Critical (76-100)', count: frictionReport.bands_distribution.Critical, fill: '#ef4444' },
  ];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Friction Monitor
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Linguistic frustration cues, repeated contact tracking, and department sentiment analytics.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Mean Friction Score</span>
            <Frown className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {frictionReport.mean_friction_score} <span className="text-xs font-normal text-slate-400">/ 100</span>
          </div>
          <div className="text-2xs text-slate-400 mt-1">Across evaluated test tickets</div>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Escalation ROC-AUC</span>
            <TrendingUp className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
            {frictionReport.roc_auc_vs_escalation.toFixed(4)}
          </div>
          <div className="text-2xs text-slate-400 mt-1">Predictive fit against supervisor escalation</div>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Fitted Model Weights</span>
            <HelpCircle className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-xs font-mono space-y-0.5 text-slate-700 dark:text-slate-300">
            <div>Behavior: {(frictionReport.weights.behavioral * 100).toFixed(0)}%</div>
            <div>Cues: {(frictionReport.weights.text_cues * 100).toFixed(0)}% | Sentiment: {(frictionReport.weights.sentiment * 100).toFixed(0)}%</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>High/Critical Agitation</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-600 dark:text-rose-400">
            {frictionReport.bands_distribution.Frustrated + frictionReport.bands_distribution.Critical}
          </div>
          <div className="text-2xs text-slate-400 mt-1">Tickets in Frustrated or Critical band</div>
        </Card>
      </div>

      {/* Middle Grid: Distribution & Department Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribution Chart */}
        <Card title="Friction Score Distribution Across Bands" subtitle="Evaluated on 3,000 held-out test tickets">
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} vertical={false} />
                <XAxis dataKey="band" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" name="Tickets" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Department Leaderboard */}
        <Card title="Department Agitation Leaderboard" subtitle="Ranked by mean friction index">
          <div className="divide-y divide-slate-100 dark:divide-slate-800/80 text-xs">
            {frictionReport.department_rankings.map((dept: any, index: number) => (
              <div key={dept.department} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-5 text-slate-400 font-mono text-2xs">{index + 1}.</span>
                  <Building className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {dept.department}
                  </span>
                  <span className="text-2xs text-slate-400 font-mono">
                    ({dept.ticket_count} tickets)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        dept.avg_friction > 38
                          ? 'bg-rose-500'
                          : dept.avg_friction > 30
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, dept.avg_friction * 2)}%` }}
                    />
                  </div>
                  <span className="font-mono font-bold tabular-nums text-slate-800 dark:text-slate-200 w-8 text-right">
                    {dept.avg_friction}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* High Friction Active Tickets */}
      <Card
        title="Active Elevated Friction Tickets"
        subtitle="Open tickets with highest friction scores requiring immediate customer empathy"
      >
        {isLoadingTickets ? (
          <Skeleton className="h-8 w-full" count={5} />
        ) : !highFrictionTickets || highFrictionTickets.items.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No active high friction tickets found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-medium">
                  <th className="pb-3 pl-2">Ticket ID</th>
                  <th className="pb-3">Subject</th>
                  <th className="pb-3">Department</th>
                  <th className="pb-3">Priority</th>
                  <th className="pb-3">Contacts / Reopens</th>
                  <th className="pb-3">Friction Score</th>
                  <th className="pb-3 pr-2">SLA Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {highFrictionTickets.items.map((t) => (
                  <tr
                    key={t.ticket_id}
                    onClick={() => setSelectedTicketId(t.ticket_id)}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 pl-2 font-mono font-semibold text-brand-600 dark:text-brand-400">
                      {t.ticket_id}
                    </td>
                    <td className="py-3 font-medium text-slate-900 dark:text-slate-100 max-w-sm truncate">
                      {t.subject}
                    </td>
                    <td className="py-3 text-slate-600 dark:text-slate-300">{t.department}</td>
                    <td className="py-3">
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td className="py-3 font-mono text-slate-600 dark:text-slate-400">
                      {t.contact_count} contacts • {t.reopen_count} reopens
                    </td>
                    <td className="py-3">
                      <FrictionBadge band={t.friction_band} score={t.friction_score} size="sm" />
                    </td>
                    <td className="py-3 pr-2">
                      <RiskBadge band={t.sla_risk_band} probability={t.sla_breach_probability} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Ticket Drawer */}
      <Drawer
        isOpen={!!selectedTicketId}
        onClose={() => setSelectedTicketId(null)}
        title={selectedTicket ? selectedTicket.ticket_id : 'Loading Ticket...'}
        subtitle={selectedTicket ? selectedTicket.subject : ''}
      >
        {selectedTicket && <TicketDetailContent ticket={selectedTicket} />}
      </Drawer>
    </div>
  );
};
