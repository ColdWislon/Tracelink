// Mirrors the backend Pydantic read models (app/schemas).

export type VerificationStatus = 'covered' | 'partial' | 'failing' | 'not_run' | 'uncovered';

export type WorkflowStatus = 'draft' | 'in_review' | 'approved';
export type BaseKind = 'requirement' | 'verification_item' | 'other';
export type LinkType = 'derives_from' | 'verified_by' | 'evidenced_by';
export type EvidenceKind = 'test' | 'coverpoint' | 'assertion';

export interface Variant {
  id: string;
  key: string;
  name: string;
  description?: string | null;
}

export interface ProjectNode {
  id: string;
  key: string;
  name: string;
  kind: 'soc' | 'subsystem' | 'ip';
  parent_id: string | null;
  is_ip_library: boolean;
  description?: string | null;
  variants: Variant[];
  children: ProjectNode[];
  item_count: number;
}

export interface AttributeField {
  key: string;
  label?: string;
  type: 'string' | 'text' | 'number' | 'bool' | 'enum';
  required?: boolean;
  options?: string[];
  default?: unknown;
}

export interface ItemType {
  id: string;
  project_id: string | null;
  key: string;
  name: string;
  base_kind: BaseKind;
  id_prefix: string;
  attribute_schema: AttributeField[];
}

export interface LinkRef {
  link_id: string;
  link_type: LinkType;
  target: 'item' | 'evidence';
  id: string;
  human_id: string;
  title: string;
  suspect: boolean;
  base_kind?: BaseKind | null;
  evidence_kind?: EvidenceKind | null;
  status?: VerificationStatus | null;
}

export interface Revision {
  id: string;
  rev_number: number;
  title: string;
  body: string;
  attributes: Record<string, unknown>;
  ears_pattern: string | null;
  author: string;
  message: string | null;
  created_at: string;
}

export interface Item {
  id: string;
  human_id: string;
  project_id: string;
  project_key: string;
  item_type_id: string;
  type_key: string;
  base_kind: BaseKind;
  title: string;
  body: string;
  attributes: Record<string, unknown>;
  ears_pattern: string | null;
  workflow_status: WorkflowStatus;
  applicability: string | null;
  rev_number: number;
  current_revision_id: string | null;
  status: VerificationStatus | null;
  upstream: LinkRef[];
  downstream: LinkRef[];
}

export interface ItemDetail extends Item {
  revisions: Revision[];
}

export interface EarsFinding {
  code: string;
  message: string;
  severity: 'error' | 'warning';
  start: number;
  end: number;
  term: string | null;
}

export interface EarsReport {
  pattern: string | null;
  ok: boolean;
  findings: EarsFinding[];
}

export interface ItemCreate {
  project_id: string;
  item_type_id: string;
  title: string;
  body?: string;
  attributes?: Record<string, unknown>;
  applicability?: string | null;
  workflow_status?: WorkflowStatus;
  message?: string;
}

export interface ItemUpdate {
  title?: string;
  body?: string;
  attributes?: Record<string, unknown>;
  applicability?: string | null;
  workflow_status?: WorkflowStatus;
  message?: string;
}

export interface Evidence {
  id: string;
  project_id: string;
  kind: EvidenceKind;
  fqn: string;
  name: string;
  in_git: boolean;
  in_regression: boolean;
  link_count: number;
  passed: number | null;
  failed: number | null;
  total: number | null;
  hits: number | null;
  goal: number | null;
  fired: number | null;
  ran: boolean;
  satisfied: boolean;
}

export interface KindSummary {
  total: number;
  satisfied: number;
  partial: number;
  failing: number;
  not_run: number;
}

export interface RegressionRun {
  id: string;
  project_id: string;
  source: string;
  external_id: string | null;
  label: string | null;
  started_at: string | null;
  finished_at: string | null;
  imported_at: string | null;
  result_count: number;
  tests: KindSummary;
  coverpoints: KindSummary;
  assertions: KindSummary;
}

export interface StatusCounts {
  covered: number;
  partial: number;
  failing: number;
  not_run: number;
  uncovered: number;
}

export interface Dashboard {
  requirements: StatusCounts;
  verification_items: StatusCounts;
  requirement_total: number;
  covered_pct: number;
  suspect_links: number;
  orphan_requirements: number;
  orphan_verification_items: number;
  orphan_evidence: number;
  latest_run: RegressionRun | null;
}

export interface EvidenceCreate {
  kind: EvidenceKind;
  fqn: string;
  name?: string;
}

export interface LinkCreate {
  link_type: LinkType;
  upstream_item_id: string;
  downstream_item_id?: string;
  downstream_evidence_id?: string;
}

export interface LinkCreated {
  link_id: string;
  link_type: LinkType;
  upstream_item_id: string;
  downstream_item_id: string | null;
  downstream_evidence_id: string | null;
  suspect: boolean;
}
