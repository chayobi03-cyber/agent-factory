"""Claim-evidence verification: does the cited evidence actually support the
claim, or merely exist?

This is a *kernel* capability, not an RE one. ARCHITECTURE_REFACTOR_PLAN
2026-08-19 lists "Evidence + Claim verification" as a shared-kernel concern
(goal 1) and puts it directly after hybrid retrieval in the implementation
sequence. Nothing here knows what a radiated emission is: a Domain Pack
supplies its own tokenizer and its own threshold, and the mechanism is the
same for any domain.

**The hole this closes.** `CERGateRuntime.evaluate` treated a claim as
supported when at least one cited evidence id *exists*. Existence is not
support. A claim could cite a real fragment with almost no lexical
relationship to what it asserts and still reach PASS, in a system whose
entire purpose is that answers are grounded in evidence. Meanwhile
`domains/re/domain_pack.yaml` has declared `require_evidence_for_claims:
true` and `abstain_when_evidence_insufficient: true` the whole time, with
nothing enforcing either -- the same declared-but-unimplemented pattern
OPEN_DECISIONS D-09 found in the audit evidence contract.

**What this deliberately does not claim to do.** It does not decide the
near-miss abstention case of OPEN_DECISIONS D-11. That was measured, not
assumed: five verification-side statistics were scored on separating the 139
answerable benchmark cases from the near-miss ones, and the best of them
costs 29 answerable cases to catch all five. Lexical verification is no more
able to tell "the corpus lacks this subject" from "the question is phrased
differently" than lexical retrieval was. D-11's option C is therefore *not*
the fix for that class, and the register says so.

What it does contribute to D-11 is a partial catch as a side effect, and
something more useful than the catch: `unsupported_terms` names exactly which
parts of a question the cited evidence never mentions. When the threshold
cannot decide, that list is what puts a near-miss in front of a reviewer --
turning D-11's "a human catching it" from a hope into an output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from interfaces import Claim, EvidenceCandidate

Tokenizer = Callable[[str], Sequence[str]]


@dataclass(frozen=True)
class ClaimVerdict:
    claim_id: str
    cited_evidence: tuple[str, ...]
    grounding: float
    grounded: bool
    unsupported_terms: tuple[str, ...]
    #: Documents cited at two or more revisions at once, as
    #: (document_id, (revision_id, ...)). A retest and the test it supersedes
    #: answer the same question differently, and a reader shown one of them
    #: cannot tell that the other exists.
    conflicting_revisions: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "cited_evidence": list(self.cited_evidence),
            "grounding": round(self.grounding, 4),
            "grounded": self.grounded,
            "unsupported_terms": list(self.unsupported_terms),
            "conflicting_revisions": [
                {"document_id": d, "revisions": list(r)} for d, r in self.conflicting_revisions
            ],
        }


@dataclass(frozen=True)
class VerificationReport:
    verdicts: tuple[ClaimVerdict, ...]
    grounding_floor: float

    @property
    def all_grounded(self) -> bool:
        # An empty claim set is not "all grounded". Nothing was checked, and a
        # verifier that returns True for having done no work is the failure
        # mode this module exists to prevent.
        return bool(self.verdicts) and all(v.grounded for v in self.verdicts)

    @property
    def ungrounded_claim_ids(self) -> tuple[str, ...]:
        return tuple(v.claim_id for v in self.verdicts if not v.grounded)

    @property
    def conflicting_revision_claim_ids(self) -> tuple[str, ...]:
        return tuple(v.claim_id for v in self.verdicts if v.conflicting_revisions)

    def as_dict(self) -> dict[str, Any]:
        return {
            "grounding_floor": self.grounding_floor,
            "claims": {v.claim_id: v.as_dict() for v in self.verdicts},
            "all_grounded": self.all_grounded,
            "ungrounded_claim_ids": list(self.ungrounded_claim_ids),
            "conflicting_revision_claim_ids": list(self.conflicting_revision_claim_ids),
        }


def _conflicting_revisions(
    cited: "Sequence[EvidenceCandidate]",
    retrieved: "Sequence[EvidenceCandidate]",
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Documents cited at more than one revision in the same answer.

    This is a narrow claim, made narrow on purpose. It does not detect
    contradiction in general -- two documents asserting incompatible things is
    a semantic judgement that no lexical method here can make, and
    OPEN_DECISIONS D-11 records why. What it does detect is the case that is
    decidable from the citation list alone: the same report cited at a revision
    *and* its retest.

    That case is not hypothetical. Asked what EUT-7 measured at 132 MHz, the
    corpus answers 38.2 dBuV/m (REV-A, over the limit) and 31.4 dBuV/m (REV-B,
    under it after mitigation). Both are true of their moment, they answer the
    question oppositely, and nothing in a citation list marks which one is
    current. A person has to say which applies, which is what REVIEW is for.

    Two fragments of the *same* revision are not a conflict -- that is an
    answer drawn from two paragraphs, which is the normal case.

    The other revision counts whether or not it was *cited*. Scoped to the
    citations alone this missed its own headline example: asked what EUT-7
    measured at 132 MHz, retrieval returns 38.2 dBuV/m from REV-A and 31.4
    dBuV/m from REV-B, but REV-B contributes no term REV-A had not already
    supplied, so the citation selector correctly drops it and the conflict
    disappeared with it. A retest that disagrees in *numbers* while agreeing in
    *words* is invisible to any lexical selector -- which is the whole reason
    this check exists, so it reads the retrieved set instead.
    """
    cited_revisions: dict[str, set[str]] = {}
    for item in cited:
        cited_revisions.setdefault(item.document_id, set()).add(item.revision_id)
    available: dict[str, set[str]] = {}
    for item in retrieved:
        if item.document_id in cited_revisions:
            available.setdefault(item.document_id, set()).add(item.revision_id)
    return tuple(
        (document_id, tuple(sorted(revisions)))
        for document_id, revisions in sorted(available.items())
        if len(revisions) > 1
    )


class ClaimVerifier:
    """Scores how much of a claim's vocabulary the evidence it cites supplies.

    `grounding_floor` is domain-supplied and corpus-fitted; it belongs in the
    Domain Pack policy, not here. The kernel owns the mechanism and has no
    defensible opinion about the number.
    """

    def __init__(
        self,
        tokenize: Tokenizer,
        *,
        grounding_floor: float,
        ignore_terms: Iterable[str] = (),
    ) -> None:
        self._tokenize = tokenize
        self._floor = float(grounding_floor)
        self._ignore = frozenset(ignore_terms)

    @property
    def grounding_floor(self) -> float:
        return self._floor

    def _informative(self, text: str) -> list[str]:
        return [t for t in dict.fromkeys(self._tokenize(text)) if t not in self._ignore]

    def select_citations(
        self, statement: str, evidence: Sequence[EvidenceCandidate]
    ) -> list[EvidenceCandidate]:
        """Which of the retrieved fragments the claim should actually cite.

        Both callers used to cite `evidence[0]` and nothing else, so a claim
        needing two fragments could not be grounded however well retrieval had
        done. Asked what the EUT-7 level was *before mitigation and how far
        above the limit*, the pack retrieved the before-figure at rank 1 and
        the mitigation at ranks 2 and 3, cited only rank 1, and then reported
        `mitigation` as unsupported -- by evidence it was holding.

        Nor is the answer to cite all ten. A citation that supports nothing is
        padding, and it inflates grounding without adding support: the fix for
        an under-cited claim must not be an over-cited one.

        So this is a greedy set cover over the claim's informative terms.
        Fragments are considered in rank order and kept only when they supply a
        term no kept fragment supplied, which stops as soon as the evidence
        stops adding anything. Rank 1 is always kept when there is any evidence
        at all -- it is what the answer is drawn from, whether or not it
        happens to widen the cover.
        """
        if not evidence:
            return []
        wanted = set(self._informative(statement))
        kept = [evidence[0]]
        covered = self._supplied(evidence[0])
        for item in evidence[1:]:
            supplies = self._supplied(item)
            if wanted & supplies - covered:
                kept.append(item)
                covered |= supplies
        return kept

    def _supplied(self, item: EvidenceCandidate) -> set[str]:
        """Every term a fragment puts on the table, body and title alike."""
        supplied = set(self._tokenize(item.text))
        title = item.metadata.get("title") if item.metadata else None
        if title:
            supplied |= set(self._tokenize(str(title)))
        return supplied

    def verify(
        self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate]
    ) -> VerificationReport:
        by_id = {item.evidence_id: item for item in evidence}
        verdicts: list[ClaimVerdict] = []
        for claim in claims:
            cited = [by_id[eid] for eid in claim.evidence_ids if eid in by_id]
            terms = self._informative(claim.statement)

            # The title carries what the document *is*, which is often the part
            # of a claim the body never restates. Retrieval indexes it for the
            # same reason, and `select_citations` reads it through the same
            # helper so the two cannot drift.
            supplied: set[str] = set()
            for item in cited:
                supplied |= self._supplied(item)

            unsupported = tuple(t for t in terms if t not in supplied)
            conflicting = _conflicting_revisions(cited, evidence)
            grounding = (len(terms) - len(unsupported)) / len(terms) if terms else 0.0
            # No evidence is never grounded, whatever the arithmetic says: with
            # no cited text `terms` is entirely unsupported, but a claim with no
            # informative terms at all would otherwise score 0.0 and be judged
            # against the floor rather than rejected outright.
            grounded = bool(cited) and bool(terms) and grounding >= self._floor
            verdicts.append(
                ClaimVerdict(
                    claim_id=claim.claim_id,
                    cited_evidence=tuple(item.evidence_id for item in cited),
                    grounding=grounding,
                    grounded=grounded,
                    unsupported_terms=unsupported,
                    conflicting_revisions=conflicting,
                )
            )
        return VerificationReport(verdicts=tuple(verdicts), grounding_floor=self._floor)
