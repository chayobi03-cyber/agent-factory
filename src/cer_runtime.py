from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence
import uuid

from claim_verification import VerificationReport
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
        verification: VerificationReport | None = None,
    ) -> CERDecision:
        """`verification`, when supplied, is what makes support mean support.

        Without it this gate can only check that a claim cites an evidence id
        that *exists*, which is not the same thing: a claim citing a real
        fragment with almost no relationship to what it asserts still reached
        PASS. A Domain Pack that wants its own
        `verification_policy.require_evidence_for_claims` honoured must pass
        the report from its verifier. See src/claim_verification.py.
        """
        evidence_by_id = {item.evidence_id: item for item in evidence}
        claim_ids = tuple(claim.claim_id for claim in claims)
        evidence_refs = tuple(sorted(evidence_by_id))
        unsupported = [claim for claim in claims if not any(eid in evidence_by_id for eid in claim.evidence_ids)]
        ungrounded_ids = set(verification.ungrounded_claim_ids) if verification else set()
        # A claim whose evidence does not support it is unsupported in
        # substance, so it lands in the same fail-closed branch rather than a
        # softer one. Excluding the claims already caught above keeps one claim
        # from producing two findings for the same defect.
        ungrounded = [
            claim for claim in claims
            if claim.claim_id in ungrounded_ids and claim not in unsupported
        ]
        contradictory = [
            claim for claim in claims
            if len(claim.evidence_ids) >= 2
            and len({evidence_by_id[eid].text.strip() for eid in claim.evidence_ids if eid in evidence_by_id}) >= 2
        ]

        if unsupported or ungrounded:
            result = "BLOCK"
            human_required = False
            findings = (
                tuple(f"UNSUPPORTED_CLAIM:{claim.claim_id}" for claim in unsupported)
                + tuple(f"UNGROUNDED_CLAIM:{claim.claim_id}" for claim in ungrounded)
            )
            actions = ("REMEDIATE_EVIDENCE",)
        elif contradictory:
            result = "REVIEW"
            human_required = True
            findings = tuple(f"CONTRADICTORY_EVIDENCE:{claim.claim_id}" for claim in contradictory)
            actions = ("HUMAN_REVIEW_REQUIRED", "RECONCILE_EVIDENCE")
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
            snapshot_id=snapshot.snapshot_id,
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
        if human.snapshot_id != decision.snapshot_id:
            raise ValueError("Human decision snapshot does not match CER decision snapshot")
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
            snapshot_id=decision.snapshot_id,
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
        "REVIEW_REQUIRED": {"RUNNING", "WAITING", "BLOCKED", "ABORTED"},
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
