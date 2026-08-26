"""Which domain should answer this question -- or none, or a person.

`interfaces.RouteDecision` has existed since the kernel was written and nothing
ever constructed one. That makes four declared-and-unimplemented items this
codebase has turned up: the audit evidence contract (D-09), three retrieval
modes and a reranker (D-12), a gating mechanism described in a docstring after
its deletion (the 2026-08-26 audit), and routing. The pattern is consistent
enough to be worth naming: an interface is not a capability.

Routing matters the moment more than one Domain Pack is loaded, which is now.
Six domains share one engine, and a question about battery cycle life must not
be answered from a thermal corpus that happens to discuss temperature.

**The signal.** Each domain reports a `VocabularyProfile`: how much of the
question's informative vocabulary its corpus contains at all, how strongly it
is *about* those terms, and how much of the question its single best fragment
covers. Raw retrieval scores are deliberately *not* used -- each pack
normalizes BM25 against its own corpus maximum, so the top hit in every corpus
scores 1.0 and the number says nothing across domains. Comparing them would
have produced a router that looked confident and chose arbitrarily.

**Three outcomes, not one.** A router that always names a domain is a router
that is wrong silently. This one refuses when no domain's vocabulary covers the
question, and asks for a person when two domains are too close to separate --
which is the HOTL path the kernel already has, finally reachable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from domain_retrieval import VocabularyProfile
from interfaces import RouteDecision


class RoutablePack(Protocol):
    """Everything routing needs from a domain, and nothing else.

    Deliberately not `GenericDomainPack`: the router has no business knowing
    how a pack indexes text. An earlier draft declared this same two-member
    protocol and then reached through `pack._ignore` and `pack._index` anyway,
    which would have made it the fifth interface in this codebase that
    describes something other than what the code does.
    """

    domain_id: str

    def vocabulary_profile(self, query: str) -> VocabularyProfile: ...


@dataclass(frozen=True)
class DomainScore:
    domain: str
    profile: VocabularyProfile

    @property
    def vocabulary(self) -> float:
        return self.profile.known_fraction

    @property
    def concentration(self) -> float:
        return self.profile.document_share

    @property
    def coverage(self) -> float:
        return self.profile.best_coverage

    @property
    def score(self) -> float:
        """Concentration leads; coverage confirms. Vocabulary is reported but
        deliberately not scored.

        Vocabulary -- the share of a question's terms the corpus contains at
        all -- is the obvious signal and it is biased twice over.

        It scales with corpus size: RE, with 108 fragments against everyone
        else's nine, won four of six out-of-scope routing questions on
        vocabulary alone, because a larger corpus contains more ordinary
        English by accident.

        And it rewards *worse* tokenization. Asked "which build superseded
        FW-4.1.3", the firmware pack keeps `fw-4.1.3` as one token, as it
        should; RE shatters it into `fw`, `4`, `1`, `3`, and its corpus happens
        to contain those bare numbers, so RE scored 0.57 against firmware's
        0.33 and won a firmware question. The domain handling the text
        correctly lost *because* it handled it correctly.

        Concentration -- the mean share of a corpus's fragments that mention
        each query term -- has neither bias. On that same question firmware
        leads RE by four times. Measured over the routing benchmark it also
        ranks better: 23 of 24 in-scope questions against vocabulary's 22.
        """
        return 0.6 * self.concentration + 0.4 * self.coverage

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "vocabulary": round(self.vocabulary, 4),
            "coverage": round(self.coverage, 4),
            "concentration": round(self.concentration, 4),
            "score": round(self.score, 4),
        }


@dataclass(frozen=True)
class Routing:
    decision: RouteDecision | None
    scores: tuple[DomainScore, ...]
    reason: str

    @property
    def domain(self) -> str | None:
        return self.decision.domain if self.decision else None

    @property
    def requires_human(self) -> bool:
        return bool(self.decision and self.decision.requires_human)

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "requires_human": self.requires_human,
            "reason": self.reason,
            "scores": [s.as_dict() for s in self.scores],
        }


#: Below this, no loaded domain is about the question and the honest answer is
#: that nothing here can answer it.
#:
#: Measured over the cross-domain routing benchmark with the concentration-led
#: score: out-of-scope questions -- boiler feedwater, concrete curing, fibre
#: bend radius -- peak at 0.102, and in-scope ones sit at 0.191 and above with
#: one exception. 0.15 leaves margin on both sides rather than sitting on
#: either boundary.
#:
#: The exception is real and not designed around: "which interface material
#: tolerates the larger gap variation" is a thermal question scoring 0.075,
#: because it names nothing thermal-specific -- no unit, no identifier, no
#: term the thermal corpus is about. No floor separates that from a question
#: about boiler feedwater, and none is claimed to. It is refused, which is the
#: better of the two available errors: a refusal is visible, a confident answer
#: from the wrong corpus is not.
MINIMUM_SCORE = 0.15

#: How far ahead the winner must be before it is picked without a person.
#:
#: Below this the two domains are not separable, and guessing between them is
#: worse than saying so. The kernel has had a `requires_human` path since it
#: was written; this is the first thing that reaches it.
#:
#: Scaled to the concentration-led score, whose in-scope range runs roughly
#: 0.08 to 0.50. One benchmark question lands inside it and is referred rather
#: than answered: "which build superseded FW-4.1.3" (firmware 0.19, RE 0.15,
#: because RE's larger corpus half-matches the shattered identifier). The
#: referral is not wrong -- firmware is named first -- but a router that
#: answered on a 0.04 margin would be guessing.
#:
#: No *benchmark* case is labelled ambiguous, because the six example corpora
#: are subject-disjoint and no genuinely ambiguous question exists over them;
#: `cross_domain_routing_v0.1.json` records the two cases that were wrongly
#: labelled so. The margin is exercised instead by `tests/test_domain_router.py`
#: over two corpora built to overlap on purpose.
DECISIVE_MARGIN = 0.05


def score_domain(pack: RoutablePack, query: str) -> DomainScore:
    return DomainScore(pack.domain_id, pack.vocabulary_profile(query))


def route(
    packs: Mapping[str, RoutablePack],
    query: str,
    *,
    minimum_score: float = MINIMUM_SCORE,
    decisive_margin: float = DECISIVE_MARGIN,
) -> Routing:
    """Pick a domain, refuse, or ask for a person."""
    scores = tuple(sorted(
        (score_domain(pack, query) for pack in packs.values()),
        key=lambda s: s.score, reverse=True,
    ))
    if not scores:
        return Routing(None, (), "no domains are loaded")

    best = scores[0]
    if best.score < minimum_score:
        return Routing(
            None, scores,
            f"no loaded domain covers this question (best {best.domain}: "
            f"concentration {best.concentration:.3f}, score {best.score:.2f})",
        )

    runner_up = scores[1] if len(scores) > 1 else None
    ambiguous = runner_up is not None and (best.score - runner_up.score) < decisive_margin
    reason = (
        f"{best.domain} and {runner_up.domain} are within {decisive_margin} "
        f"({best.score:.2f} vs {runner_up.score:.2f})"
        if ambiguous else
        f"{best.domain} at {best.score:.2f}"
        + (f", next {runner_up.domain} at {runner_up.score:.2f}" if runner_up else "")
    )
    return Routing(
        RouteDecision(
            domain=best.domain,
            intent="engineering_question",
            difficulty="ambiguous" if ambiguous else "routine",
            risk_level="medium" if ambiguous else "low",
            workflow_id=f"{best.domain}-QA",
            retrieval_modes=("hybrid",),
            requires_human=ambiguous,
        ),
        scores,
        reason,
    )
