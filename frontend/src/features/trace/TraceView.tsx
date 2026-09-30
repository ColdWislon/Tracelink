import { useMemo } from 'react';

import { useEvidence, useItems } from '@/api/hooks';
import type { Item, ProjectNode } from '@/api/types';
import { statusStyle } from '@/lib/status';

function Tile({ count, label }: { count: number; label: string }) {
  return (
    <div className="border-line border px-3 py-2.5">
      <div className="font-head text-fail-ink text-[26px] leading-none">{count}</div>
      <div className="text-mut-700 mt-1 text-[12px]">{label}</div>
    </div>
  );
}

function LegendItem({ token, label }: { token: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span style={{ width: 11, height: 11, background: `var(--st-${token})` }} />
      {label}
    </span>
  );
}

export function TraceView({
  project,
  onOpenItem,
}: {
  project: ProjectNode | undefined;
  onOpenItem: (id: string) => void;
}) {
  const projectId = project?.id;
  const { data: items = [] } = useItems(projectId);
  const { data: evidence = [] } = useEvidence(projectId);

  const requirements = useMemo(
    () => items.filter((i) => i.base_kind === 'requirement').sort(cmpId),
    [items],
  );
  const vps = useMemo(
    () => items.filter((i) => i.base_kind === 'verification_item').sort(cmpId),
    [items],
  );

  // requirement id -> (vp id -> suspect?)
  const links = useMemo(() => {
    const map = new Map<string, Map<string, boolean>>();
    for (const req of requirements) {
      const inner = new Map<string, boolean>();
      for (const l of req.downstream) {
        if (l.link_type === 'verified_by' && l.target === 'item') inner.set(l.id, l.suspect);
      }
      map.set(req.id, inner);
    }
    return map;
  }, [requirements]);

  const orphanReqs = requirements.filter((r) => (links.get(r.id)?.size ?? 0) === 0);
  const orphanVps = vps.filter((v) => v.upstream.length === 0);
  const orphanEvidence = evidence.filter((e) => e.link_count === 0);

  if (!project) return <div className="text-mut-700 p-8">Select an IP from the hierarchy.</div>;

  const template = `minmax(220px, 1fr) repeat(${vps.length}, 26px)`;

  return (
    <div className="max-w-[1280px] p-6 pb-16">
      <div className="text-brand-700 mb-1 text-[11px] tracking-widest uppercase">Traceability</div>
      <h2 className="font-head mb-4 text-[28px]">Requirements × plan items</h2>

      <div className="mb-4 grid max-w-[760px] grid-cols-3 gap-4">
        <Tile count={orphanReqs.length} label="orphan requirements" />
        <Tile count={orphanVps.length} label="plan items without requirement" />
        <Tile count={orphanEvidence.length} label="orphan evidence" />
      </div>

      <div className="text-mut-700 mb-2 flex flex-wrap gap-3.5 text-[12px]">
        <LegendItem token="ok" label="Covered" />
        <LegendItem token="part" label="Partial" />
        <LegendItem token="fail" label="Failing" />
        <LegendItem token="none" label="Not run" />
        <LegendItem token="sus" label="Suspect link" />
      </div>

      {vps.length === 0 || requirements.length === 0 ? (
        <div className="border-line text-mut-700 border p-6">
          Need both requirements and plan items to plot the matrix.
        </div>
      ) : (
        <div className="border-line inline-block max-w-full overflow-x-auto border">
          {/* Column headers */}
          <div
            className="border-line bg-panel grid border-b"
            style={{ gridTemplateColumns: template }}
          >
            <div className="text-mut-700 flex items-end gap-1 p-2 text-[11px]">
              {requirements.length} requirements · {vps.length} plan items
            </div>
            {vps.map((vp) => (
              <button
                key={vp.id}
                type="button"
                title={vp.human_id}
                onClick={() => onOpenItem(vp.id)}
                className="border-line/60 flex h-[104px] items-end justify-center border-l pb-1.5"
              >
                <span
                  className="text-mut-700 font-mono text-[10.5px] whitespace-nowrap"
                  style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
                >
                  {vp.human_id}
                </span>
              </button>
            ))}
          </div>
          {/* Rows */}
          {requirements.map((req) => {
            const inner = links.get(req.id) ?? new Map();
            const orphan = inner.size === 0;
            return (
              <div
                key={req.id}
                className="border-line/60 grid border-b"
                style={{ gridTemplateColumns: template }}
              >
                <button
                  type="button"
                  onClick={() => onOpenItem(req.id)}
                  className="flex h-[26px] items-center gap-1.5 px-2 text-left"
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      flex: 'none',
                      background: statusStyle(req.status).dot,
                    }}
                  />
                  <span className="text-brand-700 flex-none font-mono text-[11px]">
                    {req.human_id}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-[12px]">{req.title}</span>
                  {orphan && (
                    <span className="border-fail text-fail-ink flex-none border px-1 text-[10px]">
                      no plan item
                    </span>
                  )}
                </button>
                {vps.map((vp) => {
                  const linked = inner.has(vp.id);
                  const suspect = inner.get(vp.id);
                  const fill = suspect
                    ? 'var(--st-sus)'
                    : linked
                      ? statusStyle(vp.status).dot
                      : 'transparent';
                  return (
                    <div
                      key={vp.id}
                      title={`${req.human_id} × ${vp.human_id}`}
                      className="border-line/60 flex h-[26px] items-center justify-center border-l"
                    >
                      {linked && (
                        <span
                          style={{
                            width: 16,
                            height: 16,
                            background: fill,
                            outline: '1px solid rgba(0,0,0,.06)',
                          }}
                          className="grid place-items-center text-[10px] text-white"
                        >
                          {suspect ? '!' : ''}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {/* Orphan evidence table */}
      <div className="mt-8 max-w-[900px]">
        <div className="mb-1.5 flex items-baseline gap-2.5">
          <h4 className="font-head text-[19px]">Orphan evidence</h4>
          <span className="text-mut-700 text-[12px]">
            In Git or regression results, linked to no plan item
          </span>
        </div>
        {orphanEvidence.length === 0 ? (
          <div className="text-mut-700 text-[13px]">None — all evidence is linked.</div>
        ) : (
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr className="bg-panel text-mut-700 text-left text-[11px] tracking-wide uppercase">
                <th className="border-line border-b px-2 py-1.5">Kind</th>
                <th className="border-line border-b px-2 py-1.5">Name</th>
                <th className="border-line border-b px-2 py-1.5">Source</th>
              </tr>
            </thead>
            <tbody>
              {orphanEvidence.map((e) => (
                <tr key={e.id}>
                  <td className="border-line/60 border-b px-2 py-1.5">
                    <span className="border-brand-400 text-brand-700 border px-1 font-mono text-[10px]">
                      {e.kind}
                    </span>
                  </td>
                  <td className="border-line/60 border-b px-2 py-1.5 font-mono text-[12.5px]">
                    {e.fqn}
                  </td>
                  <td className="border-line/60 text-mut-700 border-b px-2 py-1.5">
                    {[e.in_git && 'Git', e.in_regression && 'Regression']
                      .filter(Boolean)
                      .join(' · ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function cmpId(a: Item, b: Item): number {
  return a.human_id.localeCompare(b.human_id);
}
