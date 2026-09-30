import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table';
import { AlertTriangle } from 'lucide-react';
import { useMemo, useState } from 'react';

import type { Item, ItemUpdate } from '@/api/types';
import { StatusBadge } from '@/components/StatusBadge';
import { SUSPECT_STYLE } from '@/lib/status';

interface Props {
  requirements: Item[];
  onUpdate: (id: string, patch: ItemUpdate) => void;
}

const PRIORITIES = ['P1', 'P2', 'P3'];
const WORKFLOW_LABEL: Record<string, string> = {
  draft: 'Draft',
  in_review: 'In review',
  approved: 'Approved',
};

const column = createColumnHelper<Item>();

export function GridView({ requirements, onUpdate }: Props) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'human_id', desc: false }]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
  const [editingTitle, setEditingTitle] = useState<string | null>(null);
  const [titleDraft, setTitleDraft] = useState('');

  const columns = useMemo(
    () => [
      column.accessor('human_id', {
        header: 'ID',
        cell: (ctx) => (
          <span className="text-brand-700 font-mono text-[12px]">{ctx.getValue()}</span>
        ),
      }),
      column.accessor('title', {
        header: 'Title',
        cell: (ctx) => {
          const item = ctx.row.original;
          if (editingTitle === item.id) {
            return (
              <input
                autoFocus
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={() => {
                  setEditingTitle(null);
                  if (titleDraft.trim() && titleDraft !== item.title)
                    onUpdate(item.id, { title: titleDraft.trim() });
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') e.currentTarget.blur();
                  if (e.key === 'Escape') setEditingTitle(null);
                }}
                className="border-brand bg-canvas w-full border px-1.5 py-0.5 text-[13px] outline-none"
              />
            );
          }
          return (
            <span
              className="cursor-text"
              onDoubleClick={() => {
                setEditingTitle(item.id);
                setTitleDraft(item.title);
              }}
            >
              {ctx.getValue()}
            </span>
          );
        },
      }),
      column.accessor((r) => (r.attributes.category as string) ?? '—', {
        id: 'category',
        header: 'Type',
      }),
      column.accessor((r) => (r.attributes.priority as string) ?? '—', {
        id: 'priority',
        header: 'Priority',
        cell: (ctx) => {
          const item = ctx.row.original;
          return (
            <select
              value={(item.attributes.priority as string) ?? 'P2'}
              onChange={(e) =>
                onUpdate(item.id, { attributes: { ...item.attributes, priority: e.target.value } })
              }
              className="border-line bg-canvas border px-1 py-0.5 font-mono text-[12px] outline-none"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          );
        },
      }),
      column.accessor((r) => r.applicability ?? 'A0 | A1-lite', {
        id: 'variants',
        header: 'Variants',
        enableSorting: false,
        cell: (ctx) => (
          <div className="flex gap-1">
            {ctx
              .getValue()
              .split('|')
              .map((v) => (
                <span key={v} className="bg-mut-200 text-mut-800 px-1.5 font-mono text-[11px]">
                  {v.trim()}
                </span>
              ))}
          </div>
        ),
      }),
      column.accessor((r) => WORKFLOW_LABEL[r.workflow_status], {
        id: 'review',
        header: 'Review',
      }),
      column.accessor((r) => r.downstream.length, {
        id: 'vps',
        header: 'Linked VP items',
        cell: (ctx) => {
          const links = ctx.row.original.downstream;
          if (links.length === 0)
            return <span className="text-fail-ink text-[11.5px]">No plan item</span>;
          return (
            <div className="flex flex-wrap gap-1">
              {links.map((l) => (
                <span
                  key={l.link_id}
                  className="border-line inline-flex items-center gap-1 border px-1.5 font-mono text-[11px]"
                  style={l.suspect ? { borderColor: SUSPECT_STYLE.color } : undefined}
                >
                  {l.human_id}
                  {l.suspect && <AlertTriangle size={11} style={{ color: SUSPECT_STYLE.color }} />}
                </span>
              ))}
            </div>
          );
        },
      }),
      column.accessor((r) => r.status ?? 'uncovered', {
        id: 'coverage',
        header: 'Coverage',
        cell: (ctx) => <StatusBadge status={ctx.row.original.status} />,
      }),
    ],
    [editingTitle, titleDraft, onUpdate],
  );

  const table = useReactTable({
    data: requirements,
    columns,
    state: { sorting, globalFilter, rowSelection },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    getRowId: (row) => row.id,
    globalFilterFn: (row, _col, value) => {
      const q = String(value).toLowerCase();
      return (
        row.original.human_id.toLowerCase().includes(q) ||
        row.original.title.toLowerCase().includes(q)
      );
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const selectedCount = Object.keys(rowSelection).length;

  return (
    <div className="min-w-0 px-5 pt-4 pb-16">
      <div className="mb-2.5 flex flex-wrap items-center gap-2">
        <div className="border-line bg-panel flex h-7 items-center gap-1.5 border px-2">
          <input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Filter by ID or title"
            className="text-ink w-40 bg-transparent text-[12.5px] outline-none"
          />
        </div>
        <span className="text-mut-700 text-[12px]">{table.getRowModel().rows.length} rows</span>
      </div>

      {selectedCount > 0 && (
        <div className="bg-brand-100 text-brand-800 mb-2 flex items-center gap-2 px-2.5 py-1.5 text-[12.5px]">
          <b className="font-semibold">{selectedCount} selected</b>
          <button type="button" className="hover:underline" onClick={() => setRowSelection({})}>
            Clear
          </button>
        </div>
      )}

      <div className="border-line overflow-x-auto border">
        <table className="w-full border-collapse text-[13px]" style={{ minWidth: 1000 }}>
          <thead>
            <tr className="bg-panel">
              <th className="border-line w-8 border-b px-2 py-1.5">
                <input
                  type="checkbox"
                  checked={table.getIsAllRowsSelected()}
                  onChange={table.getToggleAllRowsSelectedHandler()}
                />
              </th>
              {table.getFlatHeaders().map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className="border-line text-mut-700 border-b px-2 py-1.5 text-left text-[11px] font-medium tracking-wide uppercase"
                  style={{
                    cursor: header.column.getCanSort() ? 'pointer' : 'default',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {{ asc: ' ↑', desc: ' ↓' }[header.column.getIsSorted() as string] ?? ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-mut-200/40">
                <td className="border-line/50 border-b px-2 py-1.5">
                  <input
                    type="checkbox"
                    checked={row.getIsSelected()}
                    onChange={row.getToggleSelectedHandler()}
                  />
                </td>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="border-line/50 border-b px-2 py-1.5 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {table.getRowModel().rows.length === 0 && (
          <div className="text-mut-700 p-7 text-center">No requirements match these filters.</div>
        )}
      </div>
      <div className="text-mut-700 mt-2 text-[11.5px]">
        Double-click a title to edit · change a priority inline · click a header to sort
      </div>
    </div>
  );
}
