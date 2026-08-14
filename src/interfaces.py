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

class LLMProvider(Protocol):
    def generate(self, *, prompt: str, model_profile: str, **kwargs: Any) -> str: ...

class Retriever(Protocol):
    def retrieve(self, *, query: str, top_k: int, filters: dict[str, Any]) -> list[EvidenceCandidate]: ...

class Verifier(Protocol):
    def verify(self, claims: Sequence[Claim], evidence: Sequence[EvidenceCandidate]) -> dict[str, Any]: ...

class Evaluator(Protocol):
    def evaluate(self, case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]: ...
