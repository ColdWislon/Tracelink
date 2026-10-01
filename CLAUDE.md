# Tracelink

Requirement-tracking web app for SoC/ASIC development, aimed at a digital
verification team (SystemVerilog/UVM, Cadence Xcelium/vManager/IMC, Jenkins CI).
Requirements **and** the verification plan are native to the app — no dependency
on vManager vPlan.

This file is the source of truth for architecture, conventions, commands, and the
roadmap. **Keep it updated as the app evolves.**

---

## Product in one paragraph

Two synchronized views (a Notion-like **document** editor and a spreadsheet-like
**grid**) over the same items. Items are requirements (authored in EARS style) and
verification-plan items. Plan items reference three kinds of **evidence** — UVM
tests, functional coverage (covergroups/coverpoints), and SVA assertions (code
coverage is out of scope). Evidence comes from Git (parsing the SV testbench) and
from regression results (vManager/Jenkins). A per-item **status** is computed from
the latest regression run and rolled up to requirements. Linking is done entirely
in the UI (drag & drop, autocomplete, `@mentions`). Change management (immutable
revisions, suspect links, baselines, reviews) is designed in from the start.

## Stack

| Layer     | Tech |
|-----------|------|
| Backend   | Python 3.12, FastAPI, SQLAlchemy 2.x + Alembic, Pydantic v2, PostgreSQL 16 (JSONB for configurable attributes) |
| Frontend  | React + TypeScript + Vite, TanStack Query, TanStack Table (grid), TipTap/ProseMirror (document), Tailwind v4, light/dark themes |
| CLI       | `rtrack-push` — Python CLI, ships with the backend package |
| Tooling   | ruff + mypy (Python); eslint + prettier (TS); pytest / vitest; Playwright later |
| Local dev | docker-compose (db + backend + frontend) |

> **Runtime vs. local dev.** The **target runtime is Python 3.12** (see
> `backend/Dockerfile`). The repo was scaffolded on a machine with Python 3.14
> only; a local `.venv` on 3.14 works for fast iteration, but Docker is the
> reference environment. Node target is 22 (Docker); scaffolded with Node 25.

## Repository layout

```
Tracelink/
  docker-compose.yml        db (pg16) + backend + frontend
  design_template/          high-fidelity design comp (authoritative UI spec + seed data)
  backend/
    pyproject.toml          ruff + mypy + pytest config; deps; rtrack-push entrypoint
    Dockerfile
    alembic.ini, alembic/   migrations (env.py injects the DB URL from settings)
    app/
      core/                 config (pydantic-settings), db (engine/session/Base)
      models/               SQLAlchemy ORM (imports every model for Alembic autogen)
      schemas/              Pydantic v2 request/response models
      repositories/         data access
      services/
        domain/             PURE, well-tested logic: id-gen, revisions, status, suspect, EARS
        ...                 orchestration services
      api/                  FastAPI routers
      llm/                  LLMProvider interface + stub
      catalog/              pyslang SystemVerilog scanner
      seed.py               seed mirroring design_template
    cli/rtrack_push/        regression/coverage push CLI (fake-data mode for now)
    tests/                  pytest
  frontend/
    src/{api,components,features,lib,test}
    src/index.css           design tokens (light/dark) exposed to Tailwind via @theme inline
```

## Architecture & conventions

- **Backend layering is strict:** `api → services → repositories → models`.
  Routers do no business logic; repositories do no business logic; services
  orchestrate. Keep **status computation and suspect-link logic as pure domain
  functions** in `app/services/domain/` — no DB, no I/O — so they are trivially
  unit-testable.
- **Every edit creates an immutable `ItemRevision`.** `Item` points at its current
  revision. Never mutate a revision in place.
- **A `Link` stores the upstream revision it was last reviewed against.** It is
  **suspect** when the upstream's current revision differs. "Clear suspect"
  re-pins to the current upstream revision.
- **Status rule (default, configurable).** A verification item is `covered` when
  all linked tests pass in the latest run, all coverpoints reach their goal, and
  all assertions fired with zero failures; `partial` when some evidence is
  satisfied; `failing` when evidence failed; `not run` when evidence exists but
  never ran; `uncovered` when there is no evidence. A requirement rolls up from its
  plan items (all required by default; weighting is a later option).
- **Configurable attributes** live in JSONB on `Item`, validated against the
  item's `ItemType` schema.
- **Auth is a pluggable seam.** A single local user (`TRACELINK_CURRENT_USER`) for
  now; do not hard-code identity outside that seam.
- **Pluggable LLM provider.** Everything AI goes behind `app/llm` `LLMProvider`;
  only a stub exists now.
- **Frontend colors** come from the design tokens in `src/index.css`. Use the
  Tailwind semantic utilities (`bg-canvas`, `bg-panel`, `text-ink`, `border-line`,
  `text-brand-700`, `bg-mut-200`, `text-ok-ink`, …) rather than raw hex. Fonts:
  `font-sans` (Barlow), `font-head` (Barlow Condensed), `font-mono` (JetBrains Mono).

## Commands

### Everything via Docker (reference environment)
```bash
docker compose up --build        # db + backend (migrate + seed + reload) + frontend
docker compose up -d db          # just Postgres
```
Backend: http://localhost:8000 (docs at `/docs`). Frontend: http://localhost:5173.

### Backend (local venv)
```bash
cd backend
py -m venv .venv && ./.venv/Scripts/python -m pip install -e ".[dev]"
./.venv/Scripts/ruff check . && ./.venv/Scripts/ruff format --check .
./.venv/Scripts/mypy app cli
./.venv/Scripts/pytest
# migrations / seed (needs Postgres up; set TRACELINK_DATABASE_URL if not default)
./.venv/Scripts/python -m alembic upgrade head
./.venv/Scripts/python -m app.seed
```

### Frontend
```bash
cd frontend
npm install
npm run typecheck && npm run lint && npm run format:check
npm run test
npm run dev        # or: npm run build
```

## Working rules (for this project)

- Work **phase by phase, in small verifiable steps**. Run tests + linters after
  each step and fix failures before moving on.
- **Write tests for all domain logic** (revisions, suspect detection, status
  computation, EARS checks).
- **Commit at the end of each coherent step** with a clear message.
- **Ask before any change to the data model or the stack.**

## Roadmap

- **Phase 0 — Scaffold & infra.** ✅ Repo layout, docker-compose, backend + frontend
  skeletons, tooling green, Alembic + DB up, this file.
- **Phase 1 — Authoring.** ✅ Project/Item CRUD, ItemTypes + attribute templates,
  revisions on every save; document view (TipTap: requirement blocks, slash menu,
  inline status badges, EARS underline+tooltip); grid view (TanStack Table: inline
  edit, filter, sort, multi-select); EARS quality checker. Status computation is
  implemented and tested this phase (badges/grid read it from the seeded run).
  → **Session checkpoint after Phase 1 (reached).**
- **Phase 2 — Linking & traceability.** ✅ Link create/delete/clear-suspect APIs;
  `@mention` autocomplete creating links; evidence-catalog drag & drop onto plan
  items (Verification Plan view); item detail drawer (Details / Links + suspect +
  Clear / History with diff); traceability matrix with orphan highlighting.
- **Phase 3 — Regression import & status pipeline.** ✅ Ingestion endpoint +
  JSON Schema; run history + per-kind summaries; verification-closure dashboard
  (status counts, coverage %, suspect/orphan counts, latest run); import-run UI;
  `rtrack-push --fake`/`--file`. *(The real Cadence vManager/IMC export that
  produces the payload stays out of scope — no tooling here; the documented JSON
  payload is the ingestion contract.)*
- **Phase 4 — Reviews & baselines UI.**
- **Phase 5 — IP reuse & variants UI.**
- **Phase 6 — AI assistant & Word import.**

### Scaffolded early, non-blocking
- `LLMProvider` interface + stub (`app/llm`).
- Regression-ingestion `POST` endpoint + documented JSON Schema.
- `rtrack-push` CLI with a fake-data mode.
- pyslang SystemVerilog catalog scanner with fixture tests.
