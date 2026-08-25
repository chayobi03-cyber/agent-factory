# Open Decisions — 2026-08-25

Everything below needs a person. Nothing here is blocked on analysis: each item
states what was verified, what the options are, and what it costs to be wrong.

Trunk at time of writing: `main`, `gate: FACTORY_KERNEL_GREEN`,
`audited_baseline_sha: 20a54b92aad0857f75c6200d984b13098c6f4927`.

**Status:** D-01, D-02, D-03, D-04, D-07 and D-09 resolved 2026-08-25. Resolved
entries are kept as the record of why.

**Still open — and neither is a judgement call I can make:** D-05 and D-06 both
require deleting remote refs, which returns `HTTP 403` from an agent session;
they need one command from a local clone. D-08 is about this repository's public
visibility and belongs to its owner.

---

## D-01 — `RE_domain_implementation` forbidden vs. M1 being the next milestone

> **RESOLVED 2026-08-25 — Option A.** The constraint is now time-bounded in the
> validator and discharged once `gate` reaches `FACTORY_KERNEL_GREEN`. M1 RE
> expansion is unblocked. Implementation notes at the end of this entry; the
> analysis below is kept as the record of why.

`scripts/validate_session_resume.py` hardcodes:

```python
REQUIRED_HANDOFF_CONSTRAINTS = {
    "GEPA_implementation",
    "OPRO_promotion",
    "RE_domain_implementation",      # <-- absolute, no time bound
    "audited_baseline_redefinition",
    "PASS_without_primary_execution_evidence",
}
```

RC-07 fails unless the handoff front-matter's `forbidden` list is a **superset**
of that set. So `RE_domain_implementation` cannot be removed from the handoff
without editing the validator.

Meanwhile `docs/ROADMAP_WBS.md` says M1 RE Hybrid RAG *"Starts only after M0.5
Factory Kernel GREEN"* — and the kernel is now GREEN, confirmed by run
`32804843817`. `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` puts `RE Domain Pack`
immediately after `Factory Kernel GREEN`.

The state file's own wording is time-bounded —
`RE_domain_implementation_until_kernel_gate` — but the handoff and validator
tokens are not. The M1 first slice (`src/re_domain_pack.py`, `src/re_corpus.py`,
`scripts/re_demo.py`, 15-case benchmark) has already shipped under the
time-bounded reading.

**Options**

| | Change | Consequence |
|---|---|---|
| A | Replace the validator token with `RE_domain_implementation_until_kernel_gate` and make RC-07 treat it as satisfied once `gate == FACTORY_KERNEL_GREEN` | Encodes the intent that was always in the state file. Requires a validator change + handoff edit, both gated by RC-07 itself. |
| B | Drop the token from `REQUIRED_HANDOFF_CONSTRAINTS` entirely | Simplest, but loses the guard that kept RE work behind the kernel gate. |
| C | Leave as-is | M1 cannot expand past the delivered first slice without the validator contradicting the roadmap. |

**Recommendation:** A. It is the only option that makes the contract say what the
project already means.

**Cost of getting it wrong:** RC-07 is fail-closed. A malformed change blocks
every session's resume until fixed.

### How Option A was implemented

`REQUIRED_HANDOFF_CONSTRAINTS` was split in `scripts/validate_session_resume.py`:

- `PERMANENT_HANDOFF_CONSTRAINTS` — GEPA implementation, OPRO promotion, audited
  baseline redefinition, and PASS-without-primary-evidence. Always required, at
  every gate.
- `KERNEL_GATED_CONSTRAINT_ALIASES` — the RE constraint, accepting **both**
  spellings, since the state file always used `_until_kernel_gate` while the
  handoff and prose used the bare form.
- `KERNEL_GATE_CLEARED_GATES = {"FACTORY_KERNEL_GREEN"}` and a
  `constraints_satisfied(gate, declared)` helper: permanent constraints are
  checked unconditionally, and the kernel-gated one only while the gate is still
  closed.

The prose fallback path carries the identical time bound, so the structured and
prose paths cannot disagree about whether RE work is held back. The state-side
`gate_constraints_ok` check was moved onto the same alias set — it had been
demanding the bare token that the state file never used, a latent failure that
would have fired the moment the gate returned to a blocking value.

Discharged means discharged, not deleted: a document may keep declaring the
constraint or drop it, and both satisfy RC-07. The handoff front-matter and
`CURRENT_SESSION_STATE.forbidden` both retain it, annotated, as the record of
the bound.

Six regression tests were added. Five fail against the pre-fix validator,
including the end-to-end witness that RC-07 passes on a GREEN-gate handoff
omitting the RE constraint — a combination that was previously unreachable. The
sixth asserts the constraint still bites while the gate is closed, guarding
against over-correction. Suite: 92 passed.

---

## D-02 — Context Guard rejects any local feature-branch checkout

> **RESOLVED 2026-08-25 — Option B.** `AGENTFACTORY_TARGET_BRANCH` declares the
> landing target for a local checkout, and is ignored outright whenever
> `GITHUB_ACTIONS` is set, so it cannot weaken CI. Three regression tests cover
> the override, the CI lockout, and unchanged behaviour when it is absent.

`scripts/validate_project_context.py` resolves the branch as:

```
git branch --show-current  ->  GITHUB_BASE_REF  ->  GITHUB_REF_NAME
```

and then requires `branch == EXPECTED_BRANCH`. On a developer's machine the
first step wins, so the guard fails on **any** branch not literally named
`main`. Throughout the 2026-08-25 session, local verification only worked by
naming the scratch checkout after the trunk.

The LSN-0002 base-ref fix repaired this for CI only. Locally the guard still
asks *"what is this checkout called"* rather than *"where would this land"* —
and the latter is what the governance boundary actually cares about.

**Options**

| | Change | Consequence |
|---|---|---|
| A | Local runs resolve the target via the branch's upstream/merge base rather than its name | Matches the CI semantics; more logic in a fail-closed guard. |
| B | Honor an explicit opt-out (e.g. `AGENTFACTORY_TARGET_BRANCH`) for local runs | Small and obvious; adds an override on a fail-closed guard, which needs care. |
| C | Leave as-is, document the rename workaround | Zero risk, permanent friction, and it silently teaches contributors to rename branches to get past a guard. |

**Recommendation:** B, with the override ignored whenever `GITHUB_ACTIONS` is
set, so it can never weaken CI.

---

## D-03 — Three stale open pull requests

> **RESOLVED 2026-08-25 — partly.** #13 and #11 closed. **#1 stays open**: the
> confirmation this entry asked for returned the opposite of what it assumed,
> and closing it would have discarded unmerged implementation of a canonical
> contract. Raised as D-09.

All three predate the trunk move and none can pass CI as they stand: PRs #13 and
#11 target `p0/opro-baseline`, which the workflow no longer triggers on
(`branches: [main]`).

| PR | Head | State | Disposition |
|---|---|---|---|
| [#13](https://github.com/chayobi03-cyber/agent-factory/pull/13) | `fix/rc-schema-drift-e11a663a` | Every change superseded by #14; all four files landed on the trunk | **Close.** Nothing is lost. |
| [#11](https://github.com/chayobi03-cyber/agent-factory/pull/11) | `p1/domain-matrix-workflow-v0.1` | Carries genuinely valuable domain-matrix assets **and** 12 quarantined investment files | **Do not merge.** See D-04 — salvage the files, then close. |
| [#1](https://github.com/chayobi03-cyber/agent-factory/pull/1) | `audit/evidence-chain-remediation` | Draft since 2026-08-18, base pinned at `16936fe` | **Close or rebase.** Its evidence-chain work appears already reflected in `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md`; confirm before closing. |

Merging #11 as a branch would reintroduce paths listed in the guard's
`FORBIDDEN_CANONICAL_PATHS` and turn the Context Guard red on the trunk.

### Outcome

**#13 closed.** Supersession verified rather than assumed: all four files it
touches exist on `main` with the trunk strictly ahead on each, and RC-01..08 pass
there. Its own CI failure was the LSN-0002 guard bug, not its content.

**#11 closed.** Its assets landed via D-04, recovered file-by-file. The branch
itself must never merge.

**#1 kept open.** This entry said *"confirm before closing"* — the confirmation
came back the other way, and the assumption behind the disposition was wrong.
See **D-09**.

The lesson generalises past this entry: two of the three dispositions here were
written from document names rather than diffs, and one of them was wrong. A
branch is closeable when a diff says its content is reachable from the trunk,
not when a similarly-named document exists there.

---

## D-04 — Domain-matrix assets still stranded (AF-004 / M9)

> **RESOLVED 2026-08-25 — recovered.** Eleven files taken individually from
> `p1/domain-matrix-workflow-v0.1`, no branch merge, no quarantined artifact.
> All eight recovered tests pass against the *current* kernel, and the demo
> exercises four synthetic Domain Packs end to end. Recovery notes at the end
> of this entry.

`p1/domain-matrix-workflow-v0.1` holds work that maps directly onto the roadmap's
*"kernel loads Domain Pack without code fork"* acceptance criterion:

- `src/synthetic_domain_matrix.py`
- `scripts/domain_matrix_demo.py`
- `fixtures/domain_matrix/domain_packs.yaml`
- `schemas/engineering_evidence.schema.yaml`
- `fixtures/engineering_evidence/domain_envelopes.yaml`
- `docs/governance/GENERIC_ENGINEERING_EVIDENCE_CONTRACT_V1.md` (+ RCA, runtime status)

These are AgentFactory-native by `AGENT_FACTORY_SCOPE_V1.md` §5 (generic
evidence provenance is explicitly allowed). They sit on the same branch as 12
quarantined investment files, which is why the branch was never merged.

**Decision:** whether to spend a session recovering these file-by-file — the same
method used on 2026-08-25 for `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` and
`CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md` — or to rebuild them later against
the current kernel.

**Recommendation:** recover. They are written against this kernel, and the
alternative is rebuilding work that already exists — the exact failure LSN-0001
was written about.

### What was recovered

Eleven files, each taken individually with `git show <branch>:<path>` — no
branch merge, so none of the 12 quarantined investment artifacts came with them.
Two dependencies the list above had missed turned up during the work:

- `src/engineering_evidence.py` — the module implementing the contract, required
  by `tests/test_engineering_evidence_contract.py`. Standard library only.
- `tests/test_domain_matrix_workflow.py` and
  `tests/test_engineering_evidence_contract.py` — recovering the code without
  its tests would have imported unverified code into a repository whose whole
  discipline is that a change without a matching test is not complete.

Every recovered file was scanned for quarantined terms before placement, and the
staged set was re-checked for any path matching the guard's
`FORBIDDEN_CANONICAL_PATHS`. Both clean.

**The recovered tests pass against the current kernel, not merely the branch
they came from** — 8 passed, suite 100 passed. `synthetic_domain_matrix.py`
imports only `factory_runtime` and `interfaces`, both already on the trunk, so
nothing had to be back-ported to accommodate it.

A `Domain Matrix E2E` step was added to the workflow. Without it the recovered
demo would sit unexecuted, which is how these assets became strandable in the
first place. The demo runs four synthetic Domain Packs
(`ingest→parse→normalize→retrieve→verify→evaluate→cer_gate→execute→report→trace`),
each reaching `cer_decision: PASS` under `fixture_only: true`.

Deliberately left behind: `CER_SESSION_CLOSURE_2026-08-19_DOMAIN_MATRIX.md`,
`NEXT_SESSION_HANDOFF_2026-08-20_DOMAIN_MATRIX.md`, and
`CER_M2_LESSONS_2026-08-20.md`. These are that session's historical records
rather than the assets, and the first two are the branch's *decontamination*
narrative — their finance mentions are boundary statements ("financial-data
ingestion is not part of the core roadmap"), permitted by scope §7 but adding
no live contract to the trunk.

---

## D-05 — Execute the prepared branch deletion

30 remote branches were each verified to carry **zero** commits not already
reachable from the trunk. Deleting them loses no history.

**Not done.** Every `git push origin --delete` from the 2026-08-25 session
returned `HTTP 403` — that session's credentials permit pushes but not ref
deletions, and the GitHub MCP server exposes no branch-deletion tool. The
repository owner has `admin`, so this succeeds from a normal local clone.

**Step-by-step procedure:** `11_Audit/MERGED_BRANCH_CLEANUP_2026-08-25.md`. It
re-derives the safe set against *your* current `main` rather than trusting a
hardcoded list, prints `SAFE` / `KEEP` per branch, and deletes only what it just
proved safe. A branch that has gained commits since the snapshot shows `KEEP` and
is skipped automatically — including `audit/evidence-chain-remediation`, which
must survive (D-09). Restore SHAs are in the same file; deletion is reversible
with `git push origin <sha>:refs/heads/<name>`.

The verifier was dry-run on 2026-08-25 and reproduces 30 `SAFE` / 8 `KEEP`.

Rationale: LSN-0001 named the ambient condition — many stale branches, no single
canonical trunk — as the cause of a session re-deriving its plan from the wrong
line and proposing to rebuild ~6,000 lines that already existed.

---

## D-06 — When to retire `p0/opro-baseline`

Kept as a transition pointer during the trunk move. It is now fully contained in
`main`, and CI no longer triggers on it.

Retire once no open PR targets it (see D-03) and no external reference depends on
the name. Until then it is harmless but misleading — it looks like a live trunk
and is not.

---

## D-07 — `RESUME_CONTRACT_V1.md`

> **RESOLVED 2026-08-25 — kept as history, and its header corrected.** The file
> declared itself *"Active governance contract"* while nothing referenced it, so
> two documents each claimed to be the live v1.1 resume contract. It now carries
> a superseded banner naming what replaced it. Retained, not deleted.

Indexed **SUPERSEDED** by `CER_SESSION_CONTINUITY_CONTRACT_V1.md`. Both are
labelled "v1.1" with the same purpose; only the Continuity Contract is read by
code. Keep as history, or delete. Low stakes either way — recorded so it stops
being rediscovered.

---

## D-08 — This repository is public

`visibility: public`. Everything discussed here is world-readable, including the
quarantined investment artifacts on the retained branches and the full forensic
contamination record.

No action implied — flagged because it was never an explicit decision in any
governance document, and the quarantine discussion reads as though the material
were internal.

---

## D-09 — The trunk declares an evidence-chain contract it cannot enforce

> **RESOLVED 2026-08-25 — recovered and extended.** The gate tooling is on the
> trunk, wired into a CI workflow, and covers all six gates rather than the four
> it knew about. Recovery notes at the end of this entry.

Found while confirming D-03's disposition for PR #1, and the reason that PR is
still open.

`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` is CANONICAL on the trunk — referenced
by `CURRENT_SESSION_STATE.audit_evidence_contract`, indexed as actively
enforced — and it requires, among other items, *"independent digest verification
where the artifact is downloaded"*.

Nothing on the trunk does that:

```
$ grep -rl "sha256\|digest" scripts/ .github/workflows/
(no matches)
```

`CURRENT_SESSION_STATE.last_verified_primary_evidence.independently_verified_digest`
is recorded by hand. No tool on the trunk produces or checks it.

The enforcement exists, unmerged, on `audit/evidence-chain-remediation` (PR #1,
draft since 2026-08-18) — nine files absent from `main`:

| | |
|---|---|
| Gate tooling | `scripts/evidence_gate.py`, `scripts/capture_execution.py`, `scripts/verify_artifact_sha256.py` |
| Schemas | `schemas/audit_evidence_manifest.schema.json`, `schemas/execution_evidence.schema.json` |
| CI | `.github/workflows/audit-evidence-chain.yml` |
| Records | remediation doc, external cold-audit record, internal rating matrix |

**The decision:** recover this tooling the way D-04's assets were recovered, or
weaken the contract to match what is actually enforced. Leaving both as they are
means a canonical contract whose central requirement is satisfied by assertion.

**Recommendation:** recover, but as its own reviewed change. It adds a second CI
workflow and gate tooling that can block merges — larger and more consequential
than D-04's demo-and-fixtures recovery, and it needs the base rebased from
`16936fe` onto the current `main` first.

**Why this matters beyond PR #1:** the contract is what
`AUDIT_EVIDENCE_CHAIN=GREEN` claims rest on. A gate that cannot fail is not a
gate, and every evidence claim citing this contract inherits that.

---

## Not a decision — the actual next work

Once D-01 is resolved: expand the M1 RE corpus and benchmark from the delivered
first slice (8 documents / 15 cases) toward the `RE_POC.md` target (20+
documents / 150 cases).

### How D-09 was closed

`evidence_gate.py`, `capture_execution.py`, `verify_artifact_sha256.py` and both
schemas were recovered individually from `audit/evidence-chain-remediation` —
all stdlib-only, no dependency on the branch they came from.

Recovering them unchanged would have shipped a gate that certifies a subset:
`EXPECTED_IDS` named four gates, and the workflow now runs six.
`E-M1-RE-DEMO` and `E-DOMAIN-MATRIX` both postdate the 2026-08-18 branch, so a
GREEN decision would have covered four of six while reading as complete. Both
are now required, with checks matching what those gates actually emit — a
partially-passing M1 benchmark blocks, and a matrix that drops below two domains
or stops being `fixture_only` blocks.

The workflow was adapted rather than copied: its `push` triggers named
`audit/**` and `p0/**`, branches that are no longer the canonical line;
`PYTHONPATH` lacked the repository root that `src.`-prefixed imports need; and
`pyyaml` was missing from the install step.

**The gate was verified to fail, not merely to pass.** A gate that cannot fail
is the whole subject of this entry. Locally, against real captured evidence from
all six gates: complete evidence returns `GREEN` (exit 0), while tampered stdout
(digest mismatch), a missing gate record, evidence from another commit, and a
non-zero exit each return `AMBER` (exit 1). Seventeen tests encode these,
including one that a pytest run producing no result line must not pass —
silence is not success.

`verify_artifact_sha256.py` closes the contract's item 14 directly: it reports
observed and expected digests and exits non-zero on mismatch, so
`independently_verified_digest` can be produced by a tool instead of by hand.
