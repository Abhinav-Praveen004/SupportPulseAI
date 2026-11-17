import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  Clock,
  Flame,
  Info,
  Sliders,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { RiskBadge } from '../components/common/RiskBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { Button } from '../components/common/Button';
import { Drawer } from '../components/common/Drawer';
import { Skeleton } from '../components/common/Skeleton';
import { TicketDetailContent } from './TicketDetail';

export const SLARiskForecast: React.FC = () => {
  const [sliderThreshold, setSliderThreshold] = useState<number>(0.35);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);

  const { data: forecast, isLoading, refetch } = useQuery({
    queryKey: ['risk_forecast', sliderThreshold],
    queryFn: () => api.getRiskForecast(sliderThreshold),
    refetchInterval: 20000,
  });

  const { data: selectedTicket, isLoading: isLoadingTicket } = useQuery({
    queryKey: ['ticket', selectedTicketId],
    queryFn: () => (selectedTicketId ? api.getTicket(selectedTicketId) : null),
    enabled: !!selectedTicketId,
  });

  if (isLoading || !forecast) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-64 w-full" count={2} />
      </div>
    );
  }

  // Calculate precision and recall estimate for current slider value
  const estimatedRecall = Math.max(50, Math.min(98, Math.round(95 - sliderThreshold * 55)));
  const estimatedPrecision = Math.max(40, Math.min(96, Math.round(50 + sliderThreshold * 50)));

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          SLA Risk Forecast
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Predictive multi-snapshot breach trajectory and team congestion heatmaps.
        </p>
      </div>

      {/* Threshold Slider and Precision/Recall Trade-Off Card */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-500" />
            <span>Proactive Alert Decision Threshold</span>
          </div>
        }
        subtitle="Tune threshold to balance early breach detection recall against agent alert fatigue"
      >
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1 max-w-xl">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-slate-500 font-medium">Alert Threshold</span>
                <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                  {(sliderThreshold * 100).toFixed(0)}% Probability
                </span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.85"
                step="0.05"
                value={sliderThreshold}
                onChange={(e) => setSliderThreshold(parseFloat(e.target.value))}
                className="w-full accent-brand-600 cursor-pointer h-2 bg-slate-200 dark:bg-slate-700 rounded-lg"
              />
              <div className="flex justify-between text-2xs text-slate-400 mt-1">
                <span>0.10 (High Sensitivity / Recall)</span>
                <span>0.50 (Balanced)</span>
                <span>0.85 (High Precision)</span>
              </div>
            </div>

            {/* Dynamic Trade-off Indicators */}
            <div className="flex gap-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <div className="text-center px-2">
                <span className="text-2xs text-slate-400 block mb-0.5">Est. Recall</span>
                <span className="text-base font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {estimatedRecall}%
                </span>
              </div>
              <div className="text-center px-2 border-l border-slate-200 dark:border-slate-700">
                <span className="text-2xs text-slate-400 block mb-0.5">Est. Precision</span>
                <span className="text-base font-bold font-mono text-blue-600 dark:text-blue-400">
                  {estimatedPrecision}%
                </span>
              </div>
              <div className="text-center px-2 border-l border-slate-200 dark:border-slate-700">
                <span className="text-2xs text-slate-400 block mb-0.5">Flagged Tickets</span>
                <span className="text-base font-bold font-mono text-rose-600 dark:text-rose-400">
                  {forecast.total_at_risk}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Team x Hour Congestion Heatmap */}
      <Card
        title="Team x Hour Congestion Matrix"
        subtitle="Open at-risk ticket distribution by creation hour (00-23h UTC) and assigned team"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-center border-collapse text-2xs font-mono min-w-[760px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                <th className="text-left font-sans text-xs font-semibold py-2 pl-2 w-44">Team</th>
                {Array.from({ length: 24 }, (_, h) => (
                  <th key={h} className="py-2 px-0.5 font-normal text-slate-400">
                    {h.toString().padStart(2, '0')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40 text-xs">
              {forecast.team_hour_heatmap.map((row) => (
                <tr key={row.team} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                  <td className="text-left font-sans font-medium text-slate-800 dark:text-slate-200 py-2.5 pl-2 truncate">
                    {row.team}
                  </td>
                  {Array.from({ length: 24 }, (_, h) => {
                    const count = row.hours[h.toString()] || 0;
                    const bgClass =
                      count === 0
                        ? 'bg-slate-100/60 dark:bg-slate-800/20 text-slate-400/30'
                        : count < 3
                        ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold'
                        : count < 6
                        ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 font-bold'
                        : 'bg-rose-500/20 dark:bg-rose-950/80 text-rose-700 dark:text-rose-300 font-bold border border-rose-500/30';

                    return (
                      <td key={h} className="p-0.5">
                        <div
                          className={`h-7 rounded flex items-center justify-center text-2xs select-none ${bgClass}`}
                          title={`${row.team} at ${h.toString().padStart(2, '0')}:00 UTC - ${count} at-risk tickets`}
                        >
                          {count > 0 ? count : '-'}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          {/* Heatmap Legend */}
          <div className="flex items-center justify-end gap-4 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-2xs text-slate-400">
            <span>Congestion Level:</span>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-slate-100/60 dark:bg-slate-800/20 inline-block border border-slate-300 dark:border-slate-700" />
              <span>0 (Quiet)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-blue-100 dark:bg-blue-950/60 inline-block" />
              <span>1-2 (Normal)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-amber-100 dark:bg-amber-950/60 inline-block" />
              <span>3-5 (Warning)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-rose-500/20 dark:bg-rose-950/80 border border-rose-500/30 inline-block" />
              <span>6+ (High Surge)</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Ranked At-Risk Table */}
      <Card
        title={`Ranked At-Risk Tickets (${forecast.total_at_risk} tickets)`}
        subtitle="Tickets exceeding alert threshold, sorted by breach probability"
      >
        {forecast.at_risk_tickets.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No open tickets exceed the current threshold ({sliderThreshold * 100}%).
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-medium">
                  <th className="pb-3 pl-2">Ticket ID</th>
                  <th className="pb-3">Subject</th>
                  <th className="pb-3">Category</th>
                  <th className="pb-3">Priority</th>
                  <th className="pb-3">Assigned Team</th>
                  <th className="pb-3">Breach Probability</th>
                  <th className="pb-3 pr-2 text-right">Est. Time Remaining</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {forecast.at_risk_tickets.map((t) => (
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
                    <td className="py-3 text-slate-600 dark:text-slate-300">{t.category}</td>
                    <td className="py-3">
                      <PriorityBadge priority={t.priority as any} />
                    </td>
                    <td className="py-3 text-slate-600 dark:text-slate-300">{t.assigned_team}</td>
                    <td className="py-3">
                      <RiskBadge band={t.sla_risk_band as any} probability={t.sla_breach_probability} size="sm" />
                    </td>
                    <td className="py-3 pr-2 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300">
                      {t.estimated_minutes_to_breach > 0
                        ? `${t.estimated_minutes_to_breach.toFixed(0)}m`
                        : 'Breached'}
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
