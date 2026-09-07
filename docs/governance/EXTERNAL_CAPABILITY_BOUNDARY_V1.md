# External Capability Boundary V1

**Status:** Canonical boundary contract
**Owner:** AgentFactory
**Origin:** Salvaged from the APF Living Specification vNext 0.1 audit
(`11_Audit/APF_LIVING_SPEC_VNEXT_AUDIT_2026-08-30.md`, §5). That package was
rejected as a specification; this was the one normative statement in it the
trunk did not already have in some form.

## 1. Why this exists

`AGENT_FACTORY_SCOPE_V1.md` fixes the *domain* boundary — what subject matter
is ours — and §7 forbids importing another repository's governance. Neither it
nor any other canonical document says anything about **external engineering
capabilities**: agent runtimes, durable workflow engines, telemetry backends,
tool-calling protocols.

That silence is a real gap. Agent runtime, durable execution, and observability
are mature elsewhere, and a kernel that drifts into reimplementing them spends
its budget on solved problems. The imported package was right about that much.

## 2. The rule it got wrong

The imported package's stance was *borrow the mature capability, adapt via
contract, do not reimplement.* Applied here without qualification that rule is
wrong, because this repository has a constraint the package could not see.

`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` requires a run to be re-derivable from
the commit it names. `OPEN_DECISIONS` D-12 ruled out reaching a hosted model API
for exactly this reason, and `tests/test_no_hosted_model_dependency.py` asserts
the property at AST level: nothing under `src/` or `scripts/` performs network
access at all. A GREEN decision citing a SHA stops being reproducible from that
SHA the moment the run depends on a remote service's state.

So "borrow it" and "keep the evidence chain" are in direct tension for any
capability that lives across a network boundary.

## 3. The boundary

The discriminator is not maturity. It is **whether the capability can run
in-process and deterministically inside the commit under test.**

| Capability class | Stance |
|---|---|
| Runs in-process, deterministic, pinned by the commit | **Borrow.** A dependency is cheaper than an implementation. |
| Requires a network service, external clock, or state outside the commit | **Contract, do not adopt into the governed path.** Express the need as a kernel contract; if an adapter exists it runs outside the evidence chain, or the chain is renegotiated first by explicit decision. |
| Neither — the semantics are ours | **Own it.** Evidence, claim, CER gate, HOTL decision, Domain Pack boundary. |

The third row is small on purpose, and it is the only row where writing code is
the default answer.

## 4. Current position per capability

Recorded as of `8236dfa`, so a later reader can see whether this drifted.

| Capability | Mature external option | What the kernel does today | Stance |
|---|---|---|---|
| Agent runtime / tool calling | OpenAI Agents SDK, LangGraph | `src/interfaces.py` Protocols (`LLMProvider`, `Retriever`, `Verifier`, `Evaluator`); no agent framework, no network | Contract. The Protocol *is* the adapter seam; adopting a runtime is a D-12 question, not a free choice. |
| Durable execution | Temporal, LangGraph checkpointers | Session layer only: RC-01..RC-08 resume over git SHA + state file, fail-closed. **`WorkflowRunState` is an in-memory dict with no persistence path** — see D-17. | Contract, and the gap is open. |
| Telemetry / tracing | OpenTelemetry semconv | Execution evidence records with SHA-256 digests, verified by `scripts/evidence_gate.py` and `verify_artifact_sha256.py` | Own the evidence record; telemetry is additive and must never become required for the record to be readable. |
| Provenance model | W3C PROV | `provenance` as a nested field on evidence/claim schemas; no relational form — see D-16 | Adapt concepts if D-16 goes that way; do not import a vocabulary wholesale. |

## 5. What this contract forbids

1. Introducing a network-dependent capability into the governed execution path
   without first amending `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` by recorded
   decision. Convenience is not a reason.
2. Reimplementing a capability from row one of §3 — one that would run
   in-process and deterministically — because writing it felt faster than
   evaluating it.
3. Declaring an external standard "adopted" in a document without an adapter,
   a test, and a named consumer. That is the D-09 pattern, and this repository
   has now recorded it four times.

## 6. What it does not do

This contract does not rank the external systems, does not commit the project
to adopting any of them, and does not make the kernel's current minimal
implementations provisional. They are the deliberate consequence of §2.

Whether the kernel earns its place above these substrates at all is a separate
open question, recorded as **D-15**. This contract governs how that question
gets answered; it does not answer it.

## 7. Enforcement

Not machine-enforced today, and this section says so rather than implying
otherwise. The nearest executable guards are
`tests/test_no_hosted_model_dependency.py` (which enforces §3 row two for the
network case) and `scripts/evidence_gate.py`. A guard for §5.3 would need a
declared-adopted-standards list with named consumers; that is not written.
