import React, { useState } from 'react';
import {
  AlertTriangle,
  Beaker,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  Flame,
  Frown,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { RiskBadge } from '../components/common/RiskBadge';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { TermHighlighter } from '../components/common/TermHighlighter';
import { AnalysisResponse } from '../lib/types';
import { tokens } from '../styles/tokens';

const PRESETS = [
  {
    label: 'Critical VPN Outage',
    category: 'Network/VPN',
    text: 'URGENT: Corporate GlobalProtect VPN completely disconnected across entire team. Remote gateway timeout error GW-504. BLOCKING ALL DEPLOYMENTS!',
    dept: 'Engineering',
    contacts: 3,
    reopens: 1,
  },
  {
    label: 'Password Lockout',
    category: 'Password/Access',
    text: 'Hello team, my Okta password has expired and I am locked out of Jira and GitHub after 3 attempts. Could you please reset my MFA token?',
    dept: 'Finance',
    contacts: 1,
    reopens: 0,
  },
  {
    label: 'Frustrated Swollen Battery',
    category: 'Hardware',
    text: 'THIS IS TOTALLY UNACCEPTABLE! Third time I am submitting this request! My MacBook battery is visibly swollen and trackpad is not clicking. Immediate safety hazard, escalate now!',
    dept: 'Sales',
    contacts: 4,
    reopens: 2,
  },
  {
    label: 'Security Incident',
    category: 'Security Incident',
    text: 'Received suspicious unauthorized Duo MFA push prompt at 03:15 AM from unknown foreign IP address. Suspect credential compromise on Active Directory.',
    dept: 'Operations',
    contacts: 1,
    reopens: 0,
  },
];

export const Playground: React.FC = () => {
  const [text, setText] = useState(PRESETS[0].text);
  const [department, setDepartment] = useState(PRESETS[0].dept);
  const [contacts, setContacts] = useState(PRESETS[0].contacts);
  const [reopens, setReopens] = useState(PRESETS[0].reopens);

  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setIsLoading(true);
    const t0 = performance.now();
    try {
      const res = await api.analyzeText({
        text,
        department,
        contact_count: contacts,
        reopen_count: reopens,
      });
      const t1 = performance.now();
      setLatencyMs(Math.round(t1 - t0));
      setResults(res);
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    setText(preset.text);
    setDepartment(preset.dept);
    setContacts(preset.contacts);
    setReopens(preset.reopens);
    setResults(null);
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Inference Playground
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Stateless multi-model evaluation testing category, priority, SLA risk, and friction score on ad-hoc text.
        </p>
      </div>

      {/* Preset Scenario Quick-Buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-400 mr-1">Preset Scenarios:</span>
        {PRESETS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleApplyPreset(p)}
            className="text-xs px-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-brand-500 text-slate-700 dark:text-slate-300 font-medium transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-5 space-y-4">
          <Card title="Input Ticket Text & Context">
            <div className="space-y-4 text-xs">
              <div>
                <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                  Ticket Content (Subject & Description)
                </label>
                <textarea
                  rows={6}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste or write IT support request description..."
                  className="w-full p-2.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                    Department
                  </label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                  >
                    <option value="Engineering">Engineering</option>
                    <option value="Sales">Sales</option>
                    <option value="Finance">Finance</option>
                    <option value="Human Resources">HR</option>
                    <option value="Operations">Operations</option>
                    <option value="Marketing">Marketing</option>
                  </select>
                </div>

                <div>
                  <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                    Contacts
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={contacts}
                    onChange={(e) => setContacts(parseInt(e.target.value) || 1)}
                    className="w-full p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                    Reopens
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    value={reopens}
                    onChange={(e) => setReopens(parseInt(e.target.value) || 0)}
                    className="w-full p-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>

              <Button
                variant="primary"
                className="w-full"
                onClick={handleAnalyze}
                isLoading={isLoading}
                icon={<Play className="w-3.5 h-3.5 mr-1" />}
              >
                Run Multi-Model Analysis
              </Button>
            </div>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-7">
          {!results ? (
            <Card className="h-full flex items-center justify-center p-12 text-center text-slate-400">
              <div>
                <Zap className="w-10 h-10 mx-auto mb-3 opacity-30 text-brand-500" />
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Ready for Inference
                </h4>
                <p className="text-xs max-w-sm">
                  Click "Run Multi-Model Analysis" to evaluate classification, explainability n-grams, SLA breach risk, and friction score on CPU.
                </p>
              </div>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* Header with Execution Latency */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 text-xs">
                <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Inference Complete: 4 models evaluated simultaneously</span>
                </div>
                {latencyMs !== null && (
                  <span className="font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/60 px-2 py-0.5 rounded">
                    {latencyMs} ms (CPU)
                  </span>
                )}
              </div>

              {/* M1: Classification & N-Gram Highlights */}
              <Card title="M1 Classification & Text Attribution">
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <span className="text-2xs text-slate-400 block mb-1">Predicted Category</span>
                    <span className="text-sm font-bold text-brand-600 dark:text-brand-400 block mb-1">
                      {results.category}
                    </span>
                    <ConfidenceBar
                      confidence={results.category_confidence}
                      needsHumanTriage={results.needs_human_triage}
                    />
                  </div>
                  <div>
                    <span className="text-2xs text-slate-400 block mb-1">Predicted Priority</span>
                    <PriorityBadge priority={results.priority as any} />
                    <div className="mt-1">
                      <ConfidenceBar confidence={results.priority_confidence} />
                    </div>
                  </div>
                </div>

                {/* Highlighted text */}
                <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Influential N-Grams Highlighted
                  </span>
                  <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                    <TermHighlighter text={text} terms={results.top_contributing_ngrams} />
                  </div>
                </div>
              </Card>

              {/* M3 & M4 Predictions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* M3 SLA Risk */}
                <Card title="M3 SLA Breach Risk">
                  <div className="flex items-center justify-between mb-3">
                    <RiskBadge band={results.sla_risk_band as any} probability={results.sla_breach_probability} size="lg" />
                    <div className="text-right">
                      <span className="text-2xs text-slate-400 block">Est. Time Remaining</span>
                      <span className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200">
                        {results.estimated_minutes_to_breach.toFixed(0)}m
                      </span>
                    </div>
                  </div>

                  {results.sla_top_drivers.length > 0 && (
                    <div className="space-y-1.5 mt-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                      <span className="text-2xs font-semibold text-slate-400 block">Counterfactual Drivers</span>
                      {results.sla_top_drivers.map((d, i) => (
                        <div
                          key={i}
                          className="text-2xs p-1.5 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex justify-between"
                        >
                          <span className="text-slate-700 dark:text-slate-300">{d.description}</span>
                          <span className="font-mono font-bold text-amber-600">+{d.impact_pct}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>

                {/* M4 Friction Score */}
                <Card title="M4 Friction Index">
                  <div className="flex items-center justify-between mb-3">
                    <FrictionBadge band={results.friction_band as any} score={results.friction_score} size="lg" />
                    <div className="text-right">
                      <span className="text-2xs text-slate-400 block">Overall Agitation</span>
                      <span className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200">
                        {results.friction_score} / 100
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-center text-xs">
                    <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                      <span className="text-2xs text-slate-400 block">Sentiment</span>
                      <span className="font-mono font-bold">
                        {results.friction_breakdown.sentiment_subscore}
                      </span>
                    </div>
                    <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                      <span className="text-2xs text-slate-400 block">Text Cues</span>
                      <span className="font-mono font-bold">
                        {results.friction_breakdown.text_cues_subscore}
                      </span>
                    </div>
                    <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                      <span className="text-2xs text-slate-400 block">Behavior</span>
                      <span className="font-mono font-bold">
                        {results.friction_breakdown.behavioral_subscore}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* M2 Routing */}
              <Card title="M2 Routing Recommendation">
                <div className="p-3 rounded-lg bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 text-xs">
                  <span className="font-semibold text-blue-900 dark:text-blue-200 block mb-1">
                    Recommended Team: {results.routing_recommendation}
                  </span>
                  <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                    {results.routing_reasoning}
                  </p>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
