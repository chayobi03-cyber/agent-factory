from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


@dataclass
class QueryRequest:
    query: str
    domain_hint: str | None = None
    report: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteDecision:
    domain: str
    intent: str
    difficulty: str
    risk_level: str
    workflow_id: str
    retrieval_modes: Sequence[str]
    requires_human: bool = False


@dataclass
class EvidenceCandidate:
    evidence_id: str
    document_id: str
    revision_id: str
    fragment_id: str
    score: float
    text: str
    metadata: dict[str, Any]


@dataclass
class Claim:
    claim_id: str
    statement: str
    claim_type: str
    evidence_ids: list[str]
    confidence: float = 0.0


@dataclass(frozen=True)
class CERSnapshot:
    policy_id: str
    policy_version: str
    snapshot_id: str
    snapshot_hash: str
    source_commit: str
    required_checks: Sequence[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_checks", tuple(self.required_checks))


@dataclass(frozen=True)
class CERDecision:
    decision_id: str
    result: str
    gate_id: str
    run_id: str
    human_required: bool = False
    snapshot_id: str = ""
    triggered_findings: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    decided_at: str = ""


class CERGate(Protocol):
    def evaluate(
        self,
        *,
        snapshot: CERSnapshot,
        run_id: str,
        gate_id: str,
        claims: Sequence[Claim],
        evidence: Sequence[EvidenceCandidate],
    ) -> CERDecision: ...


class DomainPack(Protocol):
    domain_id: str
    version: str

    def ingest(self, source: Any) -> Any: ...
    def parse(self, artifact: Any) -> Any: ...
    def normalize(self, artifact: Any) -> Any: ...
    def retrieve(self, query: str, **kwargs: Any) -> Sequence[EvidenceCandidate]: ...
    def verify(self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate], **kwargs: Any) -> dict[str, Any]: ...
    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]: ...
    def render_report(self, result: dict[str, Any], **kwargs: Any) -> Any: ...


class LLMProvider(Protocol):
    def generate(self, *, prompt: str, model_profile: str, **kwargs: Any) -> str: ...


class Retriever(Protocol):
    def retrieve(self, *, query: str, top_k: int, filters: dict[str, Any]) -> list[EvidenceCandidate]: ...


class Verifier(Protocol):
    def verify(self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate]) -> dict[str, Any]: ...


class Evaluator(Protocol):
    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]: ...
