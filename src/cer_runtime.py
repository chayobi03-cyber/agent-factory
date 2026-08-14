from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence
import uuid

from interfaces import CERDecision, CERSnapshot, Claim, EvidenceCandidate

DECISIONS = {"PASS", "REVIEW", "CHANGE", "BLOCK"}


@dataclass(frozen=True)
class WorkflowRunState:
    run_id: str
    task_id: str
    cer_snapshot_id: str
    status: str = "CREATED"
    idempotency_key: str = ""
    checkpoint_ref: str | None = None
    parent_run_id: str | None = None
    history: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HumanDecision:
    decision_id: str
    run_id: str
    gate_id: str
    snapshot_id: str
    decision: str
    actor_id: str
    reason: str
    resulting_state: str
    correction_ref: str | None = None


class CERGateRuntime:
    """Deterministic CER/HOTL gate semantics; BLOCK is fail-closed."""

    def evaluate(
        self,
        *,
        snapshot: CERSnapshot,
        run_id: str,
        gate_id: str,
        claims: Sequence[Claim],
        evidence: Sequence[EvidenceCandidate],
        risk_level: str = "low",
    ) -> CERDecision:
        evidence_ids = {item.evidence_id for item in evidence}
        claim_ids = tuple(claim.claim_id for claim in claims)
        evidence_refs = tuple(sorted(evidence_ids))
        unsupported = [
            claim for claim in claims
            if not any(eid in evidence_ids for eid in claim.evidence_ids)
        ]

        if unsupported:
            result = "BLOCK"
            human_required = False
            findings = tuple(f"UNSUPPORTED_CLAIM:{claim.claim_id}" for claim in unsupported)
            actions = ("REMEDIATE_EVIDENCE",)
        elif risk_level in {"critical", "high"}:
            result = "REVIEW"
            human_required = True
            findings = (f"HIGH_RISK:{risk_level}",)
            actions = ("HUMAN_REVIEW_REQUIRED",)
        else:
            result = "PASS"
            human_required = False
            findings = ()
            actions = ()

        return CERDecision(
            decision_id=f"CER-{snapshot.snapshot_id}-{gate_id}-{uuid.uuid4().hex[:8]}",
            result=result,
            gate_id=gate_id,
            run_id=run_id,
            human_required=human_required,
            triggered_findings=findings,
            evidence_ids=evidence_refs,
            claim_ids=claim_ids,
            required_actions=actions,
            decided_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def apply_human_decision(decision: CERDecision, human: HumanDecision) -> CERDecision:
        if decision.result != "REVIEW":
            raise ValueError("Human decision is only applicable to REVIEW decisions")
        if human.run_id != decision.run_id or human.gate_id != decision.gate_id:
            raise ValueError("Human decision does not match CER decision context")
        if human.snapshot_id != decision.run_id and not human.snapshot_id:
            raise ValueError("Human decision snapshot context is missing")
        if human.decision == "APPROVE":
            result, actions = "PASS", ()
        elif human.decision in {"REJECT", "ESCALATE"}:
            result, actions = "BLOCK", ("STOP_GOVERNED_PATH",)
        elif human.decision in {"MODIFY", "REQUEST_RETRY"}:
            result, actions = "CHANGE", ("CREATE_CORRECTION_LINEAGE",)
        else:
            raise ValueError(f"Unsupported human decision: {human.decision}")
        return CERDecision(
            decision_id=decision.decision_id + "-H-" + human.decision,
            result=result,
            gate_id=decision.gate_id,
            run_id=decision.run_id,
            human_required=False,
            triggered_findings=decision.triggered_findings,
            evidence_ids=decision.evidence_ids,
            claim_ids=decision.claim_ids,
            required_actions=actions,
            decided_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def assert_can_continue(decision: CERDecision) -> None:
        if decision.result == "PASS":
            return
        if decision.result not in DECISIONS:
            raise ValueError(f"Invalid CER decision: {decision.result}")
        raise RuntimeError(f"CER gate prevents workflow continuation: {decision.result}")


def transition(state: WorkflowRunState, target: str) -> WorkflowRunState:
    allowed = {
        "CREATED": {"RUNNING", "ABORTED"},
        "RUNNING": {"WAITING", "REVIEW_REQUIRED", "RETRYING", "BLOCKED", "COMPLETED", "FAILED", "ABORTED"},
        "WAITING": {"RUNNING", "REVIEW_REQUIRED", "BLOCKED", "ABORTED"},
        "REVIEW_REQUIRED": {"RUNNING", "BLOCKED", "ABORTED"},
        "RETRYING": {"RUNNING", "FAILED", "BLOCKED", "ABORTED"},
        "BLOCKED": set(),
        "COMPLETED": set(),
        "FAILED": set(),
        "ABORTED": set(),
    }
    if target not in allowed.get(state.status, set()):
        raise ValueError(f"Invalid workflow transition {state.status} -> {target}")
    return WorkflowRunState(
        run_id=state.run_id,
        task_id=state.task_id,
        cer_snapshot_id=state.cer_snapshot_id,
        status=target,
        idempotency_key=state.idempotency_key,
        checkpoint_ref=state.checkpoint_ref,
        parent_run_id=state.parent_run_id,
        history=state.history + (target,),
    )
