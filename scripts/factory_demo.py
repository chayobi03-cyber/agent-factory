#!/usr/bin/env python3
"""Run the AgentFactory synthetic HOTL/CER golden-path demo.

No real engineering-domain ingestion is performed. The demo exercises the
shared factory contract using synthetic evidence and claims.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from interfaces import CERDecision, CERSnapshot, Claim, EvidenceCandidate
from cer_runtime import CERGateRuntime, HumanDecision, WorkflowRunState, transition

SNAPSHOT = CERSnapshot(
    policy_id="CER",
    policy_version="1.0.0",
    snapshot_id="DEMO-SNAP-001",
    snapshot_hash="demo-snapshot-hash",
    source_commit="demo-runtime",
    required_checks=("GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"),
)

EVIDENCE = EvidenceCandidate(
    evidence_id="E-DEMO-001",
    document_id="DOC-DEMO-001",
    revision_id="REV-DEMO-001",
    fragment_id="FRAG-DEMO-001",
    score=1.0,
    text="Synthetic engineering evidence supporting the claim.",
    metadata={"domain": "demo.engineering"},
)


def _decision_payload(decision: CERDecision) -> dict:
    return asdict(decision)


def run_pass(gate: CERGateRuntime) -> dict:
    run_id = "RUN-DEMO-PASS"
    claim = Claim("C-DEMO-PASS", "Supported synthetic claim", "fact", [EVIDENCE.evidence_id], 0.95)
    state = transition(WorkflowRunState(run_id, "TASK-DEMO-PASS", SNAPSHOT.snapshot_id), "RUNNING")
    decision = gate.evaluate(
        snapshot=SNAPSHOT, run_id=run_id, gate_id="PRE-001", claims=[claim], evidence=[EVIDENCE]
    )
    gate.assert_can_continue(decision)
    state = transition(state, "COMPLETED")
    return {"scenario": "PASS", "decision": _decision_payload(decision), "final_state": state.status, "human_intervention": 0}


def run_review(gate: CERGateRuntime) -> dict:
    run_id = "RUN-DEMO-REVIEW"
    claim = Claim("C-DEMO-REVIEW", "High-risk synthetic claim", "recommendation", [EVIDENCE.evidence_id], 0.96)
    state = transition(WorkflowRunState(run_id, "TASK-DEMO-REVIEW", SNAPSHOT.snapshot_id), "RUNNING")
    review = gate.evaluate(
        snapshot=SNAPSHOT,
        run_id=run_id,
        gate_id="PRE-001",
        claims=[claim],
        evidence=[EVIDENCE],
        risk_level="high",
    )
    if review.result != "REVIEW":
        raise AssertionError(f"Expected REVIEW, got {review.result}")
    state = transition(state, "REVIEW_REQUIRED")
    human = HumanDecision(
        decision_id="HD-DEMO-001",
        run_id=run_id,
        gate_id="PRE-001",
        snapshot_id=SNAPSHOT.snapshot_id,
        decision="APPROVE",
        actor_id="demo-human",
        reason="Synthetic high-risk case approved for demonstration.",
        resulting_state="RUNNING",
        correction_ref=None,
    )
    approved = gate.apply_human_decision(review, human)
    gate.assert_can_continue(approved)
    state = transition(state, "RUNNING")
    state = transition(state, "COMPLETED")
    return {
        "scenario": "REVIEW",
        "initial_decision": _decision_payload(review),
        "human_decision": asdict(human),
        "resulting_decision": _decision_payload(approved),
        "final_state": state.status,
        "human_intervention": 1,
    }


def run_block(gate: CERGateRuntime) -> dict:
    run_id = "RUN-DEMO-BLOCK"
    claim = Claim("C-DEMO-BLOCK", "Unsupported synthetic claim", "fact", ["E-MISSING"], 0.99)
    state = transition(WorkflowRunState(run_id, "TASK-DEMO-BLOCK", SNAPSHOT.snapshot_id), "RUNNING")
    blocked = gate.evaluate(
        snapshot=SNAPSHOT, run_id=run_id, gate_id="PRE-001", claims=[claim], evidence=[]
    )
    if blocked.result != "BLOCK":
        raise AssertionError(f"Expected BLOCK, got {blocked.result}")
    state = transition(state, "BLOCKED")
    try:
        transition(state, "RUNNING")
    except ValueError:
        pass
    else:
        raise AssertionError("BLOCKED state must not re-enter execution")
    return {"scenario": "BLOCK", "decision": _decision_payload(blocked), "final_state": state.status, "human_intervention": 0}


def run(scenario: str) -> list[dict]:
    gate = CERGateRuntime()
    handlers = {"pass": run_pass, "review": run_review, "block": run_block}
    if scenario == "all":
        return [handler(gate) for handler in handlers.values()]
    return [handlers[scenario](gate)]


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentFactory synthetic CER/HOTL demo")
    parser.add_argument("--scenario", choices=["all", "pass", "review", "block"], default="all")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    results = run(args.scenario)
    if args.json:
        print(json.dumps({"demo": "factory-hotl", "results": results}, indent=2, sort_keys=True))
    else:
        print("AgentFactory HOTL Demo")
        print("======================")
        for item in results:
            print(f"{item['scenario']:>6}: {item.get('final_state')} | human={item['human_intervention']}")
        print("PASS / REVIEW / BLOCK paths verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
