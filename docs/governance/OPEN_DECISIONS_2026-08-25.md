# Open Decisions — 2026-08-25

Everything below needs a person. Nothing here is blocked on analysis: each item
states what was verified, what the options are, and what it costs to be wrong.

Trunk at time of writing: `main` @ `cf8bf5f`, `gate: FACTORY_KERNEL_GREEN`,
`audited_baseline_sha: 20a54b92aad0857f75c6200d984b13098c6f4927`.

---

## D-01 — `RE_domain_implementation` forbidden vs. M1 being the next milestone

**This is the one that blocks the roadmap.**

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

---

## D-02 — Context Guard rejects any local feature-branch checkout

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

---

## D-04 — Domain-matrix assets still stranded (AF-004 / M9)

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

---

## D-05 — Execute the prepared branch deletion

30 remote branches were each verified to carry **zero** commits not already
reachable from the trunk. Deleting them loses no history.

**Not done.** Every `git push origin --delete` from the 2026-08-25 session
returned `HTTP 403` — that session's credentials permit pushes but not ref
deletions, and the GitHub MCP server exposes no branch-deletion tool. The
repository owner has `admin`, so this succeeds from a normal local clone.

Command and restore SHAs: `11_Audit/MERGED_BRANCH_CLEANUP_2026-08-25.md`.

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

## Not a decision — the actual next work

Once D-01 is resolved: expand the M1 RE corpus and benchmark from the delivered
first slice (8 documents / 15 cases) toward the `RE_POC.md` target (20+
documents / 150 cases).
