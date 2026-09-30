import { AlertTriangle, X } from 'lucide-react';
import { useEffect, useState } from 'react';

import { useClearSuspect, useItem } from '@/api/hooks';
import type { ItemDetail, LinkRef, Revision } from '@/api/types';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { cn } from '@/lib/cn';
import { diffText, stripHtml } from '@/lib/diff';
import { SUSPECT_STYLE } from '@/lib/status';

type Tab = 'details' | 'links' | 'history';

const KIND_LABEL: Record<string, string> = {
  requirement: 'Requirement',
  verification_item: 'Verification item',
  other: 'Item',
};
const WORKFLOW_LABEL: Record<string, string> = {
  draft: 'Draft',
  in_review: 'In review',
  approved: 'Approved',
};

function DiffBlock({ oldBody, newBody }: { oldBody: string; newBody: string }) {
  const d = diffText(stripHtml(oldBody), stripHtml(newBody));
  if (!d.changed) return null;
  return (
    <span className="border-line bg-canvas block border px-2 py-1.5 text-[12.5px] leading-relaxed">
      {d.pre}
      {d.deleted && (
        <del style={{ background: 'var(--st-fail-bg)', color: 'var(--st-fail-ink)' }}>
          {d.deleted}
        </del>
      )}
      {d.inserted && (
        <ins
          style={{
            background: 'var(--st-ok-bg)',
            color: 'var(--st-ok-ink)',
            textDecoration: 'none',
          }}
        >
          {d.inserted}
        </ins>
      )}
      {d.post}
    </span>
  );
}

function LinkRow({
  link,
  itemRevisions,
  isUpstream,
  onClear,
  onOpenItem,
}: {
  link: LinkRef;
  itemRevisions: Revision[];
  isUpstream: boolean;
  onClear: (linkId: string) => void;
  onOpenItem: (id: string) => void;
}) {
  // A downstream suspect link means THIS item changed — show its latest diff.
  const selfDiff = !isUpstream && link.suspect && itemRevisions.length >= 2 ? itemRevisions : null;
  return (
    <div className="border-line border">
      <button
        type="button"
        onClick={() => link.target === 'item' && onOpenItem(link.id)}
        className="grid w-full items-center gap-2 px-2.5 py-1.5 text-left"
        style={{ gridTemplateColumns: '8px minmax(0,1fr) auto' }}
      >
        {link.target === 'item' ? <StatusDot status={link.status ?? null} /> : <span />}
        <span className="flex min-w-0 flex-col leading-tight">
          <span className="text-brand-700 font-mono text-[11.5px]">{link.human_id}</span>
          <span className="truncate text-[12.5px]">{link.title}</span>
        </span>
        <span className="text-mut-700 text-[11px]">
          {link.evidence_kind ?? link.link_type.replace('_', ' ')}
        </span>
      </button>
      {link.suspect && (
        <div
          className="flex flex-col gap-2 border-t px-2.5 py-2 text-[12px]"
          style={{
            borderColor: SUSPECT_STYLE.color,
            background: SUSPECT_STYLE.bg,
            color: SUSPECT_STYLE.ink,
          }}
        >
          <span className="flex items-center gap-1.5">
            <AlertTriangle size={13} />
            <b className="font-semibold">Suspect</b> · upstream changed since last review
          </span>
          {selfDiff && <DiffBlock oldBody={selfDiff[1].body} newBody={selfDiff[0].body} />}
          <div className="flex gap-1.5">
            {isUpstream && (
              <button
                type="button"
                onClick={() => onOpenItem(link.id)}
                className="border px-2 py-0.5"
                style={{ borderColor: SUSPECT_STYLE.color, color: SUSPECT_STYLE.ink }}
              >
                Review change
              </button>
            )}
            <button
              type="button"
              onClick={() => onClear(link.link_id)}
              className="border px-2 py-0.5"
              style={{ borderColor: SUSPECT_STYLE.color, color: SUSPECT_STYLE.ink }}
            >
              Clear suspect
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailsTab({ item }: { item: ItemDetail }) {
  const attrs = Object.entries(item.attributes ?? {}).filter(([, v]) => v !== null && v !== '');
  return (
    <div>
      <div className="text-mut-700 mb-1 text-[10.5px] tracking-wider uppercase">
        Statement{item.ears_pattern ? ` · ${item.ears_pattern}` : ''}
      </div>
      <div
        className="border-line mb-4 border px-3 py-2.5 text-[14px] leading-relaxed"
        dangerouslySetInnerHTML={{ __html: item.body || '<em>No statement</em>' }}
      />
      <div className="grid text-[13px]" style={{ gridTemplateColumns: '110px minmax(0,1fr)' }}>
        <Field k="Status" v={<StatusBadge status={item.status} />} />
        <Field k="Workflow" v={WORKFLOW_LABEL[item.workflow_status]} />
        <Field k="Variants" v={item.applicability ?? 'All'} />
        {attrs.map(([k, v]) => (
          <Field key={k} k={cap(k)} v={String(v)} />
        ))}
      </div>
    </div>
  );
}

function Field({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <>
      <div className="border-line/60 text-mut-700 border-b py-1.5">{k}</div>
      <div className="border-line/60 border-b py-1.5">{v}</div>
    </>
  );
}

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function ItemDrawer({
  itemId,
  projectId,
  onClose,
  onOpenItem,
}: {
  itemId: string | undefined;
  projectId: string | undefined;
  onClose: () => void;
  onOpenItem: (id: string) => void;
}) {
  const [tab, setTab] = useState<Tab>('details');
  const { data: item } = useItem(itemId);
  const clearSuspect = useClearSuspect(projectId);

  useEffect(() => setTab('details'), [itemId]);

  if (!itemId) return null;

  return (
    <aside
      className="border-line bg-canvas fixed top-12 right-0 bottom-0 z-40 flex w-[392px] max-w-[92%] flex-col border-l"
      style={{ boxShadow: 'var(--shadow-lg)' }}
    >
      {!item ? (
        <div className="text-mut-700 p-4">Loading…</div>
      ) : (
        <>
          <div className="flex-none px-4 pt-3.5">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-brand-700 font-mono text-[12px]">{item.human_id}</span>
              <span className="text-mut-700 text-[11px]">{KIND_LABEL[item.base_kind]}</span>
              <span className="flex-1" />
              <StatusBadge status={item.status} />
              <button
                type="button"
                onClick={onClose}
                title="Close"
                className="text-ink hover:bg-panel flex h-6 w-6 items-center justify-center"
              >
                <X size={15} />
              </button>
            </div>
            <h3 className="font-head mb-2.5 text-[22px]">{item.title}</h3>
            <div className="border-line flex gap-4 border-b">
              {(
                [
                  ['details', 'Details', ''],
                  ['links', 'Links', String(item.upstream.length + item.downstream.length)],
                  ['history', 'History', String(item.revisions.length)],
                ] as [Tab, string, string][]
              ).map(([id, label, count]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setTab(id)}
                  className={cn(
                    '-mb-px flex items-center gap-1.5 border-b-2 pt-1.5 pb-2 text-[13px]',
                    tab === id ? 'border-brand text-ink' : 'text-mut-700 border-transparent',
                  )}
                >
                  {label}
                  {count && <span className="text-mut-700 font-mono text-[10.5px]">{count}</span>}
                </button>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-auto px-4 pt-3.5 pb-6">
            {tab === 'details' && <DetailsTab item={item} />}
            {tab === 'links' && (
              <div className="flex flex-col gap-4">
                <Section title={`↑ Upstream`}>
                  {item.upstream.length === 0 ? (
                    <Empty>No upstream links.</Empty>
                  ) : (
                    item.upstream.map((l) => (
                      <LinkRow
                        key={l.link_id}
                        link={l}
                        itemRevisions={item.revisions}
                        isUpstream
                        onClear={(id) => clearSuspect.mutate(id)}
                        onOpenItem={onOpenItem}
                      />
                    ))
                  )}
                </Section>
                <Section title="↓ Downstream">
                  {item.downstream.length === 0 ? (
                    <Empty>No downstream links.</Empty>
                  ) : (
                    item.downstream.map((l) => (
                      <LinkRow
                        key={l.link_id}
                        link={l}
                        itemRevisions={item.revisions}
                        isUpstream={false}
                        onClear={(id) => clearSuspect.mutate(id)}
                        onOpenItem={onOpenItem}
                      />
                    ))
                  )}
                </Section>
              </div>
            )}
            {tab === 'history' && (
              <div className="flex flex-col">
                {item.revisions.map((rev, i) => {
                  const older = item.revisions[i + 1];
                  return (
                    <div
                      key={rev.id}
                      className="grid gap-2.5"
                      style={{ gridTemplateColumns: '14px minmax(0,1fr)' }}
                    >
                      <div className="flex flex-col items-center">
                        <span
                          className="mt-1 h-2.5 w-2.5 rounded-full"
                          style={{
                            background: i === 0 ? 'var(--st-ok)' : 'var(--color-neutral-400)',
                          }}
                        />
                        <span
                          className="w-px flex-1"
                          style={{ background: 'var(--color-divider)' }}
                        />
                      </div>
                      <div className="min-w-0 pb-4">
                        <div className="flex items-baseline gap-2">
                          <span className="font-mono text-[11.5px] font-medium">
                            r{rev.rev_number}
                          </span>
                          <span className="text-[13px]">{rev.message ?? 'Edited'}</span>
                        </div>
                        <div className="text-mut-700 text-[11.5px]">
                          {rev.author} · {new Date(rev.created_at).toLocaleString()}
                        </div>
                        {older && (
                          <div className="mt-1.5">
                            <DiffBlock oldBody={older.body} newBody={rev.body} />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-mut-700 mb-1.5 text-[10.5px] tracking-wider uppercase">{title}</div>
      <div className="flex flex-col gap-1.5">{children}</div>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="px-2.5 py-2 text-[12.5px]"
      style={{ background: 'var(--st-fail-bg)', color: 'var(--st-fail-ink)' }}
    >
      {children}
    </div>
  );
}
