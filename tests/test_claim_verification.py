"""The kernel claim-evidence verifier, tested as a kernel component.

Nothing here imports the RE Domain Pack. That is the point of the module and
of ARCHITECTURE_REFACTOR_PLAN goal 1: verification is shared-kernel behaviour,
so it must be demonstrable with a throwaway tokenizer and no domain at all. A
test that could only be written against RE would mean the mechanism had domain
knowledge baked into it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from claim_verification import ClaimVerifier, VerificationReport  # noqa: E402
from cer_runtime import CERGateRuntime  # noqa: E402
from interfaces import CERSnapshot, Claim, EvidenceCandidate  # noqa: E402


def words(text: str) -> list[str]:
    return [w for w in text.lower().replace(",", " ").replace(".", " ").split() if w]


def evidence(evidence_id: str, text: str, *, title: str = "") -> EvidenceCandidate:
    return EvidenceCandidate(
        evidence_id=evidence_id,
        document_id="DOC-1",
        revision_id="REV-A",
        fragment_id="FRAG-1",
        score=0.9,
        text=text,
        metadata={"title": title} if title else {},
    )


def claim(statement: str, *evidence_ids: str) -> Claim:
    return Claim(
        claim_id="C-1",
        statement=statement,
        claim_type="answer",
        evidence_ids=list(evidence_ids),
        confidence=0.5,
    )


@pytest.fixture
def verifier() -> ClaimVerifier:
    return ClaimVerifier(words, grounding_floor=0.5, ignore_terms={"the", "a", "is", "of", "at", "an", "during"})


def test_evidence_that_supplies_the_claim_is_grounded(verifier):
    report = verifier.verify(
        [claim("the turbine bearing failed at high load", "E-1")],
        [evidence("E-1", "The turbine bearing failed under high load during the run.")],
    )
    assert report.all_grounded
    assert report.verdicts[0].unsupported_terms == ()


def test_evidence_that_merely_exists_is_not_support(verifier):
    """The hole this module closes. The claim cites a real evidence id whose
    text has nothing to do with it."""
    report = verifier.verify(
        [claim("the turbine bearing failed at high load", "E-1")],
        [evidence("E-1", "Cafeteria hours are posted weekly on the noticeboard.")],
    )
    assert not report.all_grounded
    assert report.ungrounded_claim_ids == ("C-1",)


def test_a_claim_citing_nothing_that_exists_is_never_grounded(verifier):
    report = verifier.verify(
        [claim("the turbine bearing failed", "E-MISSING")],
        [evidence("E-1", "the turbine bearing failed")],
    )
    verdict = report.verdicts[0]
    assert verdict.cited_evidence == ()
    assert not verdict.grounded


def test_the_document_title_counts_as_supplied_text(verifier):
    """A title carries what a document *is*, which the body often never
    restates. Retrieval indexes it for the same reason."""
    ungrounded = ClaimVerifier(words, grounding_floor=0.9, ignore_terms={"the"}).verify(
        [claim("bearing inspection procedure", "E-1")],
        [evidence("E-1", "Remove the cover and check for scoring.")],
    )
    assert not ungrounded.all_grounded

    grounded = ClaimVerifier(words, grounding_floor=0.9, ignore_terms={"the"}).verify(
        [claim("bearing inspection procedure", "E-1")],
        [evidence("E-1", "Remove the cover and check for scoring.",
                  title="Bearing Inspection Procedure")],
    )
    assert grounded.all_grounded


def test_unsupported_terms_name_what_the_evidence_never_mentions(verifier):
    """The output that matters where the threshold cannot decide: it puts the
    gap in front of a reviewer by name. See OPEN_DECISIONS D-11."""
    report = verifier.verify(
        [claim("field strength during an immunity test", "E-1")],
        [evidence("E-1", "Field strength is derived from the receiver reading during a test.")],
    )
    assert "immunity" in report.verdicts[0].unsupported_terms


def test_an_empty_claim_set_is_not_all_grounded(verifier):
    """A verifier that returns True for having checked nothing is the failure
    mode this module exists to prevent."""
    assert not VerificationReport(verdicts=(), grounding_floor=0.5).all_grounded
    assert not verifier.verify([], []).all_grounded


def test_the_floor_is_what_decides(verifier):
    """Same claim, same evidence, different domain policy -- so the threshold
    is genuinely the Domain Pack's half and not a kernel opinion."""
    claims = [claim("alpha beta gamma delta", "E-1")]
    ev = [evidence("E-1", "alpha beta")]
    assert ClaimVerifier(words, grounding_floor=0.5).verify(claims, ev).all_grounded
    assert not ClaimVerifier(words, grounding_floor=0.75).verify(claims, ev).all_grounded


# --- the gate has to act on the verdict, or none of the above matters --------

SNAPSHOT = CERSnapshot(
    policy_id="CER",
    policy_version="1.0.0",
    snapshot_id="TEST-SNAP",
    snapshot_hash="hash",
    source_commit="commit",
    required_checks=("GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"),
)


def _decide(verification):
    return CERGateRuntime().evaluate(
        snapshot=SNAPSHOT,
        run_id="RUN-1",
        gate_id="GATE-1",
        claims=[claim("the turbine bearing failed at high load", "E-1")],
        evidence=[evidence("E-1", "Cafeteria hours are posted weekly.")],
        verification=verification,
    )


def test_gate_passes_unsupported_claims_when_no_verification_is_supplied():
    """Records the pre-existing behaviour precisely, so the next reader can see
    what the verifier is for: on evidence-id existence alone, a claim about a
    bearing citing a note about cafeteria hours reaches PASS."""
    assert _decide(None).result == "PASS"


def test_gate_blocks_an_ungrounded_claim_once_verification_is_supplied():
    verifier = ClaimVerifier(words, grounding_floor=0.5, ignore_terms={"the", "at"})
    decision = _decide(verifier.verify(
        [claim("the turbine bearing failed at high load", "E-1")],
        [evidence("E-1", "Cafeteria hours are posted weekly.")],
    ))
    assert decision.result == "BLOCK"
    assert any(f.startswith("UNGROUNDED_CLAIM:") for f in decision.triggered_findings)


def test_one_defect_does_not_produce_two_findings():
    """A claim citing an evidence id that does not exist is already
    UNSUPPORTED_CLAIM; it must not also be reported as UNGROUNDED_CLAIM."""
    verifier = ClaimVerifier(words, grounding_floor=0.5)
    claims = [claim("anything at all", "E-MISSING")]
    ev = [evidence("E-1", "unrelated")]
    decision = CERGateRuntime().evaluate(
        snapshot=SNAPSHOT, run_id="RUN-1", gate_id="GATE-1",
        claims=claims, evidence=ev, verification=verifier.verify(claims, ev),
    )
    assert decision.result == "BLOCK"
    findings = [f for f in decision.triggered_findings if f.endswith("C-1")]
    assert findings == ["UNSUPPORTED_CLAIM:C-1"], findings
