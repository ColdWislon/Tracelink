import { AlertTriangle, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';

import type { Item, ItemCreate, ItemType, ItemUpdate, LinkCreate, LinkRef } from '@/api/types';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { SUSPECT_STYLE } from '@/lib/status';

import { EarsEditor } from './EarsEditor';
import type { MentionItem } from './MentionList';

interface Props {
  projectName: string;
  requirements: Item[];
  linkTargets: Item[];
  requirementType: ItemType | undefined;
  onUpdate: (id: string, patch: ItemUpdate) => void;
  onCreate: (payload: ItemCreate) => void;
  onCreateLink: (payload: LinkCreate) => void;
  onOpenItem: (id: string) => void;
  projectId: string;
}

const WORKFLOW_LABEL: Record<string, string> = {
  draft: 'Draft',
  in_review: 'In review',
  approved: 'Approved',
};

function DownstreamChip({ ref: link }: { ref: LinkRef }) {
  if (link.suspect) {
    return (
      <span
        className="inline-flex items-center gap-1 border px-1.5 py-px font-mono text-[11px]"
        style={{
          borderColor: SUSPECT_STYLE.color,
          color: SUSPECT_STYLE.ink,
          background: SUSPECT_STYLE.bg,
        }}
      >
        <AlertTriangle size={11} /> {link.human_id} · suspect
      </span>
    );
  }
  return (
    <span className="border-line text-ink border px-1.5 py-px font-mono text-[11px]">
      ↳ {link.human_id}
    </span>
  );
}

function RequirementBlock({
  item,
  linkTargets,
  onUpdate,
  onCreateLink,
  onOpenItem,
}: {
  item: Item;
  linkTargets: Item[];
  onUpdate: (id: string, patch: ItemUpdate) => void;
  onCreateLink: (payload: LinkCreate) => void;
  onOpenItem: (id: string) => void;
}) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [title, setTitle] = useState(item.title);
  const [pattern, setPattern] = useState<string | null>(item.ears_pattern);

  const mentionItems: MentionItem[] = useMemo(
    () =>
      linkTargets
        .filter((t) => t.id !== item.id)
        .map((t) => ({
          id: t.id,
          human_id: t.human_id,
          title: t.title,
          base_kind: t.base_kind,
          status: t.status,
        })),
    [linkTargets, item.id],
  );

  const onMention = (mentioned: MentionItem) => {
    // Mentioning a plan item verifies this requirement; mentioning a requirement
    // records a derives_from (this item derives from the mentioned upstream).
    if (mentioned.base_kind === 'verification_item') {
      onCreateLink({
        link_type: 'verified_by',
        upstream_item_id: item.id,
        downstream_item_id: mentioned.id,
      });
    } else {
      onCreateLink({
        link_type: 'derives_from',
        upstream_item_id: mentioned.id,
        downstream_item_id: item.id,
      });
    }
  };

  const commitTitle = () => {
    setEditingTitle(false);
    if (title.trim() && title !== item.title) onUpdate(item.id, { title: title.trim() });
  };

  return (
    <div
      className="grid gap-3 px-2.5 py-3"
      style={{ gridTemplateColumns: '24px minmax(0,1fr) 96px' }}
    >
      <div className="flex justify-center pt-1.5">
        <StatusDot status={item.status} size={10} />
      </div>
      <div className="min-w-0">
        <div className="mb-1 flex flex-wrap items-baseline gap-2">
          <button
            type="button"
            onClick={() => onOpenItem(item.id)}
            className="text-brand-700 font-mono text-[11.5px] hover:underline"
          >
            {item.human_id}
          </button>
          {editingTitle ? (
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commitTitle();
                if (e.key === 'Escape') {
                  setTitle(item.title);
                  setEditingTitle(false);
                }
              }}
              className="border-brand bg-canvas border px-1 text-[14.5px] font-semibold outline-none"
            />
          ) : (
            <button
              type="button"
              onClick={() => setEditingTitle(true)}
              className="text-left text-[14.5px] font-semibold hover:underline"
            >
              {item.title}
            </button>
          )}
          <span
            className="text-[11px]"
            style={{ color: pattern ? 'var(--color-neutral-700)' : 'var(--st-fail-ink)' }}
          >
            {pattern ?? 'No EARS pattern'}
          </span>
        </div>

        <div className="ears-body text-[14.5px] leading-relaxed">
          <EarsEditor
            body={item.body}
            onCommit={(text) => onUpdate(item.id, { body: text })}
            onReport={(report) => setPattern(report.pattern)}
            mentionItems={mentionItems}
            onMention={onMention}
          />
        </div>

        {item.downstream.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {item.downstream.map((link) => (
              <DownstreamChip key={link.link_id} ref={link} />
            ))}
          </div>
        )}
      </div>
      <div className="flex flex-col items-end gap-1 pt-0.5">
        <StatusBadge status={item.status} />
        <span className="text-mut-700 text-[11px]">{WORKFLOW_LABEL[item.workflow_status]}</span>
      </div>
    </div>
  );
}

const TEMPLATES: { label: string; hint: string; body: string }[] = [
  { label: 'Requirement', hint: 'Blank requirement block', body: 'The system shall ' },
  {
    label: 'Template — Event-driven',
    hint: 'When <trigger>, … shall …',
    body: 'When <trigger>, the system shall <response>.',
  },
  {
    label: 'Template — State-driven',
    hint: 'While <state>, … shall …',
    body: 'While <state>, the system shall <response>.',
  },
  {
    label: 'Template — Ubiquitous',
    hint: 'The <system> shall …',
    body: 'The system shall <response>.',
  },
];

function AddBlock({
  requirementType,
  projectId,
  onCreate,
}: {
  requirementType: ItemType | undefined;
  projectId: string;
  onCreate: (payload: ItemCreate) => void;
}) {
  const [value, setValue] = useState('');
  const open = value.startsWith('/');
  const filter = value.slice(1).toLowerCase();
  const options = useMemo(
    () => TEMPLATES.filter((t) => t.label.toLowerCase().includes(filter)),
    [filter],
  );

  if (!requirementType) return null;

  const insert = (body: string) => {
    onCreate({
      project_id: projectId,
      item_type_id: requirementType.id,
      title: 'New requirement',
      body,
      attributes: { priority: 'P2' },
    });
    setValue('');
  };

  return (
    <div
      className="relative grid gap-3 px-2.5 py-3"
      style={{ gridTemplateColumns: '24px minmax(0,1fr)' }}
    >
      <div className="text-mut-500 flex justify-center pt-1">
        <Plus size={14} />
      </div>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder='Type "/" for commands to insert a requirement or template…'
        className="text-ink placeholder:text-mut-500 bg-transparent text-[14.5px] outline-none"
      />
      {open && (
        <div
          className="border-line bg-canvas absolute top-10 left-11 z-20 w-[360px] border p-1"
          style={{ boxShadow: 'var(--shadow-lg)' }}
        >
          {options.map((opt) => (
            <button
              key={opt.label}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                insert(opt.body);
              }}
              className="hover:bg-mut-200/60 flex w-full flex-col px-2 py-1.5 text-left"
            >
              <span className="text-[13px] font-medium">{opt.label}</span>
              <span className="text-mut-700 font-mono text-[11px]">{opt.hint}</span>
            </button>
          ))}
          {options.length === 0 && (
            <div className="text-mut-700 px-2 py-1.5 text-[13px]">No commands</div>
          )}
        </div>
      )}
    </div>
  );
}

export function DocumentView({
  projectName,
  requirements,
  linkTargets,
  requirementType,
  onUpdate,
  onCreate,
  onCreateLink,
  onOpenItem,
  projectId,
}: Props) {
  const counts = useMemo(() => {
    const by = { covered: 0, partial: 0, not_run: 0 } as Record<string, number>;
    for (const r of requirements) if (r.status && r.status in by) by[r.status] += 1;
    return by;
  }, [requirements]);

  return (
    <div className="mx-auto max-w-[880px] px-8 pt-7 pb-40">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-brand-700 mb-1 text-[11px] tracking-widest uppercase">
            Requirements · Document
          </div>
          <h1 className="font-head text-[34px]">{projectName}</h1>
          <div className="text-mut-700 mt-1 text-[12px]">{requirements.length} requirements</div>
        </div>
        <div className="text-mut-700 flex gap-3.5 text-[12px]">
          <span className="flex items-center gap-1.5">
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--st-ok)' }}
            />
            {counts.covered} covered
          </span>
          <span className="flex items-center gap-1.5">
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--st-part)' }}
            />
            {counts.partial} partial
          </span>
          <span className="flex items-center gap-1.5">
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--st-none)' }}
            />
            {counts.not_run} not run
          </span>
        </div>
      </div>

      <div className="divide-line/60 divide-y">
        {requirements.map((item) => (
          <RequirementBlock
            key={item.id}
            item={item}
            linkTargets={linkTargets}
            onUpdate={onUpdate}
            onCreateLink={onCreateLink}
            onOpenItem={onOpenItem}
          />
        ))}
      </div>

      <AddBlock requirementType={requirementType} projectId={projectId} onCreate={onCreate} />
    </div>
  );
}
