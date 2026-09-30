import type { VerificationStatus } from '@/api/types';

type Token = 'ok' | 'part' | 'fail' | 'none' | 'sus';

const META: Record<VerificationStatus, { label: string; token: Token }> = {
  covered: { label: 'Covered', token: 'ok' },
  partial: { label: 'Partial', token: 'part' },
  failing: { label: 'Failing', token: 'fail' },
  not_run: { label: 'Not run', token: 'none' },
  uncovered: { label: 'Not covered', token: 'fail' },
};

export interface StatusStyle {
  label: string;
  dot: string;
  bg: string;
  ink: string;
}

export function statusStyle(status: VerificationStatus | null | undefined): StatusStyle {
  const meta = status ? META[status] : { label: '—', token: 'none' as Token };
  return {
    label: meta.label,
    dot: `var(--st-${meta.token})`,
    bg: `var(--st-${meta.token}-bg)`,
    ink: `var(--st-${meta.token}-ink)`,
  };
}

export const SUSPECT_STYLE = {
  color: 'var(--st-sus)',
  bg: 'var(--st-sus-bg)',
  ink: 'var(--st-sus-ink)',
};
