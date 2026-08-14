"""Domain-agnostic Factory Kernel orchestration.

CER remains the executable control plane. Domain behavior is injected through
DomainPack/callable interfaces; the kernel contains no RE-specific branches.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from cer_runtime import CERGateRuntime, HumanDecision, WorkflowRunState, transition
from interfaces import CERDecision, CERSnapshot, Claim, DomainPack, EvidenceCandidate

TERMINAL = {"BLOCKED", "COMPLETED", "FAILED", "ABORTED"}
HUMAN_DECISIONS = {"APPROVE", "REJECT", "MODIFY", "REQUEST_RETRY", "ESCALATE"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    task_id: str
    parent_run_id: str | None
    repository_commit: str
    cer_snapshot_id: str
    architecture_version: str
    schema_version: str
    workflow_version: str
    benchmark_version: str
    domain_pack_id: str
    domain_pack_version: str
    idempotency_key: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    command: str | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    result_summary: str = ""
    artifact_refs: tuple[str, ...] = ()
    execution_manifest_hash: str = ""


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    run_id: str
    event_type: str
    timestamp: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class Trace:
    run_id: str
    task_id: str
    snapshot_id: str
    events: tuple[TraceEvent, ...]


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    run_id: str
    gate_id: str
    decision_id: str
    snapshot_id: str
    created_at: str
    status: str = "OPEN"


class SnapshotManager:
    """Creates and stores immutable CER snapshots."""

    def __init__(self) -> None:
        self._snapshots: dict[str, CERSnapshot] = {}

    def create_snapshot(self, *, policy_id: str, policy_version: str, source_commit: str,
                        required_checks: Sequence[str], snapshot_id: str | None = None) -> CERSnapshot:
        sid = snapshot_id or f"CER-SNAP-{uuid.uuid4().hex[:12]}"
        checks = tuple(required_checks)
        digest = stable_hash({"policy_id": policy_id, "policy_version": policy_version,
                              "source_commit": source_commit, "required_checks": checks})
        snapshot = CERSnapshot(policy_id, policy_version, sid, digest, source_commit, checks)
        self._snapshots[sid] = snapshot
        return snapshot

    def load_context(self, snapshot_id: str) -> CERSnapshot:
        return self._snapshots[snapshot_id]


class HOTLReviewQueue:
    def __init__(self) -> None:
        self._items: dict[str, ReviewItem] = {}

    def request(self, *, run_id: str, gate_id: str, decision: CERDecision,
                snapshot_id: str) -> ReviewItem:
        if decision.result != "REVIEW":
            raise ValueError("Only REVIEW decisions may enter HOTL")
        item = ReviewItem(f"REVIEW-{uuid.uuid4().hex[:12]}", run_id, gate_id,
                          decision.decision_id, snapshot_id, utc_now())
        self._items[item.review_id] = item
        return item

    def get(self, review_id: str) -> ReviewItem:
        return self._items[review_id]

    def close(self, review_id: str) -> None:
        item = self._items[review_id]
        self._items[review_id] = ReviewItem(item.review_id, item.run_id, item.gate_id,
                                            item.decision_id, item.snapshot_id,
                                            item.created_at, "CLOSED")


class WorkflowStateMachine:
    def __init__(self, *, retry_limit: int = 3, loop_limit: int = 3) -> None:
        self.retry_limit = retry_limit
        self.loop_limit = loop_limit
        self._retries: dict[str, int] = {}

    def transition(self, state: WorkflowRunState, target: str) -> WorkflowRunState:
        if state.status == "BLOCKED" and target != "BLOCKED":
            raise RuntimeError("BLOCKED is fail-closed and terminal")
        if target == "RETRYING":
            count = self._retries.get(state.run_id, 0) + 1
            if count > self.retry_limit:
                raise RuntimeError(f"retry limit exceeded: {state.run_id}")
            self._retries[state.run_id] = count
        if state.history.count(target) >= self.loop_limit and target not in TERMINAL:
            raise RuntimeError(f"loop limit exceeded: {state.run_id} -> {target}")
        return transition(state, target)


class FactoryRuntime:
    """Reference Factory Kernel runtime orchestrator."""

    def __init__(self, *, repository_commit: str, architecture_version: str = "1.0.0",
                 schema_version: str = "1.0.0", benchmark_version: str = "0.1.0",
                 retry_limit: int = 3, loop_limit: int = 3) -> None:
        self.repository_commit = repository_commit
        self.architecture_version = architecture_version
        self.schema_version = schema_version
        self.benchmark_version = benchmark_version
        self.snapshots = SnapshotManager()
        self.state_machine = WorkflowStateMachine(retry_limit=retry_limit, loop_limit=loop_limit)
        self.gate = CERGateRuntime()
        self.hotl = HOTLReviewQueue()
        self._runs: dict[str, WorkflowRunState] = {}
        self._manifests: dict[str, RunManifest] = {}
        self._contexts: dict[str, Mapping[str, Any]] = {}
        self._traces: dict[str, list[TraceEvent]] = {}

    def create_run(self, *, task_id: str, idempotency_key: str, snapshot: CERSnapshot,
                   workflow_version: str = "1.0.0", domain_pack_id: str = "kernel",
                   domain_pack_version: str = "1.0.0", parent_run_id: str | None = None) -> WorkflowRunState:
        for run_id, manifest in self._manifests.items():
            if manifest.idempotency_key == idempotency_key:
                return self._runs[run_id]
        run_id = f"RUN-{uuid.uuid4().hex[:12]}"
        state = WorkflowRunState(run_id, task_id, snapshot.snapshot_id,
                                 idempotency_key=idempotency_key, parent_run_id=parent_run_id)
        self._runs[run_id] = state
        manifest = RunManifest(run_id, task_id, parent_run_id, self.repository_commit,
                               snapshot.snapshot_id, self.architecture_version,
                               self.schema_version, workflow_version, self.benchmark_version,
                               domain_pack_id, domain_pack_version, idempotency_key, utc_now())
        self._manifests[run_id] = self._with_hash(manifest)
        self._traces[run_id] = []
        self.record_trace(run_id, "RUN_CREATED", {"task_id": task_id,
                                                    "snapshot_id": snapshot.snapshot_id})
        return state

    def load_context(self, run_id: str) -> Mapping[str, Any]:
        if run_id not in self._runs:
            raise KeyError(run_id)
        return self._contexts.get(run_id, {"run_id": run_id,
                                           "repository_commit": self.repository_commit})

    def set_context(self, run_id: str, context: Mapping[str, Any]) -> None:
        self._contexts[run_id] = dict(context)
        self.record_trace(run_id, "CONTEXT_LOADED", dict(context))

    def create_snapshot(self, **kwargs: Any) -> CERSnapshot:
        return self.snapshots.create_snapshot(**kwargs)

    def load_domain_pack(self, run_id: str, domain_pack: DomainPack) -> DomainPack:
        if run_id not in self._runs:
            raise KeyError(run_id)
        self.record_trace(run_id, "DOMAIN_PACK_LOADED",
                          {"domain_id": domain_pack.domain_id, "version": domain_pack.version})
        return domain_pack

    def execute_workflow(self, run_id: str,
                         workflow: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                         *, max_seconds: float = 30.0) -> Mapping[str, Any]:
        state = self._runs[run_id]
        if state.status in TERMINAL:
            raise RuntimeError(f"run is terminal: {state.status}")
        if state.status == "CREATED":
            state = self._set_state(state, "RUNNING")
        started = time.monotonic()
        self.record_trace(run_id, "WORKFLOW_STARTED", {})
        result = workflow(self.load_context(run_id))
        if time.monotonic() - started > max_seconds:
            self._set_state(self._runs[run_id], "FAILED")
            raise TimeoutError(f"workflow timeout: {max_seconds}s")
        self.record_trace(run_id, "WORKFLOW_EXECUTED", {"result_keys": sorted(result.keys())})
        return result

    def evaluate_gate(self, *, run_id: str, gate_id: str, snapshot: CERSnapshot,
                      claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate],
                      risk_level: str = "low") -> CERDecision:
        state = self._runs[run_id]
        if snapshot.snapshot_id != state.cer_snapshot_id:
            raise ValueError("active WorkflowRun CER snapshot is immutable")
        if state.status == "CREATED":
            self._set_state(state, "RUNNING")
        decision = self.gate.evaluate(snapshot=snapshot, run_id=run_id, gate_id=gate_id,
                                      claims=claims, evidence=evidence, risk_level=risk_level)
        self.record_trace(run_id, "CER_DECISION", asdict(decision))
        if decision.result == "BLOCK":
            self._set_state(self._runs[run_id], "BLOCKED")
        elif decision.result == "REVIEW":
            self._set_state(self._runs[run_id], "REVIEW_REQUIRED")
            review = self.hotl.request(run_id=run_id, gate_id=gate_id,
                                       decision=decision, snapshot_id=snapshot.snapshot_id)
            self.record_trace(run_id, "HOTL_REVIEW_REQUESTED", asdict(review))
        return decision

    def request_human_review(self, *, run_id: str, decision: CERDecision,
                             snapshot: CERSnapshot) -> ReviewItem:
        return self.hotl.request(run_id=run_id, gate_id=decision.gate_id,
                                 decision=decision, snapshot_id=snapshot.snapshot_id)

    def apply_human_decision(self, *, review_id: str, human: HumanDecision,
                             cer_decision: CERDecision) -> CERDecision:
        review = self.hotl.get(review_id)
        if review.status != "OPEN":
            raise ValueError("review is already closed")
        if human.decision not in HUMAN_DECISIONS:
            raise ValueError(f"unsupported HumanDecision: {human.decision}")
        if human.run_id != review.run_id or human.gate_id != review.gate_id:
            raise ValueError("HumanDecision does not match review context")
        if human.decision == "MODIFY" and not human.correction_ref:
            raise ValueError("MODIFY requires correction_ref; original Claim remains immutable")
        result = self.gate.apply_human_decision(cer_decision, human)
        if result.result == "PASS":
            self._set_state(self._runs[human.run_id], "RUNNING")
        elif result.result == "BLOCK":
            self._set_state(self._runs[human.run_id], "BLOCKED")
        elif result.result == "CHANGE":
            self.record_trace(human.run_id, "CORRECTION_LINEAGE",
                              {"decision_id": human.decision_id,
                               "correction_ref": human.correction_ref})
        self.hotl.close(review_id)
        self.record_trace(human.run_id, "HUMAN_DECISION",
                          asdict(human) | {"result": result.result})
        return result

    def record_trace(self, run_id: str, event_type: str,
                     payload: Mapping[str, Any]) -> TraceEvent:
        event = TraceEvent(f"EV-{uuid.uuid4().hex[:12]}", run_id, event_type,
                           utc_now(), dict(payload))
        self._traces.setdefault(run_id, []).append(event)
        return event

    def record_execution_evidence(self, *, run_id: str, command: str, commit_sha: str,
                                  exit_code: int, stdout: str, stderr: str,
                                  result_summary: str, artifact_refs: Sequence[str] = ()) -> RunManifest:
        manifest = self._manifests[run_id]
        if commit_sha != manifest.repository_commit:
            raise ValueError("execution evidence commit does not match run commit")
        updated = RunManifest(**{**asdict(manifest),
                                 "command": command,
                                 "exit_code": exit_code,
                                 "stdout": stdout,
                                 "stderr": stderr,
                                 "result_summary": result_summary,
                                 "artifact_refs": tuple(artifact_refs),
                                 "started_at": manifest.started_at or utc_now(),
                                 "completed_at": utc_now(),
                                 "execution_manifest_hash": ""})
        updated = self._with_hash(updated)
        self._manifests[run_id] = updated
        self.record_trace(run_id, "EXECUTION_EVIDENCE", asdict(updated))
        return updated

    def evaluate_run(self, run_id: str) -> Mapping[str, Any]:
        manifest = self._manifests[run_id]
        if manifest.exit_code is None or not manifest.command or not manifest.result_summary:
            raise RuntimeError("machine-generated execution evidence is incomplete")
        if manifest.exit_code != 0:
            if self._runs[run_id].status not in TERMINAL:
                self._set_state(self._runs[run_id], "FAILED")
            return {"result": "FAIL", "exit_code": manifest.exit_code}
        state = self._runs[run_id]
        if state.status == "BLOCKED":
            return {"result": "BLOCKED", "state": state.status}
        if state.status != "COMPLETED":
            self._set_state(state, "COMPLETED")
        self.record_trace(run_id, "RUN_EVALUATED", {"result": "PASS", "state": "COMPLETED"})
        return {"result": "PASS", "state": "COMPLETED"}

    def get_manifest(self, run_id: str) -> RunManifest:
        return self._manifests[run_id]

    def get_trace(self, run_id: str) -> Trace:
        state = self._runs[run_id]
        return Trace(run_id, state.task_id, state.cer_snapshot_id,
                     tuple(self._traces.get(run_id, [])))

    def _set_state(self, state: WorkflowRunState, target: str) -> WorkflowRunState:
        updated = self.state_machine.transition(state, target)
        self._runs[state.run_id] = updated
        self.record_trace(state.run_id, "STATE_TRANSITION",
                          {"from": state.status, "to": target})
        return updated

    @staticmethod
    def _with_hash(manifest: RunManifest) -> RunManifest:
        payload = asdict(manifest)
        payload["execution_manifest_hash"] = ""
        digest = stable_hash(payload)
        return RunManifest(**{**asdict(manifest), "execution_manifest_hash": digest})
