import { Layers } from 'lucide-react';
import { useState } from 'react';

import { useBaseline, useBaselines, useCreateBaseline } from '@/api/hooks';
import type { ProjectNode } from '@/api/types';
import { cn } from '@/lib/cn';

export function BaselinesView({ project }: { project: ProjectNode | undefined }) {
  const projectId = project?.id;
  const { data: baselines = [] } = useBaselines(projectId);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [name, setName] = useState('');
  const [milestone, setMilestone] = useState('');
  const create = useCreateBaseline(projectId);
  const { data: detail } = useBaseline(selectedId ?? baselines[0]?.id);

  if (!project) return <div className="text-mut-700 p-8">Select a project from the hierarchy.</div>;

  const submit = () => {
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), milestone: milestone.trim() || undefined },
      {
        onSuccess: (b) => {
          setSelectedId(b.id);
          setName('');
          setMilestone('');
        },
      },
    );
  };

  return (
    <div className="max-w-[1100px] p-6 pb-16">
      <div className="text-brand-700 mb-1 flex items-center gap-2 text-[11px] tracking-widest uppercase">
        <Layers size={14} /> Baselines · {project.name}
      </div>
      <h2 className="font-head mb-5 text-[28px]">Milestone snapshots</h2>

      <div className="grid gap-6 md:grid-cols-[320px_minmax(0,1fr)]">
        <div className="flex flex-col gap-4">
          <div className="border-line border p-3">
            <div className="text-mut-700 mb-2 text-[10.5px] tracking-wider uppercase">
              Create baseline
            </div>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name (e.g. RTL freeze)"
              className="border-line bg-canvas mb-1.5 w-full border px-2 py-1 text-[12.5px] outline-none"
            />
            <input
              value={milestone}
              onChange={(e) => setMilestone(e.target.value)}
              placeholder="Milestone (optional)"
              className="border-line bg-canvas mb-1.5 w-full border px-2 py-1 text-[12.5px] outline-none"
            />
            <button
              type="button"
              onClick={submit}
              disabled={!name.trim() || create.isPending}
              className="bg-brand-600 text-canvas w-full py-1.5 text-[12.5px] disabled:opacity-50"
            >
              Freeze snapshot
            </button>
            <p className="text-mut-700 mt-1.5 text-[11.5px]">
              Captures every item's current revision across {project.name} and its sub-blocks.
            </p>
          </div>

          <div className="flex flex-col gap-1">
            {baselines.length === 0 && (
              <div className="text-mut-700 text-[13px]">No baselines yet.</div>
            )}
            {baselines.map((b) => (
              <button
                key={b.id}
                type="button"
                onClick={() => setSelectedId(b.id)}
                className={cn(
                  'border-line flex items-center gap-2 border px-3 py-2 text-left',
                  (selectedId ?? baselines[0]?.id) === b.id ? 'bg-brand-100' : 'hover:bg-panel',
                )}
              >
                <Layers size={14} className="text-brand" />
                <span className="flex flex-1 flex-col leading-tight">
                  <span className="text-[13px] font-semibold">{b.name}</span>
                  <span className="text-mut-700 text-[11.5px]">
                    {b.milestone ? `${b.milestone} · ` : ''}
                    {new Date(b.created_at).toLocaleDateString()} · {b.entry_count} items
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>

        <div>
          {detail ? (
            <>
              <div className="mb-2 flex items-baseline gap-2">
                <h3 className="font-head text-[20px]">{detail.name}</h3>
                <span className="text-mut-700 text-[12px]">
                  {detail.entry_count} items · frozen {new Date(detail.created_at).toLocaleString()}
                </span>
              </div>
              <div className="border-line overflow-x-auto border">
                <table className="w-full border-collapse text-[13px]">
                  <thead>
                    <tr className="bg-panel text-mut-700 text-left text-[11px] tracking-wide uppercase">
                      <th className="border-line border-b px-2 py-1.5">ID</th>
                      <th className="border-line border-b px-2 py-1.5">Title</th>
                      <th className="border-line border-b px-2 py-1.5">Revision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.entries.map((e) => (
                      <tr key={e.item_id}>
                        <td className="border-line/60 text-brand-700 border-b px-2 py-1.5 font-mono text-[12px]">
                          {e.human_id}
                        </td>
                        <td className="border-line/60 border-b px-2 py-1.5">{e.title}</td>
                        <td className="border-line/60 border-b px-2 py-1.5 font-mono text-[12px]">
                          r{e.rev_number}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="text-mut-700 text-[13px]">
              Select or create a baseline to see its snapshot.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
