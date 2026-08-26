"""Retrieval, built from a Domain Pack's policy rather than written per domain.

ARCHITECTURE_REFACTOR_PLAN goal 2 is "keep engineering-domain behavior behind
Domain Packs", and AF-004's acceptance criterion is that the kernel loads a
Domain Pack *without a code fork*. Until now only half of that held: the
domain-specific parts of RE lived in `src/re_domain_pack.py`, but so did every
generic part -- BM25, trigram similarity, IDF gating, abstention, chunking,
indexing. A second domain could not be stood up without copying 783 lines,
which is the code fork the criterion forbids. `scripts/domain_matrix_demo.py`
did not catch this: it is fixture-only by construction, refusing any spec not
marked `fixture_only: true` and returning a canned candidate from `retrieve`,
so it proves the *protocol shape* is domain-agnostic and nothing about
retrieval.

What is genuinely domain-specific turns out to be small, and was already
declared in YAML: which units the domain measures in, which prefixes name its
identifiers, which words are so common in it that they discriminate nothing,
and four tuned thresholds. All of that is data. The mechanism is not.

So a new domain is a `domain_pack.yaml` and a folder of documents. No Python.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

#: Ordinary English function words, supplied by the kernel to every domain.
#:
#: These are not domain knowledge. "the", "is" and "which" mean the same thing
#: in a thermal report and a radiated-emission one, and requiring each domain to
#: re-type them is friction that buys nothing -- worse, a domain that forgets
#: gets an unusable retriever, because every ordinary word then counts as
#: informative and a short corpus trips the absence rule on every query.
#:
#: What a domain *must* declare is its own generic vocabulary -- the words so
#: common in that field that they never discriminate between its documents
#: ("radiated", "emission" for RE; "thermal", "temperature" for heat). Those are
#: genuinely domain knowledge and the kernel cannot guess them.
DEFAULT_STOPWORDS = frozenset("""
what is are the a an of at to for and or in on was were does did how has have
had with this that it its as be by from if which should would could any who
whom whose when where why not no nor but so than then there here these those
we you they he she i me my our your their them us can may might must shall
will do done being been about into over under again further once all both each
few more most other some such only own same too very just also
""".split())

WORD_RE = re.compile(r"[a-z0-9]+")
DECIMAL_RE = re.compile(r"(?<![\w.])(\d+\.\d+)(?![\w.])")

#: Minimum length a stem may be reduced to. Below this, suffix stripping starts
#: merging unrelated words ("used" -> "us"), costing more than it buys.
MIN_STEM = 4


def stem(token: str) -> str:
    """Minimal, dependency-free suffix stripping (not a real Porter stemmer).

    Plurals, past tense, gerunds, and the trailing silent `e`, so 'route',
    'routed' and 'routing' reach one stem. Inflection alone otherwise makes a
    query term look absent from a document that plainly discusses it -- and an
    absent term takes maximum IDF, so a stemming miss does not merely fail to
    match, it dominates the query.
    """
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    if len(token) - 3 >= MIN_STEM and token.endswith("ing"):
        token = token[:-3]
    elif len(token) - 2 >= MIN_STEM and token.endswith("ed"):
        token = token[:-2]
    if len(token) - 1 >= MIN_STEM and token.endswith("e") and token[-2] not in "aeiou":
        token = token[:-1]
    return token


def trigrams(text: str) -> set[str]:
    cleaned = re.sub(r"\s+", " ", text.lower()).strip()
    if len(cleaned) < 3:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + 3] for i in range(len(cleaned) - 2)}


def canonical_number(raw: str) -> str:
    try:
        value = Decimal(raw).normalize()
    except (InvalidOperation, ValueError):
        return raw
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


class MeasurementTokenizer:
    """A tokenizer assembled from a domain's declared measurement policy.

    Engineering domains are made of numbers with units, and a bare `[a-z0-9]+`
    tokenizer shatters every one: "5.8 GHz" becomes ['5','8','ghz'], which is
    indistinguishable from "8.5 GHz". What differs between domains is only
    *which* units and identifier prefixes matter -- RE has MHz and dBuV/m and
    EUT-7, a thermal domain would have degC and W/mK. That is a table, and the
    table already lives in `domain_pack.yaml` under `measurement_policy`.

    A domain that declares no measurement policy gets ordinary word
    tokenization, which is correct rather than degraded: a domain of prose has
    no measurements to preserve.
    """

    def __init__(
        self,
        *,
        canonical_unit: str = "",
        unit_multipliers: Mapping[str, Any] | None = None,
        level_units: Sequence[str] = (),
        identifier_prefixes: Sequence[str] = (),
    ) -> None:
        self.canonical_unit = canonical_unit.lower()
        self.unit_multipliers = {
            str(k).lower(): Decimal(str(v)) for k, v in (unit_multipliers or {}).items()
        }
        # Longest first, so "dbuv/m" wins over "dbuv" and "db".
        self.level_units = tuple(sorted((u.lower() for u in level_units), key=len, reverse=True))
        self.identifier_prefixes = tuple(p.lower() for p in identifier_prefixes)

        self._scale_re = (
            re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(" +
                       "|".join(re.escape(u) for u in
                                sorted(self.unit_multipliers, key=len, reverse=True)) +
                       r")(?![\w])")
            if self.unit_multipliers else None
        )
        self._level_re = (
            re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(" +
                       "|".join(re.escape(u) for u in self.level_units) + r")(?![\w])")
            if self.level_units else None
        )
        self._ident_re = (
            re.compile(r"(?<![\w-])((?:" +
                       "|".join(re.escape(p) for p in self.identifier_prefixes) +
                       r")(?:-[a-z0-9]+)+)(?![\w-])")
            if self.identifier_prefixes else None
        )

    def is_specifier(self, token: str) -> bool:
        """Does this token name one particular thing -- a measurement or an id?

        A question naming a specifier the corpus has never seen is answerable
        by nothing, however well its remaining words match. Ordinary words carry
        no such guarantee.
        """
        if self.canonical_unit and token.startswith("q:"):
            return True
        if "-" in token and token.split("-", 1)[0] in self.identifier_prefixes:
            return True
        return any(token.endswith(unit) and any(c.isdigit() for c in token)
                   for unit in self.level_units)

    def __call__(self, text: str) -> list[str]:
        lowered = text.lower().replace("µ", "u").replace("μ", "u")
        tokens: list[str] = []

        def consume(pattern: re.Pattern[str] | None, make) -> None:
            nonlocal lowered
            if pattern is None:
                return
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
                # Masked so the matched digits do not also leak out as bare
                # numbers colliding with every other number in the corpus.
                lowered = " ".join(pieces)

        consume(self._scale_re, lambda m: "q:" + canonical_number(
            str(Decimal(m.group(1)) * self.unit_multipliers[m.group(2)])) + self.canonical_unit)
        consume(self._level_re, lambda m: canonical_number(m.group(1)) + m.group(2))
        consume(self._ident_re, lambda m: m.group(1))
        consume(DECIMAL_RE, lambda m: canonical_number(m.group(1)))

        tokens.extend(stem(t) for t in WORD_RE.findall(lowered))
        return tokens


@dataclass(frozen=True)
class RetrievalThresholds:
    """The four numbers a domain tunes. Every one is corpus-fitted, which is
    why they are domain data and not kernel constants, and why
    `scripts/calibrate_retrieval.py` exists to re-derive them."""

    coverage_floor: float = 0.12
    unseen_term_ceiling: float = 0.35
    lexical_weight: float = 0.6

    @classmethod
    def from_policy(cls, policy: Mapping[str, Any]) -> "RetrievalThresholds":
        retrieval = (policy.get("retrieval_policy") or {}) if policy else {}
        tuning = (retrieval.get("tuning") or {}) if retrieval else {}
        modes = {"bm25": 1.0, "trigram": 0.0, "hybrid": float(tuning.get("lexical_weight", 0.6))}
        mode = str(retrieval.get("default_mode", "hybrid")).lower()
        return cls(
            coverage_floor=float(tuning.get("coverage_floor", 0.12)),
            unseen_term_ceiling=float(tuning.get("unseen_term_ceiling", 0.35)),
            lexical_weight=modes.get(mode, modes["hybrid"]),
        )


class RetrievalIndex:
    """BM25 + character-trigram similarity over a fragment set.

    Nothing here knows what domain it is serving. It is handed a tokenizer, a
    vocabulary to ignore, and thresholds; everything else is arithmetic.
    """

    def __init__(
        self,
        tokenize,
        *,
        ignore_terms: Iterable[str] = (),
        thresholds: RetrievalThresholds | None = None,
    ) -> None:
        self._tokenize = tokenize
        self._ignore = frozenset(ignore_terms)
        self.thresholds = thresholds or RetrievalThresholds()
        self._texts: list[str] = []
        self._terms: list[list[str]] = []
        self._term_sets: list[set[str]] = []
        self._counts: list[Counter[str]] = []
        self._trigrams: list[set[str]] = []
        self._doc_freq: Counter[str] = Counter()
        self._avg_len = 0.0

    def build(self, texts: Sequence[str]) -> int:
        """Tokenize once, at load. Retrieval reads these for every query."""
        self._texts = list(texts)
        self._terms = [list(self._tokenize(t)) for t in self._texts]
        self._term_sets = [set(t) for t in self._terms]
        self._counts = [Counter(t) for t in self._terms]
        self._trigrams = [trigrams(t) for t in self._texts]
        self._doc_freq = Counter()
        for terms in self._term_sets:
            for term in terms:
                self._doc_freq[term] += 1
        lengths = [len(t) for t in self._terms] or [0]
        self._avg_len = sum(lengths) / len(lengths)
        return len(self._texts)

    @property
    def doc_freq(self) -> Counter[str]:
        return self._doc_freq

    @property
    def size(self) -> int:
        return len(self._texts)

    def term_idf(self, term: str) -> float:
        """Smoothed IDF: every term keeps a floor of weight.

        The `+ 1` is not cosmetic. Without it a term appearing in *every*
        fragment scores exactly zero -- log((N+1)/(N+1)) -- and with a small
        corpus that is nearly all of them. Coverage is a ratio of these
        weights, so a three-document corpus produced a coverage of 0.0 for its
        own documents and the pack abstained on every question ever asked of
        it. The factory's first-run experience with a handful of files was a
        retriever that refused everything, which is indistinguishable from a
        broken one.

        The offset is the standard smoothing (scikit-learn spells it
        `smooth_idf`), and it is measurably neutral where it does not matter:
        adopting it left RE's Evidence Recall@10 and abstention identical to
        four decimal places on a 108-fragment corpus.
        """
        return math.log((max(self.size, 1) + 1) / (self._doc_freq.get(term, 0) + 1)) + 1.0

    def query_weights(self, query_terms: Sequence[str]) -> dict[str, float]:
        return {t: self.term_idf(t) for t in dict.fromkeys(query_terms) if t not in self._ignore}

    def coverage(self, weights: Mapping[str, float], fragment_terms: set[str]) -> float:
        total = sum(weights.values())
        if total <= 0:
            return 0.0
        return sum(w for term, w in weights.items() if term in fragment_terms) / total

    def _bm25(self, query_terms: Sequence[str], index: int) -> float:
        k1, b = 1.5, 0.75
        n_docs = max(self.size, 1)
        frag_len = len(self._terms[index]) or 1
        counts = self._counts[index]
        score = 0.0
        for term in query_terms:
            df = self._doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            tf = counts.get(term, 0)
            if not tf:
                continue
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * frag_len / (self._avg_len or 1)))
        return score

    def unanswerable(self, query_terms: Sequence[str], *, is_specifier=None) -> bool:
        """Two absence rules, applied before anything is ranked.

        A question naming a specifier the corpus has never seen, or too much of
        whose informative vocabulary is absent, has no answer here -- however
        well its remaining words happen to match. Without this a max-normalized
        score always looks confident for the single closest fragment.
        """
        unique = list(dict.fromkeys(query_terms))
        if is_specifier is not None:
            if any(is_specifier(t) and self._doc_freq.get(t, 0) == 0 for t in unique):
                return True
        informative = [t for t in unique if t not in self._ignore]
        if not informative:
            return False
        unseen = sum(1 for t in informative if self._doc_freq.get(t, 0) == 0)
        return unseen / len(informative) > self.thresholds.unseen_term_ceiling

    def rank(
        self,
        query: str,
        *,
        top_k: int,
        lexical_weight: float | None = None,
        is_specifier=None,
    ) -> list[tuple[int, float, float, float]]:
        """(fragment index, combined score, bm25 normalized, trigram jaccard)."""
        if not self._texts:
            return []
        query_terms = list(self._tokenize(query))
        if self.unanswerable(query_terms, is_specifier=is_specifier):
            return []

        weight = self.thresholds.lexical_weight if lexical_weight is None else lexical_weight
        weights = self.query_weights(query_terms)
        query_tri = trigrams(query)
        raw = [self._bm25(query_terms, i) for i in range(self.size)]
        top = max(raw) or 1.0

        scored: list[tuple[int, float, float, float]] = []
        for index, bm25 in enumerate(raw):
            if weights and self.coverage(weights, self._term_sets[index]) < self.thresholds.coverage_floor:
                continue
            frag_tri = self._trigrams[index]
            union = query_tri | frag_tri
            jaccard = len(query_tri & frag_tri) / len(union) if union else 0.0
            normalized = bm25 / top
            combined = weight * normalized + (1.0 - weight) * jaccard
            if combined > 0:
                scored.append((index, combined, normalized, jaccard))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
