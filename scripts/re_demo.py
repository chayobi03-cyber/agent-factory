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
from re_domain_pack import RETRIEVAL_MODES, REDomainPack  # noqa: E402

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


# docs/RE_POC.md states the acceptance target as Evidence Recall@10, so the run
# that produces it must retrieve ten. It retrieved five, which reported a
# Recall@10 measured at k=5 -- the same class of mislabelling as a compliance
# reading taken at the wrong resolution bandwidth.
TOP_K = 10


def run_case(pack: REDomainPack, gate: CERGateRuntime, case: dict,
             *, mode: str | None = None) -> dict:
    evidence = pack.retrieve(case["query"], top_k=TOP_K, mode=mode)
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

    # Verify first, then gate on the verdict. Running the gate on evidence-id
    # existence and computing verification afterwards -- which is what this did
    # -- means the grounding check can never affect an outcome.
    report = pack.claim_verifier.verify(claims, evidence)
    decision = gate.evaluate(
        snapshot=SNAPSHOT,
        run_id=f"RUN-{case['case_id']}",
        gate_id="RE-QA-001",
        claims=claims,
        evidence=evidence,
        verification=report,
    )
    verification = {"domain": pack.domain_id, **report.as_dict()}

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


def score_benchmark(benchmark: dict, results: list[dict]) -> dict:
    """Aggregate the run into the RE_POC.md acceptance metrics.

    Per-case pass/fail is kept for diagnosis but is no longer the verdict. At
    159 cases a benchmark that must be 100% green can only stay green by
    containing questions the retriever already answers, which is how a
    benchmark stops measuring anything. RE_POC.md states thresholds; this
    scores against them.

    Abstention is scored per band. Two of the three are decidable from corpus
    statistics and must be perfect; the near-miss band is a measured open
    limitation (OPEN_DECISIONS D-11) and is reported, not gated.
    """
    by_id = {c["case_id"]: c for c in benchmark["cases"]}
    recalls: list[float] = []
    ranks: list[int | None] = []
    bands: dict[str, list[bool]] = {}
    for result in results:
        case = by_id[result["case_id"]]
        if case.get("expect_abstain"):
            bands.setdefault(case["abstention_band"], []).append(
                result["score"]["abstention_correct"]
            )
        elif result["score"]["evidence_recall"] is not None:
            recalls.append(result["score"]["evidence_recall"])
            ranks.append(result["score"].get("first_relevant_rank"))

    targets = benchmark.get("acceptance_targets", {})
    recall = sum(recalls) / len(recalls) if recalls else 0.0
    band_scores = {b: {"held": sum(v), "total": len(v)} for b, v in bands.items()}
    gated = ("subject_outside_domain", "entity_absent_from_corpus")
    decidable_ok = all(
        band_scores[b]["held"] == band_scores[b]["total"] for b in gated if b in band_scores
    )
    recall_ok = recall >= targets.get("evidence_recall_at_10", 0.90)
    all_abstain = [v for results_ in bands.values() for v in results_]
    # Rank-sensitive metrics, because Recall@10 is not.
    #
    # Measured across every blend from pure trigram to pure BM25, Recall@10 is
    # 0.914 for all of them: the coverage floor and the abstention rules decide
    # the result set, and ranking rarely moves a document across k=10. A metric
    # that cannot separate the retrieval methods RE_POC.md asks us to compare
    # three of is not measuring retrieval. R@1 and MRR do separate them.
    hit = [r for r in ranks if r]
    n_ans = len(ranks) or 1
    return {
        "evidence_recall_at_10": round(recall, 4),
        "recall_at_1": round(sum(1 for r in hit if r <= 1) / n_ans, 4),
        "recall_at_3": round(sum(1 for r in hit if r <= 3) / n_ans, 4),
        "mean_reciprocal_rank": round(sum(1.0 / r for r in hit) / n_ans, 4),
        "retrieval_mode": benchmark.get("retrieval_mode", "hybrid"),
        "evidence_recall_target": targets.get("evidence_recall_at_10"),
        "evidence_recall_meets_target": recall_ok,
        "abstention_overall": round(sum(all_abstain) / len(all_abstain), 4) if all_abstain else None,
        "abstention_by_band": band_scores,
        "abstention_decidable_bands_perfect": decidable_ok,
        "known_limitation": "near_miss_domain_subject -- OPEN_DECISIONS D-11",
        "meets_acceptance_targets": recall_ok and decidable_ok,
    }


def run(benchmark_id: str | None = None, *, mode: str | None = None) -> dict:
    pack = REDomainPack()
    loaded = pack.load()
    gate = CERGateRuntime()
    benchmark = load_benchmark()
    benchmark["retrieval_mode"] = mode or pack.default_retrieval_mode
    cases = benchmark["cases"]
    results = [run_case(pack, gate, case, mode=mode) for case in cases]
    passed = sum(1 for r in results if r["score"]["passed"])
    return {
        "domain_pack": {"domain_id": pack.domain_id, "version": pack.version},
        "benchmark_id": benchmark["benchmark_id"],
        "fragments_indexed": loaded,
        "documents_indexed": len({(d["document_id"], d["revision_id"]) for d in pack._raw_corpus}),
        "cases_total": len(results),
        "cases_passed": passed,
        "cases_failed": len(results) - passed,
        "acceptance": score_benchmark(benchmark, results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--report", metavar="CASE_ID", help="render a markdown report for one case")
    parser.add_argument("--mode", choices=sorted(RETRIEVAL_MODES),
                        help="retrieval method (default: the Domain Pack policy's)")
    args = parser.parse_args()

    summary = run(mode=args.mode)

    if args.report:
        pack = REDomainPack()
        pack.load()
        gate = CERGateRuntime()
        case = next(c for c in load_benchmark()["cases"] if c["case_id"] == args.report)
        evidence = pack.retrieve(case["query"], top_k=TOP_K)
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
        acc = summary["acceptance"]
        print("AgentFactory M1 RE Hybrid RAG Demo")
        print("==================================")
        print(f"Documents indexed: {summary['documents_indexed']}"
              f"   Fragments: {summary['fragments_indexed']}"
              f"   Cases: {summary['cases_total']}")
        print()
        for r in summary["results"]:
            if not r["score"]["passed"]:
                print(f"[FAIL] {r['case_id']:>10} ({r['query_type']:>34}): CER={r['cer_result']}")
        print()
        mark = "MEETS" if acc["evidence_recall_meets_target"] else "BELOW"
        print(f"Evidence Recall@10 : {acc['evidence_recall_at_10']:.3f}  "
              f"[{mark} target {acc['evidence_recall_target']}]")
        print(f"Recall@1 / @3      : {acc['recall_at_1']:.3f} / {acc['recall_at_3']:.3f}"
              f"   MRR: {acc['mean_reciprocal_rank']:.3f}"
              f"   (mode: {acc['retrieval_mode']})")
        print("Abstention by band :")
        for band, s_ in sorted(acc["abstention_by_band"].items()):
            gated = band != "near_miss_domain_subject"
            note = "" if gated else "   (known limitation, OPEN_DECISIONS D-11)"
            print(f"  {band:28s} {s_['held']}/{s_['total']}{note}")
        print()
        print(f"{summary['cases_passed']}/{summary['cases_total']} cases pass per-case; "
              f"acceptance targets {'MET' if acc['meets_acceptance_targets'] else 'NOT MET'}")

    return 0 if summary["acceptance"]["meets_acceptance_targets"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
