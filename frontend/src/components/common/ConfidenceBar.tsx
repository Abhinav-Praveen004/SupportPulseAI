import React from 'react';
import { UserCheck } from 'lucide-react';

interface ConfidenceBarProps {
  confidence: number; // 0.0 to 1.0
  needsHumanTriage?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  confidence,
  needsHumanTriage = false,
}) => {
  const pct = Math.round(confidence * 100);

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            needsHumanTriage
              ? 'bg-amber-500'
              : pct >= 80
              ? 'bg-blue-500'
              : 'bg-indigo-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono tabular-nums text-slate-600 dark:text-slate-400">
        {pct}%
      </span>
      {needsHumanTriage && (
        <span
          className="inline-flex items-center text-2xs font-medium text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-800 px-1 py-0.2 rounded"
          title="Confidence below threshold; human triage required"
        >
          <UserCheck className="w-2.5 h-2.5 mr-0.5" />
          Triage
        </span>
      )}
    </div>
  );
};
