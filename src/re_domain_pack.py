"""M1 RE Hybrid RAG Domain Pack — now a binding, not an implementation.

Implements the interfaces.DomainPack protocol for the RE (Radiated Emission)
engineering domain, per docs/RE_POC.md.

**What changed, and why it is the point.** This module used to be 783 lines,
and almost all of them were generic: BM25, trigram similarity, IDF gating,
abstention, chunking, indexing, scoring, reporting. None of that is about
radiated emission. It meant standing up a second engineering domain required
copying the file — the code fork AF-004's acceptance criterion
("kernel loads Domain Pack without code fork") exists to forbid, and which
`scripts/domain_matrix_demo.py` could never have caught, being fixture-only by
construction.

The mechanism now lives in `src/generic_domain_pack.py` and
`src/domain_retrieval.py`, shared by every domain. What remains here is what is
genuinely RE's: its in-tree corpus, and the module-level names that the RE
tests and tooling address. Everything else — the unit tables, the stopwords,
the four tuned thresholds — moved into `domains/re/domain_pack.yaml`, where it
was always described and is now also *read from*.

`domains/thermal/` is the same protocol with no Python at all, which is the
test that this split is real rather than cosmetic.

Scope honesty note: still a first working slice. See OPEN_DECISIONS D-11 and
D-12 for what a lexical retriever cannot do, and
`scripts/calibrate_retrieval.py` for re-deriving the thresholds against a real
corpus — every one of them is fitted to the synthetic documents in
`src/re_corpus.py`.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

import yaml

from domain_retrieval import MeasurementTokenizer, stem, trigrams  # noqa: F401
from generic_domain_pack import Document, Fragment, GenericDomainPack  # noqa: F401
from interfaces import Claim, EvidenceCandidate  # noqa: F401

from re_corpus import CORPUS, RawDocument

DOMAIN_ID = "RE"
DOMAIN_VERSION = "0.1.0"
POLICY_PATH = Path(__file__).resolve().parents[1] / "domains" / "re" / "domain_pack.yaml"


def load_domain_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    """Load the declarative Domain Pack policy. Returns {} if absent so the
    pack still runs in a minimal code-only mode rather than hard-failing."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


_POLICY = load_domain_policy()
_MEASUREMENT = _POLICY.get("measurement_policy") or {}
_TERMINOLOGY = _POLICY.get("terminology") or {}
_TUNING = ((_POLICY.get("retrieval_policy") or {}).get("tuning") or {})
_VERIFICATION = _POLICY.get("verification_policy") or {}

# --- module-level names the RE tests and tooling address ---------------------
#
# These are now *read from* domains/re/domain_pack.yaml rather than duplicated
# beside it. tests/test_re_domain_pack.py asserts the code and the policy agree,
# which used to be a consistency check between two hand-maintained copies and is
# now simply true by construction.

# Decimal, not float: unit scaling must be exact. "5.8 GHz" has to land on
# precisely the same token as "5800 MHz", and binary floating point does not
# guarantee that for every multiplier in the table.
_FREQ_TO_MHZ = {k: Decimal(str(v)) for k, v in (_MEASUREMENT.get("frequency_units") or {}).items()}
_LEVEL_UNITS = tuple(_MEASUREMENT.get("level_units") or ())
_ID_PREFIXES = tuple(_MEASUREMENT.get("identifier_prefixes") or ())

_STOPWORDS = frozenset(_TERMINOLOGY.get("stopwords") or ())
_DOMAIN_GENERIC_TERMS = frozenset(_TERMINOLOGY.get("generic_terms") or ())

_COVERAGE_FLOOR = float(_TUNING.get("coverage_floor", 0.12))
_UNSEEN_TERM_CEILING = float(_TUNING.get("unseen_term_ceiling", 0.35))
_CLAIM_GROUNDING_FLOOR = float(_VERIFICATION.get("claim_grounding_floor", 0.25))

RETRIEVAL_MODES: dict[str, float] = {
    "bm25": 1.0,
    "trigram": 0.0,
    "hybrid": float(_TUNING.get("lexical_weight", 0.6)),
}

#: The RE tokenizer, assembled from the policy above. Importable directly
#: because the measurement tests exercise tokenization on its own.
_tokenize = MeasurementTokenizer(
    canonical_unit=str(_MEASUREMENT.get("canonical_frequency_unit", "MHz")).lower(),
    unit_multipliers=_MEASUREMENT.get("frequency_units") or {},
    level_units=_LEVEL_UNITS,
    identifier_prefixes=_ID_PREFIXES,
)
_is_specifier = _tokenize.is_specifier


class REDomainPack(GenericDomainPack):
    """The RE domain: the shared engine, plus this domain's corpus and policy.

    That this class is a handful of lines is the evidence the extraction was
    real. If RE needed behaviour `GenericDomainPack` cannot express, the split
    would have been cosmetic and this file would still be doing the work.
    """

    def __init__(
        self,
        corpus: Sequence[RawDocument] | None = None,
        policy: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            policy if policy is not None else _POLICY,
            corpus=list(corpus) if corpus is not None else list(CORPUS),
            corpus_origin="in-tree:src/re_corpus.CORPUS",
        )
        self.domain_id = DOMAIN_ID
        self.version = DOMAIN_VERSION
        # Honour the module-level constants, which the calibration sweeps and
        # several tests set directly at runtime.
        self._sync_module_thresholds()

    def _sync_module_thresholds(self) -> None:
        from dataclasses import replace

        self.thresholds = replace(
            self.thresholds,
            coverage_floor=_COVERAGE_FLOOR,
            unseen_term_ceiling=_UNSEEN_TERM_CEILING,
        )
        self._index.thresholds = self.thresholds
        self.modes = dict(RETRIEVAL_MODES)

    def retrieve(self, query: str, top_k: int = 5, *, mode: str | None = None,
                 **kwargs: Any) -> list[EvidenceCandidate]:
        # Re-read the module constants on every call: scripts/calibrate_retrieval.py
        # and the stability sweeps vary them in place, and a value cached at
        # construction would silently ignore the sweep and report the shipped
        # number for every candidate threshold.
        self._sync_module_thresholds()
        return super().retrieve(query, top_k, mode=mode, **kwargs)

    @property
    def claim_verifier(self):
        if self._verifier is None:
            from claim_verification import ClaimVerifier as _CV

            self._verifier = _CV(
                _tokenize,
                grounding_floor=float(_VERIFICATION.get("claim_grounding_floor",
                                                        _CLAIM_GROUNDING_FLOOR)),
                ignore_terms=_STOPWORDS | _DOMAIN_GENERIC_TERMS,
            )
        return self._verifier
