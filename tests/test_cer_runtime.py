from interfaces import CERSnapshot, Claim, EvidenceCandidate
from cer_runtime import CERGateRuntime, HumanDecision, WorkflowRunState, transition


def test_unsupported_claim_is_blocked():
    snapshot = CERSnapshot("CER", "1.0.0", "SNAP-1", "hash", "commit", ["EVIDENCE"])
    claim = Claim("C1", "unsupported", "fact", ["E999"], 0.99)
    decision = CERGateRuntime().evaluate(snapshot=snapshot, run_id="RUN-1", gate_id="G1", claims=[claim], evidence=[])
    assert decision.result == "BLOCK"


def test_high_risk_requires_review_then_human_approval():
    snapshot = CERSnapshot("CER", "1.0.0", "SNAP-1", "hash", "commit", ["RISK"])
    claim = Claim("C1", "supported", "fact", ["E1"], 0.9)
    evidence = [EvidenceCandidate("E1", "D1", "R1", "F1", 1.0, "text", {})]
    decision = CERGateRuntime().evaluate(snapshot=snapshot, run_id="RUN-1", gate_id="G1", claims=[claim], evidence=evidence, risk_level="high")
    assert decision.result == "REVIEW"
    human = HumanDecision("HD-1", "RUN-1", "G1", "SNAP-1", "APPROVE", "human-1", "reviewed evidence", "RUNNING")
    final = CERGateRuntime.apply_human_decision(decision, human)
    assert final.result == "PASS"


def test_human_rejection_blocks_review():
    snapshot = CERSnapshot("CER", "1.0.0", "SNAP-1", "hash", "commit", ["RISK"])
    claim = Claim("C1", "supported", "fact", ["E1"], 0.9)
    evidence = [EvidenceCandidate("E1", "D1", "R1", "F1", 1.0, "text", {})]
    decision = CERGateRuntime().evaluate(snapshot=snapshot, run_id="RUN-1", gate_id="G1", claims=[claim], evidence=evidence, risk_level="critical")
    human = HumanDecision("HD-2", "RUN-1", "G1", "SNAP-1", "REJECT", "human-1", "insufficient risk evidence", "BLOCKED")
    assert CERGateRuntime.apply_human_decision(decision, human).result == "BLOCK"


def test_blocked_state_is_terminal():
    state = WorkflowRunState("RUN-1", "TASK-1", "SNAP-1", status="RUNNING")
    blocked = transition(state, "BLOCKED")
    assert blocked.status == "BLOCKED"
    try:
        transition(blocked, "RUNNING")
    except ValueError:
        return
    raise AssertionError("BLOCKED must not transition back into execution")
