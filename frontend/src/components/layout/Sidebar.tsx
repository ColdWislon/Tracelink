import {
  FileText,
  FlaskConical,
  Grid3x3,
  Layers,
  LayoutDashboard,
  Link2,
  ListChecks,
  MessagesSquare,
} from 'lucide-react';

import type { ProjectNode, RegressionRun } from '@/api/types';
import { cn } from '@/lib/cn';

import { SECTION_LABELS, type Section } from './types';

function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '';
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.round(diffMs / 3_600_000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}

const NAV: { section: Section; icon: typeof FileText }[] = [
  { section: 'requirements', icon: FileText },
  { section: 'plan', icon: ListChecks },
  { section: 'evidence', icon: FlaskConical },
  { section: 'trace', icon: Grid3x3 },
  { section: 'dashboard', icon: LayoutDashboard },
  { section: 'reviews', icon: MessagesSquare },
  { section: 'baselines', icon: Layers },
];

interface Props {
  projects: ProjectNode[];
  selectedProjectId: string | undefined;
  onSelectProject: (id: string) => void;
  section: Section;
  onSection: (s: Section) => void;
  latestRun?: RegressionRun;
}

function TreeNode({
  node,
  depth,
  selectedProjectId,
  onSelectProject,
}: {
  node: ProjectNode;
  depth: number;
  selectedProjectId: string | undefined;
  onSelectProject: (id: string) => void;
}) {
  const selected = node.id === selectedProjectId;
  return (
    <>
      <button
        type="button"
        onClick={() => onSelectProject(node.id)}
        style={{ paddingLeft: 8 + depth * 14 }}
        className={cn(
          'flex w-full items-center gap-1.5 py-1 pr-2 text-left',
          selected ? 'bg-brand-100 text-brand-800' : 'text-ink hover:bg-mut-200/60',
        )}
      >
        <span className="min-w-0 flex-1 truncate" style={{ fontWeight: depth === 0 ? 600 : 400 }}>
          {node.name}
        </span>
        <span className="text-mut-700 font-mono text-[11px]">{node.item_count || ''}</span>
      </button>
      {node.children.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          depth={depth + 1}
          selectedProjectId={selectedProjectId}
          onSelectProject={onSelectProject}
        />
      ))}
    </>
  );
}

export function Sidebar({
  projects,
  selectedProjectId,
  onSelectProject,
  section,
  onSection,
  latestRun,
}: Props) {
  const root = projects[0];
  return (
    <aside className="border-line bg-panel row-span-2 flex min-h-0 flex-col border-r">
      <div className="border-line flex h-12 flex-none items-center gap-2 border-b px-3.5">
        <Link2 className="text-brand" size={18} strokeWidth={1.5} />
        <span className="font-head text-[19px] font-semibold tracking-tight">Tracelink</span>
      </div>

      {root?.variants?.length ? (
        <div className="flex flex-col gap-2 px-2.5 pt-3">
          <div className="border-line flex flex-col border px-2.5 py-1.5">
            <span className="text-mut-700 text-[10px] tracking-widest uppercase">Project</span>
            <span className="font-head text-[15px] font-semibold">{root.name}</span>
          </div>
          <div className="border-line grid grid-cols-2 border">
            {root.variants.map((v) => (
              <span
                key={v.id}
                className="border-line text-mut-700 px-0 py-1 text-center font-mono text-[12px] [&:not(:last-child)]:border-r"
              >
                {v.key}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col gap-3.5 overflow-auto px-2.5 pt-1 pb-3">
        <div className="flex flex-col gap-px">
          <div className="text-mut-700 px-2 py-1 text-[10px] tracking-widest uppercase">
            Hierarchy
          </div>
          {projects.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              depth={0}
              selectedProjectId={selectedProjectId}
              onSelectProject={onSelectProject}
            />
          ))}
        </div>

        <nav className="flex flex-col gap-px">
          <div className="text-mut-700 px-2 py-1 text-[10px] tracking-widest uppercase">
            Workspace
          </div>
          {NAV.map(({ section: s, icon: Icon }) => (
            <button
              key={s}
              type="button"
              onClick={() => onSection(s)}
              className={cn(
                'flex w-full items-center gap-2.5 px-2 py-1.5 text-left',
                section === s ? 'bg-brand-100 text-brand-800' : 'text-ink hover:bg-mut-200/60',
              )}
            >
              <Icon size={15} strokeWidth={1.5} />
              <span className="flex-1">{SECTION_LABELS[s]}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="border-line text-mut-700 flex flex-none items-center gap-2 border-t px-3.5 py-2.5 text-[11.5px]">
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--st-ok)' }} />
        {latestRun ? (
          <span>
            {latestRun.source} <span className="font-mono">{latestRun.external_id ?? ''}</span>{' '}
            imported {relativeTime(latestRun.imported_at)}
          </span>
        ) : (
          <span>No regression run imported</span>
        )}
      </div>
    </aside>
  );
}
