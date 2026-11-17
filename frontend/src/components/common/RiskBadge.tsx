import React from 'react';
import { AlertCircle, AlertTriangle, Flame, ShieldCheck } from 'lucide-react';
import { tokens } from '../../styles/tokens';

interface RiskBadgeProps {
  band: 'Low' | 'Medium' | 'High' | 'Critical';
  probability?: number;
  size?: 'sm' | 'md' | 'lg';
  showProbability?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  band,
  probability,
  size = 'md',
  showProbability = true,
}) => {
  const conf = tokens.risk[band] || tokens.risk.Low;

  const renderIcon = () => {
    const iconProps = { className: size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5', 'aria-hidden': true };
    switch (band) {
      case 'Critical':
        return <Flame {...iconProps} />;
      case 'High':
        return <AlertTriangle {...iconProps} />;
      case 'Medium':
        return <AlertCircle {...iconProps} />;
      default:
        return <ShieldCheck {...iconProps} />;
    }
  };

  const sizeClasses = {
    sm: 'text-2xs px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2 py-0.5 gap-1.5',
    lg: 'text-sm px-2.5 py-1 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-medium rounded-md border ${conf.bgLight} ${conf.bgDark} ${sizeClasses}`}
      title={conf.description}
      aria-label={`${conf.label}${probability !== undefined ? ` with probability ${(probability * 100).toFixed(0)}%` : ''}`}
    >
      {renderIcon()}
      <span>{conf.shortLabel}</span>
      {showProbability && probability !== undefined && (
        <span className="tabular-nums font-mono opacity-80">
          {(probability * 100).toFixed(0)}%
        </span>
      )}
    </span>
  );
};
