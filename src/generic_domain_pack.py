"""A Domain Pack assembled from a policy file and a folder of documents.

This is the thing AF-004's acceptance criterion actually asks for -- "kernel
loads Domain Pack without code fork" -- discharged for real rather than by a
fixture. `scripts/domain_matrix_demo.py` proved the protocol *shape* was
domain-agnostic while refusing any spec not marked `fixture_only: true` and
returning a canned candidate from `retrieve`. It could not have caught the fact
that standing up a second domain required copying 783 lines of RE.

    from generic_domain_pack import GenericDomainPack
    pack = GenericDomainPack.from_directory("domains/thermal")
    pack.load(from_directory("/local/thermal-reports"))
    pack.retrieve("what caused the junction temperature excursion?")

No subclass, no new module, no entry in a registry. A new engineering domain is
a `domain_pack.yaml` describing what it measures and what its words mean, plus
documents. Everything mechanical -- tokenizing, indexing, ranking, gating,
abstaining, chunking, scoring, reporting -- is the kernel's and is shared.

`REDomainPack` is now a thin binding over this, keeping its own corpus default
and its own tuned constants. That it can be is the test that the split is real:
if RE needed behaviour this class cannot express, the extraction would have
been cosmetic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from claim_verification import ClaimVerifier
from corpus_source import CorpusSource, from_documents
from domain_retrieval import (
    DEFAULT_STOPWORDS,
    MeasurementTokenizer,
    RetrievalIndex,
    RetrievalThresholds,
    VocabularyProfile,
)
from interfaces import Claim, EvidenceCandidate

#: Weights for the retrieval methods docs/RE_POC.md requires ("3 retrieval
#: methods minimum"), as the share given to BM25 against trigram similarity.
#: `hybrid` is overridden per domain from `retrieval_policy.tuning`.
RETRIEVAL_MODES: dict[str, float] = {"bm25": 1.0, "trigram": 0.0, "hybrid": 0.6}


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

    @property
    def index_text(self) -> str:
        """What retrieval searches, as opposed to what a report quotes.

        The title is the field that answers "which document describes X", and
        searching only bodies cannot see one.
        """
        title = self.metadata.get("title", "")
        return f"{title}. {self.text}" if title else self.text


class GenericDomainPack:
    """Implements the Domain Pack protocol from declarative policy alone."""

    def __init__(
        self,
        policy: Mapping[str, Any],
        *,
        corpus: Sequence[Mapping[str, Any]] | None = None,
        corpus_origin: str = "caller:sequence",
    ) -> None:
        self.policy = dict(policy or {})
        self.domain_id = str(self.policy.get("domain_id", "GENERIC"))
        self.version = str(self.policy.get("version", "0.0.0"))
        self._default_corpus = list(corpus) if corpus is not None else []
        self._corpus_origin = corpus_origin

        measurement = self.policy.get("measurement_policy") or {}
        # What this domain calls the quantity it scales. RE fragments carry
        # `frequencies`; a thermal fragment has none, and calling its watts
        # "frequencies" would be the kernel imposing one domain's vocabulary on
        # every other.
        self._quantity_key = str(measurement.get("quantity_metadata_key", "quantities"))
        self.tokenize = MeasurementTokenizer(
            canonical_unit=str(measurement.get("canonical_unit",
                               measurement.get("canonical_frequency_unit", ""))).lower(),
            unit_multipliers=(measurement.get("unit_multipliers")
                              or measurement.get("frequency_units") or {}),
            level_units=measurement.get("level_units") or (),
            identifier_prefixes=measurement.get("identifier_prefixes") or (),
        )

        terminology = self.policy.get("terminology") or {}
        # A declared list replaces the default; it does not merge with it.
        #
        # A domain that lists its stopwords has made a measured choice, and
        # every threshold calibrated against that domain was fitted under
        # exactly that vocabulary. Merging a kernel default into it silently
        # moves all of them -- which is not hypothetical: doing so here shifted
        # RE's Evidence Recall@10 from 0.914 to 0.921 and its self-answering
        # case count from 11 to 16, quietly invalidating the tables in
        # OPEN_DECISIONS D-10 through D-12 during what was supposed to be a
        # behaviour-preserving refactor.
        #
        # A domain that declares nothing gets the kernel's English function
        # words, which is what lets a policy file with only a name and some
        # units be usable on the day it is written.
        declared = terminology.get("stopwords")
        self.stopwords = frozenset(declared) if declared else DEFAULT_STOPWORDS
        # Vocabulary present in nearly every document of the domain by
        # definition, so it never discriminates *which* document is relevant.
        self.generic_terms = frozenset(terminology.get("generic_terms") or ())
        self._ignore = self.stopwords | self.generic_terms

        self.thresholds = RetrievalThresholds.from_policy(self.policy)
        self.modes = dict(RETRIEVAL_MODES, hybrid=self.thresholds.lexical_weight)

        ontology = self.policy.get("ontology") or {}
        self._ontology_entities: list[str] = list(ontology.get("entities") or [])

        self._index = RetrievalIndex(self.tokenize, ignore_terms=self._ignore,
                                     thresholds=self.thresholds)
        self._fragments: list[Fragment] = []
        self._corpus_source: CorpusSource | None = None
        self._verifier: ClaimVerifier | None = None
        self._loaded = False

    # --- construction --------------------------------------------------------

    @classmethod
    def from_policy_file(cls, path: str | Path, **kwargs: Any) -> "GenericDomainPack":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: domain policy must be a YAML mapping")
        return cls(data, **kwargs)

    @classmethod
    def from_directory(cls, directory: str | Path, **kwargs: Any) -> "GenericDomainPack":
        """`domains/<id>/` holding a `domain_pack.yaml`."""
        root = Path(directory)
        policy = root / "domain_pack.yaml"
        if not policy.exists():
            raise FileNotFoundError(f"{root}: no domain_pack.yaml")
        return cls.from_policy_file(policy, **kwargs)

    # --- protocol ------------------------------------------------------------

    def ingest(self, source: Any = None) -> list[Document]:
        if isinstance(source, CorpusSource):
            self._corpus_source = source
        elif source is not None:
            self._corpus_source = from_documents(source, origin="caller:sequence")
        else:
            self._corpus_source = from_documents(self._default_corpus,
                                                 origin=self._corpus_origin)
        return [Document(**{k: d[k] for k in
                            ("document_id", "revision_id", "title", "doc_type", "text")})
                for d in self._corpus_source.documents]

    @property
    def corpus_identity(self) -> dict[str, Any]:
        self._ensure_loaded()
        return self._corpus_source.identity() if self._corpus_source else {}

    def parse(self, artifact: Document) -> list[str]:
        """Split a document into paragraph-level chunks."""
        parts = [p.strip() for p in re.split(r"(?<=[.;])\s+", artifact.text) if p.strip()]
        merged: list[str] = []
        for part in parts:
            if merged and len(merged[-1]) < 80:
                merged[-1] = merged[-1] + " " + part
            else:
                merged.append(part)
        return merged or [artifact.text]

    def _scaled_quantities(self, text: str) -> list[str]:
        """Quantities in a unit the domain scales, as written."""
        pattern = self.tokenize._scale_re
        if pattern is None:
            return []
        return [f"{m.group(1)} {m.group(2).upper()}" for m in pattern.finditer(text.lower())]

    def _levels(self, text: str) -> list[str]:
        """Quantities in a unit the domain keeps attached rather than scaling."""
        pattern = self.tokenize._level_re
        if pattern is None:
            return []
        return [f"{m.group(1)} {m.group(2)}" for m in pattern.finditer(text.lower())]

    def normalize(self, artifact: Document) -> list[Fragment]:
        fragments: list[Fragment] = []
        for index, chunk in enumerate(self.parse(artifact)):
            metadata: dict[str, Any] = {
                "domain": self.domain_id,
                "doc_type": artifact.doc_type,
                "title": artifact.title,
            }
            # Measurements lifted into fragment metadata so a consumer can read
            # what a fragment quantifies without re-parsing its prose. Driven by
            # the same policy tables the tokenizer is built from, so a domain
            # that declares no units simply gets none of these keys rather than
            # a hardcoded regex for somebody else's domain.
            scaled = self._scaled_quantities(chunk)
            if scaled:
                metadata[self._quantity_key] = scaled
            levels = self._levels(chunk)
            if levels:
                metadata["levels"] = levels
            if self._ontology_entities:
                lowered = chunk.lower()
                mentioned = [e for e in self._ontology_entities
                             if e.replace("_", " ") in lowered or e in lowered]
                if mentioned:
                    metadata["ontology_entities"] = mentioned
            fragments.append(Fragment(
                fragment_id=f"FRAG-{artifact.document_id}-{artifact.revision_id}-{index:03d}",
                document_id=artifact.document_id,
                revision_id=artifact.revision_id,
                text=chunk,
                metadata=metadata,
            ))
        return fragments

    def load(self, source: Any = None) -> int:
        fragments: list[Fragment] = []
        for document in self.ingest(source):
            fragments.extend(self.normalize(document))
        self._fragments = fragments
        self._index.build([f.index_text for f in fragments])
        self._loaded = True
        return len(fragments)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def vocabulary_profile(self, query: str) -> VocabularyProfile:
        """How much this domain's corpus knows about a question.

        This is the whole surface `domain_router` needs, and it exists so the
        router does not reach into an index it should not know the shape of.
        Anything answering to `domain_id` and this method can be routed,
        including a pack that is not a `GenericDomainPack` at all.
        """
        self._ensure_loaded()
        return self._index.profile(self.tokenize(query))

    @property
    def default_retrieval_mode(self) -> str:
        declared = str(((self.policy.get("retrieval_policy") or {})
                        .get("default_mode", "hybrid"))).lower()
        return declared if declared in self.modes else "hybrid"

    def retrieve(self, query: str, top_k: int = 5, *, mode: str | None = None,
                 **kwargs: Any) -> list[EvidenceCandidate]:
        resolved = (mode or self.default_retrieval_mode).lower()
        if resolved not in self.modes:
            raise ValueError(
                f"unknown retrieval mode {resolved!r}; implemented: {sorted(self.modes)}"
            )
        self._ensure_loaded()
        ranked = self._index.rank(
            query, top_k=top_k, lexical_weight=self.modes[resolved],
            is_specifier=self.tokenize.is_specifier,
        )
        results: list[EvidenceCandidate] = []
        for index, combined, bm25, jaccard in ranked:
            fragment = self._fragments[index]
            results.append(EvidenceCandidate(
                evidence_id=f"E-{fragment.fragment_id}",
                document_id=fragment.document_id,
                revision_id=fragment.revision_id,
                fragment_id=fragment.fragment_id,
                score=round(combined, 4),
                text=fragment.text,
                metadata={**fragment.metadata, "retrieval_mode": resolved,
                          "bm25": round(bm25, 4), "trigram": round(jaccard, 4)},
            ))
        return results

    @property
    def claim_verifier(self) -> ClaimVerifier:
        if self._verifier is None:
            policy = self.policy.get("verification_policy") or {}
            self._verifier = ClaimVerifier(
                self.tokenize,
                grounding_floor=float(policy.get("claim_grounding_floor", 0.25)),
                ignore_terms=self._ignore,
            )
        return self._verifier

    def build_claim(self, query: str, evidence: Sequence[EvidenceCandidate],
                    *, claim_id: str = "C-QUERY") -> Claim:
        """The claim a query plus its evidence amounts to.

        One definition, in the kernel. `re_demo.py` and `run_domain.py` each
        built this themselves and each cited `evidence[0]` alone; the same
        definition living in two places is the pattern this repository has now
        hit four times, and it is how the two of them could have drifted apart
        without anything noticing.

        `confidence` is the IDF-weighted share of the question that the cited
        evidence accounts for, not the retrieval score. The score cannot serve:
        `rank` normalizes BM25 against each query's own maximum, so the top
        fragment's lexical component is always exactly 1.0 and the number sits
        near 0.69 whatever the match is worth. Measured over 127 answerable
        benchmark cases it separates a correct top hit from a wrong one by
        d=0.40; coverage separates the same cases by d=0.87, is bounded in
        [0, 1], and means something a reader can act on -- how much of what was
        asked the evidence speaks to.
        """
        self._ensure_loaded()
        cited = self.claim_verifier.select_citations(query, evidence)
        if not cited:
            return Claim(claim_id=claim_id, statement=query, claim_type="answer",
                         evidence_ids=["E-NO-EVIDENCE-FOUND"], confidence=0.0)
        return Claim(
            claim_id=claim_id, statement=query, claim_type="answer",
            evidence_ids=[item.evidence_id for item in cited],
            confidence=round(self.evidence_coverage(query, cited), 4),
        )

    def evidence_coverage(self, query: str, evidence: Sequence[EvidenceCandidate]) -> float:
        """How much of a question's informative weight these fragments carry.

        IDF-weighted, so a fragment matching `EUT-12` counts for more than one
        matching `measured`, and bounded in [0, 1] so it is comparable between
        one query and the next -- which the retrieval score is not.
        """
        weights = self._index.query_weights(self.tokenize(query))
        if not weights:
            return 0.0
        supplied: set[str] = set()
        for item in evidence:
            supplied |= self.claim_verifier._supplied(item)
        return self._index.coverage(weights, supplied)

    def verify(self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate],
               **kwargs: Any) -> dict[str, Any]:
        report = self.claim_verifier.verify(claims, evidence)
        return {"domain": self.domain_id, **report.as_dict()}

    def query_is_verbatim_in_its_answer(self, case: Mapping[str, Any]) -> bool:
        """Is every informative term of this query already in the document the
        benchmark expects back? Such a case cannot really fail and inflates
        recall; measured from the corpus rather than hand-labelled, because a
        hand-labelled flag drifts the first time a document is edited."""
        self._ensure_loaded()
        expected = set(case.get("expected_document_ids") or [])
        if not expected:
            return False
        terms = [t for t in dict.fromkeys(self.tokenize(case.get("query", "")))
                 if t not in self._ignore]
        if not terms:
            return False
        available: set[str] = set()
        for document in self.ingest():
            if document.document_id in expected:
                available |= set(self.tokenize(f"{document.title} {document.text}"))
        return all(t in available for t in terms)

    def evaluate(self, case: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
        evidence = list(result.get("evidence", []))
        retrieved = {e.document_id for e in evidence}
        expected = set(case.get("expected_document_ids") or [])
        recall = len(retrieved & expected) / len(expected) if expected else None
        first_rank = next(
            (i + 1 for i, e in enumerate(evidence) if e.document_id in expected), None
        )
        abstained = result.get("cer_result") == "BLOCK"
        expect_abstain = bool(case.get("expect_abstain", False))
        return {
            "case_id": case.get("case_id"),
            "query_type": case.get("query_type"),
            "evidence_recall": recall,
            "first_relevant_rank": first_rank,
            "abstained": abstained,
            "expect_abstain": expect_abstain,
            "abstention_correct": abstained == expect_abstain,
            "passed": (recall is None or recall >= case.get("min_recall", 1.0))
                      and abstained == expect_abstain,
        }

    def render_report(self, result: Mapping[str, Any], **kwargs: Any) -> str:
        lines = [f"# {self.domain_id} Query Report", "",
                 f"**Query:** {result.get('query', '')}", "",
                 f"**CER result:** {result.get('cer_result')}", "", "## Evidence"]
        for item in result.get("evidence", []):
            lines.append(f"- `{item.evidence_id}` ({item.document_id}/{item.revision_id}, "
                         f"score={item.score}): {item.text}")
        lines += ["", "## Claims"]
        for claim in result.get("claims", []):
            lines.append(f"- `{claim.claim_id}` ({claim.claim_type}): {claim.statement}")
        return "\n".join(lines)
