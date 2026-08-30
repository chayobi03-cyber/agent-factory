#!/usr/bin/env python3
"""Re-derive the retrieval constants against whatever corpus you point it at.

Four numbers decide how this Domain Pack retrieves, and every one of them was
fitted to a 30-document synthetic corpus:

    _COVERAGE_FLOOR         src/re_domain_pack.py    how much of a question's
                                                     IDF mass a fragment must
                                                     cover to be a candidate
    _UNSEEN_TERM_CEILING    src/re_domain_pack.py    how much of a question may
                                                     be absent before it is
                                                     treated as unanswerable
    RETRIEVAL_MODES         src/re_domain_pack.py    the BM25/trigram blend
    claim_grounding_floor   domains/re/domain_pack.yaml
                                                     how much of a claim its
                                                     evidence must supply

Until now the sweeps that produced them lived in throwaway scripts, so the
register cited numbers nobody could re-derive. That is fine exactly once. The
moment the corpus changes -- and OPEN_DECISIONS D-08 means the real one arrives
from outside the tree -- those four values are unfounded until re-measured, and
re-measuring has to be a command rather than an archaeology exercise.

    python3 scripts/calibrate_retrieval.py
    python3 scripts/calibrate_retrieval.py --corpus /path/to/real/docs \\
                                           --benchmark /path/to/cases.json

It does not edit anything. It prints what each value would buy and exits
non-zero when a shipped constant is no longer the right choice for the corpus
it just measured -- so "our constants have gone stale" is a CI signal rather
than something noticed a milestone later.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import re_domain_pack as rdp  # noqa: E402
from claim_verification import ClaimVerifier  # noqa: E402
from corpus_source import (  # noqa: E402
    CorpusError,
    from_directory,
    DECIDABLE_ABSTENTION_BANDS,
    from_documents,
    missing_benchmark_documents,
)
from interfaces import Claim  # noqa: E402
from re_corpus import CORPUS, adversarial_corpus, term_saturating_documents  # noqa: E402
from re_domain_pack import RETRIEVAL_MODES, REDomainPack  # noqa: E402

DEFAULT_BENCHMARK = ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json"
TOP_K = 10

COVERAGE_FLOORS = [0.00, 0.04, 0.08, 0.12, 0.16, 0.20, 0.24]
UNSEEN_CEILINGS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
GROUNDING_FLOORS = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]


# --- measurement -------------------------------------------------------------

def score(pack: REDomainPack, cases: Sequence[dict]) -> dict[str, Any]:
    recalls: list[float] = []
    ranks: list[int | None] = []
    bands: dict[str, list[bool]] = {}
    for case in cases:
        found = pack.retrieve(case["query"], top_k=TOP_K)
        docs = [e.document_id for e in found]
        if case.get("expect_abstain"):
            band = case.get("abstention_band", "unbanded")
            bands.setdefault(band, []).append(not found)
            continue
        expected = set(case.get("expected_document_ids") or [])
        if not expected:
            continue
        recalls.append(len(set(docs) & expected) / len(expected))
        ranks.append(next((i + 1 for i, d in enumerate(docs) if d in expected), None))
    hit = [r for r in ranks if r]
    n = len(recalls) or 1
    return {
        "recall_at_10": sum(recalls) / n,
        "recall_at_1": sum(1 for r in hit if r <= 1) / n,
        "mrr_at_10": sum(1.0 / r for r in hit) / n,
        "bands": {b: (sum(v), len(v)) for b, v in bands.items()},
        "abstention": (
            sum(sum(v) for v in bands.values()) / sum(len(v) for v in bands.values())
            if bands else None
        ),
    }


def build_shapes(documents: Sequence[dict], synthetic: bool) -> dict[str, Callable[[], list]]:
    """Corpus shapes to test stability across.

    The adversarial generators only make sense for the synthetic corpus they
    were written against -- against real documents they would inject fabricated
    ones. With a real corpus this degrades to the corpus itself, and stability
    is reported as not measured rather than silently faked.
    """
    if not synthetic:
        return {"as-provided": lambda: list(documents)}
    shapes: dict[str, Callable[[], list]] = {"baseline": lambda: adversarial_corpus(0)}
    for volume in (10, 40, 100, 250):
        shapes[f"distractors-{volume}"] = (lambda v=volume: adversarial_corpus(v))
    for term in ("antenna", "setup", "calibration", "cable", "chamber"):
        for count in (3, 20):
            shapes[f"saturate-{term}-{count}"] = (
                lambda t=term, c=count: list(CORPUS) + term_saturating_documents(c, phrase=t)
            )
    return shapes


# --- sweeps ------------------------------------------------------------------
#
# A sweep answers one of three things, not two. `STALE` and `FITS` were the
# whole vocabulary, so a sweep that could not decide had to claim one of them,
# and both existing cases claimed `FITS`: `sweep_unseen_ceiling` returned it
# when the benchmark carried no banded abstention cases, and `sweep_modes`
# returned it unconditionally. Pointed at a corpus whose benchmark lacked
# `abstention_band`, the tool printed a sweep showing the shipped ceiling
# costing a third of the recall and then declared every constant the right
# choice, exit 0 -- while the handoff tells the reader it exits non-zero when a
# shipped value no longer fits. `UNVERIFIED` is the missing answer: not a
# failure of the constant, a failure to have measured it, and non-zero either
# way because a green light neither has earned.

FITS = "fits"
STALE = "stale"
UNVERIFIED = "unverified"

def sweep_coverage_floor(packs: dict[str, REDomainPack], cases, shipped: float) -> str:
    print("\n## _COVERAGE_FLOOR")
    print(f"{'floor':>7} {'Recall@10':>10} {'R@1':>7} {'unstable':>9}   ")
    base = packs[next(iter(packs))]
    best: list[tuple[float, float]] = []
    original = rdp._COVERAGE_FLOOR
    try:
        for floor in COVERAGE_FLOORS:
            rdp._COVERAGE_FLOOR = floor
            primary = score(base, cases)
            outcomes = {
                name: {c["case_id"]: _outcome(p, c) for c in cases}
                for name, p in packs.items()
            }
            unstable = [
                cid for cid in outcomes[next(iter(outcomes))]
                if len({outcomes[n][cid] for n in outcomes}) > 1
            ]
            mark = "  <-- shipped" if abs(floor - shipped) < 1e-9 else ""
            print(f"{floor:7.2f} {primary['recall_at_10']:10.3f} {primary['recall_at_1']:7.3f} "
                  f"{len(unstable):9d}{mark}")
            best.append((primary["recall_at_10"], floor))
    finally:
        rdp._COVERAGE_FLOOR = original
    top = max(r for r, _ in best)
    band = [f for r, f in best if r >= top - 1e-9]
    ok = any(abs(f - shipped) < 1e-9 for f in band)
    print(f"   best Recall@10 {top:.3f} at floors {band}; shipped {shipped} "
          f"{'is in the band' if ok else 'IS NOT in the band'}")
    return FITS if ok else STALE


def sweep_unseen_ceiling(pack: REDomainPack, cases, shipped: float) -> str:
    print("\n## _UNSEEN_TERM_CEILING")
    print(f"{'ceiling':>8} {'Recall@10':>10} {'abstention':>11}   bands")
    rows = []
    original = rdp._UNSEEN_TERM_CEILING
    try:
        for ceiling in UNSEEN_CEILINGS:
            rdp._UNSEEN_TERM_CEILING = ceiling
            s = score(pack, cases)
            bands = "  ".join(f"{b}={h}/{t}" for b, (h, t) in sorted(s["bands"].items()))
            mark = "  <-- shipped" if abs(ceiling - shipped) < 1e-9 else ""
            abst = s["abstention"]
            print(f"{ceiling:8.2f} {s['recall_at_10']:10.3f} "
                  f"{(f'{abst:.3f}' if abst is not None else 'n/a'):>11}   {bands}{mark}")
            rows.append((ceiling, s))
    finally:
        rdp._UNSEEN_TERM_CEILING = original

    # The selection rule the register records: the largest ceiling at which the
    # abstention bands that are decidable from corpus statistics stay perfect.
    decidable = DECIDABLE_ABSTENTION_BANDS
    perfect = [
        c for c, s in rows
        if all(s["bands"].get(b, (0, 0))[0] == s["bands"].get(b, (0, 0))[1] for b in decidable)
        and any(b in s["bands"] for b in decidable)
    ]
    if not perfect:
        print("   UNVERIFIED: no ceiling keeps the decidable bands perfect -- the benchmark "
              "carries no case labelled with an `abstention_band` of "
              f"{' or '.join(decidable)}, or the corpus cannot decide them.")
        print("   The shipped ceiling is neither confirmed nor refuted by this benchmark. "
              "Add banded abstention cases (docs/ADDING_A_DOMAIN.md) and re-run.")
        return UNVERIFIED
    chosen = max(perfect)
    ok = abs(chosen - shipped) < 1e-9
    print(f"   largest ceiling keeping the decidable bands perfect: {chosen}; "
          f"shipped {shipped} {'matches' if ok else 'DOES NOT match'}")
    return FITS if ok else STALE


def sweep_modes(pack: REDomainPack, cases) -> str:
    print("\n## RETRIEVAL_MODES")
    print(f"{'mode':<10} {'R@1':>7} {'R@10':>7} {'MRR@10':>8}")
    results = {}
    for mode in sorted(RETRIEVAL_MODES):
        original = rdp.RETRIEVAL_MODES.copy()
        try:
            def retrieve(query, top_k=TOP_K, _m=mode):
                return pack.retrieve(query, top_k=top_k, mode=_m)
            s = _score_with(retrieve, cases)
        finally:
            rdp.RETRIEVAL_MODES = original
        results[mode] = s
        print(f"{mode:<10} {s['recall_at_1']:7.3f} {s['recall_at_10']:7.3f} {s['mrr_at_10']:8.3f}")
    # Tied on every metric, not merely on Recall@10. A first version of this
    # check keyed off Recall@10 alone and turned the in-tree run non-zero:
    # all three modes score 0.914 there, while R@1 and MRR separate trigram
    # (0.799 / 0.841) from BM25 and hybrid (0.827 / 0.868). Recall@10 being
    # blind is the D-14 finding, not an inability to compare -- the sweep's own
    # advice is to judge on R@1/MRR, and that advice is only honest if the
    # table can still be read.
    tied = {
        metric: len({round(s[metric], 4) for s in results.values()}) == 1
        for metric in ("recall_at_1", "recall_at_10", "mrr_at_10")
    }
    if tied["recall_at_10"] and not all(tied.values()):
        print("   Recall@10 is identical for every mode -- it cannot compare retrieval "
              "methods on this corpus. Judge on R@1/MRR, which do separate them.")
    if all(tied.values()):
        print("   UNVERIFIED: every mode scores identically on R@1, Recall@10 and MRR -- "
              "this benchmark cannot compare retrieval methods at all.")
        return UNVERIFIED
    # Deliberately no staleness rule for the blend itself. That the shipped
    # hybrid contributes about 6.5:1 in BM25's favour is a measured, recorded,
    # open item (OPEN_DECISIONS D-14); picking a threshold at which the blend
    # becomes "stale" would fit that decision to whichever corpus ran last,
    # which is the one thing this repository does not do to a retrieval
    # constant. The table is the finding; the reader makes the call.
    return FITS


def sweep_grounding_floor(pack: REDomainPack, cases, shipped: float) -> str:
    print("\n## claim_grounding_floor  (domains/re/domain_pack.yaml)")
    print(f"{'floor':>7} {'answerable ungrounded':>22} {'abstention caught':>18}")
    answerable = [c for c in cases if not c.get("expect_abstain")]
    abstaining = [c for c in cases if c.get("expect_abstain")]
    rows = []
    for floor in GROUNDING_FLOORS:
        verifier = ClaimVerifier(
            rdp._tokenize, grounding_floor=floor,
            ignore_terms=rdp._STOPWORDS | rdp._DOMAIN_GENERIC_TERMS,
        )
        lost = caught = 0
        for case in answerable:
            found = pack.retrieve(case["query"], top_k=TOP_K)
            if not found:
                continue
            claim = Claim(f"C-{case['case_id']}", case["query"], "answer",
                          [found[0].evidence_id], 0.5)
            if not verifier.verify([claim], found).all_grounded:
                lost += 1
        for case in abstaining:
            found = pack.retrieve(case["query"], top_k=TOP_K)
            if not found:
                continue
            claim = Claim(f"C-{case['case_id']}", case["query"], "answer",
                          [found[0].evidence_id], 0.5)
            if not verifier.verify([claim], found).all_grounded:
                caught += 1
        mark = "  <-- shipped" if abs(floor - shipped) < 1e-9 else ""
        print(f"{floor:7.2f} {lost:22d} {caught:18d}{mark}")
        rows.append((floor, lost, caught))
    safe = [f for f, lost, _ in rows if lost == 0]
    if not safe:
        print("   every floor rejects a legitimately grounded claim -- lower the range")
        return STALE
    highest = max(safe)
    ok = abs(shipped - highest) < 1e-9 or shipped in safe
    print(f"   floors rejecting no answerable case: {safe}; shipped {shipped} "
          f"{'is safe' if ok else 'REJECTS answerable cases'}")
    return FITS if ok else STALE


def _outcome(pack: REDomainPack, case: dict) -> bool:
    found = pack.retrieve(case["query"], top_k=TOP_K)
    if case.get("expect_abstain"):
        return not found
    expected = set(case.get("expected_document_ids") or [])
    return expected.issubset({e.document_id for e in found}) if expected else bool(found)


def _score_with(retrieve, cases) -> dict[str, Any]:
    recalls, ranks = [], []
    for case in cases:
        if case.get("expect_abstain"):
            continue
        expected = set(case.get("expected_document_ids") or [])
        if not expected:
            continue
        docs = [e.document_id for e in retrieve(case["query"])]
        recalls.append(len(set(docs) & expected) / len(expected))
        ranks.append(next((i + 1 for i, d in enumerate(docs) if d in expected), None))
    hit = [r for r in ranks if r]
    n = len(recalls) or 1
    return {
        "recall_at_10": sum(recalls) / n,
        "recall_at_1": sum(1 for r in hit if r <= 1) / n,
        "mrr_at_10": sum(1.0 / r for r in hit) / n,
    }


# --- entry point -------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", metavar="DIR",
                        help="directory of JSON documents; default is the in-tree corpus")
    parser.add_argument("--benchmark", metavar="PATH", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    args = parser.parse_args()

    try:
        source = from_directory(args.corpus) if args.corpus else from_documents(CORPUS)
    except CorpusError as exc:
        print(f"corpus error: {exc}", file=sys.stderr)
        return 2

    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    cases = benchmark["cases"]
    missing = missing_benchmark_documents(cases, source.documents)
    if missing:
        print(f"benchmark error: {len(missing)} expected document(s) absent from the corpus: "
              f"{missing[:5]}{'...' if len(missing) > 5 else ''}", file=sys.stderr)
        print("A benchmark that names documents the corpus lacks measures nothing.",
              file=sys.stderr)
        return 2

    synthetic = not args.corpus
    print(f"# Retrieval calibration")
    print(f"corpus    : {source.origin}")
    print(f"digest    : {source.digest}")
    print(f"documents : {source.document_count} ({source.distinct_document_ids} identifiers)")
    print(f"benchmark : {args.benchmark.name}  {len(cases)} cases")
    if not synthetic:
        print("note      : stability sweeps are skipped -- the adversarial generators are "
              "written against the synthetic corpus and would inject fabricated documents")

    shapes = build_shapes(source.documents, synthetic)
    packs: dict[str, REDomainPack] = {}
    for name, build in shapes.items():
        pack = REDomainPack()
        pack.load(build() if synthetic else source)
        packs[name] = pack
    primary = packs[next(iter(packs))]

    grounding_shipped = float(
        ((primary.policy or {}).get("verification_policy", {}) or {})
        .get("claim_grounding_floor", rdp._CLAIM_GROUNDING_FLOOR)
    )
    verdicts = {
        "coverage_floor": sweep_coverage_floor(packs, cases, rdp._COVERAGE_FLOOR),
        "unseen_ceiling": sweep_unseen_ceiling(primary, cases, rdp._UNSEEN_TERM_CEILING),
        "retrieval_modes": sweep_modes(primary, cases),
        "claim_grounding_floor": sweep_grounding_floor(primary, cases, grounding_shipped),
    }

    stale = sorted(k for k, v in verdicts.items() if v == STALE)
    unverified = sorted(k for k, v in verdicts.items() if v == UNVERIFIED)
    print()
    if stale:
        print(f"STALE: {', '.join(stale)} no longer fit this corpus. "
              f"Re-derive before trusting any benchmark number measured against it.")
    if unverified:
        print(f"UNVERIFIED: {', '.join(unverified)} could not be checked against this "
              f"benchmark. The shipped values are neither confirmed nor refuted, so a "
              f"number measured with them here carries no more authority than before.")
    if not stale and not unverified:
        print("All shipped constants remain the right choice for this corpus.")

    if args.json:
        print(json.dumps({"corpus": source.identity(), "verdicts": verdicts,
                          "stale": stale, "unverified": unverified},
                         indent=2, sort_keys=True))
    return 0 if not stale and not unverified else 1


if __name__ == "__main__":
    raise SystemExit(main())
