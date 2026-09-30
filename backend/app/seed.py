"""Seed a realistic dataset mirroring design_template.

SoC "Aurora" (variants A0, A1-lite) with IPs PCIe Gen4 Controller, DMA Engine,
and Interrupt Controller; ~15 EARS requirements, ~20 verification items, an
evidence catalog, and one regression run ("Jenkins #1842") — so computed
statuses and suspect links reproduce the design comp.

Run: ``python -m app.seed`` (idempotent; skips if Aurora already exists).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import (
    Evidence,
    EvidenceResult,
    Item,
    ItemRevision,
    ItemType,
    Link,
    Project,
    RegressionRun,
    Variant,
)
from app.models.enums import (
    EvidenceKind,
    ItemBaseKind,
    LinkType,
    ProjectKind,
    WorkflowStatus,
)
from app.repositories.projects import get_project_by_key
from app.services.domain.ears import detect_pattern

REQUIREMENT_SCHEMA = [
    {
        "key": "priority",
        "label": "Priority",
        "type": "enum",
        "options": ["P1", "P2", "P3"],
        "required": True,
        "default": "P2",
    },
    {
        "key": "category",
        "label": "Category",
        "type": "enum",
        "options": ["Functional", "Interface", "Power", "Safety"],
    },
    {"key": "owner", "label": "Owner", "type": "string"},
    {"key": "reference", "label": "Reference", "type": "string"},
]
VERIFICATION_SCHEMA = [
    {"key": "owner", "label": "Owner", "type": "string"},
    {"key": "method", "label": "Method", "type": "string", "default": "Simulation · UVM"},
]

WORKFLOW = {
    "Approved": WorkflowStatus.APPROVED,
    "In review": WorkflowStatus.IN_REVIEW,
    "Draft": WorkflowStatus.DRAFT,
}

IP_NAMES = {
    "pcie": "PCIe Gen4 Controller",
    "dma": "DMA Engine",
    "irq": "Interrupt Controller",
}

# id, ip, title, category, priority, variants(A0|AB), review, [vp ids], body, owner, rev
REQS = [
    (
        "REQ-PCIE-001",
        "pcie",
        "Gen4 link training on x4",
        "Functional",
        "P1",
        "A0",
        "Approved",
        ["VP-PCIE-001", "VP-PCIE-002"],
        "When both link partners advertise 16.0 GT/s, the PCIe controller shall complete link training at Gen4 on 4 lanes.",
        "A. Moreau",
        3,
    ),
    (
        "REQ-PCIE-004",
        "pcie",
        "Equalization phase sequencing",
        "Functional",
        "P1",
        "A0",
        "Approved",
        ["VP-PCIE-005"],
        "While the LTSSM is in Recovery.Equalization, the PCIe controller shall execute phases 0 to 3 in order and record the final preset per lane.",
        "A. Moreau",
        2,
    ),
    (
        "REQ-PCIE-007",
        "pcie",
        "512-byte max payload size",
        "Functional",
        "P2",
        "AB",
        "Approved",
        ["VP-PCIE-008"],
        "The PCIe controller shall support a Max_Payload_Size of 512 bytes for transmitted and received TLPs.",
        "S. Brandt",
        2,
    ),
    (
        "REQ-PCIE-012",
        "pcie",
        "ECRC error discard and interrupt",
        "Functional",
        "P1",
        "AB",
        "In review",
        ["VP-PCIE-021", "VP-PCIE-022"],
        "When a TLP with ECRC error is received, the PCIe controller shall discard the packet and assert the ecrc_err interrupt within 16 cycles.",
        "A. Moreau",
        4,
    ),
    (
        "REQ-PCIE-015",
        "pcie",
        "AER header log capture",
        "Functional",
        "P2",
        "AB",
        "Approved",
        ["VP-PCIE-016"],
        "When an uncorrectable error is detected, the PCIe controller shall capture the first 4 DW of the TLP header in the AER Header Log register.",
        "S. Brandt",
        1,
    ),
    (
        "REQ-PCIE-018",
        "pcie",
        "L1 entry on idle link",
        "Power",
        "P2",
        "AB",
        "Draft",
        ["VP-PCIE-019"],
        "While the link is idle beyond the L1 entry timer, the PCIe controller shall enter the L1 link state fast.",
        "S. Brandt",
        2,
    ),
    (
        "REQ-PCIE-020",
        "pcie",
        "Completion timeout handling",
        "Functional",
        "P1",
        "AB",
        "Draft",
        ["VP-PCIE-024"],
        "The controller should handle completion timeouts gracefully.",
        "A. Moreau",
        1,
    ),
    (
        "REQ-DMA-001",
        "dma",
        "Four independent channels",
        "Functional",
        "P1",
        "AB",
        "Approved",
        ["VP-DMA-001", "VP-DMA-002"],
        "The DMA engine shall provide 4 channels that operate independently, sharing only the AXI master port.",
        "L. Chen",
        2,
    ),
    (
        "REQ-DMA-003",
        "dma",
        "Scatter-gather descriptor chains",
        "Functional",
        "P1",
        "AB",
        "Approved",
        ["VP-DMA-004", "VP-DMA-005"],
        "When a channel is started, the DMA engine shall fetch and execute descriptors until a descriptor with the EOC bit set completes.",
        "L. Chen",
        3,
    ),
    (
        "REQ-DMA-006",
        "dma",
        "Transfer completion interrupt",
        "Interface",
        "P2",
        "AB",
        "Approved",
        ["VP-DMA-007"],
        "When a descriptor with IRQ_EN completes, the DMA engine shall assert dma_done[ch] until cleared by software.",
        "L. Chen",
        3,
    ),
    (
        "REQ-DMA-009",
        "dma",
        "AXI4 bursts up to 256 beats",
        "Interface",
        "P2",
        "A0",
        "In review",
        ["VP-DMA-010"],
        "The DMA engine shall issue AXI4 INCR bursts of up to 256 beats without crossing a 4 KB boundary.",
        "R. Iyer",
        2,
    ),
    (
        "REQ-DMA-011",
        "dma",
        "Abort on descriptor error",
        "Safety",
        "P1",
        "AB",
        "In review",
        [],
        "If a descriptor fetch returns SLVERR or DECERR, then the DMA engine shall abort the channel and set ERR_STAT within 8 cycles.",
        "R. Iyer",
        1,
    ),
    (
        "REQ-IRQ-001",
        "irq",
        "256 interrupt sources",
        "Functional",
        "P1",
        "A0",
        "Approved",
        ["VP-IRQ-001"],
        "The interrupt controller shall accept 256 level-sensitive interrupt sources, each individually enabled.",
        "M. Haddad",
        2,
    ),
    (
        "REQ-IRQ-004",
        "irq",
        "Priority-based arbitration",
        "Functional",
        "P1",
        "AB",
        "Approved",
        ["VP-IRQ-003", "VP-IRQ-005"],
        "When several enabled interrupts are pending, the interrupt controller shall forward the highest-priority one, round-robin among equal priorities.",
        "M. Haddad",
        2,
    ),
    (
        "REQ-IRQ-007",
        "irq",
        "MSI-X forwarding to host",
        "Interface",
        "P2",
        "A0",
        "Approved",
        ["VP-IRQ-008"],
        "Where MSI-X is enabled, the interrupt controller shall forward up to 256 vectors to the PCIe controller as memory writes.",
        "M. Haddad",
        3,
    ),
    (
        "REQ-IRQ-009",
        "irq",
        "Interrupt masking",
        "Functional",
        "P3",
        "AB",
        "Draft",
        [],
        "The interrupt controller should mask interrupts properly.",
        "M. Haddad",
        1,
    ),
]

# id, ip, title, owner, tests[[fqn,passed,total]], coverpoints[[fqn,hits,goal]], assertions[[fqn,fired,failed]]
VPS = [
    (
        "VP-PCIE-001",
        "pcie",
        "Gen4 x4 link-up",
        "J. Lindqvist",
        [["pcie_gen4_linkup_test", 50, 50]],
        [["cg_ltssm.cp_rate", 100, 100], ["cg_ltssm.cp_width", 100, 100]],
        [["a_ltssm_legal_trans", 88120, 0]],
    ),
    (
        "VP-PCIE-002",
        "pcie",
        "Speed fallback to Gen3/Gen2",
        "J. Lindqvist",
        [["pcie_speed_downgrade_test", 40, 40]],
        [["cg_ltssm.cx_rate_x_fail", 100, 100]],
        [],
    ),
    (
        "VP-PCIE-005",
        "pcie",
        "EQ phase 0-3 sequencing",
        "J. Lindqvist",
        [["pcie_eq_phase_test", 30, 30]],
        [["cg_eq.cp_preset", 71, 100]],
        [["a_eq_phase_order", 3610, 0]],
    ),
    (
        "VP-PCIE-008",
        "pcie",
        "MPS 512 B TLP generation",
        "C. Martin",
        [["pcie_mps_512_test", 25, 25]],
        [["cg_tlp_tx.cp_len", 100, 100]],
        [],
    ),
    (
        "VP-PCIE-016",
        "pcie",
        "AER header log capture",
        "C. Martin",
        [["pcie_aer_hdr_log_test", 20, 20]],
        [["cg_aer.cp_err_type", 100, 100]],
        [["a_aer_log_stable", 602, 0]],
    ),
    (
        "VP-PCIE-019",
        "pcie",
        "L1 entry / exit",
        "C. Martin",
        [["pcie_l1_entry_test", 18, 20]],
        [["cg_pm.cp_l1_state", 80, 100]],
        [["a_l1_no_tlp_pending", 955, 0]],
    ),
    (
        "VP-PCIE-021",
        "pcie",
        "ECRC error discard & interrupt",
        "C. Martin",
        [["pcie_ecrc_err_test", 48, 50], ["pcie_ecrc_seq_test", 12, 12]],
        [["cg_tlp_err.cp_ecrc", 87, 100], ["cg_tlp_err.cx_ecrc_x_type", 72, 90]],
        [["a_ecrc_irq_latency", 1204, 0], ["a_ecrc_tlp_discarded", 1198, 0]],
    ),
    (
        "VP-PCIE-022",
        "pcie",
        "ECRC interrupt latency bound",
        "C. Martin",
        [["pcie_ecrc_irq_lat_test", 20, 20]],
        [["cg_irq_lat.cp_cycles", 100, 100]],
        [["a_ecrc_irq_latency", 1204, 0]],
    ),
    (
        "VP-PCIE-024",
        "pcie",
        "Completion timeout ranges",
        "J. Lindqvist",
        [["pcie_cpl_timeout_test", 0, 0]],
        [["cg_cpl.cp_timeout_range", 0, 100]],
        [],
    ),
    (
        "VP-DMA-001",
        "dma",
        "Channel isolation",
        "P. Nowak",
        [["dma_ch_isolation_test", 30, 30]],
        [["cg_dma_ch.cp_active", 100, 100]],
        [["a_dma_ch_no_crosstalk", 12400, 0]],
    ),
    (
        "VP-DMA-002",
        "dma",
        "4-channel concurrent stress",
        "P. Nowak",
        [["dma_4ch_stress_test", 60, 60]],
        [["cg_dma_ch.cx_ch_x_len", 100, 100]],
        [],
    ),
    (
        "VP-DMA-004",
        "dma",
        "SG descriptor chain walk",
        "P. Nowak",
        [["dma_sg_chain_test", 40, 40]],
        [["cg_dma_desc.cp_chain_len", 100, 100]],
        [["a_desc_ptr_aligned", 5530, 0]],
    ),
    (
        "VP-DMA-005",
        "dma",
        "Descriptor fetch error",
        "P. Nowak",
        [["dma_desc_fetch_err_test", 9, 12]],
        [["cg_dma_desc.cp_err", 66, 100]],
        [],
    ),
    (
        "VP-DMA-007",
        "dma",
        "Completion interrupt",
        "P. Nowak",
        [["dma_done_irq_test", 30, 30]],
        [["cg_dma_irq.cp_ch", 100, 100]],
        [["a_dma_done_pulse", 2410, 0]],
    ),
    (
        "VP-DMA-010",
        "dma",
        "AXI4 256-beat bursts",
        "R. Iyer",
        [["dma_axi_burst256_test", 14, 20]],
        [["cg_axi_m.cp_awlen", 94, 100]],
        [["a_axi_wlast_align", 20114, 3]],
    ),
    (
        "VP-IRQ-001",
        "irq",
        "256-source mapping",
        "M. Haddad",
        [["irq_src_map_test", 16, 16]],
        [["cg_irq_src.cp_id", 100, 100]],
        [],
    ),
    (
        "VP-IRQ-003",
        "irq",
        "Priority arbitration",
        "M. Haddad",
        [["irq_prio_arb_test", 24, 24]],
        [["cg_irq_arb.cp_prio", 100, 100]],
        [["a_irq_highest_wins", 7702, 0]],
    ),
    (
        "VP-IRQ-005",
        "irq",
        "Same-priority round-robin",
        "M. Haddad",
        [["irq_rr_fair_test", 12, 12]],
        [["cg_irq_arb.cp_rr_order", 100, 100]],
        [],
    ),
    (
        "VP-IRQ-008",
        "irq",
        "MSI-X forwarding",
        "M. Haddad",
        [["irq_msix_fwd_test", 0, 0]],
        [],
        [["a_msix_addr_valid", 0, 0]],
    ),
    (
        "VP-IRQ-012",
        "irq",
        "Spurious interrupt handling",
        "M. Haddad",
        [["irq_spurious_test", 10, 10]],
        [],
        [],
    ),
]

# Orphan / catalog-only evidence: fqn, ip, kind, in_git, in_regression, result-or-None
# result: ("test", passed, total) | ("coverpoint", hits, goal) | ("assertion", fired, failed)
CATALOG = [
    ("pcie_ecrc_multi_tlp_test", "pcie", "t", 1, 0, None),
    ("pcie_ltssm_recovery_test", "pcie", "t", 1, 1, ("t", 25, 25)),
    ("pcie_legacy_intx_test", "pcie", "t", 0, 1, ("t", 8, 8)),
    ("dma_ch_reset_test", "dma", "t", 1, 1, ("t", 18, 20)),
    ("irq_msix_vector_test", "irq", "t", 1, 0, None),
    ("cg_tlp_err.cp_ecrc_type", "pcie", "c", 1, 1, ("c", 64, 100)),
    ("cg_irq_nesting.cp_depth", "irq", "c", 1, 1, ("c", 40, 100)),
    ("a_ecrc_err_sticky", "pcie", "a", 1, 0, None),
    ("a_pcie_rx_credit_ovf", "pcie", "a", 1, 1, ("a", 4410, 0)),
]

# Requirement -> downstream VP that is suspect (upstream changed after the link was reviewed).
SUSPECTS = {
    ("REQ-PCIE-012", "VP-PCIE-021"),
    ("REQ-DMA-006", "VP-DMA-007"),
    ("REQ-IRQ-007", "VP-IRQ-008"),
}
# Previous-body substitutions for requirements with change history (produce the diff).
PREV_BODY = {
    "REQ-PCIE-012": ("within 16 cycles", "within 32 cycles"),
    "REQ-DMA-006": ("until cleared by software", "for one cycle"),
    "REQ-IRQ-007": ("up to 256 vectors", "up to 64 vectors"),
}

_KIND = {"t": EvidenceKind.TEST, "c": EvidenceKind.COVERPOINT, "a": EvidenceKind.ASSERTION}


def _applicability(code: str) -> str:
    return "A0" if code == "A0" else "A0 | A1-lite"


def _seq(human_id: str) -> int:
    return int(human_id.rsplit("-", 1)[1])


def seed(session: Session) -> None:
    now = datetime.now(UTC)

    aurora = Project(key="aurora", name="Aurora", kind=ProjectKind.SOC, description="Aurora SoC")
    session.add(aurora)
    session.flush()
    session.add_all(
        [
            Variant(project_id=aurora.id, key="A0", name="A0 (full)"),
            Variant(project_id=aurora.id, key="A1-lite", name="A1-lite (derivative)"),
        ]
    )

    ip_projects: dict[str, Project] = {}
    req_types: dict[str, ItemType] = {}
    vp_types: dict[str, ItemType] = {}
    for key, name in IP_NAMES.items():
        project = Project(key=key, name=name, kind=ProjectKind.IP, parent_id=aurora.id)
        session.add(project)
        session.flush()
        ip_projects[key] = project
        req_types[key] = ItemType(
            project_id=project.id,
            key="requirement",
            name="Requirement",
            base_kind=ItemBaseKind.REQUIREMENT,
            id_prefix="REQ",
            attribute_schema=REQUIREMENT_SCHEMA,
        )
        vp_types[key] = ItemType(
            project_id=project.id,
            key="verification_item",
            name="Verification Item",
            base_kind=ItemBaseKind.VERIFICATION_ITEM,
            id_prefix="VP",
            attribute_schema=VERIFICATION_SCHEMA,
        )
        session.add_all([req_types[key], vp_types[key]])
    session.flush()

    items: dict[str, Item] = {}
    # revision objects per item, indexed by rev_number (for suspect baselines).
    revisions: dict[str, dict[int, ItemRevision]] = {}

    def add_item(
        human_id: str,
        ip: str,
        item_type: ItemType,
        title: str,
        body: str,
        attributes: dict[str, object],
        workflow: WorkflowStatus,
        applicability: str | None,
        author: str,
        rev_count: int,
    ) -> Item:
        item = Item(
            project_id=ip_projects[ip].id,
            item_type_id=item_type.id,
            human_id=human_id,
            seq=_seq(human_id),
            workflow_status=workflow,
            applicability=applicability,
        )
        session.add(item)
        session.flush()
        prev = PREV_BODY.get(human_id)
        revisions[human_id] = {}
        for number in range(1, rev_count + 1):
            # Older revisions of a changed requirement carry the pre-change body.
            rev_body = body
            if prev and number < rev_count:
                rev_body = body.replace(prev[0], prev[1])
            revision = ItemRevision(
                item_id=item.id,
                rev_number=number,
                title=title,
                body=rev_body,
                attributes=attributes,
                ears_pattern=detect_pattern(rev_body),
                author=author,
                message="Created" if number == 1 else "Edited",
            )
            session.add(revision)
            session.flush()
            revisions[human_id][number] = revision
        item.current_revision_id = revisions[human_id][rev_count].id
        session.flush()
        items[human_id] = item
        return item

    for human_id, ip, title, category, priority, variants, review, _vps, body, owner, rev in REQS:
        add_item(
            human_id,
            ip,
            req_types[ip],
            title,
            body,
            {"priority": priority, "category": category, "owner": owner},
            WORKFLOW[review],
            _applicability(variants),
            owner,
            rev,
        )

    for human_id, ip, title, owner, _t, _c, _a in VPS:
        add_item(
            human_id,
            ip,
            vp_types[ip],
            title,
            "",
            {"owner": owner, "method": "Simulation · UVM"},
            WorkflowStatus.APPROVED,
            None,
            owner,
            1,
        )

    # Evidence catalog (from verification items + orphan catalog entries).
    evidence: dict[tuple[str, str], Evidence] = {}

    def ensure_evidence(
        fqn: str, ip: str, kind: EvidenceKind, in_git: bool, in_reg: bool
    ) -> Evidence:
        existing = evidence.get((ip, fqn))
        if existing is not None:
            return existing
        ev = Evidence(
            project_id=ip_projects[ip].id,
            kind=kind,
            fqn=fqn,
            name=fqn,
            in_git=in_git,
            in_regression=in_reg,
            last_seen_git_at=now if in_git else None,
            last_seen_regression_at=now if in_reg else None,
        )
        session.add(ev)
        session.flush()
        evidence[(ip, fqn)] = ev
        return ev

    run = RegressionRun(
        project_id=aurora.id,
        source="Jenkins",
        external_id="#1842",
        label="nightly",
        started_at=now,
        finished_at=now,
        imported_at=now,
    )
    session.add(run)
    session.flush()

    results_added: set[uuid.UUID] = set()

    def add_result(ev: Evidence, kind: EvidenceKind, a: int, b: int) -> None:
        # A shared evidence item produces one result per run, even if linked twice.
        if ev.id in results_added:
            return
        results_added.add(ev.id)
        if kind is EvidenceKind.TEST:
            session.add(
                EvidenceResult(
                    run_id=run.id, evidence_id=ev.id, kind=kind, passed=a, failed=0, total=b
                )
            )
        elif kind is EvidenceKind.COVERPOINT:
            session.add(EvidenceResult(run_id=run.id, evidence_id=ev.id, kind=kind, hits=a, goal=b))
        else:
            session.add(
                EvidenceResult(run_id=run.id, evidence_id=ev.id, kind=kind, fired=a, failed=b)
            )

    # Verification items: create evidence, evidenced_by links, and results.
    for human_id, ip, _title, _owner, tests, cps, asserts in VPS:
        vp = items[human_id]
        for groups, kind in (
            (tests, EvidenceKind.TEST),
            (cps, EvidenceKind.COVERPOINT),
            (asserts, EvidenceKind.ASSERTION),
        ):
            for fqn, a, b in groups:
                ev = ensure_evidence(fqn, ip, kind, in_git=True, in_reg=True)
                session.add(
                    Link(
                        link_type=LinkType.EVIDENCED_BY,
                        upstream_item_id=vp.id,
                        downstream_evidence_id=ev.id,
                    )
                )
                add_result(ev, kind, a, b)

    # Requirement -> verification-item links (verified_by), with suspect baselines.
    for human_id, _ip, _title, _cat, _prio, _var, _review, vp_ids, _body, _owner, _rev in REQS:
        req = items[human_id]
        current_rev = max(revisions[human_id])
        for vp_id in vp_ids:
            linked_vp = items.get(vp_id)
            if linked_vp is None:
                continue
            if (human_id, vp_id) in SUSPECTS:
                # Reviewed against the previous revision -> now suspect.
                reviewed = revisions[human_id][max(1, current_rev - 1)]
            else:
                reviewed = revisions[human_id][current_rev]
            session.add(
                Link(
                    link_type=LinkType.VERIFIED_BY,
                    upstream_item_id=req.id,
                    downstream_item_id=linked_vp.id,
                    reviewed_upstream_revision_id=reviewed.id,
                )
            )

    # Orphan / catalog-only evidence (with results where they ran).
    for fqn, ip, kind_code, in_git, in_reg, result in CATALOG:
        kind = _KIND[kind_code]
        ev = ensure_evidence(fqn, ip, kind, in_git=bool(in_git), in_reg=bool(in_reg))
        if result is not None:
            add_result(ev, kind, result[1], result[2])

    session.flush()


def main() -> None:
    session = SessionLocal()
    try:
        if get_project_by_key(session, "aurora") is not None:
            print("Seed skipped: 'aurora' already exists.")
            return
        seed(session)
        session.commit()
        print("Seeded Aurora SoC with PCIe/DMA/IRQ, requirements, plan items, evidence, run #1842.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
