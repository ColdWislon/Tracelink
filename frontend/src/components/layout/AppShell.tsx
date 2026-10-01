import { useEffect, useMemo, useState } from 'react';

import type { ProjectNode } from '@/api/types';
import { useBaselines, useProjects, useRuns } from '@/api/hooks';
import { applyTheme, getInitialTheme, type Theme } from '@/lib/theme';
import { ItemDrawer } from '@/components/drawer/ItemDrawer';
import { BaselinesView } from '@/features/baselines/BaselinesView';
import { DashboardView } from '@/features/dashboard/DashboardView';
import { PlanView } from '@/features/plan/PlanView';
import { RequirementsView } from '@/features/requirements/RequirementsView';
import { TraceView } from '@/features/trace/TraceView';

import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { SECTION_LABELS, type Section, type View } from './types';

function flatten(nodes: ProjectNode[]): ProjectNode[] {
  return nodes.flatMap((n) => [n, ...flatten(n.children)]);
}

export function AppShell() {
  const { data: projects = [], isLoading, isError } = useProjects();
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();
  const [section, setSection] = useState<Section>('requirements');
  const [view, setView] = useState<View>('document');
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [openItemId, setOpenItemId] = useState<string | undefined>();

  const all = useMemo(() => flatten(projects), [projects]);
  const socName = projects[0]?.name ?? 'Tracelink';

  // Default to the first IP that has items (falls back to any project).
  useEffect(() => {
    if (selectedProjectId || all.length === 0) return;
    const withItems = all.find((p) => p.item_count > 0);
    setSelectedProjectId((withItems ?? all[0]).id);
  }, [all, selectedProjectId]);

  const project = all.find((p) => p.id === selectedProjectId);
  const { data: runs = [] } = useRuns(selectedProjectId);
  const latestRun = runs[0];
  const { data: baselines = [] } = useBaselines(selectedProjectId);
  const [viewingBaselineId, setViewingBaselineId] = useState<string | undefined>();
  const viewingBaseline = baselines.find((b) => b.id === viewingBaselineId);
  const readOnly = Boolean(viewingBaseline);

  const toggleTheme = () =>
    setTheme((prev) => {
      const next: Theme = prev === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      return next;
    });

  return (
    <div
      className="bg-canvas text-ink grid h-screen"
      style={{ gridTemplateColumns: '232px minmax(0,1fr)', gridTemplateRows: '48px minmax(0,1fr)' }}
    >
      <Sidebar
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={(id) => {
          setSelectedProjectId(id);
          setViewingBaselineId(undefined);
        }}
        section={section}
        onSection={setSection}
        latestRun={latestRun}
      />
      <Header
        socName={socName}
        project={project}
        section={section}
        view={view}
        onView={setView}
        theme={theme}
        onToggleTheme={toggleTheme}
        baselines={baselines}
        viewingBaselineId={viewingBaselineId}
        onSelectBaseline={setViewingBaselineId}
      />
      <main className="col-start-2 flex min-h-0 min-w-0 flex-col overflow-hidden">
        {viewingBaseline && (
          <div className="border-line bg-brand-100 text-brand-800 flex flex-none items-center gap-2.5 border-b px-4 py-1.5 text-[12.5px]">
            <span>
              Viewing baseline <b className="font-semibold">{viewingBaseline.name}</b> (
              {new Date(viewingBaseline.created_at).toLocaleDateString()}) — read-only snapshot.
            </span>
            <button
              type="button"
              onClick={() => setViewingBaselineId(undefined)}
              className="ml-auto hover:underline"
            >
              Back to Working
            </button>
          </div>
        )}
        <div className="min-h-0 flex-1 overflow-auto">
          {isLoading ? (
            <div className="text-mut-700 p-8">Loading…</div>
          ) : isError ? (
            <div className="text-fail-ink p-8">
              Could not reach the API. Is the backend running on{' '}
              <span className="font-mono">:8000</span>?
            </div>
          ) : section === 'requirements' ? (
            <RequirementsView
              project={project}
              view={view}
              onOpenItem={setOpenItemId}
              readOnly={readOnly}
            />
          ) : section === 'plan' ? (
            <PlanView project={project} onOpenItem={setOpenItemId} readOnly={readOnly} />
          ) : section === 'trace' ? (
            <TraceView project={project} onOpenItem={setOpenItemId} />
          ) : section === 'dashboard' ? (
            <DashboardView project={project} />
          ) : section === 'baselines' ? (
            <BaselinesView project={project} />
          ) : (
            <div className="text-mut-700 p-8">
              <span className="font-head text-ink text-xl">{SECTION_LABELS[section]}</span>
              <p className="mt-1 text-[13px]">Arrives in a later phase.</p>
            </div>
          )}
        </div>
      </main>
      <ItemDrawer
        itemId={openItemId}
        projectId={selectedProjectId}
        onClose={() => setOpenItemId(undefined)}
        onOpenItem={setOpenItemId}
      />
    </div>
  );
}
