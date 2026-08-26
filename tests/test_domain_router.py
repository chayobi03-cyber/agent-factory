"""Routing has to be able to say "not me", "not here", and "ask a person".

`interfaces.RouteDecision` carried a `requires_human` flag from the day the
kernel was written and nothing ever set it, because nothing ever built a
`RouteDecision` at all. These tests exist to keep the three outcomes real: a
router that can only name a domain is a router that is wrong silently, and the
silent case is the one no reader catches.

The ambiguity tests build their own corpora rather than using
`domains/*/examples`, and that is the point. The six example domains are
subject-disjoint -- no two describe the same artefact -- so no genuinely
ambiguous question exists over them. Two routing benchmark cases were labelled
`ambiguous` anyway, on the wording alone, and both turned out to be decisively
one domain when measured. Here the overlap is constructed on purpose, so the
assertion is about the router rather than about a guess.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (str(SRC), str(ROOT / "scripts")):
    if path not in sys.path:
        sys.path.insert(0, path)

from corpus_source import from_documents  # noqa: E402
from domain_retrieval import VocabularyProfile  # noqa: E402
from domain_router import (  # noqa: E402
    DECISIVE_MARGIN,
    MINIMUM_SCORE,
    DomainScore,
    route,
    score_domain,
)
from generic_domain_pack import GenericDomainPack  # noqa: E402

DOMAINS = ROOT / "domains"
BENCHMARK = ROOT / "templates" / "benchmark" / "cross_domain_routing_v0.1.json"


def _pack(domain_id: str, docs: list[dict], **policy) -> GenericDomainPack:
    pack = GenericDomainPack({"domain_id": domain_id, "version": "0.0.1", **policy})
    pack.load(from_documents(docs))
    return pack


def _doc(doc_id: str, title: str, text: str) -> dict:
    return {"document_id": doc_id, "revision_id": "REV-A", "title": title,
            "doc_type": "test_document", "text": text}


# One incident report, filed under two document numbers in two domains -- which
# is a thing that happens, and is the limiting case of ambiguity: the corpora
# are word-for-word inseparable, so the margin between them is exactly zero and
# the fixture cannot drift as prose is edited.
#
# An earlier version of this fixture wrote two *similar* corpora by hand and
# landed at a margin of 0.064 -- outside the 0.05 band, so it asserted
# ambiguity on text that was not ambiguous. Testing a threshold with prose
# tuned by eye measures the prose.
OVERLAP_TITLE = "Cell venting incident"
OVERLAP_BODY = (
    "The cell vented during the abuse sequence after the venting temperature "
    "was exceeded. Venting released electrolyte into the enclosure."
)
OVERLAP_A = [_doc("DOC-A-1", OVERLAP_TITLE, OVERLAP_BODY)]
OVERLAP_B = [_doc("DOC-B-1", OVERLAP_TITLE, OVERLAP_BODY)]


@pytest.fixture(scope="module")
def example_packs():
    from run_domain import load_all

    packs = load_all(examples=True)
    if len(packs) < 2:
        pytest.skip("routing needs at least two loaded domains")
    return packs


class TestThreeOutcomes:
    def test_names_the_domain_whose_corpus_is_about_the_question(self, example_packs):
        routing = route(example_packs, "What was the CELL-A3 capacity fade after 800 cycles?")
        assert routing.domain == "BATTERY"
        assert routing.requires_human is False
        assert routing.decision is not None
        assert routing.decision.workflow_id == "BATTERY-QA"

    def test_refuses_when_no_loaded_domain_covers_the_question(self, example_packs):
        routing = route(example_packs, "How long must concrete cure before formwork is struck?")
        assert routing.domain is None
        assert routing.decision is None
        assert "no loaded domain covers" in routing.reason

    def test_asks_for_a_person_when_two_domains_cannot_be_separated(self):
        packs = {"a": _pack("ALPHA", OVERLAP_A), "b": _pack("BETA", OVERLAP_B)}
        routing = route(packs, "What venting temperature did the cell reach when it vented?")
        top, second = routing.scores[0], routing.scores[1]
        assert abs(top.score - second.score) < DECISIVE_MARGIN, (
            "the two corpora were built to be inseparable; if this fails the "
            "fixture no longer tests ambiguity"
        )
        assert routing.requires_human is True
        assert routing.domain == top.domain, "the best domain is still named, not discarded"
        assert routing.decision.risk_level == "medium"
        assert routing.decision.difficulty == "ambiguous"
        assert "are within" in routing.reason

    def test_requires_human_is_reachable_only_through_a_decision(self):
        """A refusal is not a referral. Nothing should be able to report both."""
        packs = {"a": _pack("ALPHA", OVERLAP_A), "b": _pack("BETA", OVERLAP_B)}
        refusal = route(packs, "How is a hydraulic accumulator pre-charge pressure set?")
        assert refusal.domain is None and refusal.requires_human is False


class TestScoringIsComparableAcrossCorpora:
    def test_a_larger_corpus_does_not_win_on_size(self):
        """The bias that cost four of six out-of-scope questions.

        The large corpus here is about none of the question and knows five of
        its seven terms by accident, scattered one apiece across forty notes.
        The small one is about the question and knows three. On vocabulary the
        large corpus wins, which is exactly how RE -- 108 fragments against
        everyone else's nine -- took four out-of-scope questions it had no
        documents for. On the scored signal it must lose.
        """
        small = _pack("SMALL", [
            _doc("D-1", "Widget torque study", "Widget torque was recorded at 12 units."),
        ])
        large = _pack("LARGE", [
            _doc("P-0", "Scheduling note", "A widget was moved between bays on Tuesday."),
            _doc("P-1", "Staffing note", "Torque wrenches were issued to the day shift."),
            _doc("P-2", "Facilities note", "Rig 7 maintenance is scheduled quarterly."),
        ] + [
            _doc(f"P-{i}", "Meeting minutes",
                 f"Item {i} concerns budget, staffing and calibration intervals.")
            for i in range(3, 40)
        ])
        query = "What widget torque was recorded on rig 7 after calibration?"
        assert score_domain(large, query).vocabulary > score_domain(small, query).vocabulary, (
            "the fixture no longer reproduces the size bias it exists to catch"
        )
        assert score_domain(small, query).score > score_domain(large, query).score

    def test_the_pack_that_tokenizes_an_identifier_correctly_wins_it(self, example_packs):
        """The second bias, and the more surprising one.

        Firmware keeps `fw-4.1.3` whole; RE shatters it into `fw`, `4`, `1`,
        `3` and its larger corpus contains those bare numbers, so on vocabulary
        RE beat firmware on a firmware question -- the pack that handled the
        text correctly lost *because* it did.
        """
        query = "Which build superseded FW-4.1.3 and what did it change?"
        scores = {s.domain: s for s in
                  (score_domain(p, query) for p in example_packs.values())}
        assert scores["FIRMWARE"].concentration > scores["RE"].concentration
        assert max(scores.values(), key=lambda s: s.score).domain == "FIRMWARE"

    def test_an_empty_question_scores_zero_rather_than_dividing_by_zero(self, example_packs):
        for pack in example_packs.values():
            score = score_domain(pack, "the and of is")
            assert score.score == 0.0
            assert score.profile.terms == 0


class TestTheMarginItself:
    """Where referral starts, pinned without a corpus.

    The corpus tests prove the referral path is reachable through a real pack.
    These pin the arithmetic: a fixture built from prose can only ever assert
    that some text happened to land inside the band.
    """

    @staticmethod
    def _stub(domain_id: str, share: float):
        class Stub:
            pass

        stub = Stub()
        stub.domain_id = domain_id
        stub.vocabulary_profile = lambda query, s=share: VocabularyProfile(1.0, s, s, 3)
        return stub

    def test_just_inside_the_margin_refers(self):
        # scores are share exactly, since 0.6*s + 0.4*s == s
        packs = {"a": self._stub("A", 0.60), "b": self._stub("B", 0.60 - 0.049)}
        routing = route(packs, "q")
        assert routing.requires_human is True
        assert routing.domain == "A"

    def test_just_outside_the_margin_decides(self):
        packs = {"a": self._stub("A", 0.60), "b": self._stub("B", 0.60 - 0.051)}
        routing = route(packs, "q")
        assert routing.requires_human is False
        assert routing.domain == "A"

    def test_the_margin_is_measured_against_the_runner_up_not_the_field(self):
        """Three domains, two of them far behind, must not force a referral."""
        packs = {"a": self._stub("A", 0.60), "b": self._stub("B", 0.20),
                 "c": self._stub("C", 0.19)}
        routing = route(packs, "q")
        assert routing.domain == "A" and routing.requires_human is False


class TestEdges:
    def test_no_loaded_domains_is_a_refusal_not_a_crash(self):
        routing = route({}, "anything at all")
        assert routing.domain is None and routing.scores == ()
        assert routing.reason == "no domains are loaded"

    def test_a_single_domain_is_never_ambiguous(self):
        packs = {"a": _pack("ALPHA", OVERLAP_A)}
        routing = route(packs, "What venting temperature did the cell reach?")
        assert routing.domain == "ALPHA"
        assert routing.requires_human is False

    def test_thresholds_are_arguments_not_hardcoded(self, example_packs):
        query = "What was the CELL-A3 capacity fade after 800 cycles?"
        assert route(example_packs, query, minimum_score=0.99).domain is None
        assert route(example_packs, query, decisive_margin=1.0).requires_human is True

    def test_as_dict_is_json_serializable(self, example_packs):
        routing = route(example_packs, "What caused the LOT-2291 solder defects?")
        json.dumps(routing.as_dict())
        assert routing.as_dict()["scores"][0]["domain"] == routing.domain


class TestVocabularyProfileIsThePublicSurface:
    def test_routing_uses_no_private_attribute_of_a_pack(self):
        """A pack that is not a GenericDomainPack must still be routable.

        The protocol says routing needs `domain_id` and `vocabulary_profile`.
        An earlier draft declared exactly that and then reached through
        `pack._ignore` and `pack._index`, which would have made this object
        crash. It is the test, not the docstring, that keeps the claim true.
        """

        class Minimal:
            domain_id = "MINIMAL"

            def vocabulary_profile(self, query: str) -> VocabularyProfile:
                return VocabularyProfile(1.0, 0.9, 0.9, 3)

        routing = route({"m": Minimal()}, "anything")
        assert routing.domain == "MINIMAL"
        assert routing.scores[0].score == pytest.approx(0.6 * 0.9 + 0.4 * 0.9)

    def test_profile_numbers_stay_within_their_range(self, example_packs):
        for pack in example_packs.values():
            profile = pack.vocabulary_profile("junction temperature at 18 W on DUT-4")
            assert 0.0 <= profile.known_fraction <= 1.0
            assert 0.0 <= profile.document_share <= 1.0
            assert 0.0 <= profile.best_coverage <= 1.0

    def test_document_share_reflects_what_a_corpus_is_about(self):
        about = _pack("ABOUT", [
            _doc("D-1", "Torque study", "Torque was measured. Torque drifted."),
            _doc("D-2", "Torque review", "Torque again. Torque throughout."),
        ])
        passing = _pack("PASSING", [
            _doc("D-1", "Scheduling note", "Torque is mentioned once here."),
            _doc("D-2", "Staffing note", "This note is about staffing only."),
        ])
        query = "What torque was recorded?"
        assert (score_domain(about, query).concentration
                > score_domain(passing, query).concentration)


class TestBenchmarkIntegrity:
    """The benchmark is an artefact that can be wrong, and was."""

    @pytest.fixture(scope="class")
    @classmethod
    def benchmark(cls):
        return json.loads(BENCHMARK.read_text(encoding="utf-8"))

    def test_every_expected_domain_is_a_loaded_domain_or_none(self, benchmark, example_packs):
        loaded = {p.domain_id for p in example_packs.values()}
        for case in benchmark["cases"]:
            want = case["expected_domain"]
            assert want is None or want in loaded, f"{case['case_id']} names {want!r}"

    def test_case_ids_are_unique(self, benchmark):
        ids = [c["case_id"] for c in benchmark["cases"]]
        assert len(ids) == len(set(ids))

    def test_out_of_scope_cases_expect_no_domain(self, benchmark):
        for case in benchmark["cases"]:
            if case["band"] == "out_of_scope":
                assert case["expected_domain"] is None

    def test_the_removed_ambiguous_band_is_recorded_not_erased(self, benchmark):
        """Correcting a label silently is indistinguishable from tuning one."""
        removed = benchmark.get("removed_band")
        assert removed and removed["band"] == "ambiguous"
        assert set(removed["cases"]) == {"RT-031", "RT-032"}
        assert not any(c["band"] == "ambiguous" for c in benchmark["cases"])
        for case_id in removed["cases"]:
            case = next(c for c in benchmark["cases"] if c["case_id"] == case_id)
            assert case["expected_domain"] is not None

    def test_the_relabelled_cases_route_to_their_new_labels(self, benchmark, example_packs):
        """The relabelling has to be right, not merely recorded."""
        for case_id, want in (("RT-031", "BATTERY"), ("RT-032", "MANUFACTURING")):
            case = next(c for c in benchmark["cases"] if c["case_id"] == case_id)
            assert case["expected_domain"] == want
            routing = route(example_packs, case["query"])
            assert routing.domain == want and not routing.requires_human


class TestMeasuredAcceptance:
    """The shipped figures, re-derived here rather than quoted from a docstring.

    `scripts/routing_benchmark.py` prints them and exits non-zero below target;
    these assert the same thing in the suite, so a regression fails a test run
    rather than waiting for someone to run the script.
    """

    @staticmethod
    def _measure():
        import routing_benchmark
        from run_domain import load_all

        packs = load_all(examples=True)
        cases = json.loads(BENCHMARK.read_text(encoding="utf-8"))["cases"]
        return [(c, routing_benchmark.judge(c, route(packs, c["query"]))[0]) for c in cases]

    def test_routing_meets_its_acceptance_targets(self):
        results = self._measure()
        rate = sum(ok for _, ok in results) / len(results)
        assert rate >= 0.9, f"routing fell to {rate:.3f}"

    def test_out_of_scope_refusal_is_perfect(self):
        """The one band held to 1.0.

        Missing an in-scope question produces a refusal or a referral, which a
        reader sees. Naming a domain for a question no corpus covers produces a
        confident answer from the wrong documents, which nobody sees.
        """
        misses = [c["case_id"] for c, ok in self._measure()
                  if c["band"] == "out_of_scope" and not ok]
        assert not misses, f"out-of-scope questions routed to a domain: {misses}"

    def test_minimum_score_is_the_constant_the_measurement_supports(self):
        """A threshold nobody can re-derive is a magic number."""
        assert MINIMUM_SCORE == 0.15
        assert 0.102 < MINIMUM_SCORE < 0.191, (
            "MINIMUM_SCORE must sit between the highest out-of-scope score and "
            "the lowest in-scope one; re-measure before moving it"
        )
