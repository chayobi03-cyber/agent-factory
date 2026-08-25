#!/usr/bin/env python3
"""Run the M1 RE Hybrid RAG Domain Pack end to end: ingest the corpus, run
the benchmark query set through retrieval -> claim generation -> CER gate
-> evaluation, and report results.

Unlike scripts/factory_demo.py (single synthetic evidence item, PASS/REVIEW/
BLOCK golden paths only), this exercises the real M1 Domain Pack against a
real (if small) document corpus and a real (if small) benchmark set, per
docs/RE_POC.md. See src/re_domain_pack.py for scope-honesty notes.
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

from interfaces import CERSnapshot, Claim  # noqa: E402
from cer_runtime import CERGateRuntime  # noqa: E402
from re_domain_pack import REDomainPack  # noqa: E402

BENCHMARK_PATH = ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json"

SNAPSHOT = CERSnapshot(
    policy_id="CER",
    policy_version="1.0.0",
    snapshot_id="RE-M1-SNAP-001",
    snapshot_hash="re-m1-snapshot-hash",
    source_commit="re-m1-runtime",
    required_checks=("GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"),
)


def load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def run_case(pack: REDomainPack, gate: CERGateRuntime, case: dict) -> dict:
    evidence = pack.retrieve(case["query"], top_k=5)
    if evidence:
        claim = Claim(
            claim_id=f"C-{case['case_id']}",
            statement=case["query"],
            claim_type="answer",
            evidence_ids=[evidence[0].evidence_id],
            confidence=round(evidence[0].score, 4),
        )
        claims = [claim]
    else:
        # No evidence found: generate a claim with no supportable evidence
        # id so the CER gate correctly BLOCKs (abstention), rather than
        # silently answering with nothing to cite.
        claim = Claim(
            claim_id=f"C-{case['case_id']}",
            statement=case["query"],
            claim_type="answer",
            evidence_ids=["E-NO-EVIDENCE-FOUND"],
            confidence=0.0,
        )
        claims = [claim]

    decision = gate.evaluate(
        snapshot=SNAPSHOT,
        run_id=f"RUN-{case['case_id']}",
        gate_id="RE-QA-001",
        claims=claims,
        evidence=evidence,
    )
    verification = pack.verify(claims, evidence)

    result = {
        "query": case["query"],
        "evidence": evidence,
        "claims": claims,
        "cer_result": decision.result,
        "verification": verification,
    }
    score = pack.evaluate(case, result)
    return {
        "case_id": case["case_id"],
        "query_type": case["query_type"],
        "query": case["query"],
        "cer_result": decision.result,
        "cer_findings": list(decision.triggered_findings),
        "evidence_ids": [e.evidence_id for e in evidence],
        "evidence_document_ids": sorted({e.document_id for e in evidence}),
        "verification": verification,
        "score": score,
    }


def run(benchmark_id: str | None = None) -> dict:
    pack = REDomainPack()
    loaded = pack.load()
    gate = CERGateRuntime()
    benchmark = load_benchmark()
    cases = benchmark["cases"]
    results = [run_case(pack, gate, case) for case in cases]
    passed = sum(1 for r in results if r["score"]["passed"])
    return {
        "domain_pack": {"domain_id": pack.domain_id, "version": pack.version},
        "benchmark_id": benchmark["benchmark_id"],
        "fragments_indexed": loaded,
        "cases_total": len(results),
        "cases_passed": passed,
        "cases_failed": len(results) - passed,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--report", metavar="CASE_ID", help="render a markdown report for one case")
    args = parser.parse_args()

    summary = run()

    if args.report:
        pack = REDomainPack()
        pack.load()
        gate = CERGateRuntime()
        case = next(c for c in load_benchmark()["cases"] if c["case_id"] == args.report)
        evidence = pack.retrieve(case["query"], top_k=5)
        claims = [
            Claim(f"C-{case['case_id']}", case["query"], "answer",
                  [evidence[0].evidence_id] if evidence else ["E-NO-EVIDENCE-FOUND"],
                  round(evidence[0].score, 4) if evidence else 0.0)
        ]
        decision = gate.evaluate(snapshot=SNAPSHOT, run_id="RUN-REPORT", gate_id="RE-QA-001",
                                  claims=claims, evidence=evidence)
        print(pack.render_report({"query": case["query"], "evidence": evidence, "claims": claims,
                                   "cer_result": decision.result}))
        return 0

    if args.json:
        def default(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)
            raise TypeError(f"not JSON serializable: {obj!r}")
        print(json.dumps(summary, indent=2, sort_keys=True, default=default))
    else:
        print("AgentFactory M1 RE Hybrid RAG Demo")
        print("==================================")
        print(f"Fragments indexed: {summary['fragments_indexed']}")
        for r in summary["results"]:
            mark = "PASS" if r["score"]["passed"] else "FAIL"
            print(f"[{mark}] {r['case_id']:>10} ({r['query_type']:>32}): CER={r['cer_result']}")
        print(f"\n{summary['cases_passed']}/{summary['cases_total']} benchmark cases passed")

    return 0 if summary["cases_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
