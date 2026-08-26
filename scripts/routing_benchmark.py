#!/usr/bin/env python3
"""Does the right Domain Pack get picked when several are loaded?

    python3 scripts/routing_benchmark.py
    python3 scripts/routing_benchmark.py --json

Retrieval accuracy and routing accuracy are different questions and only one of
them needs real documents. Accuracy *within* a domain is a claim about whether
the right paragraph of a real report comes back, and invented documents cannot
support it -- which is why OPEN_DECISIONS defers RE tuning to the corpus
arriving after handover. Discrimination *between* domains is a claim about
whether battery vocabulary looks like battery vocabulary, and the corpora only
need to be about different things, which invented ones are.

Two biases were found this way, on invented documents, and both were real:
routing on vocabulary coverage favoured whichever corpus was largest, and it
favoured whichever pack tokenized *worst*. Neither would have shown up in a
single-domain retrieval score.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from domain_router import route  # noqa: E402
from run_domain import load_all  # noqa: E402

BENCHMARK = ROOT / "templates" / "benchmark" / "cross_domain_routing_v0.1.json"

#: What routing has to do to be worth having, per band.
#:
#: `out_of_scope` is 1.0 and the others are not, deliberately. Naming a domain
#: for a question no corpus covers produces a confident answer from the wrong
#: documents, which is the failure mode with no visible symptom; missing a
#: `clear` case produces a refusal or a referral, which a reader sees.
ACCEPTANCE = {
    "clear": 0.85,
    "shared_vocabulary": 0.85,
    "out_of_scope": 1.0,
}


def judge(case: dict, routing) -> tuple[bool, str]:
    """A case passes when the routed domain is the expected one.

    `requires_human` is counted as a miss even when the right domain is named
    first. It is a better failure than a wrong answer, but it is still a
    question a person has to field, and a router that referred everything would
    otherwise score perfectly.
    """
    want = case["expected_domain"]
    if want is None:
        return routing.domain is None, "refused" if routing.domain is None else "named a domain"
    if routing.domain is None:
        return False, "refused"
    if routing.requires_human:
        return False, "referred to a person"
    return routing.domain == want, f"routed {routing.domain}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--benchmark", default=str(BENCHMARK))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    benchmark = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    packs = load_all(examples=True)
    if len(packs) < 2:
        print("error: routing needs at least two loaded domains", file=sys.stderr)
        return 2

    per_band: Counter[str] = Counter()
    band_total: Counter[str] = Counter()
    misses = []
    for case in benchmark["cases"]:
        routing = route(packs, case["query"])
        ok, what = judge(case, routing)
        band_total[case["band"]] += 1
        per_band[case["band"]] += int(ok)
        if not ok:
            misses.append({
                "case_id": case["case_id"], "band": case["band"],
                "query": case["query"], "expected": case["expected_domain"],
                "got": routing.domain, "requires_human": routing.requires_human,
                "reason": routing.reason,
            })

    bands = {
        band: {
            "passed": per_band[band], "total": band_total[band],
            "rate": round(per_band[band] / band_total[band], 4),
            "target": ACCEPTANCE.get(band),
            "meets_target": (per_band[band] / band_total[band]) >= ACCEPTANCE[band]
            if band in ACCEPTANCE else None,
        }
        for band in sorted(band_total)
    }
    passed, total = sum(per_band.values()), sum(band_total.values())
    meets = all(b["meets_target"] for b in bands.values() if b["meets_target"] is not None)
    report = {
        "benchmark_id": benchmark["benchmark_id"],
        "domains": sorted(p.domain_id for p in packs.values()),
        "passed": passed, "total": total,
        "rate": round(passed / total, 4) if total else 0.0,
        "bands": bands,
        "meets_acceptance_targets": meets,
        "misses": misses,
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"{benchmark['benchmark_id']}  over {', '.join(report['domains'])}")
        print(f"routed correctly: {passed}/{total}  ({report['rate']:.3f})\n")
        for band, stats in bands.items():
            target = f"  target {stats['target']:.2f}" if stats["target"] else ""
            mark = "" if stats["meets_target"] is not False else "   BELOW TARGET"
            print(f"  {band:20s} {stats['passed']:2d}/{stats['total']:<2d} "
                  f"{stats['rate']:.3f}{target}{mark}")
        if misses:
            print("\nmisses:")
            for m in misses:
                human = " human=True" if m["requires_human"] else ""
                print(f"  {m['case_id']} [{m['band']}] want={m['expected']} "
                      f"got={m['got']}{human}\n      {m['query']}\n      {m['reason']}")
        print(f"\nmeets acceptance targets: {meets}")

    return 0 if meets else 1


if __name__ == "__main__":
    raise SystemExit(main())
