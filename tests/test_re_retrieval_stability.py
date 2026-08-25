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
    DISTRACTOR_CHAMBERS,
    adversarial_corpus,
    contradicting_documents,
    distractor_documents,
    near_duplicate_revisions,
    notation_variant_documents,
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
    candidates = pack.retrieve(case["query"], top_k=10)
    if case.get("expect_abstain"):
        return not candidates
    expected = set(case.get("expected_document_ids") or [])
    found = {c.document_id for c in candidates}
    return expected.issubset(found) if expected else bool(candidates)


def _metrics(outcomes: dict[str, bool]) -> tuple[float, float]:
    """(Evidence Recall, abstention rate) -- the two RE_POC.md acceptance
    targets this benchmark can compute deterministically."""
    ans = [c["case_id"] for c in CASES if not c.get("expect_abstain")]
    abst = [c["case_id"] for c in CASES if c.get("expect_abstain")]
    return (
        sum(outcomes[cid] for cid in ans) / len(ans),
        sum(outcomes[cid] for cid in abst) / len(abst),
    )


def _outcomes_for(build) -> dict[str, bool]:
    pack = REDomainPack()
    pack.load(build())
    return {case["case_id"]: _outcome(pack, case) for case in CASES}


@pytest.fixture(scope="module")
def outcomes_by_size() -> dict[str, dict[str, bool]]:
    return {name: _outcomes_for(build) for name, build in CORPUS_SHAPES.items()}


# How far the headline metrics may drift across corpus shapes. This is the
# property RE_POC.md's fixed acceptance targets actually depend on: a number
# that moves with the archive cannot be compared to a threshold.
#
# Not zero, and deliberately so. At 159 cases some sit near a decision
# boundary by construction, and demanding bit-identical outcomes at every
# shape would either force the benchmark to contain only easy cases or make
# this test a tuning oracle. What must not happen is the metric *sliding* as
# unrelated documents arrive.
_METRIC_DRIFT_TOLERANCE = 0.05


def test_headline_metrics_do_not_move_with_the_corpus(outcomes_by_size) -> None:
    measured = {shape: _metrics(o) for shape, o in outcomes_by_size.items()}
    recalls = [m[0] for m in measured.values()]
    abstentions = [m[1] for m in measured.values()]
    for name, values in (("Evidence Recall", recalls), ("abstention rate", abstentions)):
        spread = max(values) - min(values)
        assert spread <= _METRIC_DRIFT_TOLERANCE, (
            f"{name} moves {spread:.3f} across corpus shapes "
            f"({min(values):.3f}..{max(values):.3f}); a fixed acceptance target "
            f"cannot be applied to a metric that depends on the archive.\n"
            + "\n".join(f"  {s}: recall={m[0]:.3f} abstain={m[1]:.3f}"
                         for s, m in sorted(measured.items()))
        )


def test_no_case_flips_back_and_forth_as_the_corpus_grows(outcomes_by_size) -> None:
    """The D-10 signature, pinned directly.

    That defect was not merely instability -- it was *non-monotonic*
    instability: RE-BC-002 passed at baseline, failed at 40 distractors and
    passed again at 100, because a term crossed a document-frequency threshold
    and then the required-hit count crossed one too. A case that changes once
    as the corpus grows is a boundary case. A case that changes twice is a
    gate keyed to corpus statistics.
    """
    volumes = ["baseline"] + [f"distractors-{n}" for n in (10, 40, 100, 250)]
    offenders = {}
    for case in CASES:
        cid = case["case_id"]
        series = [outcomes_by_size[shape][cid] for shape in volumes]
        flips = sum(1 for a, b in zip(series, series[1:]) if a != b)
        if flips > 1:
            offenders[cid] = dict(zip(volumes, series))
    assert not offenders, (
        "outcome oscillates as unrelated documents are added:\n"
        + "\n".join(f"  {cid}: {series}" for cid, series in offenders.items())
    )


def test_abstention_holds_at_every_corpus_size(outcomes_by_size) -> None:
    """The out-of-corpus cases are the ones most at risk: a query naming
    something absent gets *more* plausible-looking near-matches as the corpus
    grows. Scored as a rate rather than per-case, because the near-miss band
    is a known open limitation (OPEN_DECISIONS D-11) -- what must hold is that
    adding documents does not make abstention *worse*."""
    abstain_ids = [c["case_id"] for c in CASES if c.get("expect_abstain")]
    assert abstain_ids, "benchmark has no abstention case to protect"
    baseline = sum(outcomes_by_size["baseline"][cid] for cid in abstain_ids)
    for shape, outcomes in outcomes_by_size.items():
        held = sum(outcomes[cid] for cid in abstain_ids)
        assert held >= baseline, (
            f"abstention degraded under corpus shape {shape!r}: "
            f"{held}/{len(abstain_ids)} against {baseline}/{len(abstain_ids)} at baseline"
        )


def test_no_generator_collides_with_a_baseline_document_identity() -> None:
    """Every adversarial shape must add documents, never silently replace one.

    `near_duplicate_revisions()` emitted DOC-RE-001/REV-B, which the baseline
    corpus already held, so the adversarial corpus carried two different
    documents under one identity and every df statistic counted them twice.
    Nothing detected it until the corpus loader started validating identities.
    """
    from corpus_source import from_documents

    baseline = {(d["document_id"], d["revision_id"]) for d in CORPUS}
    for name, generated in (
        ("near_duplicate_revisions", near_duplicate_revisions()),
        ("contradicting_documents", contradicting_documents()),
        ("notation_variant_documents", notation_variant_documents()),
        ("distractor_documents", distractor_documents(25)),
        ("term_saturating_documents", term_saturating_documents(25)),
    ):
        clashes = baseline & {(d["document_id"], d["revision_id"]) for d in generated}
        assert not clashes, f"{name} reuses baseline identities: {sorted(clashes)}"

    # And the assembled corpus must load cleanly through the same validation a
    # real out-of-tree corpus goes through.
    for n in (0, 40):
        from_documents(adversarial_corpus(n), origin=f"adversarial_corpus({n})")


def test_distractor_chambers_are_reserved_in_both_directions() -> None:
    """A generated distractor may not supply an identifier the corpus or a
    query depends on, and no query may assert the absence of one a distractor
    introduces. Both directions have already produced a silently-useless probe
    -- see the note on DISTRACTOR_CHAMBERS in src/re_corpus.py."""
    reserved = {f"ch-{n}" for n in DISTRACTOR_CHAMBERS}
    for doc in CORPUS:
        text = f"{doc['title']} {doc['text']}".lower()
        clashes = {c for c in reserved if c in text}
        assert not clashes, f"{doc['document_id']}/{doc['revision_id']} uses reserved {clashes}"
    for case in CASES:
        clashes = {c for c in reserved if c in case["query"].lower()}
        assert not clashes, f"{case['case_id']} uses reserved chamber {clashes}"


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
