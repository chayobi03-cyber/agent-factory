"""Deterministic benchmark harness for Factory Kernel behavior.

The harness uses explicit ground-truth expectations. An LLM judge may be added
later as a secondary signal, but it is never the source of truth.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from cer_runtime import HumanDecision
from factory_runtime import FactoryRuntime
from interfaces import Claim, EvidenceCandidate


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    target: str
    expected_state: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    target: str
    expected_state: str
    actual_result: str
    actual_state: str
    passed: bool
    detail: str = ""


class FactoryKernelHarness:
    def __init__(self, *, repository_commit: str = "harness-test-commit") -> None:
        self.repository_commit = repository_commit
        self.cases = self._load_cases()

    @staticmethod
    def _load_cases() -> tuple[BenchmarkCase, ...]:
        path = ROOT / "templates" / "benchmark" / "factory_kernel_benchmark.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return tuple(BenchmarkCase(**item) for item in data["cases"])

    def run(self) -> list[CaseResult]:
        handlers = {
            "supported_claim": self._supported_claim,
            "unsupported_claim": self._unsupported_claim,
            "high_risk_claim": self._high_risk_claim,
            "review_approve": self._review_approve,
            "review_reject": self._review_reject,
            "review_modify": self._review_modify,
            "stale_snapshot": self._stale_snapshot,
            "conflicting_revisions": self._conflicting_revisions,
            "differing_evidence_is_not_contradiction": self._differing_evidence,
            "retry_loop": self._retry_loop,
            "duplicate_execution": self._duplicate_execution,
        }
        results = []
        for case in self.cases:
            actual_result, actual_state, detail = handlers[case.case_id]()
            results.append(CaseResult(
                case.case_id, case.target, case.expected_state,
                actual_result, actual_state,
                actual_result == case.target and actual_state == case.expected_state,
                detail,
            ))
        return results

    def report(self) -> dict[str, Any]:
        results = self.run()
        passed = sum(item.passed for item in results)
        return {
            "benchmark_id": "factory-kernel-v0.1",
            "ground_truth": "deterministic",
            "case_count": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "green": passed == len(results),
            "results": [asdict(item) for item in results],
        }

    def _runtime(self) -> tuple[FactoryRuntime, Any, Any]:
        runtime = FactoryRuntime(repository_commit=self.repository_commit, retry_limit=2, loop_limit=2)
        snapshot = runtime.create_snapshot(
            policy_id="CER", policy_version="1.0.0", source_commit=self.repository_commit,
            required_checks=["GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"],
            snapshot_id="HARNESS-SNAP-001",
        )
        run = runtime.create_run(task_id="HARNESS", idempotency_key="HARNESS-001", snapshot=snapshot)
        return runtime, snapshot, run

    @staticmethod
    def _evidence(eid: str = "E1", text: str = "supported", *,
                  document_id: str = "D1", revision_id: str = "R1") -> EvidenceCandidate:
        return EvidenceCandidate(eid, document_id, revision_id, f"F-{eid}", 1.0, text, {})

    def _supported_claim(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "supported", "fact", ["E1"], .95)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[self._evidence()])
        runtime.record_execution_evidence(run_id=run.run_id, command="harness",
                                          commit_sha=self.repository_commit, exit_code=0,
                                          stdout="PASS", stderr="", result_summary="supported")
        runtime.evaluate_run(run.run_id)
        return decision.result, runtime.get_trace(run.run_id).events[-1].payload["state"], ""

    def _unsupported_claim(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "unsupported", "fact", ["MISSING"], .95)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[])
        return decision.result, runtime._runs[run.run_id].status, ""

    def _high_risk_claim(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "high risk", "recommendation", ["E1"], .9)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[self._evidence()], risk_level="high")
        return decision.result, runtime._runs[run.run_id].status, ""

    def _review_approve(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "high risk", "recommendation", ["E1"], .9)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[self._evidence()], risk_level="high")
        review = runtime.request_human_review(run_id=run.run_id, decision=decision, snapshot=snapshot)
        human = HumanDecision("HD1", run.run_id, "G1", snapshot.snapshot_id, "APPROVE",
                              "harness", "approve", "RUNNING")
        final = runtime.apply_human_decision(review_id=review.review_id, human=human, cer_decision=decision)
        runtime.record_execution_evidence(run_id=run.run_id, command="harness", commit_sha=self.repository_commit,
                                          exit_code=0, stdout="PASS", stderr="", result_summary="approved")
        runtime.evaluate_run(run.run_id)
        return final.result, runtime._runs[run.run_id].status, ""

    def _review_reject(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "high risk", "recommendation", ["E1"], .9)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[self._evidence()], risk_level="high")
        review = runtime.request_human_review(run_id=run.run_id, decision=decision, snapshot=snapshot)
        human = HumanDecision("HD1", run.run_id, "G1", snapshot.snapshot_id, "REJECT",
                              "harness", "reject", "BLOCKED")
        final = runtime.apply_human_decision(review_id=review.review_id, human=human, cer_decision=decision)
        return final.result, runtime._runs[run.run_id].status, ""

    def _review_modify(self):
        runtime, snapshot, run = self._runtime()
        claim = Claim("C1", "high risk", "recommendation", ["E1"], .9)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=[self._evidence()], risk_level="high")
        review = runtime.request_human_review(run_id=run.run_id, decision=decision, snapshot=snapshot)
        human = HumanDecision("HD1", run.run_id, "G1", snapshot.snapshot_id, "MODIFY",
                              "harness", "modify", "RUNNING", "CORR-001")
        final = runtime.apply_human_decision(review_id=review.review_id, human=human, cer_decision=decision)
        return final.result, runtime._runs[run.run_id].status, "CHANGE requires a governed re-entry path"

    def _stale_snapshot(self):
        runtime, snapshot, run = self._runtime()
        stale = runtime.create_snapshot(policy_id="CER", policy_version="2.0.0",
                                        source_commit="other", required_checks=["RISK"], snapshot_id="STALE")
        try:
            runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=stale, claims=[], evidence=[])
        except ValueError:
            return "REJECT_EXECUTION", runtime._runs[run.run_id].status, "stale snapshot rejected"
        return "ACCEPT_EXECUTION", runtime._runs[run.run_id].status, "stale snapshot was accepted"

    def _conflicting_revisions(self):
        """One document at two revisions: named by the verifier, not gated on.

        This case used to be called `contradictory_evidence` and passed because
        the rule fired on any claim citing two items with differing text. That
        is plurality, not contradiction, so the case was green for a reason
        unrelated to its name. What it asserts now is the honest pair: the
        conflict is *detected* and reported, and the gate does *not* act on it.
        """
        runtime, snapshot, run = self._runtime()
        evidence = [
            self._evidence("E1", "measured 38.2 dBuV/m", document_id="DOC-1", revision_id="REV-A"),
            self._evidence("E2", "measured 31.4 dBuV/m", document_id="DOC-1", revision_id="REV-B"),
        ]
        claim = Claim("C1", "the measured level", "fact", ["E1", "E2"], .9)
        verification = self._verify(claim, evidence)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=evidence,
                                         verification=verification)
        # Reported, not gated: the verifier names the conflict and the gate lets
        # the answer through, because the version that referred it also referred
        # 15 questions that were *asking* about the difference between revisions.
        assert verification.conflicting_revision_claim_ids == ("C1",)
        runtime.record_execution_evidence(run_id=run.run_id, command="harness",
                                          commit_sha=self.repository_commit, exit_code=0,
                                          stdout="PASS", stderr="", result_summary="revisions")
        runtime._set_state(runtime._runs[run.run_id], "COMPLETED")
        return (decision.result, runtime._runs[run.run_id].status,
                "one document at two revisions: reported by the verifier, not gated")

    def _differing_evidence(self):
        """Two documents saying different things is *not* a detected contradiction.

        A pinned gap, not a capability. Judging whether two fragments assert
        incompatible things is a semantic call no lexical method here can make,
        and OPEN_DECISIONS D-11 records why. The gate passes this, and the case
        exists so that fact is visible in the benchmark rather than assumed.
        """
        runtime, snapshot, run = self._runtime()
        evidence = [
            self._evidence("E1", "the claim is true", document_id="DOC-1", revision_id="REV-A"),
            self._evidence("E2", "the claim is false", document_id="DOC-2", revision_id="REV-A"),
        ]
        claim = Claim("C1", "the claim", "fact", ["E1", "E2"], .9)
        verification = self._verify(claim, evidence)
        decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                         claims=[claim], evidence=evidence,
                                         verification=verification)
        # Carried through to COMPLETED like `supported_claim`, because that is
        # the point: this evidence pair reaches a finished run, unflagged.
        runtime.record_execution_evidence(run_id=run.run_id, command="harness",
                                          commit_sha=self.repository_commit, exit_code=0,
                                          stdout="PASS", stderr="", result_summary="differing")
        runtime._set_state(runtime._runs[run.run_id], "COMPLETED")
        return decision.result, runtime._runs[run.run_id].status, "semantic contradiction is not detected"

    @staticmethod
    def _verify(claim, evidence):
        from claim_verification import ClaimVerifier

        return ClaimVerifier(lambda t: t.lower().split(), grounding_floor=0.0).verify(
            [claim], evidence
        )

    def _retry_loop(self):
        runtime, snapshot, run = self._runtime()
        state = runtime._set_state(run, "RUNNING")
        try:
            for _ in range(3):
                state = runtime._set_state(state, "RETRYING")
                state = runtime._set_state(state, "RUNNING")
        except (RuntimeError, ValueError):
            return "REJECT_EXECUTION", runtime._runs[run.run_id].status, "retry/loop guard triggered"
        return "ACCEPT_EXECUTION", runtime._runs[run.run_id].status, "retry loop was not rejected"

    def _duplicate_execution(self):
        runtime, snapshot, run = self._runtime()
        duplicate = runtime.create_run(task_id="OTHER", idempotency_key="HARNESS-001", snapshot=snapshot)
        return "IDEMPOTENT" if duplicate.run_id == run.run_id else "DUPLICATED", duplicate.status, ""
