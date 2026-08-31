# CER Session Closure — 2026-08-31 — APF Living Specification Audit

**Session:** cold audit of an externally-supplied specification package, and
the work that audit turned up in this repository.
**Branch:** `claude/audit-sgts3o`
**Entry baseline:** `8236dfa38a895d0b4f5c30c18671a468483a5cb9` (`main`, PR #39 merged)
**Closing HEAD:** see `git log -1` on the branch.
**Audited baseline SHA:** `20a54b92aad0857f75c6200d984b13098c6f4927` — unchanged.

## 1. Evidence status — read this before citing anything below

**No primary execution evidence exists for this session.** Neither workflow
triggers on a `claude/**` push — both are `push: [main]` / `pull_request: [main]` —
and no pull request was opened. Per the primary evidence rule, that is
`EVIDENCE_UNAVAILABLE`, not inferred success.

What exists is **local execution evidence (E2)** only:

| Check | Result |
|---|---|
| `python3 -m pytest tests/ -q` | 332 passed |
| `scripts/validate_project_context.py` | scans clean (branch check reports `REVIEW_REQUIRED` on a `claude/*` branch by design — D-02) |
| `scripts/audit_schema_bindings.py` | runs; 58 unbound field names reported |
| `scripts/verify_plan_baseline.py` | runs; all 24 APF files return `REVIEW_REQUIRED` |

Everything in this document is E0/E1/E2. Opening a PR against `main` is what
would raise it to E3/E4, and is the first action for the next session.

## 2. What the session was asked to do, and what it found

A specification package — *APF Living Specification vNext 0.1*, 24 files, 368
lines — was supplied for a cold audit.

**Verdict: RED as a specification, AMBER as a position paper.** Full report at
`11_Audit/APF_LIVING_SPEC_VNEXT_AUDIT_2026-08-30.md`. Three grounds:

1. It specifies a system it never names. `APF` appears zero times in this
   repository; its sources cite five external frameworks and zero internal
   artifacts.
2. Seven of its eight hypotheses are marked `OPEN` against evidence already in
   the tree. The suite that settles most of them runs in twelve seconds.
3. It fails its own rules: 8 of 14 registered assets have no file, the
   traceability chain is broken at 2 of 7 hops, 6 of 6 existing assets violate
   its own mandatory-field rule, and none of its eight falsification tests
   contains a measurable quantity.

In this repository's evidence scale the package is uniformly **E0**, proposing
contracts that already run at E3/E4.

## 3. The audit was wrong twice, and both corrections are recorded

Stated here rather than quietly amended, per the session update discipline.

**RA-012 was already built.** The audit called it the package's best item and
recommended making its falsification test executable. It already existed and
was green at `tests/test_claim_verification.py:151-166` — a claim citing a real
evidence id reaches PASS on structural checks alone and BLOCKs as
`UNGROUNDED_CLAIM` once verification is supplied. The salvage list dropped from
four items to three.

**The Test 7 row conflated two layers, and this is the one place the package
was right.** The audit credited RC-01..RC-08 as covering durability. That is
*session* resume. *Run* state is `self._runs: dict[str, WorkflowRunState] = {}`
with no persistence path in the module, so a run interrupted between a tool call
and its gate loses its state — and `HOTLReviewQueue` lives in the same object,
making `REVIEW_REQUIRED` a state the architecture claims and cannot honour
across a restart. A fail-open inside an otherwise fail-closed gate. Recorded as
**D-17**.

A third, milder correction: the audit described
`schemas/execution_evidence.schema.json` as "validated in CI". The *records* are
validated; nothing loads the schema file.

## 4. What landed

**Governance**
- `EXTERNAL_CAPABILITY_BOUNDARY_V1.md` — the one normative gap the package
  filled. `AGENT_FACTORY_SCOPE_V1.md` fixes the domain boundary; nothing fixed
  the capability boundary. The package's rule ("borrow what is mature") is
  corrected for this repository: the discriminator is whether a capability runs
  in-process and deterministically inside the commit under test, because the
  evidence chain requires re-derivability from a SHA. §7 states that it is not
  machine-enforced.
- **D-15** — whether the kernel earns its place above the substrates.
- **D-16** — lineage declared in three schemas, implemented in none.
- **D-17** — run-layer durability, above.

**Schemas**
- `scripts/audit_schema_bindings.py` — the repository's recurring defect, run
  mechanically instead of found by accident. 58 distinct declared field names
  are named nowhere outside `schemas/`, across 9 of 12 schema files.
- `schemas/INDEX.md` — the judgement that report needs, per schema:
  ENFORCED / PARTIAL / ASPIRATIONAL / UNBOUND. Not all 58 are defects:
  `trace.schema.yaml` is model-call telemetry for a dependency D-12 ruled out.
- `tests/test_schema_bindings.py` — `execution_evidence.schema.json` and
  `evidence_gate.py`'s hardcoded `REQUIRED` both list thirteen fields and
  nothing held them in agreement. Bound as a test rather than by making the
  fail-closed gate read a file. Verified to fail on real drift.

**Lessons**
- `scripts/verify_plan_baseline.py` + `tests/test_plan_baseline.py` — the
  regression guard LSN-0001 recorded as `N/A`, which is why it recurred.
- **LSN-0003** — the meta-lesson: `regression_guard: N/A` is a finding to be
  justified, not a field to be filled.
- `11_Audit/LSN-INDEX.md` — the third register to get a status index.

## 5. Rule-gap review (HOTL §5)

> Could this happen again? → **YES** → propose permanent rule / regression seed / automation

Done for LSN-0001: the automation exists and has a regression witness. The
lesson stays `status: candidate` — §4 reserves promotion for a human and forbids
inferring approval from a passing test. **Three lessons await that review**;
`11_Audit/LSN-INDEX.md` is the one page to read for it.

One result worth recording separately: **LSN-0002 caught a defect in the guard
written to enforce LSN-0001, before it shipped.** The first version reported
`BLOCKED` for any unresolvable baseline, which in a shallow clone — what web
sessions get — would have failed every handoff here, since `20a54b92` lies
outside the default fetch depth. The register worked as designed.

## 6. Residual risk

- **No CI evidence for any of it.** §1. Nothing in this session has been run by
  the Factory Kernel workflow.
- `EXTERNAL_CAPABILITY_BOUNDARY_V1.md` is enforced by nothing, and says so.
  That is the pattern this session spent its time on; it is accepted here
  because the alternative — a guard over a declared-adopted-standards list that
  does not exist — would be the same defect one level up.
- The 58 unbound schema fields are catalogued, not fixed. `schemas/INDEX.md`
  states per schema whether that is a gap or a deliberate not-yet.
- D-15, D-16 and D-17 are open and need a person.

## 7. Unchanged

`audited_baseline_sha`, `checkpoint_sha`, the `forbidden` list, the roadmap, and
every retrieval or routing constant. This session touched governance,
schemas-as-documentation, lessons and tests. It changed no kernel behaviour and
no measured number.
