import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  Frown,
  HelpCircle,
  RotateCcw,
  Send,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { RiskBadge } from '../components/common/RiskBadge';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { TermHighlighter } from '../components/common/TermHighlighter';
import { Button } from '../components/common/Button';
import { Skeleton } from '../components/common/Skeleton';
import { Ticket } from '../lib/types';
import { tokens } from '../styles/tokens';

interface TicketDetailContentProps {
  ticket: Ticket;
  onUpdated?: () => void;
}

export const TicketDetailContent: React.FC<TicketDetailContentProps> = ({ ticket, onUpdated }) => {
  const [correctedCat, setCorrectedCat] = useState(ticket.category);
  const [correctedPrio, setCorrectedPrio] = useState(ticket.priority);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  // Parse explanation data if available
  let explanations: any = {};
  if (ticket.explanation_data) {
    try {
      explanations = JSON.parse(ticket.explanation_data);
    } catch {
      // Ignore
    }
  }

  const topNgrams = explanations.top_contributing_ngrams || [];
  const riskDrivers = explanations.sla_top_drivers || [];
  const frictionBreakdown = explanations.friction_breakdown || {};
  const routingReasoning = explanations.routing_reasoning || ticket.routing_recommendation;

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.submitFeedback(ticket.ticket_id, {
        corrected_category: correctedCat,
        corrected_priority: correctedPrio,
        notes: notes || undefined,
      });
      setFeedbackSuccess(true);
      if (onUpdated) onUpdated();
    } catch (err: any) {
      alert(`Feedback submission failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Ticket Meta Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 text-xs">
        <div>
          <span className="text-slate-400">Requester: </span>
          <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
            {ticket.requester_id}
          </span>
          <span className="mx-2 text-slate-300 dark:text-slate-700">|</span>
          <span className="text-slate-400">Dept: </span>
          <span className="font-medium text-slate-700 dark:text-slate-300">{ticket.department}</span>
        </div>
        <div>
          <span className="text-slate-400">Channel: </span>
          <span className="font-medium capitalize text-slate-700 dark:text-slate-300">
            {ticket.channel}
          </span>
          <span className="mx-2 text-slate-300 dark:text-slate-700">|</span>
          <span className="text-slate-400">Created: </span>
          <span className="font-mono text-slate-600 dark:text-slate-400">{ticket.created_at}</span>
        </div>
      </div>

      {/* Ticket Description with Influential Terms Highlighted */}
      <Card title="Subject & Body" subtitle="Key influential n-grams contributing to classification highlighted">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">
          {ticket.subject}
        </h4>
        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded border border-slate-200 dark:border-slate-800/80 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
          <TermHighlighter text={ticket.body} terms={topNgrams} />
        </div>
      </Card>

      {/* M1: Classification & Explainability */}
      <Card title="M1 Classification Predictions & Confidence" subtitle="Word (1-2) + Character (3-5) Calibrated Linear Model">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-slate-500">Predicted Category</span>
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                {ticket.predicted_category || ticket.category}
              </span>
            </div>
            <ConfidenceBar
              confidence={ticket.category_confidence || 0.85}
              needsHumanTriage={ticket.needs_human_triage}
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-slate-500">Predicted Priority</span>
              <PriorityBadge priority={(ticket.predicted_priority || ticket.priority) as any} />
            </div>
            <ConfidenceBar confidence={ticket.priority_confidence || 0.80} />
          </div>
        </div>

        {/* Top N-grams feature contributions */}
        {topNgrams.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-2xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
              Top Contributing N-Grams
            </span>
            <div className="flex flex-wrap gap-2">
              {topNgrams.map((ng: any, idx: number) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-mono"
                >
                  <span>"{ng.ngram}"</span>
                  <span className="text-2xs text-brand-600 dark:text-brand-400 font-semibold tabular-nums">
                    +{ng.score.toFixed(3)}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* M3 & M4: SLA Risk and Friction Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* M3 SLA Risk */}
        <Card title="M3 SLA Risk Forecast" subtitle="Multi-snapshot HistGradientBoosting">
          <div className="flex items-center justify-between mb-3">
            <RiskBadge band={ticket.sla_risk_band} probability={ticket.sla_breach_probability} size="lg" />
            <div className="text-right">
              <span className="text-2xs text-slate-400 block">Est. Time Remaining</span>
              <span className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200">
                {ticket.estimated_minutes_to_breach !== undefined && ticket.estimated_minutes_to_breach > 0
                  ? `${ticket.estimated_minutes_to_breach.toFixed(0)} mins`
                  : 'Breached'}
              </span>
            </div>
          </div>

          {/* Counterfactual Drivers */}
          {riskDrivers.length > 0 && (
            <div className="space-y-1.5 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider block">
                Top Risk Drivers (Counterfactual Ablation)
              </span>
              {riskDrivers.map((driver: any, i: number) => (
                <div
                  key={i}
                  className="text-xs p-2 rounded bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-amber-900 dark:text-amber-200 flex items-center justify-between"
                >
                  <span>{driver.description}</span>
                  <span className="font-mono font-semibold">+{driver.impact_pct}%</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* M4 Friction Score */}
        <Card title="M4 Friction Score" subtitle="Sentiment + linguistic cues + behavioral signals">
          <div className="flex items-center justify-between mb-3">
            <FrictionBadge band={ticket.friction_band} score={ticket.friction_score} size="lg" />
            <div className="text-right">
              <span className="text-2xs text-slate-400 block">Behavioral Cues</span>
              <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
                {ticket.contact_count} contacts | {ticket.reopen_count} reopens
              </span>
            </div>
          </div>

          {/* Subscores breakdown */}
          <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-center">
            <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-slate-400 block">Sentiment</span>
              <span className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200">
                {frictionBreakdown.sentiment_subscore !== undefined ? `${frictionBreakdown.sentiment_subscore}` : '24'}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-slate-400 block">Text Cues</span>
              <span className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200">
                {frictionBreakdown.text_cues_subscore !== undefined ? `${frictionBreakdown.text_cues_subscore}` : '35'}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-slate-400 block">Behavioral</span>
              <span className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200">
                {frictionBreakdown.behavioral_subscore !== undefined ? `${frictionBreakdown.behavioral_subscore}` : '40'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* M2 Routing Recommendation */}
      <Card title="M2 Intelligent Routing" subtitle="Workload-balanced team assignment">
        <div className="p-3 rounded-lg bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 text-xs">
          <div className="font-semibold text-blue-900 dark:text-blue-200 mb-1">
            Assigned Team: {ticket.assigned_team}
          </div>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
            {routingReasoning}
          </p>
        </div>
      </Card>

      {/* M6 Agent Feedback & Override Controls */}
      <Card
        title="Agent Override & Retraining Feedback (M6)"
        subtitle="Correct model predictions to feed continuous offline retraining"
      >
        {feedbackSuccess ? (
          <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Override recorded! Added to candidate dataset for next retraining cycle.</span>
            </div>
            <button
              onClick={() => setFeedbackSuccess(false)}
              className="text-2xs underline hover:no-underline font-medium"
            >
              Edit Again
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmitFeedback} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
                  Category Override
                </label>
                <select
                  value={correctedCat}
                  onChange={(e) => setCorrectedCat(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                >
                  {tokens.categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
                  Priority Override
                </label>
                <select
                  value={correctedPrio}
                  onChange={(e) => setCorrectedPrio(e.target.value as any)}
                  className="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                >
                  {Object.keys(tokens.priorities).map((p) => (
                    <option key={p} value={p}>
                      {p} - {tokens.priorities[p as keyof typeof tokens.priorities].label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-1">
                Triage Notes (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Explain the rationale for this correction..."
                className="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="flex justify-end">
              <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
                <Send className="w-3.5 h-3.5 mr-1" /> Submit Override & Feed Retraining
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};

export const TicketDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: ticket, isLoading, refetch } = useQuery({
    queryKey: ['ticket', id],
    queryFn: () => (id ? api.getTicket(id) : null),
    enabled: !!id,
  });

  if (isLoading || !ticket) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" count={3} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-mono">
          {ticket.ticket_id}
        </h1>
      </div>
      <TicketDetailContent ticket={ticket} onUpdated={refetch} />
    </div>
  );
};
