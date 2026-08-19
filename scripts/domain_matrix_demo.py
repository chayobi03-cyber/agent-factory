#!/usr/bin/env python3
"""Exercise the same Factory workflow across multiple synthetic domains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import yaml

from factory_runtime import FactoryRuntime
from interfaces import Claim, DomainPack, EvidenceCandidate


class FixtureDomainPack:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.domain_id = spec["domain_id"]
        self.version = spec["version"]
        self.knowledge = spec["knowledge"]
        self.workflow = spec["workflow"]
        self.risk_level = spec["risk_level"]

    def ingest(self, source: Any) -> dict[str, Any]:
        return {"domain_id": self.domain_id, "source": source, "knowledge": self.knowledge}

    def parse(self, artifact: Any) -> dict[str, Any]:
        return {"domain_id": self.domain_id, "parsed": artifact}

    def normalize(self, artifact: Any) -> dict[str, Any]:
        return {"domain_id": self.domain_id, "normalized": artifact}

    def retrieve(self, query: str, **kwargs: Any) -> Sequence[EvidenceCandidate]:
        evidence = EvidenceCandidate(
            evidence_id=f"E-{self.domain_id}-001",
            document_id=f"DOC-{self.domain_id}-001",
            revision_id=f"REV-{self.domain_id}-001",
            fragment_id=f"FRAG-{self.domain_id}-001",
            score=1.0,
            text=self.knowledge["fact"],
            metadata={"domain_id": self.domain_id, "fixture_only": True},
        )
        return (evidence,)

    def verify(self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate], **kwargs: Any) -> dict[str, Any]:
        evidence_ids = {item.evidence_id for item in evidence}
        supported = all(set(claim.evidence_ids) <= evidence_ids for claim in claims)
        return {"supported": supported, "claim_count": len(claims), "evidence_count": len(evidence)}

    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        return {"domain_id": self.domain_id, "passed": bool(result.get("supported")), "case": case}

    def render_report(self, result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return {"domain_id": self.domain_id, "report": result}


def load_specs(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload.get("fixture_only") is not True:
        raise ValueError("domain matrix must be explicitly marked fixture_only")
    return list(payload["domains"])


def run_domain(runtime: FactoryRuntime, spec: dict[str, Any]) -> dict[str, Any]:
    pack = FixtureDomainPack(spec)
    snapshot = runtime.create_snapshot(
        policy_id="CER",
        policy_version="1.0.0",
        source_commit=runtime.repository_commit,
        required_checks=("evidence", "verification", "risk"),
        snapshot_id=f"CER-{pack.domain_id}-FIXTURE",
    )
    run = runtime.create_run(
        task_id=f"DOMAIN-MATRIX-{pack.domain_id}",
        idempotency_key=f"fixture:{pack.domain_id}:v1",
        snapshot=snapshot,
        domain_pack_id=pack.domain_id,
        domain_pack_version=pack.version,
    )
    runtime.load_domain_pack(run.run_id, pack)
    runtime.set_context(run.run_id, {"domain_id": pack.domain_id, "workflow": pack.workflow, "fixture_only": True})

    evidence = pack.retrieve("synthetic evidence query")
    claim = Claim(
        claim_id=f"C-{pack.domain_id}-001",
        statement=pack.knowledge["fact"],
        claim_type="fixture_fact",
        evidence_ids=[evidence[0].evidence_id],
        confidence=1.0,
    )
    verification = pack.verify((claim,), evidence)
    decision = runtime.evaluate_gate(
        run_id=run.run_id,
        gate_id="PRE-001",
        snapshot=snapshot,
        claims=(claim,),
        evidence=evidence,
        risk_level=spec["risk_level"],
    )
    return {
        "domain_id": pack.domain_id,
        "workflow": pack.workflow,
        "verification": verification,
        "cer_decision": decision.result,
        "risk_level": spec["risk_level"],
        "trace_events": len(runtime.get_trace(run.run_id).events),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default="fixtures/domain_matrix/domain_packs.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    runtime = FactoryRuntime(repository_commit="FIXTURE-SYNTHETIC")
    results = [run_domain(runtime, spec) for spec in load_specs(Path(args.fixtures))]
    passed = all(item["verification"]["supported"] and item["cer_decision"] in {"PASS", "REVIEW"} for item in results)
    output = {"fixture_only": True, "domain_count": len(results), "passed": passed, "domains": results}
    print(json.dumps(output, indent=2, sort_keys=True)) if args.json else print(output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
