export type Section =
  'requirements' | 'plan' | 'evidence' | 'trace' | 'dashboard' | 'reviews' | 'baselines';

export type View = 'document' | 'grid';

export const SECTION_LABELS: Record<Section, string> = {
  requirements: 'Requirements',
  plan: 'Verification Plan',
  evidence: 'Evidence',
  trace: 'Traceability',
  dashboard: 'Dashboard',
  reviews: 'Reviews',
  baselines: 'Baselines',
};
