import { describe, expect, it } from 'vitest';

import { statusStyle } from './status';

describe('statusStyle', () => {
  it('maps statuses to labels and status tokens', () => {
    expect(statusStyle('covered').label).toBe('Covered');
    expect(statusStyle('covered').dot).toContain('--st-ok');
    expect(statusStyle('failing').dot).toContain('--st-fail');
    expect(statusStyle('not_run').dot).toContain('--st-none');
    expect(statusStyle('uncovered').label).toBe('Not covered');
    expect(statusStyle(null).label).toBe('—');
  });
});
