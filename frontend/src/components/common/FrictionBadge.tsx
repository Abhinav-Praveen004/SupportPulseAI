import React from 'react';
import { AlertOctagon, Frown, Meh, Smile } from 'lucide-react';
import { tokens } from '../../styles/tokens';

interface FrictionBadgeProps {
  band: 'Calm' | 'Uneasy' | 'Frustrated' | 'Critical';
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
}

export const FrictionBadge: React.FC<FrictionBadgeProps> = ({
  band,
  score,
  size = 'md',
  showScore = true,
}) => {
  const conf = tokens.friction[band] || tokens.friction.Calm;

  const renderIcon = () => {
    const iconProps = { className: size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5', 'aria-hidden': true };
    switch (band) {
      case 'Critical':
        return <AlertOctagon {...iconProps} />;
      case 'Frustrated':
        return <Frown {...iconProps} />;
      case 'Uneasy':
        return <Meh {...iconProps} />;
      default:
        return <Smile {...iconProps} />;
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
      aria-label={`${conf.label}${score !== undefined ? ` score ${score.toFixed(0)}` : ''}`}
    >
      {renderIcon()}
      <span>{band}</span>
      {showScore && score !== undefined && (
        <span className="tabular-nums font-mono opacity-80">
          {score.toFixed(0)}
        </span>
      )}
    </span>
  );
};
