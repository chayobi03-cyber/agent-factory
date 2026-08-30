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
from corpus_source import (  # noqa: E402
    DECIDABLE_ABSTENTION_BANDS,
    UNDECIDABLE_ABSTENTION_BANDS,
    CorpusError,
    from_directory,
    missing_benchmark_documents,
)
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


class BenchmarkError(ValueError):
    """A benchmark that cannot be scored against the corpus it was given."""


def load_benchmark(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or BENCHMARK_PATH).read_text(encoding="utf-8"))


# docs/RE_POC.md states the acceptance target as Evidence Recall@10, so the run
# that produces it must retrieve ten. It retrieved five, which reported a
# Recall@10 measured at k=5 -- the same class of mislabelling as a compliance
# reading taken at the wrong resolution bandwidth.
TOP_K = 10


def run_case(pack: REDomainPack, gate: CERGateRuntime, case: dict,
             *, mode: str | None = None) -> dict:
    evidence = pack.retrieve(case["query"], top_k=TOP_K, mode=mode)
    # One definition of what a query plus its evidence amounts to, in the
    # kernel. With no evidence it yields a claim citing E-NO-EVIDENCE-FOUND, so
    # the CER gate BLOCKs (abstention) rather than silently answering with
    # nothing to cite.
    claims = [pack.build_claim(case["query"], evidence, claim_id=f"C-{case['case_id']}")]

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


def random_baseline(pack: REDomainPack, cases: list[dict], *, top_k: int = TOP_K,
                    trials: int = 200, seed: int = 20260826) -> float:
    """What Evidence Recall@k scores when the retriever is replaced by a coin.

    Absent until 2026-08-26, and its absence made every recall figure read as
    though zero were the floor. It is not: drawing ten fragments uniformly from
    a 108-fragment corpus reaches 4.9 of its 25 documents, so a third of the
    headline is paid out before retrieval does anything at all.

    Reported, never gated on -- the acceptance target is what the RE PoC
    specifies and this does not move it. What it moves is how the number reads:
    0.906 against a floor of 0.356 is 85% of the distance available, which is
    a different sentence from 0.906 against a floor of zero.
    """
    import random

    rng = random.Random(seed)
    fragments = pack._fragments
    if not fragments or not cases:
        return 0.0
    totals = []
    for _ in range(trials):
        per_case = []
        for case in cases:
            gold = set(case["expected_document_ids"])
            drawn = {f.document_id for f in rng.sample(fragments, min(top_k, len(fragments)))}
            per_case.append(len(gold & drawn) / len(gold))
        totals.append(sum(per_case) / len(per_case))
    return sum(totals) / len(totals)


def score_benchmark(benchmark: dict, results: list[dict], pack: REDomainPack) -> dict:
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
    # Split out the cases whose query is a restatement of its own answer. See
    # REDomainPack.query_is_verbatim_in_its_answer -- they cannot really fail,
    # so the headline recall is higher than what the retriever earns.
    verbatim: list[float] = []
    earned: list[float] = []
    bands: dict[str, list[bool]] = {}
    band_cases: dict[str, list[str]] = {}
    by_result = {r["case_id"]: r for r in results}
    answerable_cases = [c for c in benchmark["cases"]
                        if not c.get("expect_abstain") and c.get("expected_document_ids")]
    for result in results:
        case = by_id[result["case_id"]]
        if case.get("expect_abstain"):
            bands.setdefault(case["abstention_band"], []).append(
                result["score"]["abstention_correct"]
            )
            band_cases.setdefault(case["abstention_band"], []).append(case["case_id"])
        elif result["score"]["evidence_recall"] is not None:
            recalls.append(result["score"]["evidence_recall"])
            ranks.append(result["score"].get("first_relevant_rank"))
            if pack.query_is_verbatim_in_its_answer(case):
                verbatim.append(result["score"]["evidence_recall"])
            else:
                earned.append(result["score"]["evidence_recall"])

    targets = benchmark.get("acceptance_targets", {})
    baseline = random_baseline(pack, answerable_cases)
    recall = sum(recalls) / len(recalls) if recalls else 0.0
    # `held` counts BLOCK only, because BLOCK and REVIEW are not the same
    # outcome and collapsing them would let a system that referred everything
    # score perfectly. But the risk D-11 actually describes is the pack
    # *answering* a question it should refuse, and that is `silently_answered`
    # -- a PASS on a case expecting abstention. Reporting only `held` left the
    # difference between "blocked" and "flagged for a person" invisible.
    band_scores = {
        b: {"held": sum(v), "total": len(v),
            "silently_answered": sum(1 for cid in band_cases[b]
                                     if by_result[cid]["cer_result"] == "PASS")}
        for b, v in bands.items()
    }
    gated = DECIDABLE_ABSTENTION_BANDS
    decidable_ok = all(
        band_scores[b]["held"] == band_scores[b]["total"] for b in gated if b in band_scores
    )
    # Gated on what the retriever earns, not on the headline. 11 of the 139
    # answerable cases restate their own answer and cannot really fail; scoring
    # the target against the inflated figure would let a real regression hide
    # behind them. The margin over 0.90 is genuinely thin -- 0.006 -- and that
    # is the point of measuring it rather than the 0.014 the headline suggests.
    earned_recall = sum(earned) / len(earned) if earned else recall
    recall_ok = earned_recall >= targets.get("evidence_recall_at_10", 0.90)
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
        # With exactly one gold document per case this is a hit rate, not a
        # recall: the score is 0 or 1 and there is no partial set to recover.
        # `evidence_recall_at_10` is kept as the name the acceptance contract
        # and scripts/evidence_gate.py were written against; `hit_rate_at_10`
        # is the same number under the name it earns.
        "evidence_recall_at_10": round(recall, 4),
        "hit_rate_at_10": round(recall, 4),
        "gold_documents_per_case": round(
            sum(len(c["expected_document_ids"]) for c in answerable_cases) / len(answerable_cases), 3
        ) if answerable_cases else None,
        "random_baseline_recall_at_10": round(baseline, 4),
        "share_of_available_headroom": round(
            (earned_recall - baseline) / (1.0 - baseline), 4
        ) if baseline < 1.0 else None,
        "evidence_recall_excluding_verbatim": round(sum(earned) / len(earned), 4) if earned else None,
        "verbatim_case_count": len(verbatim),
        "recall_at_1": round(sum(1 for r in hit if r <= 1) / n_ans, 4),
        "recall_at_3": round(sum(1 for r in hit if r <= 3) / n_ans, 4),
        "mean_reciprocal_rank": round(sum(1.0 / r for r in hit) / n_ans, 4),
        "retrieval_mode": benchmark.get("retrieval_mode", "hybrid"),
        "evidence_recall_target": targets.get("evidence_recall_at_10"),
        "evidence_recall_meets_target": recall_ok,
        "evidence_recall_gated_on": "evidence_recall_excluding_verbatim",
        "abstention_overall": round(sum(all_abstain) / len(all_abstain), 4) if all_abstain else None,
        "abstention_by_band": band_scores,
        "abstention_decidable_bands_perfect": decidable_ok,
        "known_limitation": f"{', '.join(UNDECIDABLE_ABSTENTION_BANDS)} -- OPEN_DECISIONS D-11",
        "meets_acceptance_targets": recall_ok and decidable_ok,
    }


def run(benchmark_id: str | None = None, *, mode: str | None = None,
        corpus: str | None = None, benchmark_path: str | Path | None = None) -> dict:
    pack = REDomainPack()
    source = from_directory(corpus) if corpus else None
    loaded = pack.load(source)
    gate = CERGateRuntime()
    benchmark = load_benchmark(benchmark_path)

    # The in-tree benchmark names DOC-RE-* documents. Pointed at someone else's
    # corpus it scores one corpus against another's answer key and reports a
    # recall near zero, which reads as a broken retriever rather than as the
    # mismatch it is. calibrate_retrieval.py has always refused this; this tool
    # reported 0.000 instead, and it is the one a new corpus reaches first.
    if source is not None:
        missing = missing_benchmark_documents(benchmark["cases"], source.documents)
        if missing:
            raise BenchmarkError(
                f"{len(missing)} expected document(s) named by the benchmark are absent "
                f"from the corpus: {missing[:5]}{'...' if len(missing) > 5 else ''}\n"
                f"A benchmark that names documents the corpus lacks measures nothing. "
                f"Author one for this corpus and pass it with --benchmark."
            )
    benchmark["retrieval_mode"] = mode or pack.default_retrieval_mode
    cases = benchmark["cases"]
    results = [run_case(pack, gate, case, mode=mode) for case in cases]
    passed = sum(1 for r in results if r["score"]["passed"])
    return {
        "domain_pack": {"domain_id": pack.domain_id, "version": pack.version},
        "benchmark_id": benchmark["benchmark_id"],
        "fragments_indexed": loaded,
        "documents_indexed": pack.corpus_identity["documents"],
        # Which corpus produced these numbers. Necessary once the documents can
        # live outside the repository (OPEN_DECISIONS D-08): a benchmark result
        # measured against an out-of-tree corpus is not re-derivable from the
        # commit SHA alone, so the run has to name and digest what it read.
        "corpus": pack.corpus_identity,
        "cases_total": len(results),
        "cases_passed": passed,
        "cases_failed": len(results) - passed,
        "acceptance": score_benchmark(benchmark, results, pack),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--report", metavar="CASE_ID", help="render a markdown report for one case")
    parser.add_argument("--mode", choices=sorted(RETRIEVAL_MODES),
                        help="retrieval method (default: the Domain Pack policy's)")
    parser.add_argument("--corpus", metavar="DIR",
                        help="load documents from a directory of JSON files instead of the "
                             "in-tree synthetic corpus. The result is recorded with the "
                             "corpus origin and digest, because it is no longer reproducible "
                             "from the commit SHA alone (OPEN_DECISIONS D-08)")
    parser.add_argument("--benchmark", metavar="PATH",
                        help="benchmark JSON to score, instead of the in-tree synthetic set. "
                             "A corpus of your own needs one: the in-tree benchmark names "
                             "DOC-RE-* documents and measures nothing against anything else. "
                             "See docs/ADDING_A_DOMAIN.md for the case schema")
    args = parser.parse_args()

    try:
        summary = run(mode=args.mode, corpus=args.corpus, benchmark_path=args.benchmark)
    except CorpusError as exc:
        print(f"corpus error: {exc}", file=sys.stderr)
        return 2
    except BenchmarkError as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        pack = REDomainPack()
        pack.load()
        gate = CERGateRuntime()
        case = next(c for c in load_benchmark(args.benchmark)["cases"]
                    if c["case_id"] == args.report)
        evidence = pack.retrieve(case["query"], top_k=TOP_K)
        claims = [pack.build_claim(case["query"], evidence, claim_id=f"C-{case['case_id']}")]
        # This path built its own claim *and* gated without a verification
        # report, so `--report` rendered a CER decision that had never checked
        # grounding -- a third copy of one definition, drifted. Both now come
        # from the same place as every other caller.
        report = pack.claim_verifier.verify(claims, evidence)
        decision = gate.evaluate(snapshot=SNAPSHOT, run_id="RUN-REPORT", gate_id="RE-QA-001",
                                  claims=claims, evidence=evidence, verification=report)
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
        print(f"Corpus: {summary['corpus']['origin']}  {summary['corpus']['digest'][:23]}...")
        print()
        for r in summary["results"]:
            if not r["score"]["passed"]:
                print(f"[FAIL] {r['case_id']:>10} ({r['query_type']:>34}): CER={r['cer_result']}")
        print()
        mark = "MEETS" if acc["evidence_recall_meets_target"] else "BELOW"
        print(f"Evidence Recall@10 : {acc['evidence_recall_at_10']:.3f}  "
              f"[{mark} target {acc['evidence_recall_target']}]")
        print(f"  ...excluding {acc['verbatim_case_count']} cases whose query restates its own "
              f"answer: {acc['evidence_recall_excluding_verbatim']:.3f}")
        print(f"  ...against a random-retrieval floor of "
              f"{acc['random_baseline_recall_at_10']:.3f}"
              f"  ({acc['share_of_available_headroom']:.1%} of the available headroom)")
        print(f"  one gold document per case ({acc['gold_documents_per_case']:.2f}), so this is a"
              f" hit rate; `hit_rate_at_10` reports it under that name")
        print(f"Recall@1 / @3      : {acc['recall_at_1']:.3f} / {acc['recall_at_3']:.3f}"
              f"   MRR: {acc['mean_reciprocal_rank']:.3f}"
              f"   (mode: {acc['retrieval_mode']})")
        print("Abstention by band :   held = BLOCK; silent = answered anyway")
        for band, s_ in sorted(acc["abstention_by_band"].items()):
            gated = band in DECIDABLE_ABSTENTION_BANDS
            note = "" if gated else "   (known limitation, OPEN_DECISIONS D-11)"
            print(f"  {band:28s} held {s_['held']}/{s_['total']}"
                  f"   silent {s_['silently_answered']}/{s_['total']}{note}")
        print()
        print(f"{summary['cases_passed']}/{summary['cases_total']} cases pass per-case; "
              f"acceptance targets {'MET' if acc['meets_acceptance_targets'] else 'NOT MET'}")

    return 0 if summary["acceptance"]["meets_acceptance_targets"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
