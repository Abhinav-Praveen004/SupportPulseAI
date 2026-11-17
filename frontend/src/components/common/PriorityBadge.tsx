import React from 'react';
import { tokens } from '../../styles/tokens';

interface PriorityBadgeProps {
  priority: 'P1' | 'P2' | 'P3' | 'P4';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  const conf = tokens.priorities[priority] || tokens.priorities.P3;

  return (
    <span
      className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded border font-mono ${conf.badge}`}
      title={`Target: ${conf.targetHours} hours SLA`}
      aria-label={`Priority ${priority}, SLA deadline ${conf.targetHours} hours`}
    >
      {priority}
    </span>
  );
};
