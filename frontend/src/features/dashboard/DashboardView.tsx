import { AlertTriangle, UploadCloud } from 'lucide-react';
import { useState } from 'react';

import { useDashboard, useIngestRun, useRuns } from '@/api/hooks';
import type { KindSummary, ProjectNode, RegressionRun, StatusCounts } from '@/api/types';
import { statusStyle } from '@/lib/status';
import type { VerificationStatus } from '@/api/types';

const ORDER: VerificationStatus[] = ['covered', 'partial', 'failing', 'not_run', 'uncovered'];

function StatusBar({ counts }: { counts: StatusCounts }) {
  const total = ORDER.reduce((sum, s) => sum + counts[s], 0) || 1;
  return (
    <div>
      <div className="flex h-2.5 w-full overflow-hidden rounded-sm">
        {ORDER.map((s) =>
          counts[s] > 0 ? (
            <span
              key={s}
              title={`${statusStyle(s).label}: ${counts[s]}`}
              style={{ width: `${(100 * counts[s]) / total}%`, background: statusStyle(s).dot }}
            />
          ) : null,
        )}
      </div>
      <div className="text-mut-700 mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[11.5px]">
        {ORDER.map((s) => (
          <span key={s} className="flex items-center gap-1">
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: statusStyle(s).dot }}
            />
            {statusStyle(s).label} {counts[s]}
          </span>
        ))}
      </div>
    </div>
  );
}

function Tile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="border-line flex flex-col gap-1.5 border px-4 py-3.5">
      <div className="text-mut-700 text-[10.5px] tracking-widest uppercase">{label}</div>
      <div
        className="font-head text-[36px] leading-none"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      {sub && <div className="text-mut-700 text-[12.5px]">{sub}</div>}
    </div>
  );
}

function kindLine(label: string, s: KindSummary): string {
  const parts = [`${s.satisfied}/${s.total} ok`];
  if (s.partial) parts.push(`${s.partial} partial`);
  if (s.failing) parts.push(`${s.failing} failing`);
  if (s.not_run) parts.push(`${s.not_run} not run`);
  return `${label}: ${parts.join(' · ')}`;
}

function RunRow({ run }: { run: RegressionRun }) {
  const when = run.imported_at ? new Date(run.imported_at).toLocaleString() : '—';
  return (
    <div className="border-line border px-3 py-2">
      <div className="flex items-baseline gap-2">
        <span className="text-brand-700 font-mono text-[12.5px]">
          {run.source} {run.external_id ?? ''}
        </span>
        <span className="text-mut-700 text-[11.5px]">{when}</span>
        <span className="flex-1" />
        <span className="text-mut-700 font-mono text-[11.5px]">{run.result_count} results</span>
      </div>
      <div className="text-mut-700 mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-[11.5px]">
        <span>{kindLine('Tests', run.tests)}</span>
        <span>{kindLine('Coverage', run.coverpoints)}</span>
        <span>{kindLine('Assertions', run.assertions)}</span>
      </div>
    </div>
  );
}

function examplePayload(key: string): string {
  return JSON.stringify(
    {
      project_key: key,
      source: 'jenkins',
      external_id: '#1901',
      results: [
        { kind: 'test', fqn: `${key}_new_feature_test`, passed: 20, failed: 0, total: 20 },
        { kind: 'coverpoint', fqn: `cg_${key}.cp_new`, hits: 85, goal: 100 },
        { kind: 'assertion', fqn: `a_${key}_guard`, fired: 1200, failed: 0 },
      ],
    },
    null,
    2,
  );
}

function ImportPanel({ project }: { project: ProjectNode }) {
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const ingest = useIngestRun(project.id);

  const submit = () => {
    setError(null);
    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      setError('Payload is not valid JSON.');
      return;
    }
    ingest.mutate(payload, { onError: (e) => setError(String(e)) });
  };

  return (
    <div className="border-line border p-4">
      <div className="mb-1 flex items-center gap-2">
        <UploadCloud size={16} className="text-brand" />
        <h4 className="font-head text-[17px]">Import a regression run</h4>
      </div>
      <p className="text-mut-700 mb-2 text-[12.5px]">
        Paste a normalized payload (the JSON <span className="font-mono">rtrack-push</span> sends).
        New evidence is created on the fly; statuses recompute from the latest run.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="{ project_key, source, external_id, results: [...] }"
        className="border-line bg-canvas h-40 w-full border p-2 font-mono text-[12px] outline-none"
      />
      {error && <div className="text-fail-ink mt-1 text-[12px]">{error}</div>}
      {ingest.isSuccess && !error && (
        <div className="text-ok-ink mt-1 text-[12px]">Run imported — dashboard updated.</div>
      )}
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={submit}
          disabled={!text.trim() || ingest.isPending}
          className="bg-brand-600 text-canvas px-3 py-1 text-[12.5px] disabled:opacity-50"
        >
          Import run
        </button>
        <button
          type="button"
          onClick={() => setText(examplePayload(project.key))}
          className="border-line hover:bg-panel border px-3 py-1 text-[12.5px]"
        >
          Load example
        </button>
      </div>
    </div>
  );
}

export function DashboardView({ project }: { project: ProjectNode | undefined }) {
  const projectId = project?.id;
  const { data: dash, isLoading } = useDashboard(projectId);
  const { data: runs = [] } = useRuns(projectId);

  if (!project) return <div className="text-mut-700 p-8">Select an IP from the hierarchy.</div>;
  if (isLoading || !dash) return <div className="text-mut-700 p-8">Loading dashboard…</div>;

  return (
    <div className="max-w-[1180px] p-6 pb-16">
      <div className="text-brand-700 mb-1 text-[11px] tracking-widest uppercase">
        Dashboard · {project.name}
      </div>
      <h2 className="font-head mb-5 text-[28px]">Verification closure</h2>

      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Tile
          label="Requirements covered"
          value={`${dash.covered_pct}%`}
          sub={`${dash.requirements.covered} of ${dash.requirement_total} fully covered · ${dash.requirements.partial} partial`}
          accent="var(--st-ok-ink)"
        />
        <Tile
          label="Suspect links"
          value={dash.suspect_links}
          sub="upstream changed after review"
          accent={dash.suspect_links ? 'var(--st-sus-ink)' : undefined}
        />
        <Tile
          label="Failing"
          value={dash.requirements.failing}
          sub="requirements with a failing plan item"
          accent={dash.requirements.failing ? 'var(--st-fail-ink)' : undefined}
        />
        <Tile
          label="Orphans"
          value={dash.orphan_requirements + dash.orphan_verification_items + dash.orphan_evidence}
          sub={`${dash.orphan_requirements} req · ${dash.orphan_verification_items} plan · ${dash.orphan_evidence} evidence`}
        />
      </div>

      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <div className="border-line border p-4">
          <h4 className="font-head mb-3 text-[17px]">Requirements</h4>
          <StatusBar counts={dash.requirements} />
        </div>
        <div className="border-line border p-4">
          <h4 className="font-head mb-3 text-[17px]">Verification plan items</h4>
          <StatusBar counts={dash.verification_items} />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <h4 className="font-head text-[17px]">Regression runs</h4>
            {dash.suspect_links > 0 && (
              <span
                className="flex items-center gap-1 text-[11.5px]"
                style={{ color: 'var(--st-sus-ink)' }}
              >
                <AlertTriangle size={12} /> {dash.suspect_links} suspect
              </span>
            )}
          </div>
          <div className="flex flex-col gap-2">
            {runs.length === 0 ? (
              <div className="text-mut-700 text-[13px]">No runs imported yet.</div>
            ) : (
              runs.map((run) => <RunRow key={run.id} run={run} />)
            )}
          </div>
        </div>
        <ImportPanel project={project} />
      </div>
    </div>
  );
}
