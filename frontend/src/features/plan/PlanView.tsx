import { GripVertical, Plus, X } from 'lucide-react';
import { useMemo, useState } from 'react';

import { useCreateLink, useDeleteLink, useEvidence, useItem, useItems } from '@/api/hooks';
import type { Evidence, EvidenceKind, LinkRef, ProjectNode } from '@/api/types';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { cn } from '@/lib/cn';

const KIND_LABEL: Record<EvidenceKind, string> = {
  test: 'UVM tests',
  coverpoint: 'Functional coverage',
  assertion: 'SVA assertions',
};
const KIND_ORDER: EvidenceKind[] = ['test', 'coverpoint', 'assertion'];
const DRAG_KEY = 'application/x-evidence-id';

function evidenceMeta(
  ev: Evidence | undefined,
  kind: EvidenceKind,
): { metric: string; dot: string } {
  if (!ev) return { metric: '—', dot: 'var(--st-none)' };
  let metric: string;
  if (kind === 'test') metric = `${ev.passed ?? 0}/${ev.total ?? 0}`;
  else if (kind === 'coverpoint') metric = `${ev.hits ?? 0}/${ev.goal ?? 0}`;
  else metric = `${(ev.fired ?? 0).toLocaleString()} fired · ${ev.failed ?? 0} fail`;
  let token: string;
  if (!ev.ran) token = 'none';
  else if (ev.satisfied) token = 'ok';
  else if ((ev.failed ?? 0) > 0) token = 'fail';
  else token = 'part';
  return { metric, dot: `var(--st-${token})` };
}

export function PlanView({
  project,
  onOpenItem,
}: {
  project: ProjectNode | undefined;
  onOpenItem: (id: string) => void;
}) {
  const projectId = project?.id;
  const { data: items = [] } = useItems(projectId);
  const { data: evidence = [] } = useEvidence(projectId);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [catQuery, setCatQuery] = useState('');
  const [source, setSource] = useState<'all' | 'git' | 'regression'>('all');
  const [dragOver, setDragOver] = useState(false);

  const createLink = useCreateLink(projectId);
  const deleteLink = useDeleteLink(projectId);

  const vps = useMemo(() => items.filter((i) => i.base_kind === 'verification_item'), [items]);
  const currentId = selectedId ?? vps[0]?.id;
  const { data: detail } = useItem(currentId);
  const evidenceById = useMemo(() => new Map(evidence.map((e) => [e.id, e])), [evidence]);

  const filteredCatalog = useMemo(
    () =>
      evidence.filter((e) => {
        if (source === 'git' && !e.in_git) return false;
        if (source === 'regression' && !e.in_regression) return false;
        return `${e.fqn}`.toLowerCase().includes(catQuery.toLowerCase());
      }),
    [evidence, catQuery, source],
  );

  if (!project) return <div className="text-mut-700 p-8">Select an IP from the hierarchy.</div>;

  const linkEvidence = (evidenceId: string) => {
    if (!currentId) return;
    createLink.mutate({
      link_type: 'evidenced_by',
      upstream_item_id: currentId,
      downstream_evidence_id: evidenceId,
    });
  };

  const downstreamByKind = (kind: EvidenceKind): LinkRef[] =>
    (detail?.downstream ?? []).filter((l) => l.target === 'evidence' && l.evidence_kind === kind);

  return (
    <div
      className="grid h-full min-h-0"
      style={{ gridTemplateColumns: '260px minmax(0,1fr) 340px' }}
    >
      {/* VP list */}
      <div className="border-line min-h-0 overflow-auto border-r p-2">
        <div className="flex items-baseline justify-between px-1.5 pb-2">
          <h4 className="font-head text-[18px]">Plan items</h4>
          <span className="text-mut-700 font-mono text-[11px]">{vps.length}</span>
        </div>
        {vps.map((vp) => {
          const orphan = vp.upstream.length === 0;
          const suspect = vp.upstream.some((l) => l.suspect);
          return (
            <button
              key={vp.id}
              type="button"
              onClick={() => setSelectedId(vp.id)}
              className={cn(
                'grid w-full items-center gap-2 px-1.5 py-1.5 text-left',
                vp.id === currentId ? 'bg-brand-100' : 'hover:bg-mut-200/50',
              )}
              style={{ gridTemplateColumns: '10px minmax(0,1fr) auto' }}
            >
              <StatusDot status={vp.status} />
              <span className="flex min-w-0 flex-col leading-tight">
                <span className="text-brand-700 font-mono text-[11px]">{vp.human_id}</span>
                <span className="truncate text-[12.5px]">{vp.title}</span>
              </span>
              {orphan ? (
                <span className="bg-fail-bg text-fail-ink px-1 text-[10px]">orphan</span>
              ) : suspect ? (
                <span style={{ color: 'var(--st-sus)' }}>▲</span>
              ) : (
                <span />
              )}
            </button>
          );
        })}
      </div>

      {/* VP detail + drop zone */}
      <div
        className={cn('min-h-0 overflow-auto p-6', dragOver && 'bg-brand-100/40')}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const id = e.dataTransfer.getData(DRAG_KEY);
          if (id) linkEvidence(id);
        }}
      >
        {!detail ? (
          <div className="text-mut-700">Select a plan item.</div>
        ) : (
          <>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-brand-700 font-mono text-[12px]">{detail.human_id}</span>
              <StatusBadge status={detail.status} />
              <span className="flex-1" />
              <button
                type="button"
                onClick={() => onOpenItem(detail.id)}
                className="border-line hover:bg-panel border px-2 py-0.5 text-[12.5px]"
              >
                Open details
              </button>
            </div>
            <h2 className="font-head mb-3 text-[26px]">{detail.title}</h2>

            <div className="mb-4 flex flex-wrap items-center gap-1.5">
              <span className="text-mut-700 mr-1 text-[12px]">Verifies</span>
              {detail.upstream.length === 0 ? (
                <span className="bg-fail-bg text-fail-ink px-2 py-0.5 text-[12px]">
                  No requirement — orphan plan item
                </span>
              ) : (
                detail.upstream.map((l) => (
                  <button
                    key={l.link_id}
                    type="button"
                    onClick={() => onOpenItem(l.id)}
                    className="border-line hover:bg-panel inline-flex items-center gap-1.5 border px-2 py-0.5 text-[12.5px]"
                  >
                    <span className="text-brand-700 font-mono text-[11.5px]">{l.human_id}</span>
                    {l.title}
                  </button>
                ))
              )}
            </div>

            <div className="flex flex-col gap-4">
              {KIND_ORDER.map((kind) => {
                const links = downstreamByKind(kind);
                return (
                  <div key={kind} className="border-line border">
                    <div className="border-line flex items-center gap-2 border-b px-3 py-2">
                      <span className="font-head text-[15px] font-semibold">
                        {KIND_LABEL[kind]}
                      </span>
                      <span className="text-mut-700 font-mono text-[11px]">{links.length}</span>
                    </div>
                    {links.length === 0 ? (
                      <div className="text-mut-700 px-3 py-2 text-[12px]">
                        None linked — drag evidence here or use +.
                      </div>
                    ) : (
                      links.map((l) => {
                        const meta = evidenceMeta(evidenceById.get(l.id), kind);
                        return (
                          <div
                            key={l.link_id}
                            className="border-line/60 flex items-center gap-2 border-b px-3 py-1.5 last:border-b-0"
                          >
                            <span
                              style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: meta.dot,
                              }}
                            />
                            <span className="min-w-0 flex-1 truncate font-mono text-[12.5px]">
                              {l.human_id}
                            </span>
                            <span className="text-mut-700 font-mono text-[12px]">
                              {meta.metric}
                            </span>
                            <button
                              type="button"
                              title="Unlink"
                              onClick={() => deleteLink.mutate(l.link_id)}
                              className="text-mut-500 hover:text-fail-ink"
                            >
                              <X size={13} />
                            </button>
                          </div>
                        );
                      })
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Evidence catalog */}
      <div className="border-line bg-panel flex min-h-0 flex-col border-l">
        <div className="border-line flex flex-col gap-2 border-b p-3">
          <div className="flex items-baseline justify-between">
            <h4 className="font-head text-[18px]">Evidence catalog</h4>
            <span className="text-mut-700 font-mono text-[11px]">{filteredCatalog.length}</span>
          </div>
          <input
            value={catQuery}
            onChange={(e) => setCatQuery(e.target.value)}
            placeholder="Search tests, cg_*, a_*"
            className="border-line bg-canvas border px-2 py-1 text-[12.5px] outline-none"
          />
          <div className="border-line grid grid-cols-3 border">
            {(['all', 'git', 'regression'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSource(s)}
                className={cn(
                  'py-1 text-[12px] capitalize',
                  source === s ? 'bg-brand-100 text-brand-800' : 'text-mut-700 hover:bg-canvas',
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-1.5">
          {filteredCatalog.map((ev) => {
            const meta = evidenceMeta(ev, ev.kind);
            return (
              <div
                key={ev.id}
                draggable
                onDragStart={(e) => e.dataTransfer.setData(DRAG_KEY, ev.id)}
                className="border-line bg-canvas mb-1 flex flex-col gap-1 border p-2"
              >
                <div className="flex items-center gap-1.5">
                  <GripVertical size={12} className="text-mut-500 flex-none" />
                  <span className="text-brand-700 font-mono text-[9.5px] uppercase">{ev.kind}</span>
                  <span className="min-w-0 flex-1 truncate font-mono text-[11.5px]">{ev.fqn}</span>
                  <button
                    type="button"
                    title="Link to current plan item"
                    onClick={() => linkEvidence(ev.id)}
                    className="text-brand-700 hover:text-brand-800"
                  >
                    <Plus size={14} />
                  </button>
                </div>
                <div className="flex items-center gap-1.5 pl-[18px] text-[10.5px]">
                  {ev.in_git && <span className="bg-mut-200 text-mut-800 px-1">Git</span>}
                  {ev.in_regression && (
                    <span className="bg-brand-100 text-brand-800 px-1">Regression</span>
                  )}
                  {ev.link_count === 0 && (
                    <span className="px-1" style={{ color: 'var(--st-sus-ink)' }}>
                      orphan
                    </span>
                  )}
                  <span className="flex-1" />
                  <span className="text-mut-700 font-mono">{meta.metric}</span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="border-line text-mut-700 border-t p-2 text-[11.5px]">
          Drag onto the plan item, or press + · synced from Git and vManager
        </div>
      </div>
    </div>
  );
}
