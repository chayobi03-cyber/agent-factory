# Cold Audit — APF Living Specification vNext 0.1

**Audit date:** 2026-08-30
**Repository:** `chayobi03-cyber/agent-factory`
**Branch under review:** `claude/audit-sgts3o`
**Repository baseline:** `8236dfa38a895d0b4f5c30c18671a468483a5cb9`
**Audited artifact:** `APF_Living_Spec_vNext_0.1.zip`
**Artifact SHA256:** `12346582bf486cf6fa7f3f64e6b39b318607dab2695f7d14232a2d44219a36e4`
**Artifact size:** 24 files, 368 lines total
**Method:** static review of the package, cross-checked against the live repository tree and a local run of the full test suite (322 passed, 12.00s).

Rating scale and evidence levels are those of `INTERNAL_AUDIT_RATING_MATRIX_2026-08-15.md`.

> **Corrections — 2026-08-31.** Two findings below were wrong on the facts and
> are corrected in place, marked `[CORRECTED 08-31]`. Both were found while
> landing the salvage in §7, and both changed the recommendation.
>
> 1. §7.5 proposed making RA-012's falsification test executable. **It already
>    is** — `tests/test_claim_verification.py:151-166` is exactly its case, and
>    green. RA-012 therefore leaves the salvage list; nothing needs building.
> 2. §2 credited RC-01..RC-08 as covering the package's Test 7 (durability).
>    That conflated two layers. Session resume is enforced; **run-layer
>    durability does not exist** — `WorkflowRunState` is an in-memory dict with
>    no persistence path. Test 7's failure condition is genuinely met, the one
>    place the rejected benchmark would have found something real. Recorded as
>    `OPEN_DECISIONS` D-17.
>
> The verdict is unchanged. Correction 1 strengthens it; correction 2 is the
> single point where the package was right and this audit was not.

---

## Verdict

**RED as a specification. AMBER as a position paper.**

The package does not fail because its thinking is wrong. Most of its boundary
reasoning is correct, and two or three of its items are genuinely sharp. It
fails because of what it *is*: 368 lines of declarations that nothing reads,
nothing validates, and nothing can fail against — dropped into a repository
that already implements a substantial share of what the package proposes to
one day investigate.

In this repository's own evidence scale, **the entire package is E0**
(documentation/claim only). Every one of its 24 files is E0. There is no E1,
no E2, no E3, no E4 anywhere in it. The kernel gate this project runs on
requires E3/E4. A document set that is uniformly E0 cannot be adopted as
specification here; it can only be adopted as input.

Three independent grounds, each sufficient on its own:

1. It is disconnected from the system it claims to specify (§1).
2. It marks as OPEN seven hypotheses for which this repository already holds
   evidence (§2).
3. It violates its own internal rules at a rate that would fail any of the
   contracts it proposes (§3).

---

## 1. The package does not know what it is specifying

`APF` appears **zero times** in this repository. Not in `src/`, `docs/`,
`schemas/`, `tests/`, or governance. The system is called Agent Factory; its
parts are the Factory Kernel, CER, Domain Pack, HOTL, Evidence Gate.

The package's `SOURCES.md` lists nine external URLs — W3C PROV, OpenTelemetry,
OpenAI Agents SDK, LangGraph, Temporal — and **zero internal artifacts**. It
cites five external frameworks and not one line of the codebase it is a
specification for. A specification that has read the competition but not the
product is a market survey.

This has a concrete governance consequence. `SOURCE_OF_TRUTH_MANIFEST.md` §7
records that `MATERIAL_DRIFT` was identified in the 2026-08-14 audit cycle and
**resolved** by declaring the live Git tree canonical and the numbered package
historical. This package arrives with its own `spec/`, `schemas/`, and
`decisions/` trees, overlapping repository vocabulary (evidence, validation,
decision, trace, provenance) under different names, with no path decision and
no migration record. Manifest §6 requires that "any migration from a historical
package into the current repository must be recorded as an explicit versioned
change." Adopting this package as-is re-opens exactly the drift §7 closed.

| Package schema | Collides with | Status |
|---|---|---|
| `schemas/claim.schema.yaml` | `schemas/claim_evidence.schema.yaml` | unreconciled, weaker |
| `schemas/asset.schema.yaml` | `templates/lesson`, `11_Audit/LSN-*.yaml` | unreconciled, unaware |
| `schemas/spec_change.schema.yaml` | governance ADR/closure docs | unreconciled |

The repository's `claim_evidence.schema.yaml` already carries `provenance`
(document/revision/fragment/page/locator/source_hash), a six-field
`verification` block, and a CER binding (policy_id, policy_version,
snapshot_id, run_id). The package's `claim.schema.yaml` has nine flat fields
and none of that. It is a strict downgrade of a schema already in the tree.

**Rating: RED.** Not a stylistic objection — an unreconciled second source of
truth is the specific defect this repository already paid to close.

---

## 2. Seven of eight hypotheses are marked OPEN against evidence already in the tree

`ARCHITECTURE_HYPOTHESIS_MATRIX.md` lists H1–H8, all `OPEN`, all with the
"Supporting evidence" column filled by category labels. Against the live tree:

| Hypothesis | Package status | What is already in this repository |
|---|---|---|
| H2 — executor replaceable without changing core semantics | OPEN | `src/interfaces.py` Protocols (`LLMProvider`, `Retriever`, `Verifier`, `Evaluator`, `CERGate`, `DomainPack`); `tests/test_no_hosted_model_dependency.py` enforces the boundary by AST inspection |
| H3 — evidence and provenance are distinct | OPEN | `provenance` is a structured field in `claim_evidence`, `engineering_evidence`, `optimization_benchmark` schemas |
| H4 — validation distinct from execution | OPEN | CER gate is a separate operation returning PASS/REVIEW/BLOCK; 455 CER references; `scripts/evidence_gate.py` |
| H5 — decision is a first-class state transition | OPEN | `HOTLReviewQueue` in `src/factory_runtime.py`; `schemas/human_decision.schema.yaml`; `BLOCKED` is fail-closed and terminal |
| H6 — domain semantics outside core runtime | OPEN, "3-domain portability test" | **six** declarative domain packs (re, thermal, battery, firmware, structural, manufacturing) + Domain Matrix E2E in CI |
| H7 — verified outcomes become reusable assets | OPEN | partially: `11_Audit/LSN-*.yaml` lessons carry claim/root-cause/candidate-change/validation-plan/status |
| H8 — APF adds value above telemetry/durability/agent runtime | OPEN | **genuinely open.** Correctly identified. |
| Test 7 — durability/resume | not started | **[CORRECTED 08-31]** Partly, and at the wrong layer. RC-01..RC-08 (22 tests, CI-enforced) is *session* resume. *Run* state is an in-memory dict with no persistence path — Test 7's failure condition is met. See D-17. |

Seven of eight hypotheses and at least four of eight benchmark tests have
material evidence sitting in the tree, unconsulted. The suite runs in **12
seconds**. The cost of checking was one command.

This is not a scoring quibble. A falsification programme that assigns `OPEN` to
a question its own repository has already partly answered will spend its budget
re-deriving what exists. `next_gate` in `STATUS.yaml` is
`multi-domain_executor_substitution_benchmark` — the repository ships
`src/synthetic_domain_matrix.py`, `scripts/domain_matrix_demo.py`,
`tests/test_domain_matrix_workflow.py`, and a Domain Matrix E2E CI job. The
declared next gate is, in substantial part, already built.

**Rating: RED.** The package's central instrument is miscalibrated against
observable state.

---

## 3. The package fails its own rules

Measured against the rules it sets for itself:

| # | Rule it states | Actual |
|---|---|---|
| 3.1 | `RA-INDEX` registers RA-001..RA-014 | Only RA-009..RA-014 exist as files. **8 of 14 (57%) are phantom entries** with a status column and no document. |
| 3.2 | `TRACEABILITY.md`: RA → Claim → Spec → Test → **EV-*** → **DEC-*** → Revision | Zero `EV-*` files, zero `DEC-*` files, no directory, no schema, no ID convention. **2 of 7 hops do not exist.** Decisions are actually named `ADR-00N` — a third, undeclared ID scheme. |
| 3.3 | Traceability should be followable | `FALSIFICATION_BENCHMARK.md` numbers tests "Test 1..8"; `TRACEABILITY.md` cites "TEST-05/06"; the matrix's Test column holds prose ("3-domain portability test"). **No crosswalk between H1–H8 and Test 1–8 exists anywhere.** The traceability model is not machine-checkable, which is the only thing traceability is for. |
| 3.4 | `LIFECYCLE.md`: mandatory fields for promoted assets — claim, evidence, counterexample, applicability, limitations, validation status, version, architecture impact | **6 of 6 existing RA files violate this.** All six are missing counterexamples, applicability, limitations, confidence, version, architecture_impact. Four are missing `claim`. They use an entirely different heading set (Finding / APF implication / External basis / Validation need). RA-014 does not even share that — it uses Strategic hypothesis / Proposed lifecycle. |
| 3.5 | `asset.schema.yaml` defines the asset record | It is a YAML sketch (`id: string`). No `$schema`, no `type`, no `required`, no validator, no consumer. It cannot reject the six non-conformant files above — which is why it did not. Contrast `schemas/execution_evidence.schema.json` in this repo: real Draft 2020-12, 13 required fields. **[CORRECTED 08-31]** — this originally read "validated in CI". The *records* are validated in CI, by `scripts/evidence_gate.py`, against a `REQUIRED` tuple the gate hardcodes; nothing loads the schema file. The two agreed by coincidence until `tests/test_schema_bindings.py` bound them on 08-31. The contrast with the package still holds — the schema is real and there is an enforcing consumer — but it was one binding weaker than stated. |
| 3.6 | `LIFECYCLE.md` defines a 5-tier evidence hierarchy | **No asset or claim records its tier.** `asset.schema.yaml` has `confidence: string` and no tier field. The hierarchy is undeclarable and therefore unused. The matrix's "supporting evidence" entries — "State/workflow systems", "multiple agent/tool systems", "plugin-style systems" — are category gestures that do not reach even tier 5 (expert inference), because no expert and no inference is attached. |
| 3.7 | 7-state lifecycle DISCOVERED→…→ARCHITECTURE_ADOPTED | The corpus occupies **one** state. 14/14 assets CANDIDATE, 8/8 hypotheses OPEN, 6/6 contracts CANDIDATE. Zero VALIDATING, zero VALIDATED. The words VALIDATED/VALIDATING appear only inside enum declarations. Six of seven states have never been used. |
| 3.8 | `SESSION_UPDATE_PROTOCOL.md` §7: "preserve historical status changes; do not silently rewrite the research trail" | No status-history file, field, or mechanism exists. The protocol is unimplementable as written. |
| 3.9 | A living specification | **Zero dates in 368 lines.** No owners. No per-file versions. The single CHANGELOG entry is undated. Nothing can be aged, expired, or reviewed. |
| 3.10 | `STATUS.yaml`: `auto_freeze_core: false`, `next_gate: …` | No consumer. Both keys appear exactly once each, in their own declaration. Nothing reads them. |
| 3.11 | External basis for boundary decisions | Nine URLs, **no access dates, no versions, no section anchors**. RA-011 rests a boundary decision on a 2025 blog post. Not re-verifiable at the granularity the claims require. |

### 3.12 The falsification benchmark is not falsifiable

This is the most serious item in §3, because falsifiability is the package's
stated reason to exist.

> Test 1 — Pass condition: "execution/evidence/validation/decision/trace
> contract still holds." Failure condition: "core model depends on
> agent-specific primitives."

No metric. No threshold. No dataset. No procedure. No observer-independence.
"Still holds" is adjudicated by whoever is reading. Test 5's pass condition —
"asset can influence planning/execution" — does not say what influence is or
how it is measured; Test 5's failure condition, "asset is merely retrieved text
with no operational effect," is its logical negation, so the pair partitions
nothing. Eight tests, eight pass/fail pairs, **zero measurable quantities.**

A benchmark whose outcome depends on the reader's judgement is a checklist. The
repository's actual benchmark — "M1 RE Hybrid RAG Benchmark, 15 cases" with
thresholds enforced in `factory-kernel.yml` — is what the difference looks like.

**Rating: RED.**

---

## 4. The pattern this repository has already named three times

From `tests/test_no_hosted_model_dependency.py`:

> "A decision recorded only in a document is the pattern this register has now
> caught three times: D-09 found a contract enforced by nothing, D-12 itself
> found three retrieval modes declared and absent, and the 2026-08-26 audit
> found a gating mechanism described in a docstring after its deletion. So the
> exclusion is asserted here rather than merely written down."

The package is that pattern, a fourth time and at full scale: seven contracts,
fourteen assets, eight hypotheses, eight tests, three schemas, a seven-state
lifecycle and a seven-hop traceability model — **enforced by nothing.**

It is also `LSN-0001` recurring almost verbatim. LSN-0001 records a separate
session that produced a plan to build FactoryRuntime, a workflow state machine,
CER gate enforcement, idempotency, and a run manifest from scratch — all of
which already existed, implemented and tested, on another branch; following it
would have meant rebuilding ~6,000 LOC. Root cause, as recorded:

> "Each session/agent instance re-derives its plan from whatever branch it
> happens to be pointed at, with no branch-identity check as a mandatory first
> step."

LSN-0001's mandatory first step — diff your assumed baseline against the actual
target before accepting any "build X" instruction, because X may already exist —
was not performed for this package. Its own `candidate_change` block prescribes
that check. And LSN-0001's lesson text quotes the practice this package
breaches: **"a doc-only change is not an implementation."**

This package is a doc-only change proposing to investigate contracts that are
already running and under CI.

**Rating: RED.**

---

## 5. What is actually good

A cold audit is not a hit job. The following survive, and some are valuable:

- **ADR-002 (externalize mature capabilities) — GREEN.** Correct and worth
  keeping. Not reimplementing Temporal, OpenTelemetry, or an agent SDK is the
  right call, and stating it as a decision record is the right form.
- **RA-012 (validation vs guardrail) — GREEN-W. The single best item.** The
  distinction is real, and its proposed test is the only genuinely
  constructible one in the package: build a case where a tool call passes
  runtime guardrails and the resulting outcome still fails domain validation.
  **[CORRECTED 08-31] — the test already exists and passes**
  (`tests/test_claim_verification.py:151-166`): a claim citing a real evidence
  id reaches PASS on structural checks alone, and BLOCKs as `UNGROUNDED_CLAIM`
  once verification is supplied. The distinction is correct and already settled
  here, so RA-012 leaves the salvage list — nothing needs building.
- **H8 (does the layer earn its place above the substrate?) — GREEN-W.** The
  right existential question, correctly left open, and the only hypothesis the
  repository cannot currently answer. It deserves the effort the other seven
  are absorbing.
- **RA-009 / CAND-002 (evidence ≠ provenance) — AMBER, useful.** The package
  is right that these should not collapse, and it identifies a real gap: in
  this repository provenance is a *field on a claim*, not a first-class record
  with its own identity and relations. That is a legitimate finding — the only
  place the package sees something the tree does not already have.
- **RA-014 / CAND-005 (verification-driven asset lifecycle) — AMBER.**
  Defensible as a differentiation hypothesis. It is also nearer to existing
  than the package realises: `11_Audit/LSN-*.yaml` already carries
  claim/root-cause/candidate-change/validation-plan/status, and
  `templates/lesson` exists. The hypothesis should be tested by promoting that
  embryo, not by starting a parallel registry.
- **ADR-001 (do not freeze the core early) — GREEN-W.** Defensible discipline,
  correctly reasoned. Its weakness is only that, combined with §3.7, nothing
  has moved off CANDIDATE in either direction — refusing to freeze has become
  indistinguishable from refusing to decide.

---

## 6. Findings summary

| ID | Finding | Severity |
|---|---|---|
| F-01 | Zero repository awareness: `APF` absent from the tree; zero internal citations | P0 |
| F-02 | Re-opens `MATERIAL_DRIFT` closed by `SOURCE_OF_TRUTH_MANIFEST.md` §7; no migration record per §6 | P0 |
| F-03 | 7 of 8 hypotheses marked OPEN against evidence already in the tree | P0 |
| F-04 | Falsification benchmark contains no measurable quantity — not falsifiable | P0 |
| F-05 | Entire package is E0 in a repo whose gate requires E3/E4 | P0 |
| F-06 | 8 of 14 registered research assets do not exist | P1 |
| F-07 | Traceability chain broken at 2 of 7 hops (`EV-*`, `DEC-*`); three conflicting ID schemes | P1 |
| F-08 | 6 of 6 existing assets violate the package's own mandatory-field rule | P1 |
| F-09 | Schemas are unvalidatable sketches; `claim.schema.yaml` is a downgrade of the existing `claim_evidence.schema.yaml` | P1 |
| F-10 | 5-tier evidence hierarchy has no field to record a tier; unused | P2 |
| F-11 | Zero dates, owners, or per-file versions in a "living" specification | P2 |
| F-12 | `SESSION_UPDATE_PROTOCOL` §7 (preserve status history) has no mechanism | P2 |
| F-13 | `STATUS.yaml` keys have no consumer | P2 |
| F-14 | External sources lack access dates, versions, anchors | P2 |

---

## 7. Disposition

**Do not adopt as specification.** Do not merge the tree as-is; doing so
creates a second source of truth and re-opens resolved drift.

Recommended handling, in order:

1. **Reject the structure. Keep three items.** **[CORRECTED 08-31 — was four;
   RA-012 is already settled.]** H8 (value above substrate), RA-009's
   provenance-as-relation gap, and ADR-002. Land them as normal entries in the
   existing governance tree — not as a parallel `spec/` hierarchy.
   **Done 2026-08-31:** ADR-002 became
   `docs/governance/EXTERNAL_CAPABILITY_BOUNDARY_V1.md`; H8 became D-15;
   RA-009 became D-16; the Test 7 correction became D-17.
2. **Retire the rest into `11_Audit/` as an input document**, which is what it
   is: an outside-in position paper. It has value as a record of how the system
   looks to a reader with no repository access.
3. **Before any further specification work, run the LSN-0001 first step.**
   Baseline diff against `main` before proposing any contract. This package is
   the second recorded instance of skipping it.
4. **If the asset lifecycle hypothesis is to be tested, test it on `LSN-*.yaml`**
   — promote a real lesson through DISCOVERED→VALIDATED with a real
   revalidation trigger. One executed instance settles more than fourteen
   registry rows.
5. **[CORRECTED 08-31] Drop the benchmark.** This step proposed building
   RA-012's test; it already exists and is green
   (`tests/test_claim_verification.py:151-166`). With its one constructible
   test already built, the remaining seven have no measurable pass condition
   and nothing to salvage. The benchmark goes; the run-durability gap it would
   have caught is now tracked as D-17 instead.

## 8. Closing assessment

The boundary reasoning in this package is largely sound — the author correctly
identifies that agent runtimes, durable execution, and telemetry are solved
elsewhere, and correctly refuses to claim them. Had it arrived before the
implementation, it would have been a useful document.

It arrived after. The repository it addresses has 4,203 LOC under `src/`, 322
passing tests, twelve schemas, six domain packs, an eight-check fail-closed
resume contract, and a CI chain that publishes hashed machine evidence. The
package does not mention any of it. It proposes to spend the next phase
investigating whether things that are running can be built.

The verdict is not that the ideas are bad. It is that the artifact is
**E0 asserting authority over E3**, and this project has a rule for that.
