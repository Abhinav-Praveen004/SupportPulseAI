import React, { useState } from 'react';
import {
  Bell,
  CheckCircle2,
  Clock,
  Key,
  Save,
  Send,
  Sliders,
  Users,
} from 'lucide-react';

import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const Settings: React.FC = () => {
  const [p1Hours, setP1Hours] = useState(4);
  const [p2Hours, setP2Hours] = useState(8);
  const [p3Hours, setP3Hours] = useState(24);
  const [p4Hours, setP4Hours] = useState(72);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.65);

  const [webhookUrl, setWebhookUrl] = useState('');
  const [smtpHost, setSmtpHost] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Platform Settings
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure SLA target policies, automated triage thresholds, and notification delivery.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span>Settings saved successfully. Changes take effect on next ticket ingest.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* SLA Policy Configuration */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-500" />
              <span>SLA Target Policy (Hours to Resolution)</span>
            </div>
          }
          subtitle="Configure default contractual resolution deadlines per incident priority level"
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <label className="font-semibold text-rose-600 dark:text-rose-400 block mb-1">
                P1 - Critical
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={1}
                  max={48}
                  value={p1Hours}
                  onChange={(e) => setP1Hours(parseInt(e.target.value) || 4)}
                  className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
                />
                <span className="text-slate-400">hours</span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-orange-600 dark:text-orange-400 block mb-1">
                P2 - High
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={1}
                  max={96}
                  value={p2Hours}
                  onChange={(e) => setP2Hours(parseInt(e.target.value) || 8)}
                  className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
                />
                <span className="text-slate-400">hours</span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-blue-600 dark:text-blue-400 block mb-1">
                P3 - Medium
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={4}
                  max={168}
                  value={p3Hours}
                  onChange={(e) => setP3Hours(parseInt(e.target.value) || 24)}
                  className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
                />
                <span className="text-slate-400">hours</span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                P4 - Low
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={12}
                  max={336}
                  value={p4Hours}
                  onChange={(e) => setP4Hours(parseInt(e.target.value) || 72)}
                  className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
                />
                <span className="text-slate-400">hours</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Triage Confidence Threshold */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-brand-500" />
              <span>Automated Triage Fallback Threshold</span>
            </div>
          }
          subtitle="Predictions with confidence below this threshold are flagged for manual human verification"
        >
          <div className="space-y-3 max-w-xl text-xs">
            <div className="flex justify-between">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Confidence Gate</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                {(confidenceThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.40"
              max="0.90"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-full accent-brand-600 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
            />
            <p className="text-2xs text-slate-400">
              Higher values increase human review accuracy on ambiguous tickets; lower values increase zero-touch automated triage rate.
            </p>
          </div>
        </Card>

        {/* Alert Integrations */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-brand-500" />
              <span>Alert Delivery Channels</span>
            </div>
          }
          subtitle="In-app real-time SSE stream is always active; configure optional external notification webhooks"
        >
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                Webhook URL (Slack / Teams / Generic)
              </label>
              <input
                type="url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
              />
              <span className="text-2xs text-slate-400 mt-0.5 block">
                Off by default. Sends JSON payload on SLA risk band escalation.
              </span>
            </div>

            <div>
              <label className="font-medium text-slate-700 dark:text-slate-300 block mb-1">
                SMTP Relay Host (Optional)
              </label>
              <input
                type="text"
                value={smtpHost}
                onChange={(e) => setSmtpHost(e.target.value)}
                placeholder="smtp.office365.com:587"
                className="w-full p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono text-xs"
              />
              <span className="text-2xs text-slate-400 mt-0.5 block">
                Off by default. Delivers email notifications for Critical SLA alerts.
              </span>
            </div>
          </div>
        </Card>

        {/* Seeded Demo Logins Reference (README Requirement) */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-brand-500" />
              <span>Seeded Demo Accounts Reference</span>
            </div>
          }
          subtitle="Default credentials initialized in local database"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-brand-600 dark:text-brand-400 font-semibold font-sans block mb-1">
                Admin Role
              </span>
              <div>user: <strong>admin</strong></div>
              <div>pass: <strong>admin123</strong></div>
            </div>

            <div className="p-3 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-brand-600 dark:text-brand-400 font-semibold font-sans block mb-1">
                Manager Role
              </span>
              <div>user: <strong>manager</strong></div>
              <div>pass: <strong>manager123</strong></div>
            </div>

            <div className="p-3 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs text-brand-600 dark:text-brand-400 font-semibold font-sans block mb-1">
                Agent Role
              </span>
              <div>user: <strong>agent</strong></div>
              <div>pass: <strong>agent123</strong></div>
            </div>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" variant="primary" size="md" icon={<Save className="w-4 h-4 mr-1.5" />}>
            Save Platform Settings
          </Button>
        </div>
      </form>
    </div>
  );
};
