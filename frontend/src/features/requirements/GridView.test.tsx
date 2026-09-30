import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Item } from '@/api/types';

import { GridView } from './GridView';

function makeItem(overrides: Partial<Item>): Item {
  return {
    id: crypto.randomUUID(),
    human_id: 'REQ-PCIE-001',
    project_id: 'p',
    project_key: 'pcie',
    item_type_id: 't',
    type_key: 'requirement',
    base_kind: 'requirement',
    title: 'Gen4 link training on x4',
    body: 'When ... shall ...',
    attributes: { priority: 'P1', category: 'Functional' },
    ears_pattern: 'Event-driven',
    workflow_status: 'approved',
    applicability: 'A0',
    rev_number: 1,
    current_revision_id: 'r',
    status: 'covered',
    upstream: [],
    downstream: [],
    ...overrides,
  };
}

const items: Item[] = [
  makeItem({
    human_id: 'REQ-PCIE-001',
    title: 'Gen4 link training on x4',
    downstream: [
      {
        link_id: 'l1',
        link_type: 'verified_by',
        target: 'item',
        id: 'v1',
        human_id: 'VP-PCIE-021',
        title: 'ECRC',
        suspect: true,
      },
    ],
  }),
  makeItem({
    human_id: 'REQ-DMA-011',
    title: 'Abort on descriptor error',
    status: 'uncovered',
    downstream: [],
  }),
];

describe('GridView', () => {
  it('renders rows, marks orphans, and filters', () => {
    render(<GridView requirements={items} onUpdate={vi.fn()} onOpenItem={vi.fn()} />);

    expect(screen.getByText('REQ-PCIE-001')).toBeInTheDocument();
    expect(screen.getByText('REQ-DMA-011')).toBeInTheDocument();
    expect(screen.getByText('No plan item')).toBeInTheDocument();
    expect(screen.getByText('VP-PCIE-021')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('Filter by ID or title'), {
      target: { value: 'dma' },
    });
    expect(screen.queryByText('REQ-PCIE-001')).not.toBeInTheDocument();
    expect(screen.getByText('REQ-DMA-011')).toBeInTheDocument();
  });

  it('commits an inline priority change', () => {
    const onUpdate = vi.fn();
    render(<GridView requirements={items} onUpdate={onUpdate} onOpenItem={vi.fn()} />);
    const selects = screen.getAllByRole('combobox');
    fireEvent.change(selects[0], { target: { value: 'P3' } });
    expect(onUpdate).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ attributes: expect.objectContaining({ priority: 'P3' }) }),
    );
  });
});
