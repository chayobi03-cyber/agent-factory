from dataclasses import dataclass, field
from typing import Iterable, Sequence

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

class CERGateRuntime:
    """Minimal deterministic reference implementation of the CER gate contract."""

    def evaluate(
        self,
        *,
        snapshot: CERSnapshot,
        run_id: str,
        gate_id: str,
        claims: Sequence[Claim],
        evidence: Sequence[EvidenceCandidate],
        risk_level: str = "low",
        human_approved: bool = False,
    ) -> CERDecision:
        evidence_ids = {item.evidence_id for item in evidence}
        unsupported = [claim for claim in claims if not any(eid in evidence_ids for eid in claim.evidence_ids)]

        if unsupported:
            result = "BLOCK"
            human_required = False
        elif risk_level in {"critical", "high"} and not human_approved:
            result = "REVIEW"
            human_required = True
        else:
            result = "PASS"
            human_required = False

        return CERDecision(
            decision_id=f"CER-{snapshot.snapshot_id}-{gate_id}",
            result=result,
            gate_id=gate_id,
            run_id=run_id,
            human_required=human_required,
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
