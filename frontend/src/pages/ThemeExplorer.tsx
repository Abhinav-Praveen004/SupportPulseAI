import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  Compass,
  Flame,
  Info,
  Layers,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  ResponsiveContainer,
} from 'recharts';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Skeleton } from '../components/common/Skeleton';
import { Drawer } from '../components/common/Drawer';
import { TicketDetailContent } from './TicketDetail';
import { ThemeItem } from '../lib/types';

export const ThemeExplorer: React.FC = () => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: themesData, isLoading, refetch } = useQuery({
    queryKey: ['themes'],
    queryFn: () => api.getThemes(),
  });

  const { data: selectedTicket } = useQuery({
    queryKey: ['ticket', selectedTicketId],
    queryFn: () => (selectedTicketId ? api.getTicket(selectedTicketId) : null),
    enabled: !!selectedTicketId,
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.refreshThemes();
      refetch();
    } catch {
      // Ignore
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading || !themesData) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 w-full" count={6} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Theme Explorer
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Unsupervised topic modeling (TF-IDF + NMF) and 7-day volume spike anomaly detection.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefreshing}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Re-discover Themes
          </Button>
        </div>
      </div>

      {/* Cluster Sanity Check Banner */}
      <div className="p-4 rounded-lg bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 text-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-blue-900 dark:text-blue-200">
          <Info className="w-4 h-4 text-blue-500 shrink-0" />
          <span>
            <strong>Unsupervised Clustering Sanity Check:</strong> NMI ={' '}
            <span className="font-mono font-bold">{themesData.nmi_sanity_score.toFixed(4)}</span> | ARI ={' '}
            <span className="font-mono font-bold">{themesData.ari_sanity_score.toFixed(4)}</span> against hidden
            categories. (Note: Post-hoc validation metric only; zero supervised training leakage).
          </span>
        </div>
        <div className="flex items-center gap-3 font-mono text-2xs text-slate-500">
          <span>Themes: {themesData.total_themes}</span>
          <span>•</span>
          <span className="text-rose-600 dark:text-rose-400 font-bold">
            Emerging Anomalies: {themesData.emerging_count}
          </span>
        </div>
      </div>

      {/* Theme Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {themesData.themes.map((theme: ThemeItem) => {
          const sparklineData = theme.weekly_trend.map((cnt, i) => ({ week: `W${i + 1}`, count: cnt }));

          return (
            <Card
              key={theme.id}
              className={`flex flex-col justify-between transition-all duration-200 ${
                theme.is_emerging
                  ? 'ring-2 ring-rose-500 border-rose-300 dark:border-rose-800 bg-rose-50/20 dark:bg-rose-950/10'
                  : ''
              }`}
            >
              <div>
                {/* Header & Emerging Badge */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <span className="text-2xs font-mono text-slate-400 block mb-0.5">
                      Theme #{theme.id} • {theme.ticket_count} tickets
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-snug">
                      {theme.label}
                    </h3>
                  </div>

                  {theme.is_emerging && (
                    <span
                      className="inline-flex items-center gap-1 text-2xs font-bold px-2 py-0.5 rounded-full bg-rose-500 text-white shadow-sm animate-pulse shrink-0"
                      title={`Volume z-score: +${theme.z_score} standard deviations over prior 28 days`}
                    >
                      <Flame className="w-3 h-3" /> EMERGING (+{theme.z_score}σ)
                    </span>
                  )}
                </div>

                {/* Top N-grams / Keywords */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {theme.top_terms.map((term, i) => (
                    <span
                      key={i}
                      className="text-2xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                    >
                      {term}
                    </span>
                  ))}
                </div>

                {/* 8-Week Trend Sparkline */}
                <div className="mb-4">
                  <div className="flex justify-between text-2xs text-slate-400 mb-1">
                    <span>8-Week Volume Trend</span>
                    <span className="font-mono">
                      Recent: {theme.weekly_trend[theme.weekly_trend.length - 1]} / week
                    </span>
                  </div>
                  <div className="h-14 w-full bg-slate-50 dark:bg-slate-950/60 rounded p-1 border border-slate-100 dark:border-slate-800">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={sparklineData}>
                        <defs>
                          <linearGradient id={`grad-${theme.id}`} x1="0" y1="0" x2="0" y2="1">
                            <stop
                              offset="5%"
                              stopColor={theme.is_emerging ? '#ef4444' : '#3b82f6'}
                              stopOpacity={0.4}
                            />
                            <stop
                              offset="95%"
                              stopColor={theme.is_emerging ? '#ef4444' : '#3b82f6'}
                              stopOpacity={0.0}
                            />
                          </linearGradient>
                        </defs>
                        <Area
                          type="monotone"
                          dataKey="count"
                          stroke={theme.is_emerging ? '#ef4444' : '#3b82f6'}
                          strokeWidth={1.5}
                          fillOpacity={1}
                          fill={`url(#grad-${theme.id})`}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Representative Tickets */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80">
                <span className="text-2xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                  Representative Exemplars
                </span>
                <div className="space-y-1.5">
                  {theme.representative_tickets.map((rep) => (
                    <div
                      key={rep.ticket_id}
                      onClick={() => setSelectedTicketId(rep.ticket_id)}
                      className="text-xs p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800/60 cursor-pointer transition-colors flex items-center justify-between"
                    >
                      <span className="font-mono font-medium text-brand-600 dark:text-brand-400 text-2xs">
                        {rep.ticket_id}
                      </span>
                      <span className="truncate max-w-[190px] text-slate-700 dark:text-slate-300 text-2xs ml-2">
                        {rep.subject}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

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
