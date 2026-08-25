"""Retrieval must depend on the query-document relationship, not on what else
happens to be in the corpus.

OPEN_DECISIONS D-10. `retrieve()` gated candidates on `_distinctive_terms` --
query terms with `0 < df <= 30%` of fragments -- and required
`min(2, len(distinctive))` of them to appear literally. Both the membership of
that set and the number of required hits therefore moved as the corpus changed,
so the same query against the same document behaved differently depending on
which unrelated documents sat alongside it, non-monotonically.

These tests pin that property. They are written against corpus *sizes* rather
than a single fixture precisely because a defect that only appears at one size
is what made D-10 hard to see: it passed at 0, failed at 40, and passed again
at 100.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from re_corpus import (  # noqa: E402
    CORPUS,
    adversarial_corpus,
    term_saturating_documents,
)
from re_domain_pack import REDomainPack  # noqa: E402

BENCHMARK = json.loads(
    (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json").read_text(encoding="utf-8")
)
CASES = BENCHMARK["cases"]

# Corpus shapes, not just sizes. Volume alone does not reach the boundary this
# is protecting: distractors that mention a term in a roughly constant fraction
# of their text keep its document-frequency *ratio* roughly constant however
# many are added. Crossing the line takes documents that mention one term far
# more densely than the baseline does -- so the family below varies density as
# well as volume, saturating each descriptive term the benchmark queries use.
_SATURATED_TERMS = ("antenna", "setup", "calibration", "cable", "chamber")

CORPUS_SHAPES: dict[str, "callable"] = {
    "baseline": lambda: adversarial_corpus(0),
    **{f"distractors-{n}": (lambda n=n: adversarial_corpus(n)) for n in (10, 40, 100, 250)},
    **{
        f"saturate-{term}-{n}": (lambda t=term, n=n: list(CORPUS) + term_saturating_documents(n, phrase=t))
        for term in _SATURATED_TERMS
        for n in (3, 20)
    },
}


def _outcome(pack: REDomainPack, case: dict) -> bool:
    """Did this case behave as the benchmark says it should?"""
    candidates = pack.retrieve(case["query"], top_k=5)
    if case.get("expect_abstain"):
        return not candidates
    expected = set(case.get("expected_document_ids") or [])
    found = {c.document_id for c in candidates}
    return expected.issubset(found) if expected else bool(candidates)


def _outcomes_for(build) -> dict[str, bool]:
    pack = REDomainPack()
    pack.load(build())
    return {case["case_id"]: _outcome(pack, case) for case in CASES}


@pytest.fixture(scope="module")
def outcomes_by_size() -> dict[str, dict[str, bool]]:
    return {name: _outcomes_for(build) for name, build in CORPUS_SHAPES.items()}


@pytest.mark.parametrize("case_id", [c["case_id"] for c in CASES])
def test_case_outcome_is_stable_across_corpus_size(outcomes_by_size, case_id: str) -> None:
    """Adding documents that answer none of the benchmark queries must not
    change whether a case passes. If it does, the benchmark is measuring the
    corpus rather than the retriever, and no fixed Recall threshold from
    docs/RE_POC.md can mean anything."""
    seen = {shape: outcomes[case_id] for shape, outcomes in outcomes_by_size.items()}
    if len(set(seen.values())) == 1:
        return
    passing = sorted(k for k, v in seen.items() if v)
    failing = sorted(k for k, v in seen.items() if not v)
    pytest.fail(
        f"{case_id} outcome depends on which unrelated documents are present.\n"
        f"  passes under: {passing}\n"
        f"  fails under:  {failing}"
    )


def test_abstention_holds_at_every_corpus_size(outcomes_by_size) -> None:
    """The out-of-corpus cases are the ones most at risk: a query naming
    something absent gets *more* plausible-looking near-matches as the corpus
    grows."""
    abstain_ids = [c["case_id"] for c in CASES if c.get("expect_abstain")]
    assert abstain_ids, "benchmark has no abstention case to protect"
    for case_id in abstain_ids:
        for shape, outcomes in outcomes_by_size.items():
            assert outcomes[case_id], f"{case_id} stopped abstaining under corpus shape {shape!r}"


def test_near_duplicate_revision_does_not_displace_the_baseline_revision() -> None:
    """REV-B of DOC-RE-001 differs from REV-A by one measurement. A query about
    the REV-A finding must still reach REV-A."""
    pack = REDomainPack()
    pack.load(adversarial_corpus(0))
    candidates = pack.retrieve("What peak was measured on EUT-7 at 132 MHz?", top_k=5)
    revisions = {(c.document_id, c.revision_id) for c in candidates}
    assert ("DOC-RE-001", "REV-A") in revisions, sorted(revisions)


def test_contradicting_document_is_reachable_alongside_the_original() -> None:
    """RE_POC's "evidence supporting or contradicting a hypothesis" category
    needs both sides retrievable. Returning only one, with no signal the other
    exists, is not evidence handling."""
    pack = REDomainPack()
    pack.load(adversarial_corpus(0))
    candidates = pack.retrieve("Was the EUT-7 exceedance at 132 MHz reproduced?", top_k=8)
    docs = {c.document_id for c in candidates}
    assert {"DOC-RE-001", "DOC-RE-CON-001"} <= docs, sorted(docs)


def test_adversarial_corpus_is_deterministic() -> None:
    """A stability test built on a shifting corpus proves nothing."""
    assert adversarial_corpus(25) == adversarial_corpus(25)
    assert len(adversarial_corpus(0)) > len(CORPUS)
