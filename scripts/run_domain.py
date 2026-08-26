#!/usr/bin/env python3
"""Query any Domain Pack against a local folder of documents.

    python3 scripts/run_domain.py --domain thermal \\
        --corpus /local/thermal-reports \\
        --query "what caused the junction temperature excursion?"

    python3 scripts/run_domain.py --domain re --query "..."      # in-tree corpus
    python3 scripts/run_domain.py --list

This is the entry point for the case the factory exists to serve: someone has
documents for an engineering domain and wants answers grounded in them, without
writing code. A domain is `domains/<id>/domain_pack.yaml` plus documents; both
are data.

Retrieval, verification and the CER gate all run, so what comes back is not a
search result but a gated answer -- with the evidence it rests on, what the
evidence failed to support, and an explicit refusal when the corpus cannot
answer. That last part matters more than the hit list: OPEN_DECISIONS D-11
records exactly how far the refusal can be trusted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cer_runtime import CERGateRuntime  # noqa: E402
from corpus_source import CorpusError, from_directory  # noqa: E402
from generic_domain_pack import GenericDomainPack  # noqa: E402
from interfaces import CERSnapshot, Claim  # noqa: E402

DOMAINS_DIR = ROOT / "domains"

SNAPSHOT = CERSnapshot(
    policy_id="CER",
    policy_version="1.0.0",
    snapshot_id="DOMAIN-QUERY",
    snapshot_hash="domain-query-snapshot",
    source_commit="domain-query-runtime",
    required_checks=("GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"),
)


def available_domains() -> list[str]:
    if not DOMAINS_DIR.is_dir():
        return []
    return sorted(d.name for d in DOMAINS_DIR.iterdir()
                  if (d / "domain_pack.yaml").exists())


def build_pack(domain: str, corpus: str | None) -> GenericDomainPack:
    """RE keeps its in-tree corpus as a default; every other domain must be
    given one, because it has no documents of its own in this repository."""
    directory = DOMAINS_DIR / domain
    if not (directory / "domain_pack.yaml").exists():
        raise FileNotFoundError(
            f"no domain {domain!r}; available: {', '.join(available_domains()) or 'none'}"
        )
    if domain == "re" and corpus is None:
        from re_domain_pack import REDomainPack

        pack: GenericDomainPack = REDomainPack()
        pack.load()
        return pack

    pack = GenericDomainPack.from_directory(directory)
    if corpus is None:
        raise ValueError(
            f"domain {domain!r} has no in-tree corpus -- pass --corpus with a "
            "directory of JSON documents"
        )
    pack.load(from_directory(corpus))
    return pack


def answer(pack: GenericDomainPack, query: str, *, top_k: int, mode: str | None) -> dict:
    evidence = pack.retrieve(query, top_k=top_k, mode=mode)
    claim = Claim(
        claim_id="C-QUERY",
        statement=query,
        claim_type="answer",
        evidence_ids=[evidence[0].evidence_id] if evidence else ["E-NO-EVIDENCE-FOUND"],
        confidence=round(evidence[0].score, 4) if evidence else 0.0,
    )
    report = pack.claim_verifier.verify([claim], evidence)
    decision = CERGateRuntime().evaluate(
        snapshot=SNAPSHOT, run_id="RUN-QUERY", gate_id=f"{pack.domain_id}-QA",
        claims=[claim], evidence=evidence, verification=report,
    )
    verdict = report.verdicts[0] if report.verdicts else None
    return {
        "domain": pack.domain_id,
        "query": query,
        "corpus": pack.corpus_identity,
        "cer_result": decision.result,
        "findings": list(decision.triggered_findings),
        "grounding": verdict.grounding if verdict else 0.0,
        "unsupported_terms": list(verdict.unsupported_terms) if verdict else [],
        "evidence": [
            {"evidence_id": e.evidence_id, "document_id": e.document_id,
             "revision_id": e.revision_id, "score": e.score, "text": e.text}
            for e in evidence
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domain", help="a directory under domains/")
    parser.add_argument("--corpus", metavar="DIR", help="directory of JSON documents")
    parser.add_argument("--query", help="the question to answer")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--mode", choices=("bm25", "trigram", "hybrid"))
    parser.add_argument("--list", action="store_true", help="list available domains")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name in available_domains():
            policy = DOMAINS_DIR / name / "domain_pack.yaml"
            import yaml

            data = yaml.safe_load(policy.read_text(encoding="utf-8")) or {}
            print(f"{name:12s} {data.get('domain_id', '?'):10s} {data.get('name', '')}")
        return 0

    if not args.domain or not args.query:
        parser.error("--domain and --query are required (or use --list)")

    try:
        pack = build_pack(args.domain, args.corpus)
    except (CorpusError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = answer(pack, args.query, top_k=args.top_k, mode=args.mode)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"[{result['domain']}] {result['query']}")
    print(f"corpus: {result['corpus']['origin']}  ({result['corpus']['documents']} documents)")
    print(f"CER: {result['cer_result']}"
          + (f"   {', '.join(result['findings'])}" if result["findings"] else ""))
    if not result["evidence"]:
        print("\nNo evidence. The corpus does not answer this question.")
        print("How far that refusal can be trusted is recorded in OPEN_DECISIONS D-11.")
        return 0
    if result["unsupported_terms"]:
        # The part of the question the evidence never mentions. Where the
        # threshold cannot decide, this is what puts the gap in front of a
        # reader rather than leaving it implicit in a confident answer.
        print(f"not supported by the evidence: {', '.join(result['unsupported_terms'])}")
    print()
    for item in result["evidence"]:
        print(f"  {item['score']:.3f}  {item['document_id']}/{item['revision_id']}")
        print(f"         {item['text'][:150]}{'...' if len(item['text']) > 150 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
