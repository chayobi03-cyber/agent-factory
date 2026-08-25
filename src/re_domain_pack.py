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
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

import yaml

from claim_verification import ClaimVerifier
from corpus_source import CorpusSource, from_documents
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

# --- measurement-aware tokenization ------------------------------------------
#
# The RE domain's content *is* numbers with units. A bare `[a-z0-9]+` tokenizer
# shatters every one of them: "5.8 GHz" becomes ['5','8','ghz'], which is
# indistinguishable from "8.5 GHz", and "REV-A" becomes ['rev','a']. normalize()
# below already lifts frequencies and levels into fragment metadata, so the pack
# knew these mattered -- retrieval simply could not see them.
#
# The unit tables are mirrored declaratively in domains/re/domain_pack.yaml
# under `measurement_policy`; tests/test_re_domain_pack.py asserts the two agree,
# the same code<->YAML consistency check used for the ontology.

# Multiplier to the canonical frequency unit (MHz), so "5.8 GHz" and "5800 MHz"
# produce the same token instead of sharing nothing.
_FREQ_TO_MHZ = {"hz": Decimal("0.000001"), "khz": Decimal("0.001"),
                "mhz": Decimal(1), "ghz": Decimal(1000)}
_LEVEL_UNITS = ("dbuv/m", "dbuv", "dbm", "dbi", "db")
_ID_PREFIXES = ("rev", "eut", "dut", "doc", "ch", "ant", "cispr", "en", "fcc")

_MEAS_FREQ_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(" + "|".join(_FREQ_TO_MHZ) + r")(?![\w])")
_MEAS_LEVEL_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(" + "|".join(_LEVEL_UNITS) + r")(?![\w])")
_IDENT_RE = re.compile(
    r"(?<![\w-])((?:" + "|".join(_ID_PREFIXES) + r")(?:-[a-z0-9]+)+)(?![\w-])")
_DECIMAL_RE = re.compile(r"(?<![\w.])(\d+\.\d+)(?![\w.])")


def _is_specifier(token: str) -> str | bool:
    """True for the high-specificity composite tokens _tokenize emits: a
    normalized frequency, a level with its unit, or a hyphenated identifier
    like REV-B or EUT-7.

    These name a particular thing rather than describe one. A query naming a
    specifier the corpus has never seen is asking about something that is not
    there -- which is evidence of absence, not merely a weak match.
    """
    if token.startswith("f:"):
        return True
    if "-" in token and token.split("-", 1)[0] in _ID_PREFIXES:
        return True
    return any(token.endswith(unit) and any(c.isdigit() for c in token)
               for unit in _LEVEL_UNITS)


def _canonical_number(raw: str) -> str:
    """Render a Decimal without exponent or trailing-zero noise, so 5.8 GHz and
    5800 MHz agree on `5800` rather than differing by float representation."""
    value = Decimal(raw).normalize()
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


# Minimum length a stem may be reduced to. Below this, suffix stripping starts
# merging unrelated words ("used" -> "us"), which costs more than the inflection
# match it buys.
_MIN_STEM = 4


def _stem(token: str) -> str:
    """Minimal, dependency-free suffix stripping (not a real Porter stemmer).

    Handles plurals, past tense, gerunds, and the trailing silent `e`, so that
    'route', 'routed' and 'routing' reach the same stem. Inflection alone used
    to make a query term look absent from the corpus: "how far should a harness
    be routed" scored `routed` as unseen against a guideline whose text says
    "route harnesses away from enclosure seams". Under IDF weighting an unseen
    term takes the maximum weight, so a stemming miss did not merely fail to
    match -- it actively dominated the query and pushed the right document out.
    """
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    if len(token) - 3 >= _MIN_STEM and token.endswith("ing"):
        token = token[:-3]
    elif len(token) - 2 >= _MIN_STEM and token.endswith("ed"):
        token = token[:-2]
    # 'route' -> 'rout' so it meets 'routed' -> 'rout'. Guarded by _MIN_STEM and
    # by requiring a consonant before the e, so 'free' and 'see' survive.
    if len(token) - 1 >= _MIN_STEM and token.endswith("e") and token[-2] not in "aeiou":
        token = token[:-1]
    return token


def _tokenize(text: str) -> list[str]:
    """Measurement-aware tokenization.

    Emits composite tokens for the things an RE question is actually about --
    frequencies (normalized to MHz), field-strength levels, and hyphenated
    identifiers like REV-B or EUT-7 -- and masks each matched span so its digits
    do not also leak out as bare numbers that collide with everything.
    Ordinary prose still tokenizes exactly as before.
    """
    lowered = text.lower().replace("\u00b5", "u").replace("\u03bc", "u")
    tokens: list[str] = []

    def _consume(pattern: re.Pattern[str], make: Any) -> None:
        nonlocal lowered
        pieces: list[str] = []
        last = 0
        for match in pattern.finditer(lowered):
            token = make(match)
            if token is None:
                continue
            tokens.append(token)
            pieces.append(lowered[last : match.start()])
            last = match.end()
        if pieces:
            pieces.append(lowered[last:])
            lowered = " ".join(pieces)

    _consume(_MEAS_FREQ_RE, lambda m: "f:" + _canonical_number(
        str(Decimal(m.group(1)) * _FREQ_TO_MHZ[m.group(2)])) + "mhz")
    _consume(_MEAS_LEVEL_RE, lambda m: _canonical_number(m.group(1)) + m.group(2))
    _consume(_IDENT_RE, lambda m: m.group(1))
    _consume(_DECIMAL_RE, lambda m: _canonical_number(m.group(1)))

    tokens.extend(_stem(t) for t in _WORD_RE.findall(lowered))
    return tokens


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
# Minimum share of a question's informational weight a fragment must carry to
# count as a genuine match rather than an incidental word overlap.
#
# The weight is IDF mass, not a term count, which is the whole point: a raw
# count moves whenever the corpus does, and that is what made the previous
# threshold corpus-dependent (OPEN_DECISIONS D-10). Under IDF mass the same
# question scores smoothly across corpus shapes instead of falling off a cliff
# -- RE-BC-002 ranges 0.163..0.294 over baseline, four distractor volumes, and
# ten term-saturation shapes.
#
# What the value is chosen against, measured over those fifteen shapes:
#
#   floor  benchmark on baseline  outcome stable  candidates per answerable
#                                 across shapes   query at 250 distractors
#   0.00   all pass               yes             50.0 (the top_k cap)
#   0.08   all pass               yes             19.1
#   0.12   all pass               yes             13.6   <- shipped
#   0.16   all pass               yes              8.7
#   0.18   all pass               no  (RE-BC-002)  7.4
#   0.20   RE-BC-002 fails        no  (RE-BC-002)  7.2
#
# Correctness and stability alone do not pin this down -- they hold at 0.00,
# because abstention is decided separately by _UNSEEN_TERM_CEILING below and
# does not depend on this floor at all. So the floor is doing one job here,
# precision, and it wants to be as high as it can safely go. The ceiling is
# RE-BC-002's 0.163: that case carries only ~19% of its query's weight on the
# right answer, so it is the case that binds. 0.12 keeps roughly a quarter of
# that minimum as margin while cutting returned candidates by a factor of ~3.7
# against no floor; 0.16 is better on precision but sits inside the noise of a
# minimum observed from only fifteen shapes.
#
# Honest limitation: 0.12 is fitted to a 35-fragment corpus, and its upper edge
# is set by a single marginal case. Both will move as the corpus grows.
# Re-derive it with the same sweep at PoC scale rather than carrying this value
# forward on faith -- tests/test_re_retrieval_stability.py is the harness.
_COVERAGE_FLOOR = 0.12

# Share of a question's informative terms that may be absent from the corpus
# before the question is treated as unanswerable.
#
# Abstention and match-gating are different questions and one threshold cannot
# serve both: a floor low enough to admit a legitimate query phrased in common
# words is also low enough to admit a query about something absent. Weighing
# absence separately is what lets the coverage floor stay permissive.
#
# Counted, not IDF-weighted. The first version of this rule weighted absent
# terms by IDF, which is unsound: IDF measures rarity *within* the corpus, and
# a term the corpus has never seen has no measured rarity. Giving it
# log(N+1) -- the maximum -- fabricates a weight, and the fabrication is not
# neutral: it makes absent words dominate every query they appear in. At 108
# fragments that inverted the two classes outright, scoring answerable
# questions (0.28..0.75) *above* unanswerable ones (0.28 low end). Counting
# each absent term once says only what the corpus can actually support: it
# knows the term is absent and nothing about how much that matters.
#
# Removing the fabricated weight also removed the need for the hand-curated
# list of question-form words that the previous version carried. That list was
# the most-fitted part of the D-10 resolution -- assembled by inspecting which
# of 15 queries were misclassified -- and deleting it costs nothing measurable:
# with it, Recall@10 0.935 / abstention 0.700; without it, identical to three
# decimal places.
#
# 0.35 is the largest value at which the two *decidable* abstention classes
# stay perfect. Swept against the 159-case benchmark at 108 fragments:
#
#   ceiling  Recall@10   abstention   subject absent   near-miss
#                                     (bands 1-2)      (band 3)
#     0.20     0.770        0.850        12/12           5/8
#     0.30     0.878        0.750        12/12           3/8
#     0.35     0.914        0.750        12/12           3/8   <- shipped
#     0.40     0.935        0.650        11/12           2/8
#     0.50     0.964        0.550         9/12           2/8
#
# Above 0.35 the rule starts missing questions about subjects the corpus
# plainly does not contain -- the class it exists to catch and the only class
# it decides reliably -- so that is where it stops, and 0.914 clears the
# Recall@10 >= 0.90 acceptance target with margin. Band 3 (near-miss: a real
# RE subject this corpus happens not to cover) is not decidable by any
# threshold on this statistic; 3/8 against 2/8 is noise, not signal. Raised as
# OPEN_DECISIONS D-11 rather than tuned around.
_UNSEEN_TERM_CEILING = 0.35

# Fallback for the claim-grounding floor when domain_pack.yaml is absent (the
# code-only minimal mode load_domain_policy supports). The policy file is the
# source of truth; tests assert the two agree.
_CLAIM_GROUNDING_FLOOR = 0.25

# The three retrieval methods docs/RE_POC.md requires ("3 retrieval methods
# minimum"), as the lexical weight each gives BM25 against character-trigram
# Jaccard. Measured over the 159-case benchmark at 108 fragments:
#
#   method             R@1     R@3    R@10     MRR
#   trigram only      0.799   0.885   0.914   0.842
#   hybrid 40/60      0.835   0.906   0.914   0.871
#   hybrid 60/40      0.827   0.906   0.914   0.868   <- what was shipped
#   BM25 only         0.827   0.906   0.914   0.868
#
# Three things that table says and the previous code assumed the opposite of:
#
# 1. **Recall@10 cannot tell these methods apart.** Every weight from pure
#    trigram to pure BM25 scores exactly 0.914, because the coverage floor and
#    the abstention rules decide the result set and ranking rarely moves a
#    document across k=10. The PoC's headline metric is insensitive to the
#    thing RE_POC asks for three of, which is why the demo now also reports
#    R@1, R@3 and MRR.
# 2. **At 60/40 the hybrid was BM25 with a decorative trigram term** -- same
#    R@1, same MRR, to three decimals.
# 3. Trigram alone is genuinely worse (MRR 0.842), so the leg is not useless;
#    it is just outvoted at the weight that was chosen.
#
# `hybrid` stays 0.6 rather than moving to the 0.4 that measured best: the
# difference is 0.835 against 0.827 over 139 answerable cases, which is one
# case, and refitting a shipped default to a one-case gain on the corpus it
# was measured against is how the D-10 thresholds became corpus-dependent.
# Changing it wants a corpus this result survives, not this corpus.
RETRIEVAL_MODES: dict[str, float] = {
    "bm25": 1.0,
    "trigram": 0.0,
    "hybrid": 0.6,
}

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

    @property
    def index_text(self) -> str:
        """What retrieval searches, as opposed to what a report quotes.

        `text` is the body chunk and stays quotable verbatim. The document
        title is not in it, and the title is exactly the field that answers
        RE_POC.md's `document_location` category -- "which document describes
        X" is answered by a title, and searching only bodies cannot see one.
        Titles were carried in metadata and never indexed, so a fragment of
        the fully-anechoic chamber record was unreachable by the words in its
        own heading.
        """
        title = self.metadata.get("title", "")
        return f"{title}. {self.text}" if title else self.text


class REDomainPack:
    """Domain Pack for RE (Radiated Emission) hybrid RAG."""

    domain_id = DOMAIN_ID
    version = DOMAIN_VERSION

    def __init__(self, corpus: Sequence[RawDocument] | None = None, policy: dict[str, Any] | None = None) -> None:
        self._raw_corpus = list(corpus) if corpus is not None else list(CORPUS)
        self._fragments: list[Fragment] = []
        self._frag_terms: list[list[str]] = []
        self._frag_term_sets: list[set[str]] = []
        self._frag_term_counts: list[Counter[str]] = []
        self._frag_trigrams: list[set[str]] = []
        self._verifier: ClaimVerifier | None = None
        self._corpus_source: CorpusSource | None = None
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
        """Accepts a CorpusSource, a raw document sequence, or nothing.

        A CorpusSource carries an origin and a content digest, which is what
        lets a run say *which* corpus produced its numbers -- necessary once
        the documents can live outside the repository (OPEN_DECISIONS D-08).
        A bare sequence is still accepted and gets wrapped, so nothing that
        passed a list before has to change.
        """
        if isinstance(source, CorpusSource):
            self._corpus_source = source
        elif source is not None:
            self._corpus_source = from_documents(source, origin="caller:sequence")
        else:
            self._corpus_source = from_documents(self._raw_corpus)
        return [Document(**item) for item in self._corpus_source.documents]

    @property
    def corpus_identity(self) -> dict[str, Any]:
        """Origin, digest and size of the corpus currently loaded."""
        self._ensure_loaded()
        return self._corpus_source.identity() if self._corpus_source else {}

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
        # Tokenize each fragment exactly once, at load. Retrieval reads these
        # for every query, and re-tokenizing 108 fragments per query made the
        # threshold sweeps in tests/test_re_retrieval_stability.py the slowest
        # thing in the suite.
        self._frag_terms = [_tokenize(f.index_text) for f in fragments]
        self._frag_term_sets = [set(terms) for terms in self._frag_terms]
        self._frag_term_counts = [Counter(terms) for terms in self._frag_terms]
        self._frag_trigrams = [_trigrams(f.index_text) for f in fragments]
        self._doc_freq = Counter()
        for terms in self._frag_term_sets:
            for term in terms:
                self._doc_freq[term] += 1
        lengths = [len(terms) for terms in self._frag_terms] or [0]
        self._avg_fragment_len = sum(lengths) / len(lengths)
        self._loaded = True
        return len(fragments)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _bm25_score(self, query_terms: list[str], index: int) -> float:
        """Minimal BM25 (k1=1.5, b=0.75), no external dependency."""
        k1, b = 1.5, 0.75
        n_docs = max(len(self._fragments), 1)
        frag_len = len(self._frag_terms[index]) or 1
        term_counts = self._frag_term_counts[index]
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

    def _term_idf(self, term: str) -> float:
        """Smoothed inverse document frequency, continuous in df.

        A term becoming more common lowers its weight gradually instead of
        removing it from consideration at a threshold, which is what made
        retrieval depend on corpus composition (OPEN_DECISIONS D-10).
        """
        n_fragments = max(len(self._fragments), 1)
        return math.log((n_fragments + 1) / (self._doc_freq.get(term, 0) + 1))

    def _query_weights(self, query_terms: list[str]) -> dict[str, float]:
        """How much of the question each term carries."""
        return {
            term: self._term_idf(term)
            for term in dict.fromkeys(query_terms)
            if term not in _STOPWORDS and term not in _DOMAIN_GENERIC_TERMS
        }

    def _coverage(self, weights: dict[str, float], fragment_terms: set[str]) -> float:
        """Fraction of the question's informational weight this fragment carries.

        Replaces the previous gate, which admitted query terms whose document
        frequency fell under a fixed fraction of the corpus and then required a
        literal count of them. Both the membership of that set and the required
        count moved as unrelated documents were added, so the same query against
        the same document could pass, fail, then pass again -- see
        OPEN_DECISIONS D-10 and tests/test_re_retrieval_stability.py.
        """
        total = sum(weights.values())
        if total <= 0:
            return 0.0
        return sum(w for term, w in weights.items() if term in fragment_terms) / total

    def retrieve(
        self, query: str, top_k: int = 5, *, mode: str | None = None, **kwargs: Any
    ) -> list[EvidenceCandidate]:
        """Retrieve evidence, ranked by the selected method.

        `mode` is one of RETRIEVAL_MODES: `bm25` (lexical only), `trigram`
        (character-trigram Jaccard only), or `hybrid` (a weighted blend).
        Defaults to `retrieval_policy.default_mode` in the Domain Pack. All
        three are deterministic and dependency-free.

        Three selectable methods exist because docs/RE_POC.md requires at
        least three and because the blend weight had never been measured --
        it was asserted at 60/40. Measured over the 159-case benchmark, at
        that weight the hybrid is *indistinguishable from BM25 alone*
        (R@1 0.827, MRR 0.868 for both): the trigram leg earns nothing there.
        The table at RETRIEVAL_MODES records what each method is actually
        worth.

        Ranking is only half of it. Before anything is ranked, two rules can
        return [] outright:

        - a query naming a *specifier* -- a measurement or an identifier --
          that the corpus has never seen (`_is_specifier`);
        - a query too much of whose informative vocabulary is absent
          (`_UNSEEN_TERM_CEILING`).

        Then a fragment must cover at least `_COVERAGE_FLOOR` of the query's
        IDF mass to be a candidate at all. Without those, a max-normalized
        score always looks confident for the single closest fragment even when
        the question is genuinely out of corpus -- the failure mode
        docs/RE_POC.md's "evidence sufficiency / abstention" category exists to
        catch.

        This paragraph used to describe a `_distinctive_terms` gate: query
        terms with df in (0, 30%] of fragments, of which a fragment had to
        contain a literal minimum. That gate *was* OPEN_DECISIONS D-10 -- its
        membership and its required-hit count both moved with the corpus -- and
        it was replaced by the coverage floor above. The method outlived its
        last caller and this docstring went on describing it, so anyone reading
        the entry point was told the wrong mechanism.
        """
        # Resolved before anything else, including the early returns below. An
        # unimplemented mode must raise on every call, not only on calls that
        # happen to reach the ranking loop -- `retrieve(q, mode="vector")`
        # returning [] for an out-of-corpus query reads as "vector retrieval
        # found nothing", which is the opposite of the truth.
        resolved = (mode or self.default_retrieval_mode).lower()
        if resolved not in RETRIEVAL_MODES:
            raise ValueError(
                f"unknown retrieval mode {resolved!r}; "
                f"domain_pack.yaml declares {sorted(RETRIEVAL_MODES)} as implemented"
            )
        lexical_weight = RETRIEVAL_MODES[resolved]

        self._ensure_loaded()
        if not self._fragments:
            return []
        query_terms = _tokenize(query)

        # Evidence of absence, stated as its own rule rather than left to fall
        # out of a scoring gate. Before measurement-aware tokenization this was
        # masked: "5.8 GHz" shattered into '5' and '8', which did occur in the
        # corpus, so an out-of-corpus question gated by accident. With the
        # frequency preserved as one token the accident disappears -- if the
        # query names a specifier the corpus has never seen, abstain.
        if any(_is_specifier(t) and self._doc_freq.get(t, 0) == 0
               for t in dict.fromkeys(query_terms)):
            return []

        # The same principle, generalised past specifiers. "Lunar regolith
        # shielding thickness for radiated emissions" names nothing this corpus
        # contains, but `lunar` and `regolith` are ordinary rare words rather
        # than identifiers or measurements. Weighted by IDF they carry most of
        # the question, and a question mostly about absent things has no answer
        # here -- however well its remaining words happen to match.
        informative = [t for t in dict.fromkeys(query_terms)
                       if t not in _STOPWORDS and t not in _DOMAIN_GENERIC_TERMS]
        if informative:
            unseen = sum(1 for t in informative if self._doc_freq.get(t, 0) == 0)
            if unseen / len(informative) > _UNSEEN_TERM_CEILING:
                return []

        query_trigrams = _trigrams(query)
        weights = self._query_weights(query_terms)

        bm25_raw = [self._bm25_score(query_terms, i) for i in range(len(self._fragments))]
        max_bm25 = max(bm25_raw) or 1.0

        scored: list[tuple[float, Fragment, float, float]] = []
        for index, (frag, bm25) in enumerate(zip(self._fragments, bm25_raw)):
            if weights:
                if self._coverage(weights, self._frag_term_sets[index]) < _COVERAGE_FLOOR:
                    continue
            frag_trigrams = self._frag_trigrams[index]
            union = query_trigrams | frag_trigrams
            jaccard = len(query_trigrams & frag_trigrams) / len(union) if union else 0.0
            bm25_norm = bm25 / max_bm25
            combined = lexical_weight * bm25_norm + (1.0 - lexical_weight) * jaccard
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
                    metadata={**frag.metadata, "retrieval_mode": resolved,
                              "bm25": round(bm25_norm, 4), "trigram": round(jaccard, 4)},
                )
            )
        return results

    @property
    def default_retrieval_mode(self) -> str:
        """From `retrieval_policy.default_mode`, if the Domain Pack declares an
        implemented one. The policy also lists `vector`, `graph` and `agentic`
        in `allowed_modes` and names a `cross_encoder` reranker; none of those
        exists, and selecting one raises rather than silently falling back to
        the hybrid -- a mode that resolves to something other than what was
        asked for is how a declared capability gets believed. See
        OPEN_DECISIONS D-12.
        """
        policy = (self.policy.get("retrieval_policy", {}) or {}) if self.policy else {}
        declared = str(policy.get("default_mode", "hybrid")).lower()
        return declared if declared in RETRIEVAL_MODES else "hybrid"

    @property
    def claim_verifier(self) -> ClaimVerifier:
        """The kernel's verifier, bound to this domain's tokenizer and floor.

        The mechanism is domain-agnostic and lives in src/claim_verification.py;
        what RE contributes is how its text tokenizes (measurements, unit-
        bearing levels, hyphenated identifiers) and what share of a claim its
        evidence must supply. Any Domain Pack binds the same class the same way.
        """
        if self._verifier is None:
            policy = (self.policy.get("verification_policy", {}) or {}) if self.policy else {}
            self._verifier = ClaimVerifier(
                _tokenize,
                grounding_floor=float(policy.get("claim_grounding_floor", _CLAIM_GROUNDING_FLOOR)),
                ignore_terms=_STOPWORDS | _DOMAIN_GENERIC_TERMS,
            )
        return self._verifier

    def verify(
        self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate], **kwargs: Any
    ) -> dict[str, Any]:
        """Does the cited evidence support the claim, or merely exist?

        Delegates to the kernel verifier. Previously this computed a term
        overlap and returned it, and nothing consumed the result -- the CER
        gate decided on evidence-id existence alone, so a claim citing evidence
        with almost no relationship to it still reached PASS. The verdict now
        travels into the gate; see CERGateRuntime.evaluate.
        """
        report = self.claim_verifier.verify(claims, evidence)
        return {"domain": DOMAIN_ID, **report.as_dict()}

    def query_is_verbatim_in_its_answer(self, case: dict[str, Any]) -> bool:
        """Is every informative term of this query already present, word for
        word, in the document the benchmark expects back?

        Such a case is close to a lookup by copy: retrieval cannot really fail
        it, and it inflates recall without demonstrating anything. Measured
        rather than hand-labelled, because a hand-labelled "this one is easy"
        flag drifts the moment a document is edited and nobody re-checks.

        11 of the 139 answerable cases qualify. They pass at 100%, against
        0.906 for the other 128 -- so the headline Evidence Recall@10 of 0.914
        is 0.008 higher than what the retriever earns on questions that are
        not restatements of their own answer. Both numbers are reported.
        """
        self._ensure_loaded()
        expected = set(case.get("expected_document_ids") or [])
        if not expected:
            return False
        terms = [t for t in dict.fromkeys(_tokenize(case.get("query", "")))
                 if t not in _STOPWORDS and t not in _DOMAIN_GENERIC_TERMS]
        if not terms:
            return False
        available: set[str] = set()
        for document in self.ingest():
            if document.document_id in expected:
                available |= set(_tokenize(f"{document.title} {document.text}"))
        return all(t in available for t in terms)

    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        """Score one benchmark case against a produced result.

        Expects `case` to optionally contain `expected_document_ids` and/or
        `expect_abstain`. Computes a simplified Evidence Recall and whether
        abstention behaved as expected -- deliberately not claiming the full
        RE_POC.md metric suite (Citation Accuracy, Critical Claim Unsupported
        Rate, Revision correctness) at this corpus size; those need the full
        150-case benchmark to be statistically meaningful.
        """
        evidence = list(result.get("evidence", []))
        retrieved_docs = {e.document_id for e in evidence}
        expected_docs = set(case.get("expected_document_ids", []))
        if expected_docs:
            recall = len(retrieved_docs & expected_docs) / len(expected_docs)
        else:
            recall = None
        # 1-based rank of the first correct document, or None. Recall alone is
        # blind to ordering, and ordering is the only thing that separates the
        # retrieval methods -- see RETRIEVAL_MODES.
        first_rank = next(
            (i + 1 for i, e in enumerate(evidence) if e.document_id in expected_docs), None
        )

        abstained = result.get("cer_result") == "BLOCK"
        expect_abstain = bool(case.get("expect_abstain", False))
        abstention_correct = abstained == expect_abstain

        return {
            "case_id": case.get("case_id"),
            "query_type": case.get("query_type"),
            "evidence_recall": recall,
            "first_relevant_rank": first_rank,
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
