import pytest

from cer_runtime import HumanDecision
from factory_runtime import FactoryRuntime
from interfaces import Claim, EvidenceCandidate


def make_runtime():
    runtime = FactoryRuntime(repository_commit="abc123")
    snapshot = runtime.create_snapshot(
        policy_id="CER",
        policy_version="1.0.0",
        source_commit="abc123",
        required_checks=["GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"],
    )
    run = runtime.create_run(task_id="T1", idempotency_key="K1", snapshot=snapshot)
    return runtime, snapshot, run


def evidence():
    return [EvidenceCandidate("E1", "D1", "R1", "F1", 1.0, "supported", {})]


def test_create_run_is_idempotent():
    runtime, snapshot, first = make_runtime()
    second = runtime.create_run(task_id="T1", idempotency_key="K1", snapshot=snapshot)
    assert first.run_id == second.run_id


def test_block_is_fail_closed():
    runtime, snapshot, run = make_runtime()
    claim = Claim("C1", "unsupported", "fact", ["MISSING"], 0.99)
    decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot, claims=[claim], evidence=[])
    assert decision.result == "BLOCK"
    with pytest.raises(RuntimeError):
        runtime.execute_workflow(run.run_id, lambda _: {"ok": True})


def test_review_hotl_approval_continues():
    runtime, snapshot, run = make_runtime()
    claim = Claim("C1", "high risk", "recommendation", ["E1"], 0.9)
    decision = runtime.evaluate_gate(
        run_id=run.run_id, gate_id="G1", snapshot=snapshot,
        claims=[claim], evidence=evidence(), risk_level="high"
    )
    assert decision.result == "REVIEW"
    review = runtime.request_human_review(run_id=run.run_id, decision=decision, snapshot=snapshot)
    human = HumanDecision("HD1", run.run_id, "G1", snapshot.snapshot_id,
                          "APPROVE", "human", "approved", "RUNNING")
    final = runtime.apply_human_decision(review_id=review.review_id, human=human, cer_decision=decision)
    assert final.result == "PASS"


def test_block_cannot_be_human_approved():
    runtime, snapshot, run = make_runtime()
    claim = Claim("C1", "unsupported", "fact", ["MISSING"], 0.99)
    decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot, claims=[claim], evidence=[])
    assert decision.result == "BLOCK"
    human = HumanDecision("HD-BLOCK", run.run_id, "G1", snapshot.snapshot_id,
                          "APPROVE", "human", "attempted bypass", "RUNNING")
    with pytest.raises((ValueError, RuntimeError)):
        runtime.apply_human_decision(review_id="does-not-exist", human=human, cer_decision=decision)


def test_modify_requires_correction_lineage():
    runtime, snapshot, run = make_runtime()
    claim = Claim("C1", "high risk", "recommendation", ["E1"], 0.9)
    decision = runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=snapshot,
                                     claims=[claim], evidence=evidence(), risk_level="high")
    review = runtime.request_human_review(run_id=run.run_id, decision=decision, snapshot=snapshot)
    human = HumanDecision("HD-MOD", run.run_id, "G1", snapshot.snapshot_id,
                          "MODIFY", "human", "correct", "RUNNING", None)
    with pytest.raises(ValueError):
        runtime.apply_human_decision(review_id=review.review_id, human=human, cer_decision=decision)


def test_snapshot_cannot_be_replaced_mid_run():
    runtime, snapshot, run = make_runtime()
    other = runtime.create_snapshot(policy_id="CER", policy_version="2.0.0",
                                    source_commit="def456", required_checks=["RISK"])
    with pytest.raises(ValueError):
        runtime.evaluate_gate(run_id=run.run_id, gate_id="G1", snapshot=other, claims=[], evidence=[])


def test_execution_evidence_is_required_and_tied_to_commit():
    runtime, snapshot, run = make_runtime()
    with pytest.raises(RuntimeError):
        runtime.evaluate_run(run.run_id)
    with pytest.raises(ValueError):
        runtime.record_execution_evidence(run_id=run.run_id, command="pytest",
                                          commit_sha="wrong", exit_code=0, stdout="",
                                          stderr="", result_summary="ok")
    runtime.record_execution_evidence(run_id=run.run_id, command="pytest",
                                      commit_sha="abc123", exit_code=0, stdout="PASS",
                                      stderr="", result_summary="tests passed")
    runtime._set_state(runtime._runs[run.run_id], "RUNNING")
    assert runtime.evaluate_run(run.run_id)["result"] == "PASS"
    assert runtime.get_manifest(run.run_id).execution_manifest_hash


def test_trace_contains_execution_evidence():
    runtime, snapshot, run = make_runtime()
    runtime.record_execution_evidence(run_id=run.run_id, command="demo",
                                      commit_sha="abc123", exit_code=0,
                                      stdout="{}", stderr="", result_summary="ok")
    assert any(event.event_type == "EXECUTION_EVIDENCE"
               for event in runtime.get_trace(run.run_id).events)
