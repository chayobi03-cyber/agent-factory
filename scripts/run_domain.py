#!/usr/bin/env python3
"""Query any Domain Pack against a local folder of documents.

    python3 scripts/run_domain.py --domain thermal \\
        --corpus /local/thermal-reports \\
        --query "what caused the junction temperature excursion?"

    python3 scripts/run_domain.py --domain re --query "..."      # in-tree corpus
    python3 scripts/run_domain.py --list

Omit `--domain` and the question is routed across every loaded domain instead,
which can answer that none of them covers it:

    python3 scripts/run_domain.py --examples --query "what caused the venting?"

Exit codes: 0 answered, 2 the corpus or domain could not be loaded, 3 no loaded
domain covers the question. 3 is a result, not an error -- a refusal is the
outcome this exists to make possible.

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
from domain_router import Routing, route  # noqa: E402
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


def example_corpus(domain: str) -> Path | None:
    """The invented documents under `domains/<id>/examples`.

    Never a default. They exist so a fresh clone can be *exercised* before
    anyone has documents of their own, and a run against them is not a result
    about anything -- which is why reaching them takes an explicit `--examples`
    and why the corpus origin recorded in every run says where they came from.
    """
    directory = DOMAINS_DIR / domain / "examples"
    return directory if directory.is_dir() else None


def load_all(*, examples: bool = False) -> dict[str, GenericDomainPack]:
    """Every domain that has a corpus to load, for routing across them."""
    packs: dict[str, GenericDomainPack] = {}
    for name in available_domains():
        corpus = None if name == "re" else example_corpus(name)
        if name != "re" and (corpus is None or not examples):
            continue
        try:
            packs[name] = build_pack(name, str(corpus) if corpus else None)
        except (CorpusError, FileNotFoundError, ValueError):
            continue
    return packs


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
    parser.add_argument("--domain", help="a directory under domains/; "
                        "omit to route the question across every loaded domain")
    parser.add_argument("--examples", action="store_true",
                        help="load the invented documents in domains/*/examples "
                             "(for exercising a fresh clone, not for results)")
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

    if not args.query:
        parser.error("--query is required (or use --list)")

    routing: Routing | None = None
    if not args.domain:
        # No domain named: ask the loaded domains which of them the question
        # belongs to. Three answers are possible and only one of them is a
        # domain, so this can exit without retrieving anything.
        packs = load_all(examples=args.examples)
        if not packs:
            print("error: no domain has a corpus to route across; pass --domain "
                  "with --corpus, or --examples to route over the invented "
                  "example documents", file=sys.stderr)
            return 2
        if len(packs) < 2:
            # Routing across one domain is legal and answers only "is this
            # question mine?" -- worth saying, because the interesting answer
            # ("which of these?") needs a second corpus and silence here would
            # read as if one had been given.
            only = next(iter(packs)).upper()
            print(f"note: only {only} has a corpus loaded, so routing can only "
                  f"accept or refuse -- it is not choosing between domains",
                  file=sys.stderr)
        routing = route(packs, args.query)
        if routing.domain is None:
            if args.json:
                print(json.dumps({"query": args.query, "routing": routing.as_dict()},
                                 indent=2, ensure_ascii=False))
            else:
                print(f"no domain: {routing.reason}")
            return 3
        pack = next(p for p in packs.values() if p.domain_id == routing.domain)
    else:
        try:
            pack = build_pack(args.domain, args.corpus)
        except (CorpusError, FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    result = answer(pack, args.query, top_k=args.top_k, mode=args.mode)
    if routing is not None:
        result["routing"] = routing.as_dict()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"[{result['domain']}] {result['query']}")
    if routing is not None:
        print(f"routed: {routing.reason}")
        if routing.requires_human:
            # RouteDecision.requires_human is the kernel's HOTL flag. Answering
            # anyway would hide the fact that two domains were inseparable.
            print("REVIEW: two domains are too close to separate -- a person "
                  "should confirm the domain before this answer is used.")
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
