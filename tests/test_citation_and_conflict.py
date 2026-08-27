"""What a claim cites, what that citation is worth, and what it cannot settle.

Three defects the 2026-08-26 RAG audit measured, and the boundary the fixes
stop at.

Both callers cited `evidence[0]` and nothing else, so an answer resting on two
fragments could not be grounded however well retrieval had done -- the system
reported terms as unsupported by evidence it was holding. `Claim.confidence`
carried the retrieval score, which `rank` normalizes against each query's own
maximum, so it sat near 0.69 whatever the match was worth. And nothing told a
reader that the document being quoted was also present at another revision.

The boundary matters as much as the fixes. Detecting that two documents assert
incompatible things is a semantic judgement, and deciding whether a retest
supersedes a test needs metadata `revision_id` does not carry. Neither is
claimed, and these tests pin the not-claiming.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (str(ROOT / "src"), str(ROOT / "scripts")):
    if path not in sys.path:
        sys.path.insert(0, path)

from cer_runtime import CERGateRuntime  # noqa: E402
from claim_verification import ClaimVerifier  # noqa: E402
from interfaces import CERSnapshot, Claim, EvidenceCandidate  # noqa: E402
from re_domain_pack import REDomainPack  # noqa: E402

SNAPSHOT = CERSnapshot(
    policy_id="CER", policy_version="1.0.0", snapshot_id="S", snapshot_hash="h",
    source_commit="c",
    required_checks=("GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"),
)


def _ev(eid, text, *, document_id="D1", revision_id="REV-A", title=None):
    return EvidenceCandidate(eid, document_id, revision_id, f"F-{eid}", 1.0, text,
                             {"title": title} if title else {})


@pytest.fixture(scope="module")
def pack():
    p = REDomainPack()
    p.load()
    return p


class TestCitationCoversTheClaim:
    @staticmethod
    def _verifier():
        return ClaimVerifier(lambda t: t.lower().replace("?", "").split(),
                             grounding_floor=0.25, ignore_terms={"the", "and", "was", "is"})

    def test_a_second_fragment_is_cited_when_it_supplies_something_new(self):
        cited = self._verifier().select_citations(
            "what level and what mitigation",
            [_ev("E1", "the level was 38.2"), _ev("E2", "a mitigation was fitted")],
        )
        assert [c.evidence_id for c in cited] == ["E1", "E2"]

    def test_a_fragment_supplying_nothing_new_is_not_cited(self):
        """The fix for an under-cited claim must not be an over-cited one."""
        cited = self._verifier().select_citations(
            "what level",
            [_ev("E1", "the level was 38.2"), _ev("E2", "unrelated commentary")],
        )
        assert [c.evidence_id for c in cited] == ["E1"]

    def test_rank_one_is_always_cited(self):
        """It is what the answer is drawn from, cover or no cover."""
        cited = self._verifier().select_citations(
            "something else entirely", [_ev("E1", "the level was 38.2")]
        )
        assert [c.evidence_id for c in cited] == ["E1"]

    def test_no_evidence_cites_nothing(self):
        assert self._verifier().select_citations("anything", []) == []

    def test_the_regression_that_started_this(self, pack):
        """Retrieval found the mitigation, the claim did not cite it, and the
        verifier then reported `mitigation` as unsupported by evidence in hand."""
        query = ("What was the EUT-7 132 MHz level before mitigation and how far "
                 "above the limit was it?")
        evidence = pack.retrieve(query, top_k=10)
        claim = pack.build_claim(query, evidence)
        verdict = pack.claim_verifier.verify([claim], evidence).verdicts[0]
        assert len(claim.evidence_ids) > 1
        assert "mitigation" not in " ".join(verdict.unsupported_terms)

    def test_grounding_improves_without_citing_everything(self, pack):
        query = "What caused the radiated emission limit exceedance on EUT-12 at 340 MHz?"
        evidence = pack.retrieve(query, top_k=10)
        claim = pack.build_claim(query, evidence)
        assert 0 < len(claim.evidence_ids) < len(evidence), (
            "a claim citing every retrieved fragment is padding, not grounding"
        )


class TestConfidenceMeansSomething:
    def test_confidence_is_coverage_not_the_retrieval_score(self, pack):
        query = "What caused the 375 MHz exceedance on EUT-31?"
        evidence = pack.retrieve(query, top_k=10)
        claim = pack.build_claim(query, evidence)
        expected = pack.evidence_coverage(
            query, pack.claim_verifier.select_citations(query, evidence)
        )
        assert claim.confidence == pytest.approx(round(expected, 4))
        assert claim.confidence != pytest.approx(round(evidence[0].score, 4))

    def test_confidence_is_bounded_and_varies(self, pack):
        """The old value sat in a 0.17-wide band because `rank` normalizes BM25
        against each query's own maximum, pinning rank 1 at exactly 1.0."""
        benchmark = json.loads(
            (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json")
            .read_text(encoding="utf-8")
        )
        values = []
        for case in benchmark["cases"][:60]:
            evidence = pack.retrieve(case["query"], top_k=10)
            if evidence:
                values.append(pack.build_claim(case["query"], evidence).confidence)
        assert all(0.0 <= v <= 1.0 for v in values)
        assert max(values) - min(values) > 0.3, (
            f"confidence spans only {max(values) - min(values):.3f}; a value that "
            "cannot vary cannot inform"
        )

    def test_no_evidence_is_zero_confidence(self, pack):
        claim = pack.build_claim("anything at all", [])
        assert claim.confidence == 0.0
        assert claim.evidence_ids == ["E-NO-EVIDENCE-FOUND"]


class TestRevisionConflictsAreReportedNotGated:
    @staticmethod
    def _verify(evidence, ids):
        claim = Claim("C1", "the measured level", "fact", ids, 0.9)
        verifier = ClaimVerifier(lambda t: t.lower().split(), grounding_floor=0.0)
        return claim, verifier.verify([claim], evidence)

    def test_one_document_at_two_revisions_is_named(self):
        evidence = [_ev("E1", "measured 38.2", revision_id="REV-A"),
                    _ev("E2", "measured 31.4", revision_id="REV-B")]
        _, report = self._verify(evidence, ["E1", "E2"])
        assert report.verdicts[0].conflicting_revisions == (("D1", ("REV-A", "REV-B")),)

    def test_the_other_revision_counts_even_when_it_was_not_cited(self):
        """The headline case fails without this.

        Asked what EUT-7 measured, retrieval returns 38.2 from REV-A and 31.4
        from REV-B, and REV-B supplies no term REV-A had not -- so the citation
        selector drops it, correctly. A retest disagreeing in numbers while
        agreeing in words is invisible to any lexical selector.
        """
        evidence = [_ev("E1", "measured 38.2", revision_id="REV-A"),
                    _ev("E2", "measured 31.4", revision_id="REV-B")]
        _, report = self._verify(evidence, ["E1"])
        assert report.verdicts[0].conflicting_revisions == (("D1", ("REV-A", "REV-B")),)

    def test_two_fragments_of_one_revision_are_not_a_conflict(self):
        evidence = [_ev("E1", "first paragraph"), _ev("E2", "second paragraph")]
        _, report = self._verify(evidence, ["E1", "E2"])
        assert report.verdicts[0].conflicting_revisions == ()

    def test_another_document_entirely_is_not_a_conflict(self):
        evidence = [_ev("E1", "a", document_id="D1"), _ev("E2", "b", document_id="D2")]
        _, report = self._verify(evidence, ["E1", "E2"])
        assert report.verdicts[0].conflicting_revisions == ()

    def test_the_gate_does_not_act_on_a_revision_conflict(self):
        """Measured: gating on this referred 38 of 139 answerable questions, and
        15 were `revision_comparison` cases asking about the difference between
        revisions. A rule that refers the question it was built to answer is not
        narrow enough to keep. See OPEN_DECISIONS D-14."""
        evidence = [_ev("E1", "the measured level", revision_id="REV-A"),
                    _ev("E2", "the measured level", revision_id="REV-B")]
        claim, report = self._verify(evidence, ["E1", "E2"])
        decision = CERGateRuntime().evaluate(
            snapshot=SNAPSHOT, run_id="R", gate_id="G",
            claims=[claim], evidence=evidence, verification=report,
        )
        assert report.conflicting_revision_claim_ids == ("C1",)
        assert decision.result == "PASS"

    def test_semantic_contradiction_is_not_detected_at_all(self):
        """Pinned, so the gap is never read as coverage (OPEN_DECISIONS D-11)."""
        evidence = [_ev("E1", "the claim is true", document_id="D1"),
                    _ev("E2", "the claim is false", document_id="D2")]
        claim, report = self._verify(evidence, ["E1", "E2"])
        decision = CERGateRuntime().evaluate(
            snapshot=SNAPSHOT, run_id="R", gate_id="G",
            claims=[claim], evidence=evidence, verification=report,
        )
        assert report.conflicting_revision_claim_ids == ()
        assert decision.result == "PASS"

    def test_the_reader_is_told(self, pack):
        from run_domain import answer

        result = answer(pack, "What is the EUT-7 emission level at 132 MHz?",
                        top_k=10, mode=None)
        assert result["conflicting_revisions"], (
            "the corpus holds this report at two revisions that disagree; "
            "an answer that does not say so is the audit's finding 1"
        )


class TestTheMetricSaysWhatItIs:
    def test_random_retrieval_is_measured_and_is_not_zero(self, pack):
        from re_demo import random_baseline

        benchmark = json.loads(
            (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json")
            .read_text(encoding="utf-8")
        )
        cases = [c for c in benchmark["cases"]
                 if not c.get("expect_abstain") and c.get("expected_document_ids")]
        baseline = random_baseline(pack, cases, trials=40)
        assert 0.25 < baseline < 0.45, (
            f"random baseline measured {baseline:.3f}; the shipped figure is 0.356 and "
            "every recall number is read against it"
        )

    def test_the_baseline_is_deterministic(self, pack):
        from re_demo import random_baseline

        benchmark = json.loads(
            (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json")
            .read_text(encoding="utf-8")
        )
        cases = [c for c in benchmark["cases"]
                 if not c.get("expect_abstain") and c.get("expected_document_ids")][:40]
        assert random_baseline(pack, cases, trials=10) == random_baseline(
            pack, cases, trials=10
        )

    def test_one_gold_document_per_case_makes_this_a_hit_rate(self):
        benchmark = json.loads(
            (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json")
            .read_text(encoding="utf-8")
        )
        sizes = {len(c["expected_document_ids"]) for c in benchmark["cases"]
                 if c.get("expected_document_ids")}
        assert sizes == {1}, (
            f"gold set sizes are {sizes}; with more than one gold document "
            "`evidence_recall_at_10` becomes a recall again and the `hit_rate_at_10` "
            "alias should be revisited"
        )

    def test_the_demo_reports_the_floor_and_the_headroom(self):
        import re_demo

        acceptance = re_demo.run()["acceptance"]
        assert acceptance["hit_rate_at_10"] == acceptance["evidence_recall_at_10"]
        assert 0.25 < acceptance["random_baseline_recall_at_10"] < 0.45
        assert 0.0 < acceptance["share_of_available_headroom"] < 1.0
        for band in acceptance["abstention_by_band"].values():
            assert "silently_answered" in band
