import { FileText, Grid3x3, Moon, Sun } from 'lucide-react';

import type { ProjectNode } from '@/api/types';
import type { Theme } from '@/lib/theme';
import { cn } from '@/lib/cn';

import { SECTION_LABELS, type Section, type View } from './types';

interface Props {
  socName: string;
  project: ProjectNode | undefined;
  section: Section;
  view: View;
  onView: (v: View) => void;
  theme: Theme;
  onToggleTheme: () => void;
}

export function Header({ socName, project, section, view, onView, theme, onToggleTheme }: Props) {
  return (
    <header className="border-line col-start-2 flex min-w-0 items-center gap-3 border-b px-3.5">
      <div className="flex min-w-0 flex-[0_1_auto] items-center gap-1.5 overflow-hidden text-[13px] whitespace-nowrap">
        <span className="text-mut-700 flex-none">{socName}</span>
        <span className="text-mut-500 flex-none">/</span>
        <span className="text-mut-700 min-w-0 truncate">{project?.name ?? '—'}</span>
        <span className="text-mut-500 flex-none">/</span>
        <span className="flex-none font-semibold">{SECTION_LABELS[section]}</span>
      </div>

      <span className="flex-1" />

      {section === 'requirements' ? (
        <div className="border-line flex flex-none border">
          <button
            type="button"
            onClick={() => onView('document')}
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 text-[12.5px]',
              view === 'document' ? 'bg-brand-100 text-brand-800' : 'text-ink hover:bg-panel',
            )}
          >
            <FileText size={14} strokeWidth={1.5} /> Document
          </button>
          <button
            type="button"
            onClick={() => onView('grid')}
            className={cn(
              'border-line flex items-center gap-1.5 border-l px-2.5 py-1 text-[12.5px]',
              view === 'grid' ? 'bg-brand-100 text-brand-800' : 'text-ink hover:bg-panel',
            )}
          >
            <Grid3x3 size={14} strokeWidth={1.5} /> Grid
          </button>
        </div>
      ) : null}

      <button
        type="button"
        onClick={onToggleTheme}
        title="Toggle theme"
        className="text-ink hover:bg-panel flex h-[30px] w-[30px] flex-none items-center justify-center"
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
      </button>
      <div
        title="Clara Martin — Verification"
        className="bg-brand-200 text-brand-800 grid h-7 w-7 flex-none place-items-center rounded-full text-[11px] font-semibold"
      >
        CM
      </div>
    </header>
  );
}
