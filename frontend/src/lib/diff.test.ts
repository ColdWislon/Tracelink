import { describe, expect, it } from 'vitest';

import { diffText, stripHtml } from './diff';

describe('stripHtml', () => {
  it('removes tags and collapses whitespace', () => {
    expect(stripHtml('<p>The <b>controller</b> shall act.</p>')).toBe('The controller shall act.');
    expect(stripHtml('<ul><li>a</li><li>b</li></ul>')).toBe('a b');
  });
});

describe('diffText', () => {
  it('finds a single changed span', () => {
    const d = diffText('assert within 32 cycles.', 'assert within 16 cycles.');
    expect(d.pre).toBe('assert within ');
    expect(d.deleted).toBe('32');
    expect(d.inserted).toBe('16');
    expect(d.post).toBe(' cycles.');
    expect(d.changed).toBe(true);
  });

  it('reports no change for identical text', () => {
    expect(diffText('same', 'same').changed).toBe(false);
  });
});
