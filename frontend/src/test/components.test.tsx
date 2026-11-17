import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import { RiskBadge } from '../components/common/RiskBadge';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { TermHighlighter } from '../components/common/TermHighlighter';

describe('UI Component Library Tests', () => {
  it('renders RiskBadge with multi-modal semantics (shape + icon + text + prob)', () => {
    render(<RiskBadge band="Critical" probability={0.88} />);
    expect(screen.getByText('CRIT')).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();
  });

  it('renders FrictionBadge with score and band label', () => {
    render(<FrictionBadge band="Frustrated" score={68.4} />);
    expect(screen.getByText('Frustrated')).toBeInTheDocument();
    expect(screen.getByText('68')).toBeInTheDocument();
  });

  it('renders PriorityBadge with target hours metadata', () => {
    render(<PriorityBadge priority="P1" />);
    expect(screen.getByText('P1')).toBeInTheDocument();
    expect(screen.getByLabelText(/Priority P1, SLA deadline 4 hours/i)).toBeInTheDocument();
  });

  it('renders ConfidenceBar with human triage flag when required', () => {
    render(<ConfidenceBar confidence={0.52} needsHumanTriage={true} />);
    expect(screen.getByText('52%')).toBeInTheDocument();
    expect(screen.getByText(/Triage/i)).toBeInTheDocument();
  });

  it('renders TermHighlighter wrapping influential terms in <mark> tags', () => {
    const text = 'AnyConnect VPN gateway disconnected abruptly';
    const terms = [{ ngram: 'vpn gateway', score: 0.85 }];
    const { container } = render(<TermHighlighter text={text} terms={terms} />);
    const marks = container.querySelectorAll('mark');
    expect(marks.length).toBeGreaterThan(0);
    expect(marks[0].textContent?.toLowerCase()).toContain('vpn gateway');
  });
});
