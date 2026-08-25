"""M1 RE Hybrid RAG Domain Pack.

Implements the interfaces.DomainPack protocol (ingest/parse/normalize/
retrieve/verify/evaluate/render_report) for the RE (Radiated Emission)
engineering domain, per docs/RE_POC.md.

Scope honesty note: this is a first working slice, not the full PoC target
in RE_POC.md (20+ documents, 150 benchmark cases, 3 retrieval methods, 2 LLM
providers). It ships:
  - a small labeled-synthetic document corpus (src/re_corpus.py)
  - a real, deterministic, dependency-free hybrid retriever (lexical BM25
    leg + a character-trigram similarity leg standing in for a semantic/
    vector leg -- no embedding model is downloaded or called)
  - claim/evidence verification wired into the existing CER gate
  - a small benchmark-case set covering most of the RE_POC.md query
    taxonomy (see templates/benchmark/re_hybrid_rag_v0.1.json)
  - a declarative policy file (domains/re/domain_pack.yaml, conforming to
    schemas/domain_pack.schema.yaml) that this module loads and uses for
    ontology-entity tagging and risk thresholds -- cherry-picked from the
    unmerged p0/re-domain-pack-v0.1 branch (see 11_Audit/LSN-0001) rather
    than re-authored, since it already existed and already conforms to the
    canonical schema.

No kernel code (cer_runtime.py, factory_runtime.py) was modified to build
this: it plugs in purely through the DomainPack protocol, satisfying the
RE_POC.md acceptance target "Domain Pack load without kernel modification".
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml

from interfaces import Claim, EvidenceCandidate

from re_corpus import CORPUS, RawDocument

DOMAIN_ID = "RE"
DOMAIN_VERSION = "0.1.0"
POLICY_PATH = Path(__file__).resolve().parents[1] / "domains" / "re" / "domain_pack.yaml"


def load_domain_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    """Load the declarative Domain Pack policy (ontology, terminology,
    verification/risk policy) that conforms to schemas/domain_pack.schema.yaml.
    Returns {} if the file is absent so the pack can still run in a minimal
    (code-only) mode rather than hard-failing -- the declarative policy
    enriches behavior but is not required for the protocol methods to work.
    """
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}

_WORD_RE = re.compile(r"[a-z0-9]+")
_FREQ_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(mhz|ghz|khz)\b", re.IGNORECASE)
_LEVEL_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*dbuv/m\b", re.IGNORECASE)


def _stem(token: str) -> str:
    """Minimal, dependency-free suffix stripping (not a real Porter
    stemmer) so trivial plural/inflection mismatches like 'loop' vs 'loops'
    don't cause literal-token-match false negatives in distinctiveness
    gating or BM25 term counts."""
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _WORD_RE.findall(text.lower())]


def _trigrams(text: str) -> set[str]:
    cleaned = re.sub(r"\s+", " ", text.lower()).strip()
    if len(cleaned) < 3:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + 3] for i in range(len(cleaned) - 2)}


_STOPWORDS = {
    "what", "is", "are", "the", "a", "an", "of", "at", "to", "for", "and",
    "or", "in", "on", "was", "were", "does", "did", "how", "has", "have",
    "had", "with", "this", "that", "it", "its", "as", "be", "by", "from",
    "if", "which", "should", "would", "could", "any",
}
# Domain-generic vocabulary: present in nearly every RE query/document by
# definition of the domain, so it never discriminates *which* document is
# relevant. Excluded from distinctiveness scoring even when its per-fragment
# document frequency happens to fall under the ratio threshold.
_DOMAIN_GENERIC_TERMS = {
    "radiated", "emission", "emissions", "test", "tested", "testing",
    "measurement", "measured", "measure", "device", "dut", "eut",
    "chamber", "performance", "radiated emissions",
}


@dataclass(frozen=True)
class Document:
    document_id: str
    revision_id: str
    title: str
    doc_type: str
    text: str


@dataclass(frozen=True)
class Fragment:
    fragment_id: str
    document_id: str
    revision_id: str
    text: str
    metadata: dict[str, Any]


class REDomainPack:
    """Domain Pack for RE (Radiated Emission) hybrid RAG."""

    domain_id = DOMAIN_ID
    version = DOMAIN_VERSION

    def __init__(self, corpus: Sequence[RawDocument] | None = None, policy: dict[str, Any] | None = None) -> None:
        self._raw_corpus = list(corpus) if corpus is not None else list(CORPUS)
        self._fragments: list[Fragment] = []
        self._doc_freq: Counter[str] = Counter()
        self._avg_fragment_len = 0.0
        self._loaded = False
        self.policy = policy if policy is not None else load_domain_policy()
        ontology = self.policy.get("ontology", {}) if self.policy else {}
        self._ontology_entities: list[str] = list(ontology.get("entities", []))
        risk_thresholds = (self.policy.get("risk_policy", {}) or {}).get("thresholds", {}) if self.policy else {}
        self.risk_thresholds: dict[str, float] = dict(risk_thresholds)

    # -- DomainPack protocol -------------------------------------------------

    def ingest(self, source: Any = None) -> list[Document]:
        raw = source if source is not None else self._raw_corpus
        return [Document(**item) for item in raw]

    def parse(self, artifact: Document) -> list[str]:
        """Split a document into paragraph-level chunks."""
        parts = [p.strip() for p in re.split(r"(?<=[.;])\s+", artifact.text) if p.strip()]
        # Keep paragraphs reasonably sized; merge very short trailing splits.
        merged: list[str] = []
        for part in parts:
            if merged and len(merged[-1]) < 80:
                merged[-1] = merged[-1] + " " + part
            else:
                merged.append(part)
        return merged or [artifact.text]

    def normalize(self, artifact: Document) -> list[Fragment]:
        chunks = self.parse(artifact)
        fragments: list[Fragment] = []
        for idx, chunk in enumerate(chunks):
            metadata: dict[str, Any] = {
                "domain": "RE",
                "doc_type": artifact.doc_type,
                "title": artifact.title,
            }
            freqs = [f"{m.group(1)} {m.group(2).upper()}" for m in _FREQ_RE.finditer(chunk)]
            if freqs:
                metadata["frequencies"] = freqs
            levels = [f"{m.group(1)} dBuV/m" for m in _LEVEL_RE.finditer(chunk)]
            if levels:
                metadata["levels"] = levels
            if self._ontology_entities:
                chunk_lower = chunk.lower()
                mentioned = [
                    entity for entity in self._ontology_entities
                    if entity.replace("_", " ") in chunk_lower or entity in chunk_lower
                ]
                if mentioned:
                    metadata["ontology_entities"] = mentioned
            fragments.append(
                Fragment(
                    fragment_id=f"FRAG-{artifact.document_id}-{artifact.revision_id}-{idx:03d}",
                    document_id=artifact.document_id,
                    revision_id=artifact.revision_id,
                    text=chunk,
                    metadata=metadata,
                )
            )
        return fragments

    def load(self, source: Any = None) -> int:
        """Ingest + parse + normalize the full corpus into the retrieval index."""
        documents = self.ingest(source)
        fragments: list[Fragment] = []
        for document in documents:
            fragments.extend(self.normalize(document))
        self._fragments = fragments
        self._doc_freq = Counter()
        for frag in fragments:
            for term in set(_tokenize(frag.text)):
                self._doc_freq[term] += 1
        lengths = [len(_tokenize(f.text)) for f in fragments] or [0]
        self._avg_fragment_len = sum(lengths) / len(lengths)
        self._loaded = True
        return len(fragments)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _bm25_score(self, query_terms: list[str], fragment: Fragment) -> float:
        """Minimal BM25 (k1=1.5, b=0.75), no external dependency."""
        k1, b = 1.5, 0.75
        n_docs = max(len(self._fragments), 1)
        frag_terms = _tokenize(fragment.text)
        frag_len = len(frag_terms) or 1
        term_counts = Counter(frag_terms)
        score = 0.0
        for term in query_terms:
            df = self._doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            tf = term_counts.get(term, 0)
            if tf == 0:
                continue
            denom = tf + k1 * (1 - b + b * frag_len / max(self._avg_fragment_len, 1))
            score += idf * (tf * (k1 + 1)) / denom
        return score

    def _distinctive_terms(self, query_terms: list[str]) -> list[str]:
        """Query terms that are not stopwords and are not near-ubiquitous in
        the corpus (df > 0 and df <= 30% of fragments). Used to gate
        abstention: a fragment must literally contain enough of these to
        count as a genuine (not merely score-nonzero) match. This is what
        makes retrieve() actually return [] for out-of-corpus questions
        instead of always returning "closest" fragments with a deceptively
        confident-looking normalized score.
        """
        n_fragments = max(len(self._fragments), 1)
        terms = []
        for term in dict.fromkeys(query_terms):  # dedupe, preserve order
            if term in _STOPWORDS or term in _DOMAIN_GENERIC_TERMS:
                continue
            df = self._doc_freq.get(term, 0)
            if 0 < df <= 0.3 * n_fragments:
                terms.append(term)
        return terms

    def retrieve(self, query: str, top_k: int = 5, **kwargs: Any) -> list[EvidenceCandidate]:
        """Hybrid retrieval: normalized BM25 (lexical) + trigram Jaccard
        (lightweight stand-in for a semantic/vector leg), combined 60/40.
        Deterministic and dependency-free by design.

        A candidate must also contain enough "distinctive" query terms
        (see _distinctive_terms) to count as genuine evidence -- otherwise
        retrieve() returns []. Without this, a purely relative (max-
        normalized) score always looks confident for the single closest
        fragment even when the query is genuinely out of corpus, which is
        exactly the failure mode docs/RE_POC.md's "evidence sufficiency /
        abstention" query category exists to catch.
        """
        self._ensure_loaded()
        if not self._fragments:
            return []
        query_terms = _tokenize(query)
        query_trigrams = _trigrams(query)
        distinctive = self._distinctive_terms(query_terms)
        required_hits = min(2, len(distinctive)) if distinctive else 0

        bm25_raw = [self._bm25_score(query_terms, f) for f in self._fragments]
        max_bm25 = max(bm25_raw) or 1.0

        scored: list[tuple[float, Fragment, float, float]] = []
        for frag, bm25 in zip(self._fragments, bm25_raw):
            if required_hits:
                frag_terms = set(_tokenize(frag.text))
                hits = sum(1 for term in distinctive if term in frag_terms)
                if hits < required_hits:
                    continue
            frag_trigrams = _trigrams(frag.text)
            union = query_trigrams | frag_trigrams
            jaccard = len(query_trigrams & frag_trigrams) / len(union) if union else 0.0
            bm25_norm = bm25 / max_bm25
            combined = 0.6 * bm25_norm + 0.4 * jaccard
            scored.append((combined, frag, bm25_norm, jaccard))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[EvidenceCandidate] = []
        for combined, frag, bm25_norm, jaccard in scored[:top_k]:
            if combined <= 0:
                continue
            results.append(
                EvidenceCandidate(
                    evidence_id=f"E-{frag.fragment_id}",
                    document_id=frag.document_id,
                    revision_id=frag.revision_id,
                    fragment_id=frag.fragment_id,
                    score=round(combined, 4),
                    text=frag.text,
                    metadata={**frag.metadata, "bm25": round(bm25_norm, 4), "trigram": round(jaccard, 4)},
                )
            )
        return results

    def verify(
        self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate], **kwargs: Any
    ) -> dict[str, Any]:
        """Lexical grounding check: does the claim statement's vocabulary
        actually overlap with the text of the evidence it cites? This runs
        in addition to (not instead of) the CER gate's own
        evidence-id-exists check.
        """
        evidence_by_id = {e.evidence_id: e for e in evidence}
        per_claim: dict[str, dict[str, Any]] = {}
        for claim in claims:
            cited = [evidence_by_id[eid] for eid in claim.evidence_ids if eid in evidence_by_id]
            claim_terms = set(_tokenize(claim.statement))
            overlap = 0.0
            if cited and claim_terms:
                evidence_terms: set[str] = set()
                for item in cited:
                    evidence_terms |= set(_tokenize(item.text))
                overlap = len(claim_terms & evidence_terms) / len(claim_terms)
            grounded = bool(cited) and overlap >= 0.3
            per_claim[claim.claim_id] = {
                "cited_evidence": [e.evidence_id for e in cited],
                "term_overlap": round(overlap, 4),
                "grounded": grounded,
            }
        return {
            "domain": DOMAIN_ID,
            "claims": per_claim,
            "all_grounded": all(v["grounded"] for v in per_claim.values()) if per_claim else False,
        }

    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        """Score one benchmark case against a produced result.

        Expects `case` to optionally contain `expected_document_ids` and/or
        `expect_abstain`. Computes a simplified Evidence Recall and whether
        abstention behaved as expected -- deliberately not claiming the full
        RE_POC.md metric suite (Citation Accuracy, Critical Claim Unsupported
        Rate, Revision correctness) at this corpus size; those need the full
        150-case benchmark to be statistically meaningful.
        """
        retrieved_docs = {e.document_id for e in result.get("evidence", [])}
        expected_docs = set(case.get("expected_document_ids", []))
        if expected_docs:
            recall = len(retrieved_docs & expected_docs) / len(expected_docs)
        else:
            recall = None

        abstained = result.get("cer_result") == "BLOCK"
        expect_abstain = bool(case.get("expect_abstain", False))
        abstention_correct = abstained == expect_abstain

        return {
            "case_id": case.get("case_id"),
            "query_type": case.get("query_type"),
            "evidence_recall": recall,
            "abstained": abstained,
            "expect_abstain": expect_abstain,
            "abstention_correct": abstention_correct,
            "passed": (recall is None or recall >= case.get("min_recall", 1.0)) and abstention_correct,
        }

    def render_report(self, result: dict[str, Any], **kwargs: Any) -> str:
        lines = [f"# RE Query Report", "", f"**Query:** {result.get('query', '')}", ""]
        lines.append(f"**CER result:** {result.get('cer_result')}")
        lines.append("")
        lines.append("## Evidence")
        for e in result.get("evidence", []):
            lines.append(f"- `{e.evidence_id}` ({e.document_id}/{e.revision_id}, score={e.score}): {e.text}")
        lines.append("")
        lines.append("## Claims")
        for c in result.get("claims", []):
            lines.append(f"- `{c.claim_id}` ({c.claim_type}, confidence={c.confidence}): {c.statement}")
        return "\n".join(lines)
