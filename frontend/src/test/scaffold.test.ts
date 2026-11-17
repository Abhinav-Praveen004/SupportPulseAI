import { describe, it, expect } from 'vitest';
import { tokens } from '../styles/tokens';

describe('Scaffold Frontend Test', () => {
  it('loads design tokens correctly', () => {
    expect(tokens.categories).toHaveLength(10);
    expect(tokens.risk.Critical.color).toBe('#ef4444');
    expect(tokens.priorities.P1.targetHours).toBe(4);
  });
});
