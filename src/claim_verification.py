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

    def as_dict(self) -> dict[str, Any]:
        return {
            "cited_evidence": list(self.cited_evidence),
            "grounding": round(self.grounding, 4),
            "grounded": self.grounded,
            "unsupported_terms": list(self.unsupported_terms),
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

    def as_dict(self) -> dict[str, Any]:
        return {
            "grounding_floor": self.grounding_floor,
            "claims": {v.claim_id: v.as_dict() for v in self.verdicts},
            "all_grounded": self.all_grounded,
            "ungrounded_claim_ids": list(self.ungrounded_claim_ids),
        }


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

    def verify(
        self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate]
    ) -> VerificationReport:
        by_id = {item.evidence_id: item for item in evidence}
        verdicts: list[ClaimVerdict] = []
        for claim in claims:
            cited = [by_id[eid] for eid in claim.evidence_ids if eid in by_id]
            terms = self._informative(claim.statement)

            supplied: set[str] = set()
            for item in cited:
                supplied |= set(self._tokenize(item.text))
                # The title carries what the document *is*, which is often the
                # part of a claim the body never restates. Retrieval indexes it
                # for the same reason.
                title = item.metadata.get("title") if item.metadata else None
                if title:
                    supplied |= set(self._tokenize(str(title)))

            unsupported = tuple(t for t in terms if t not in supplied)
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
                )
            )
        return VerificationReport(verdicts=tuple(verdicts), grounding_floor=self._floor)
