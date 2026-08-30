# Open Decisions — 2026-08-25

Everything below needs a person. Nothing here is blocked on analysis: each item
states what was verified, what the options are, and what it costs to be wrong.

Trunk at time of writing: `main`, `gate: FACTORY_KERNEL_GREEN`,
`audited_baseline_sha: 20a54b92aad0857f75c6200d984b13098c6f4927`.

**Status:** D-01 through D-10 resolved 2026-08-25; D-13 and D-14 raised and
closed 2026-08-26. **D-11 and D-12 are open and deferred** — both raised by the
M1 work itself, both about the same wall (what a dependency-free lexical
retriever cannot do), and both now sequenced behind the arrival of the real RE
corpus. See *Deferral* at the end of this register.

**D-15 and D-16 are open and are not deferred.** Both were raised by the
2026-08-30 goal-and-milestone audit, both are about what this repository claims
about itself rather than about what it can retrieve, and both want an answer
*before* the internal handover rather than after: each is a sentence the
receiving team will read as meaning more than it does.

Entries are kept as the record of why, not cleared; add new decisions here
rather than starting a fresh register.

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

> **RESOLVED 2026-08-25 — executed.** Run
> [32823162740](https://github.com/chayobi03-cyber/agent-factory/actions/runs/32823162740)
> deleted 31 branches. The remote went 41 → 10, matching the predicted keep-set
> exactly. Every deleted SHA remains reachable from `main`; trunk verified
> unchanged afterwards (Context Guard PASS, RC-01..08 PASS, pytest 120/120).

30 remote branches were each verified to carry **zero** commits not already
reachable from the trunk. Deleting them loses no history.

**Not done.** Every `git push origin --delete` from the 2026-08-25 session
returned `HTTP 403` — that session's credentials permit pushes but not ref
deletions, and the GitHub MCP server exposes no branch-deletion tool. The
repository owner has `admin`, so this succeeds from a normal local clone.

**One dispatch, from anything with a browser including a phone:**
`.github/workflows/branch-cleanup.yml` — *Actions → Merged Branch Cleanup → Run
workflow*. Dry-run is the default and prints the full table with restore SHAs to
the job summary; deleting requires both selecting `delete` and typing `DELETE`,
so a stray tap cannot do it. `main` and the active working branch are refused
regardless of what the merge check says. This exists because the 403 above is a
credential limit, not a reason for the work to wait on a laptop.

**Or from a local clone:** `11_Audit/MERGED_BRANCH_CLEANUP_2026-08-25.md`. It
re-derives the safe set against *your* current `main` rather than trusting a
hardcoded list, prints `SAFE` / `KEEP` per branch, and deletes only what it just
proved safe. A branch that has gained commits since the snapshot shows `KEEP` and
is skipped automatically — including `audit/evidence-chain-remediation`, which
must survive (D-09). Restore SHAs are in the same file; deletion is reversible
with `git push origin <sha>:refs/heads/<name>`.

Both paths classify identically; the shared logic was dry-run on 2026-08-25.
The set was 30 when this entry was written and is **31** now that the trunk move
folded `p0/opro-baseline` into `main` — which is why nothing here acts on a
stored list. **That also means this one operation closes D-06.**

Rationale: LSN-0001 named the ambient condition — many stale branches, no single
canonical trunk — as the cause of a session re-deriving its plan from the wrong
line and proposing to rebuild ~6,000 lines that already existed.

---

## D-06 — When to retire `p0/opro-baseline`

> **RESOLVED 2026-08-25 — retired with D-05.** `p0/opro-baseline` was fully
> merged into `main`, so the cleanup classified it as safe and removed it in the
> same dispatch. The branch name that gave this project its trunk for 239
> commits no longer exists; `main` is the only trunk.

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

> **RESOLVED 2026-08-25 — staying public.** Decided by the owner. Recorded here
> because it had never been an explicit decision in any governance document, and
> because it is now a live constraint on M1 rather than a passive fact: real RE
> test reports carry customer and product identifiers, and CISPR standards are
> copyrighted, so neither can ever be committed to this tree. The PoC's "20+
> representative legacy documents" therefore has to reach the kernel through an
> out-of-tree corpus source, not through the repository.

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

### How D-05 and D-06 were closed

The blocker was never the decision — it was that deleting a remote ref returns
`HTTP 403` from an agent session, so the work waited on someone opening a laptop
while 41 branches accumulated.

`.github/workflows/branch-cleanup.yml` removed that dependency: a
`workflow_dispatch` job that re-derives the safe set, prints it with restore SHAs
to the job summary, and deletes only on an explicit `delete` mode *plus* a typed
`DELETE`. Run 1 was a dry run; run 2 executed. Both from a phone.

The prediction held exactly — 31 deleted, 10 kept, no surprises in either
direction. Two of the kept mattered specifically:
`audit/evidence-chain-remediation`, which D-09 depended on surviving, and
`p0/opro-baseline-m1b-history-20260819`, which `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md`
requires be retained.

The workflow stays. It re-derives its set every run, so it is safe to dispatch
again whenever branches accumulate — the condition `11_Audit/LSN-0001` identified
as the cause of cross-branch plan divergence now has a one-tap remedy instead of
a documented procedure nobody runs.

---

## D-10 — Retrieval gating depends on corpus term frequency, not on the query

> **RESOLVED 2026-08-25 — Option C, with the abstention rule split out.** The
> literal-hit gate is gone; candidates are gated on the share of a query's IDF
> mass a fragment covers, and abstention is decided separately. Verified across
> fifteen corpus shapes. Implementation notes, and what is still fitted rather
> than derived, at the end of this entry.

Raised 2026-08-25 by the M1-1 tokenization work (step 1 of the M1 corpus plan),
which exposed it rather than caused it.

`retrieve()` gates candidates on `_distinctive_terms` — query terms with
`0 < df <= 30%` of fragments — and requires `min(2, len(distinctive))` of them
to appear literally in a fragment. Both the membership of that set *and* the
number of required hits therefore move as the corpus changes, so the same query
against the same document behaves differently depending on what unrelated
documents sit alongside it.

Measured on `RE-BC-002` ("Which document describes the chamber CH-2 antenna
setup and calibration?", expects `DOC-RE-003`) with same-vocabulary distractor
documents added:

| Corpus | `distinctive` | Required hits | `DOC-RE-003` returned |
|---|---|---|---|
| baseline | `ch-2`, `antenna`, `setup` | 2 | yes |
| + 40 distractors | `ch-2`, `setup` | 2 | **no** |
| + 100 distractors | `ch-2` | 1 | yes |

`antenna` crosses the 30% ubiquity threshold first and drops out; at 40
distractors two hits are still required but only two terms remain, so a fragment
must contain *both* `ch-2` and `setup` and the right document misses. At 100 the
set shrinks to one term, one hit is required, and it comes back. The failure is
non-monotonic — more context makes it worse, then better.

This is the same class as the abstention defect fixed in M1-1: behaviour keyed
to corpus term statistics rather than to the query-document relationship. That
one was fixable within tokenization because the tokenizer caused it. This one is
a gating-heuristic design question and is deliberately **not** patched in
passing.

**Why it matters for the corpus expansion:** the PoC targets
`Evidence Recall@10 >= 0.90`. A retriever whose recall moves with the number of
unrelated documents cannot be measured against a fixed threshold — scaling to
20+ documents and 150 cases before this is settled produces numbers that
describe the corpus rather than the retriever.

**Options**

| | Change | Consequence |
|---|---|---|
| A | Fixed required-hit count, independent of how many terms survive the df filter | Simplest; removes the non-monotonicity but keeps ubiquity-based membership |
| B | Rank by score and drop the literal-hit gate entirely, relying on the D-10 absence check plus a score floor for abstention | Removes the corpus dependence at its root; needs a defensible floor, which is a calibration question |
| C | Weight terms by IDF instead of admitting/excluding them at a threshold | Standard, monotonic, and keeps rare terms influential without a cliff; largest change |

**Recommendation:** C, verified against the distractor probe at several corpus
sizes rather than at one. It is the only option where adding unrelated documents
cannot flip a result, which is the property the PoC metrics need. Settle it as
part of step 2 (adversarial corpus), before any scaling.

---

### Resolution — 2026-08-25

**Option C, plus a split the option list did not anticipate.**

`_distinctive_terms` and the `min(2, len(distinctive))` literal-hit requirement
are removed. In their place, `retrieve()` weights every non-stopword,
non-domain-generic query term by IDF and admits a fragment only if it covers at
least `_COVERAGE_FLOOR` of that weight. Nothing in the rule reads a document
frequency as a *threshold* any more — df enters only through the smooth IDF
term, so adding documents shifts a score instead of flipping a membership.

The cliff is measurably gone. RE-BC-002's coverage of its correct document,
across the fifteen shapes the new stability suite exercises:

| Shape | Coverage | | Shape | Coverage |
|---|---|---|---|---|
| baseline | 0.194 | | saturate-antenna-3 | 0.184 |
| + 10 distractors | 0.203 | | saturate-antenna-20 | 0.163 |
| + 40 distractors | 0.210 | | saturate-setup-20 | 0.264 |
| + 100 distractors | 0.215 | | saturate-calibration-20 | 0.294 |
| + 250 distractors | 0.220 | | saturate-chamber-20 | 0.240 |

Monotonic in distractor volume, and bounded — 0.163 to 0.294 — where the old
gate went yes / **no** / yes over the same span.

**The split.** One threshold could not serve both jobs. A floor low enough to
admit a legitimate question phrased in common words is also low enough to admit
a question about something the corpus does not contain. So abstention became its
own rule: a query is unanswerable when more than `_UNSEEN_MASS_CEILING` (0.50)
of its *subject* weight rests on terms with `df == 0`. The two classes separate
at 0.42 and 0.65 on the current benchmark, so 0.5 sits in the gap.

**Choosing the floor.** Correctness and stability do not pin it down — both hold
at every value from 0.00 to 0.16, because abstention no longer depends on this
floor at all. What the floor buys is precision, so it wants to be as high as it
safely goes, and the ceiling is RE-BC-002's 0.163 minimum:

| Floor | Benchmark on baseline | Stable across shapes | Candidates per answerable query at 250 distractors |
|---|---|---|---|
| 0.00 | all pass | yes | 50.0 (the `top_k` cap) |
| 0.08 | all pass | yes | 19.1 |
| **0.12** | all pass | yes | **13.6** |
| 0.16 | all pass | yes | 8.7 |
| 0.18 | all pass | **no** (RE-BC-002) | 7.4 |
| 0.20 | **RE-BC-002 fails** | no | 7.2 |

0.12 keeps about a quarter of the binding minimum as margin and cuts returned
candidates by ~3.7x against no floor. 0.16 is better on precision but sits
inside the noise of a minimum observed from only fifteen shapes.

**What is fitted rather than derived — read this before trusting the numbers**

1. `_NON_EVIDENTIAL_TERMS` (question-form vocabulary excluded from the
   unseen-mass calculation) was assembled *after* inspecting which benchmark
   queries were misclassified. It is fitted to 15 cases. Without it the classes overlap and no
   threshold separates them: "Which document describes the CH-2 antenna setup"
   scores 0.685 unseen against 0.647 for a question about lunar regolith.
2. At 35 fragments, `df == 0` mostly means *the corpus is small*, not *the subject
   is absent*. The unseen-mass rule works here because the abstention cases name
   subjects far outside RE; it has not been tested against a near-miss.
3. `_COVERAGE_FLOOR = 0.12` is fitted to a 35-fragment corpus and its upper edge
   is set by one marginal case.

All three are corpus-size artefacts and all three should be re-derived from
corpus statistics at PoC scale. `tests/test_re_retrieval_stability.py` is the
harness that does it — the sweep above is reproducible by varying
`re_domain_pack._COVERAGE_FLOOR` against `CORPUS_SHAPES`.

**Regression guard.** `tests/test_re_retrieval_stability.py` fails if any
benchmark case's outcome differs across the fifteen shapes, if an abstention
case stops abstaining at any shape, if a near-duplicate revision displaces the
original, or if a contradicting document becomes unreachable alongside the
document it contradicts. It is the D-10 defect's own probe, kept as a test.

**Re-verified 2026-08-26, after a defect in the corpus it was measured against.**
The corpus loader's identity validation revealed that `near_duplicate_revisions()`
had been emitting `DOC-RE-001/REV-B`, an identity the baseline corpus already
held, so every shape in the sweep above contained two different documents under
one identity and counted that document twice in each document-frequency
statistic. The sweep was therefore run against a corrupted corpus.

Re-run after the fix, at 30 documents and 159 cases:

| floor | Recall@10 | shape-unstable cases |
|---|---|---|
| 0.00 | 0.914 | 1 |
| 0.08 | 0.914 | 1 |
| **0.12** | **0.914** | 1 |
| 0.16 | 0.906 | 1 |
| 0.20 | 0.906 | 1 |
| 0.24 | 0.906 | 2 |

The conclusion holds: 0.12 sits in the best band and 0.16 upward degrades. The
single unstable case is RE-BC-133, marginal by construction. This is recorded
because the original result was measured against a corrupted corpus and
happening to survive that is not the same as having been checked — the check is
what makes the number usable.

---

## D-11 — A lexical retriever cannot abstain on a near-miss, and no threshold changes that

> **PARTIALLY ADDRESSED 2026-08-25 — option A implemented, option C built and
> measured as *not* the fix.** Claim-evidence verification is now a kernel
> capability and the CER gate acts on its verdict, which closed a separate and
> more serious hole and moved near-miss abstention from 3/8 to 4/8 as a side
> *(the 4/8 was reverted on 2026-08-26 — see D-14)*
> effect. It does not resolve this entry. The band stays open and the
> recommendation below is revised: **B is now the only remaining option that
> can close it.** Notes at the end of this entry.

Raised 2026-08-25 by the M1-3 corpus and benchmark scale-up (10 → 30 documents,
15 → 159 cases). Not a regression: the scale-up is the first thing large enough
to measure it. D-10's resolution named this exact gap — *"it has not been tested
against a near-miss"* — and this is that test coming back.

**What a near-miss is.** The 20 abstention cases now run in three bands:

| Band | Example | Abstains |
|---|---|---|
| `subject_outside_domain` | *"What quarterly revenue did the test laboratory report?"* | **5/5** |
| `entity_absent_from_corpus` | *"What was the outcome of the EUT-72 emission retest?"* | **7/7** |
| `near_miss_domain_subject` | *"What field strength is applied during a radiated immunity test?"* | **3/8** |

(The near-miss row read **4/8** between 2026-08-25 and 2026-08-26; see the
reversion note below and D-14.)

The first two are decidable from corpus statistics: the terms carrying the
question are simply absent. The third is real RE subject matter — conducted
emission, immunity, ESD, MIL-STD-461, IEC 61000-3-2, open area test sites — that
this corpus happens not to cover. It shares almost all its vocabulary with the
corpus. Only the one word that makes it a different question is missing.

**This is not a tuning problem, and that was measured rather than assumed.**
Every lexical statistic available to a dependency-free retriever was scored on
its ability to separate the 139 answerable cases from the 20 abstention ones.
The column that matters is the last: how many answerable questions must be
sacrificed to catch every abstention case.

| Statistic | Answerable lost for a full catch |
|---|---|
| Unseen share of query IDF mass (the D-10 rule) | 35 / 139 |
| Best fragment coverage over seen weight | 139 / 139 |
| Absolute seen IDF mass | 108 / 139 |
| Most specific seen term | 139 / 139 |
| Count of query terms rarer than 10% of fragments | 98 / 139 |
| Best fragment coverage over all weight | 54 / 139 |
| Clarity (best coverage over corpus mean) | 136 / 139 |
| Gap between best and tenth-best fragment | 43 / 139 |

A two-dimensional rule does no better: the best boundary over *unseen share ×
best coverage* catches 20/20 only by losing 32–42 answerable cases, taking
Recall@10 from 0.914 to roughly 0.70. There is no operating point on this
frontier worth having.

**Why it is structurally hard.** The corpus can report what it contains. It
cannot report whether a word it lacks is question-framing scaffolding
(*"summarize"*, *"status"*) or a missing subject (*"immunity"*). Both are simply
absent, and absence carries no measured weight — which is also why the D-10 rule
that assigned unseen terms the *maximum* IDF inverted the two classes outright
once the corpus reached 108 fragments.

**Options**

| | Change | Consequence |
|---|---|---|
| A | Accept and record. Gate CI on the two decidable bands; report the third | Honest, costs nothing, leaves a real hole in `Negative-case Abstention >= 0.90` |
| B | Second retrieval method with semantic similarity (embeddings) | RE_POC.md already requires "3 retrieval methods minimum", so this is scheduled work, not new scope; adds a model dependency the kernel currently does not have |
| C | Decide sufficiency at claim-evidence verification instead of retrieval | Architecturally the right home — the CER gate owns evidence sufficiency, and "these fragments are about something else" is a verification question, not a ranking one; needs a claim-level verifier that does not exist yet |
| D | Curate a domain lexicon of RE subject terms and treat an absent one as decisive | Would work, and is exactly the hand-fitted artifact D-10 spent its resolution removing |

**Recommendation:** A now, C as the real fix, B when the third retrieval method
lands. A is already implemented — `scripts/re_demo.py` gates on the two decidable
bands and prints the third as a named limitation, and
`tests/test_re_domain_pack.py` pins it at 3/8 so it cannot drift in either
direction without someone editing this entry. D is explicitly rejected: it buys
the metric back by reintroducing exactly the kind of hand-curated list that
D-10's resolution measured as worthless and deleted.

**What it costs to be wrong.** Accepting A means the PoC ships knowing it will
answer a question it should refuse roughly five times in eight of this class.
In an evidence-governed system that is the failure mode that matters most — it
produces a confident, cited answer drawn from documents about a different test.
The mitigation until C lands is that those answers are still fully traced, so a
reviewer sees the evidence is about radiated emission when the question was
about immunity. That is a human catching it, not the system.

---

### Update — 2026-08-25, after building option C

Option C was implemented rather than argued about, and the result changes the
recommendation.

**Option C does not fix this entry, and that was measured.** Five
verification-side statistics were scored on separating the 139 answerable
benchmark cases from the near-miss ones — the same treatment the eight
retrieval-side statistics got above:

| Verification statistic | Answerable lost for a full catch |
|---|---|
| Query terms present in the top evidence | 32 / 127 |
| IDF-weighted coverage of the top evidence | 29 / 127 |
| Top candidate's hybrid score | 33 / 127 |
| Corpus-known query terms present in the top evidence | 48 / 127 |
| …the same over the top three | 61 / 127 |

Verification is no better placed than retrieval to tell *"the corpus lacks
this subject"* from *"the question is phrased differently"*. Both are looking
at the same lexical evidence. The architectural intuition that sufficiency
belongs at verification was right; the expectation that moving it there would
decide the near-miss was not.

**What building it was worth anyway.** Two things, neither of them this entry:

1. **It closed a real hole.** `CERGateRuntime.evaluate` treated a claim as
   supported when a cited evidence id merely *existed*. A claim citing a real
   fragment with almost no relationship to what it asserts reached `PASS` — in
   a system whose entire purpose is that answers are grounded. Meanwhile
   `domains/re/domain_pack.yaml` had declared `require_evidence_for_claims:
   true` and `abstain_when_evidence_insufficient: true` from the beginning with
   nothing enforcing either: the same declared-but-unimplemented pattern D-09
   found in the audit evidence contract. `src/claim_verification.py` is the
   kernel mechanism; the threshold is the domain's half and lives in the policy
   file.

2. **It made this entry's mitigation concrete.** The mitigation recorded above
   was that a reviewer sees the evidence is about the wrong thing. That was a
   hope. The verifier now emits `unsupported_terms` — the parts of a question
   the cited evidence never mentions — so for *"What field strength is applied
   during a radiated immunity test?"* the report names `immunity`. Where the
   threshold cannot decide, the gap is at least on the page.

Near-miss abstention moved 3/8 → 4/8, at no cost to Evidence Recall@10 (0.914,
unchanged). The grounding floor is **0.25** against a measured answerable
minimum of 0.300.

> **Reverted 2026-08-26 — the fourth catch was a defect, not a mechanism.**
> D-14 found that every caller cited `evidence[0]` alone, so the verifier was
> judging each claim against a fraction of the evidence retrieved for it. The
> evidence looked thin because most of it was never handed over, and one
> near-miss fell below the floor for that reason. Citing what answers the claim
> removed the accident and the number with it: **the band is 3/8 again**, and
> the count of near-miss questions answered outright — the number D-11's risk
> statement is actually about — is 5/8.
>
> Restoring 4/8 by raising the floor was measured and rejected: it takes 0.70
> and costs 16.5% false abstention on answerable questions against 8.6% today.
> 8/8 is reachable at 0.85 and costs 46.8%. Which is this decision's own
> conclusion, arrived at from the other direction. It was deliberately not raised to chase this band: 0.30
catches two of five but leaves zero margin, and 0.32 starts costing answerable
cases. **The floor is not an abstention mechanism and must not be tuned as
one** — that is how the coverage floor became corpus-dependent in D-10.

**Revised recommendation.** A is implemented. C is built, worth keeping on its
own merits, and struck as a fix for this band. **B — a second retrieval method
with semantic similarity — is the only remaining option that can close it**,
and `RE_POC.md` already requires three retrieval methods, so it is scheduled
work rather than new scope. D stays rejected.

---

## D-12 — The kernel has no model dependency, and three of RE_POC's requirements need one

> **PARTIALLY DECIDED 2026-08-26 — option C is excluded, permanently.** Reaching
> a hosted model API is ruled out and now enforced by
> `tests/test_no_hosted_model_dependency.py`, not merely recorded. A, B and D
> stay open and will be decided by comparative trial against the real corpus.
> Notes at the end of this entry.

Raised 2026-08-25 while implementing the three retrieval methods `RE_POC.md`
requires. It is the decision D-11's revised recommendation runs into.

**What is declared versus what exists.** `domains/re/domain_pack.yaml` has
always said:

```yaml
retrieval_policy:
  allowed_modes: [bm25, vector, hybrid, graph, agentic]
  default_mode: hybrid
  reranker: cross_encoder
```

Three of those five modes and the reranker do not exist and never have. Until
this change `retrieve()` ignored the field entirely and hardcoded one blend, so
nothing selected a mode and nothing noticed. Selecting `vector` now raises
rather than silently returning the hybrid — a mode that resolves to something
other than what was asked for is how a declared capability gets believed.

**What was delivered without a dependency.** Three genuinely distinct,
deterministic methods: `bm25`, `trigram`, and `hybrid`. Measuring them produced
two findings that the previous code assumed the opposite of:

| method | R@1 | R@3 | R@10 | MRR |
|---|---|---|---|---|
| trigram only | 0.799 | 0.885 | 0.914 | 0.842 |
| hybrid 40/60 | 0.835 | 0.906 | 0.914 | 0.871 |
| **hybrid 60/40** (shipped) | 0.827 | 0.906 | 0.914 | 0.868 |
| BM25 only | 0.827 | 0.906 | 0.914 | 0.868 |

1. **Recall@10 cannot separate the methods.** Every blend scores 0.914, because
   the coverage floor and the abstention rules decide the result set and ranking
   rarely moves a document across k=10. The PoC's headline acceptance target is
   insensitive to the thing it asks for three of. The demo now reports R@1, R@3
   and MRR alongside it.
2. **At 60/40 the hybrid was BM25 with a decorative trigram term** — identical
   R@1 and MRR to three decimals. The trigram leg is not useless (alone it is
   measurably worse, so it carries real signal) — it was simply outvoted at the
   weight that had been chosen without measuring.

The weight was left at 0.6 rather than moved to the 0.4 that measured best:
0.835 against 0.827 over 139 cases is one case, and refitting a shipped default
to a one-case gain on the corpus it was measured against is exactly how the
D-10 thresholds became corpus-dependent.

**The decision.** Three `RE_POC.md` requirements cannot be met without a model:
a semantic retrieval method, the `cross_encoder` reranker, and "2 model
providers minimum". D-11's near-miss band needs the first of those. The kernel
currently depends on `pytest` and `pyyaml` and nothing else — no numpy, no
scipy, no torch — and every result in this repository is deterministic and
reproducible from a commit SHA, which is what
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` is built on.

| | Change | Consequence |
|---|---|---|
| A | Keep the kernel dependency-free; mark the vector/graph/agentic modes and the reranker as out of scope and remove them from `allowed_modes` | Honest and cheap. D-11's near-miss band stays open permanently, and three PoC requirements are formally dropped rather than pending |
| B | Add a local embedding model (`sentence-transformers` + `torch`, ~2 GB) | Deterministic and offline, so the evidence chain survives. Enormous dependency for a kernel that is currently two packages, and CI install time goes from seconds to minutes |
| C | Call a hosted model API for embeddings | Small dependency, and satisfies "2 model providers minimum" directly. Breaks determinism, needs network and a key in CI, and a historical run stops being reproducible — the evidence contract's central premise |
| D | Corpus-derived distributional similarity (LSA / truncated SVD in pure Python) | No dependency, deterministic, a genuinely different third method. But it cannot help D-11's near-miss: a term the corpus has never seen has no vector, which is the same `df == 0` the current rule already uses |

**Recommendation:** this one is genuinely the owner's, because it is a trade
between the PoC's stated scope and the evidence-reproducibility property the
whole governance design rests on. If pressed: **A for now, B when a domain
actually needs semantic recall**, and never C while
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` requires that a historical run be
reproducible from its SHA. D is worth building only if something other than
D-11 wants it — it was measured against D-11's problem and does not solve it.

**What it costs to be wrong.** Choosing A and being wrong means the PoC ships
without semantic recall and a class of question stays unanswerable — visible,
survivable, already recorded. Choosing C and being wrong is worse and quieter:
the evidence chain keeps producing GREEN decisions that can no longer be
re-derived from the commit they name, which is the failure the contract exists
to prevent.

---

## Audit note — 2026-08-26: what the reported numbers were hiding

A cold audit of this session's own work. Three findings, all fixed; recorded
because two of them are the failure this register keeps catching in other
people's code, committed here.

**1. The headline recall was inflated, and the margin was a third of what it
looked like.** Eleven of the 139 answerable benchmark cases have queries whose
every informative term already appears, word for word, in the document the
benchmark expects back. They are lookups by copy — they pass at 100% and cannot
really fail.

| | Evidence Recall@10 |
|---|---|
| the 11 self-answering cases | 1.000 |
| the other 128 | **0.906** |
| headline, as reported everywhere above | 0.914 |

Every claim of *"0.914, meeting the 0.90 target with margin"* in this register
and in PRs #26–#29 overstated it. The real margin is **0.006**, not 0.014 — one
case from missing the target.

Fixed by measurement rather than by a note: `evidence_recall_excluding_verbatim`
is computed on every run from the corpus itself (`query_is_verbatim_in_its_answer`
— derived, not hand-labelled, since a hand-labelled "this one is easy" flag
drifts the first time a document is edited), it is printed by the demo, and
**it is the figure the acceptance target is now gated on**, in both
`scripts/re_demo.py` and `scripts/evidence_gate.py`. Scoring the headline would
let a real regression hide behind eleven cases that cannot fail; a gate test
now proves exactly that scenario blocks.

**2. The test named for the D-10 signature could not detect D-10.**
`test_no_case_flips_back_and_forth_as_the_corpus_grows` required a case to flip
*twice* — the pass/fail/pass oscillation D-10 produced at 10 documents — and its
docstring claimed it pinned that defect directly. Re-introducing the exact
`_distinctive_terms` gate left it **green**: at 30 documents the same defect
produces a single flip, not an oscillation.

The suite as a whole did catch the re-introduced defect, through two other
tests, so this was false assurance rather than an open hole. It now asserts that
no case changes outcome at all across the distractor-volume series — measured
first: nothing differs on the current retriever, one case differs under the
re-introduced gate. Verified by re-introducing the defect and watching it fail.

**3. `_distinctive_terms` outlived its last caller, and `retrieve()`'s docstring
still described it as the live mechanism.** The method D-10 exists to have
removed was still in the file, uncalled, while the entry point told any reader
that candidate gating worked by literal distinctive-term hits. It has been
deleted and the docstring rewritten to describe the rules that actually run.

That is the same declared-but-not-implemented pattern D-09 found in the audit
evidence contract and D-12 found in `retrieval_policy.allowed_modes` — this time
in code written while fixing those.

**Two smaller items, not fixed, recorded so they are not rediscovered as news:**
`mean_reciprocal_rank` is computed over the top ten and is therefore MRR@10; the
value is identical to true MRR here because no case's correct document sits
beyond rank 10, so the number is right and only the name is loose. And the
`hybrid 40/60` row of D-12's table is not reproducible from the shipped code,
because `RETRIEVAL_MODES` has no 0.4 entry — it is the measured basis for
*not* changing the default, and a reader cannot re-derive it with `--mode`.

---

## Deferral — 2026-08-26: accuracy work waits for the real corpus

Recorded as a decision rather than a gap, because it changes what the open
entries are waiting on.

**The owner's sequencing.** The real RE source documents will be supplied
locally, after an internal handover. Accuracy work — retrieval tuning, the
near-miss band, threshold selection — happens against those, not against the
synthetic corpus. Nothing here is blocked on analysis; it is waiting on data.

**Why that is the right order and not a delay.** Every threshold this system
retrieves by is fitted to 30 synthetic documents written for this repository:

| constant | where | fitted to |
|---|---|---|
| `_COVERAGE_FLOOR` = 0.12 | `src/re_domain_pack.py` | 108 fragments |
| `_UNSEEN_TERM_CEILING` = 0.35 | `src/re_domain_pack.py` | 20 abstention cases in 3 bands |
| `RETRIEVAL_MODES["hybrid"]` = 0.6 | `src/re_domain_pack.py` | 139 answerable cases |
| `claim_grounding_floor` = 0.25 | `domains/re/domain_pack.yaml` | answerable minimum of 0.300 |

Tuning any of them further against synthetic documents would be fitting to
prose this repository wrote about itself. The measured `Recall@10` of 0.914 —
0.906 excluding the eleven self-answering cases — is a number about that
corpus, not about radiated emission engineering.

**What was built so the resumption is a command, not an excavation.** Until
now the sweeps that produced those four values lived in throwaway scripts, so
the tables in this register cited numbers nobody else could re-derive.
`scripts/calibrate_retrieval.py` now does all four against any corpus:

```
python3 scripts/calibrate_retrieval.py                      # in-tree
python3 scripts/calibrate_retrieval.py --corpus /path/to/docs \
                                       --benchmark cases.json
```

It changes nothing. It prints what each candidate value would buy and **exits
non-zero when a shipped constant is no longer the right choice for the corpus
it just measured** — so "our constants have gone stale" is a signal on the day
the corpus changes, rather than something noticed a milestone later. Verified
by deliberately staling two constants and watching it report them.

Two guards matter on the day real documents arrive:

- A benchmark whose expected documents are absent from the corpus is refused
  before any sweep runs. Pointing the tool at real documents while still
  holding the synthetic benchmark would otherwise report a catastrophic recall
  that reads as a model regression.
- The adversarial stability shapes are **not** applied to a real corpus. Those
  generators fabricate documents; running them over real ones would inject
  invented test reports into a measurement. The tool degrades to the corpus as
  provided and says so, rather than reporting a stability result it did not
  measure.

**What this means for D-11 and D-12.** Both stay open, and neither should be
forced now:

- **D-11** (near-miss abstention is not decidable by any lexical statistic) was
  measured over eight retrieval-side and five verification-side statistics on
  the synthetic corpus. Whether the wall is the same height against real
  documents — which have real vocabulary breadth, real near-misses, and real
  contradictions — is itself a question only the real corpus can answer.
- **D-12** (the kernel has no model dependency, and three PoC requirements need
  one) is unchanged by the corpus, but its urgency is: if D-11 turns out
  narrower against real documents, option A becomes more defensible; if wider,
  B becomes harder to avoid. Deciding it before the data is deciding it blind.

**The one thing that does not wait.** The evidence-reproducibility trade in
D-12's option C is not a data question. A hosted-model dependency breaks
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` whatever the corpus contains, and that
should be settled on its own terms rather than on how the accuracy numbers land.

---

### Decision — 2026-08-26: option C excluded, the rest go to trial

**C — a hosted model API — is excluded.** Not on cost or preference.
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` is built on a run being re-derivable from
the commit it names, and a hosted model breaks that whatever the corpus
contains: a GREEN decision citing a SHA stops being reproducible from that SHA,
which is precisely the failure the contract exists to prevent. That property
does not depend on how the accuracy numbers land, so it was settled without
waiting for the corpus.

**A, B and D stay open**, to be decided by comparative trial once the real RE
documents arrive. That is the right shape for them: A (stay dependency-free), B
(a local embedding model) and D (corpus-derived LSA) trade recall against
weight, and the size of that trade is exactly what synthetic documents cannot
tell us. `scripts/calibrate_retrieval.py` is the harness the comparison runs on.

**The exclusion is enforced rather than declared.** A decision living only in a
document is the pattern this register has caught three times now — D-09 found a
canonical contract enforced by nothing, D-12 itself found three retrieval modes
declared and absent, and the 2026-08-26 audit found a gating mechanism still
described in a docstring after its deletion. So:

- `tests/test_no_hosted_model_dependency.py` fails if anything under `src/` or
  `scripts/` imports a hosted-model SDK or a network transport. It parses the
  AST rather than grepping, so a mention in prose — of which these files have
  many — does not trip it, and an unusually formatted import cannot hide from
  it. A second test proves the guard can fail, against a synthetic file.
- `hosted_model_api_dependency` is in `CURRENT_SESSION_STATE.forbidden`, and the
  test asserts the two agree, so neither can go stale alone.

The property is currently **true, not aspirational**: nothing in the tree
performs any network access at all. `verify_artifact_sha256.py` takes a local
path — the CI runner downloads the artifact, the script only hashes it. The
guard therefore locks in something already achieved, so that changing it is a
deliberate act with a visible failure rather than an incidental import.

**What the guard deliberately does not block.** Option B is a *local* model. It
would add a heavyweight dependency and cost CI minutes, but it touches
reproducibility not at all — a local model produces the same output from the
same commit. It needs none of the forbidden imports and is not obstructed by
this test. If B is chosen after the trial, nothing here has to be reopened.

---

## D-13 — Routing existed as an interface and never as a capability

**Raised 2026-08-26. Closed the same day.**

Six Domain Packs now share one engine, and nothing chose between them.
`interfaces.RouteDecision` has been in the kernel since it was written —
carrying `domain`, `workflow_id`, `retrieval_modes` and a `requires_human` flag
— and no code path ever constructed one. Every entry point took the domain as
an argument. `scripts/run_domain.py` required `--domain`; the demos hardcoded
theirs. The capability the kernel appeared to have was an argument the caller
had to supply.

That makes **four** declared-and-unimplemented items this register has now
recorded: the audit evidence contract (D-09), three retrieval modes and a
reranker (D-12), a gating mechanism still described in a docstring after its
deletion (the 2026-08-26 audit note), and routing. The pattern is stable enough
to state as a rule: **an interface is not a capability, and a dataclass nobody
constructs is documentation.**

### Why this was answerable with invented documents

Retrieval accuracy and routing accuracy are different claims, and only one of
them needs real files.

Accuracy *within* a domain asks whether the right paragraph of a real report
comes back. Invented documents cannot support that claim, which is why the
2026-08-26 deferral holds RE tuning until the corpus arrives after handover.

Discrimination *between* domains asks whether battery vocabulary looks like
battery vocabulary and not like thermal vocabulary. That needs corpora about
*different things*, which invented ones are. So routing was measured now rather
than queued behind the handover — and it found two real defects that no
single-domain retrieval score could have exposed.

### Two biases, both found on invented corpora, both real

**Corpus size.** The obvious routing signal is vocabulary coverage: what share
of the question's informative terms does this corpus contain at all? It is
biased by size, because a larger corpus contains more ordinary English by
accident. RE, with 108 fragments against every other domain's nine, won **four
of six out-of-scope questions** on vocabulary alone — boiler feedwater, fibre
bend radius, concrete curing — for questions it had no documents about. The
replacement, `document_share`, is the mean share of a corpus's *fragments*
mentioning each query term: an incidental term in 1 of 108 fragments
contributes 0.009 whatever the corpus size, and a term the corpus is genuinely
about contributes far more.

**Tokenization quality — the surprising one.** Vocabulary coverage rewards the
pack that handles text *worst*. Asked "which build superseded FW-4.1.3", the
firmware pack keeps `fw-4.1.3` as a single token, which is correct. RE shatters
it into `fw`, `4`, `1`, `3`, and its corpus contains those bare numbers, so RE
scored 0.57 against firmware's 0.33 and won a firmware question. **The domain
that handled the identifier correctly lost precisely because it did.** Any
measure counting term hits has this property; `document_share` does not, and on
that same question firmware leads RE fourfold.

### What was built

- `RetrievalIndex.profile()` and `VocabularyProfile` in the kernel — three
  size-invariant readings of a corpus against one question.
- `GenericDomainPack.vocabulary_profile()` — the entire public surface routing
  needs, so the router never reaches into an index whose shape it should not
  know. An earlier draft declared a two-member `RoutablePack` protocol and then
  reached through `pack._ignore` and `pack._index` anyway, which would have
  made it the fifth interface here describing something other than the code.
  `tests/test_domain_router.py` routes a stub object implementing nothing else,
  so the protocol cannot quietly become a lie again.
- `src/domain_router.py` — `score = 0.6 · concentration + 0.4 · coverage`, with
  three outcomes: a domain, a refusal, or `requires_human`. The first code in
  this repository to construct a `RouteDecision`, and the first to reach the
  kernel's HOTL path.
- `scripts/run_domain.py` routes when `--domain` is omitted; exit code 3 means
  no loaded domain covers the question, which is a result and not an error.
- `scripts/routing_benchmark.py` and `templates/benchmark/cross_domain_routing_v0.1.json`.

### Measured

**30 of 32 (0.938)**, over all six domains loaded at once:

| band | result | target |
| --- | --- | --- |
| `clear` | 17/19 (0.895) | 0.85 |
| `shared_vocabulary` | 7/7 (1.000) | 0.85 |
| `out_of_scope` | 6/6 (1.000) | 1.00 |

`out_of_scope` is held to 1.0 and the others are not, deliberately. Missing an
in-scope question yields a refusal or a referral, which a reader sees. Naming a
domain for a question no corpus covers yields a confident answer from the wrong
documents, which nobody sees.

Both remaining misses are recorded rather than tuned away:

- **RT-006**, "which interface material tolerates the larger gap variation" — a
  thermal question scoring 0.075, because it names nothing thermal-specific: no
  unit, no identifier, no term the thermal corpus is about. No floor separates
  it from a question about boiler feedwater and none is claimed to. It is
  refused, which is the better of the two available errors.
- **RT-017**, "which build superseded FW-4.1.3" — firmware 0.19, RE 0.15, so it
  is referred to a person rather than answered on a 0.04 margin. Firmware is
  still named first. Counted as a miss because a router that referred
  everything would otherwise score perfectly.

### The benchmark was wrong, and that is recorded rather than corrected quietly

Two cases were labelled `ambiguous` — spanning two domains, where the right
answer is a person. Neither survived contact with the corpora.

RT-031 ("cell temperature rise … pack thermal runaway") *reads* as thermal and
battery both. The thermal corpus contains no occurrence of cell, pack or
runaway; only `temperature` is shared. It is a `shared_vocabulary` case and
routes to BATTERY at 0.24 against THERMAL's 0.10. RT-032 ("fixture wear …
dimensional capability") names four terms the manufacturing corpus has and
nobody else does, and routes to MANUFACTURING at 0.50 against BATTERY's 0.00.

The root cause is structural: **the six example corpora are subject-disjoint** —
no two describe the same artefact or event — so no genuinely ambiguous question
exists over them. The labels came from the wording, which is the same error as
writing a benchmark query by paraphrasing its own answer, and it is the fourth
time in this register that something was asserted without being measured.

Both were relabelled to their measured domains, the `ambiguous` band was
removed, and `removed_band` in the benchmark file records the cases, the
reasoning and the date. **A label corrected silently is indistinguishable from a
label tuned to make a score look better**, and this repository has no way to
tell those apart after the fact except by having written it down.

The `requires_human` path is covered instead by `tests/test_domain_router.py`,
over two corpora built to overlap on purpose — one incident report filed under
two document numbers, so the margin between them is exactly zero and cannot
drift as prose is edited. An earlier version of that fixture wrote two *similar*
corpora by hand and landed at 0.064, outside the 0.05 band: it asserted
ambiguity on text that was not ambiguous. Testing a threshold with prose tuned
by eye measures the prose.

### What this does not settle

Routing picks the corpus. It says nothing about whether the answer from that
corpus is right, which is D-11 and D-12 territory and still waits on the real
documents. A question routed correctly to a domain whose corpus cannot answer
it still reaches the claim verifier and the CER gate, and is still refused
there — the two mechanisms are independent and both run.

The thresholds are fitted to the example corpora, exactly as the retrieval
thresholds are fitted to the synthetic RE corpus. `MINIMUM_SCORE = 0.15` sits
between the highest out-of-scope score measured (0.102) and the lowest in-scope
one (0.191); a test asserts that band so the constant cannot drift out of the
evidence that justifies it. Both constants must be re-derived when real corpora
of markedly different sizes are loaded together.

---

## D-14 — What a claim cites, what its confidence is worth, and what a number is measured against

**Raised and closed 2026-08-26**, from a RAG-practitioner audit of the retrieval
path. Three defects, each measured before it was touched, and one of the fixes
uncovered a fourth that had been unreachable since it was written.

### 1 — Both callers cited `evidence[0]` and threw the rest away

`re_demo.py`, `run_domain.py` and `re_demo.py --report` each built their own
`Claim`, and all three cited the top fragment alone. The verifier grounds
against `claim.evidence_ids`, so an answer resting on two fragments could not
be grounded however well retrieval had done.

The demonstration, run against the shipped tree:

```
Q: What was the EUT-7 132 MHz level before mitigation and how far above the limit was it?
CER: PASS   grounding 0.375   unsupported: ['level','befor','mitigation','far','abov']
   0.655 DOC-RE-001/REV-A  38.2 dBuV/m ... 2.6 dB           <- the only citation
   0.606 DOC-RE-001/REV-B  Retest of EUT-7 after mitigation  <- retrieved, discarded
   0.518 DOC-RE-001/REV-B  dropped to 31.4 dBuV/m            <- retrieved, discarded
```

`mitigation` is reported as unsupported by evidence the system is holding.
`unsupported_terms` is what D-11 relies on to put a gap in front of a reviewer,
and it was saying something false.

Fixed by `ClaimVerifier.select_citations`: a greedy set cover over the claim's
informative terms, fragments taken in rank order and kept only when they supply
a term no kept fragment supplied. Not "cite all ten" — a citation that supports
nothing is padding, and the fix for an under-cited claim must not be an
over-cited one. Measured: 2.40 fragments cited per answered case out of 10
retrieved.

Claim construction now lives in `GenericDomainPack.build_claim`, one definition
in the kernel. Three copies of one definition is the pattern this register has
recorded four times, and the third copy had already drifted: `--report` gated
without passing a verification report at all, so it rendered CER decisions that
had never checked grounding.

### 2 — `confidence` was structurally pinned and could not inform

`Claim.confidence` carried the retrieval score. `rank` normalizes BM25 against
each query's own maximum, so the top fragment's lexical component is **always
exactly 1.0** (measured mean 0.9999) and the score is `0.6 + 0.4·jaccard` by
construction. Over 127 answerable cases it spanned 0.642 to 0.815, mean 0.693,
sd 0.029.

Candidates measured by how well each separates a correct top hit from a wrong
one (Cohen's d, n=115 correct / 12 wrong):

| candidate | correct | wrong | gap | d |
| --- | --- | --- | --- | --- |
| **coverage (IDF mass)** | 0.6198 | 0.4667 | +0.1531 | **0.87** |
| coverage × margin | 0.7435 | 0.5149 | +0.2286 | 0.87 |
| margin, rank 1 − rank 2 | 0.1814 | 0.0970 | +0.0844 | 0.64 |
| raw BM25 | 17.98 | 15.00 | +2.98 | 0.53 |
| the shipped score | 0.6939 | 0.6822 | +0.0117 | 0.40 |

Confidence is now the IDF-weighted share of the question the cited evidence
accounts for: bounded in [0, 1], comparable between queries, twice the
separation, and a sentence a reader can act on. Coverage × margin scores
identically and is more machinery for it, so it was not taken.

A correction to how this was first written up: the shipped score was described
in the audit as carrying "essentially no signal". d=0.40 is a small but real
effect. The defect is that its absolute value is uninterpretable and it is
beaten better than two to one, not that it is noise.

### 3 — Every recall figure was read against a floor of zero, and the floor is 0.356

| | random | measured | share of available headroom |
| --- | --- | --- | --- |
| Evidence Recall@10 | **0.356** | 0.906 | 85.4% |
| Recall@1 | **0.043** | 0.827 | 81.9% |

Drawing ten fragments uniformly from 108 reaches 4.9 of the corpus's 25
documents, so a third of the headline is paid before retrieval does anything.
0.906 against a floor of 0.356 is a different sentence from 0.906 against zero,
and the acceptance target of 0.90 is +0.54 over a coin rather than +0.90. This
also settles why Recall@10 could not separate the retrieval methods, which the
2026-08-26 note attributed to the metric being insensitive: it is insensitive
*because* it starts a third of the way up.

Reported, never gated on — the target is what the RE PoC specifies and this
does not move it.

**And it is not a recall.** Every case has exactly one gold document, so the
score is 0 or 1 with no partial set to recover: it is a hit rate.
`evidence_recall_at_10` is kept as the name the acceptance contract and
`evidence_gate.py` were written against, with `hit_rate_at_10` reporting the
same number under the name it earns. A test asserts the gold sets are all size
one, so if that ever stops being true the alias is revisited rather than
quietly becoming wrong.

### 4 — The fix reached a gate rule that had never been reachable

`cer_runtime` flagged `CONTRADICTORY_EVIDENCE` when a claim cited two or more
evidence items whose texts differed. That is a test for **plurality**, not
contradiction — two paragraphs corroborating each other are also two distinct
texts — and it had never fired, because every caller cited exactly one item.
With citations fixed it fired on **103 of 139** answerable questions.

The replacement was to be narrower: the same document cited at a revision and
at its retest, which is the one conflict decidable from a citation list. It was
built, measured, and **rejected on the measurement**: it referred 38 of 139
answerable questions, and **15 of those were `revision_comparison` cases** —
"how did the peak change between the original test and the retest" — where two
revisions in view is precisely what was asked for. A rule that refers the
question it was built to answer is not narrow enough to keep.

Separating those needs one of two things the system does not have:

- the question's **time scope**, which is a semantic judgement — D-11 again, in
  a new place;
- a corpus that declares **which revision supersedes which**. `revision_id` is
  an opaque string; nothing in `REV-B` says it replaces `REV-A`.

So nothing gates on it. The verifier reports `conflicting_revisions` and
`run_domain.py` prints it, because the reader needs to know regardless:

```
NOTE: DOC-RE-001 is in evidence at REV-A and REV-B; these may not agree,
      and nothing here records which supersedes which
```

The check reads the **retrieved** set, not the cited one. Scoped to citations
it missed its own headline example: asked what EUT-7 measured at 132 MHz,
retrieval returns 38.2 dBuV/m (REV-A) and 31.4 dBuV/m (REV-B), and REV-B
supplies no term REV-A had not, so the selector correctly drops it and the
conflict went with it. A retest that disagrees in *numbers* while agreeing in
*words* is invisible to any lexical selector, which is the whole reason the
check exists.

**This leaves a decision that is not the system's to make.** Whether a query
should prefer the newest revision, return both and mark the disagreement, or
refer to a person when the question carries no time scope is a working rule for
how RE documents are managed. It waits for the internal handover, together with
whether the corpus can carry supersession metadata at all.

`FactoryRuntime.evaluate_gate` also turned out not to forward `verification`,
so the grounding and conflict checks were unreachable through the runtime
wrapper entirely. Fixed with the rest.

### What it cost

| | before | after |
| --- | --- | --- |
| Evidence Recall@10 (earned) | 0.906 | 0.906 |
| Recall@1 / MRR | 0.827 / 0.868 | 0.827 / 0.868 |
| `subject_outside_domain` held | 5/5 | 5/5 |
| `entity_absent_from_corpus` held | 7/7 | 7/7 |
| **`near_miss_domain_subject` held** | **4/8** | **3/8** |
| answerable questions answered | 127/139 | 127/139 |

Retrieval is untouched, so every retrieval number is identical. The one change
is the fourth near-miss abstention, and it was never a capability: the record
already said it came from "claim verification catching one more as a side
effect: where the cited evidence supplies too little of what the question
asks." The evidence only *looked* thin because most of it was never handed to
the verifier. Abstaining because you failed to cite your own evidence is not
abstention — the same class as the headline recall inflated by eleven
self-answering cases, a number real as arithmetic and false as a claim.

Restoring 4/8 by raising the grounding floor was measured and rejected: it
takes a floor of 0.70 and costs 16.5% false abstention against 8.6% today. 8/8
is reachable at 0.85 and costs **46.8%** — nearly half of all answerable
questions refused, which is D-11's point stated in numbers.

`abstention_by_band` now also reports `silently_answered`. `held` counts BLOCK
only, deliberately — collapsing BLOCK and REVIEW would let a system that
referred everything score perfectly — but the risk D-11 describes is the pack
*answering* a question it should refuse, and that number was not being
reported at all.

### Still open from the same audit, not fixed here

Measured, recorded, not addressed: the hybrid blend contributes 6.5 : 1 in
BM25's favour at rank 1 and is close to a no-op (RRF is the dependency-free
alternative); chunking has 0% overlap and splits mid-sentence on `;`, which
produced the orphan fragment *"use an isolated ground strap if this is
suspected"*; there is no de-duplication of near-identical fragments; and there
is no acronym or alias table, so adding "equipment under test" to a query
changes which revision comes back. All four are retrieval-quality work that
should be measured against the real corpus rather than fitted to this one.


---

## D-15 — Five of the seven PoC acceptance targets are neither met nor unmet

> **OPEN, raised 2026-08-30.** Needs a person: the options differ in what the
> project promises, not in what it can build.

`docs/RE_POC.md` states seven acceptance targets. `scripts/re_demo.py` prints
`acceptance targets MET` and `scripts/evidence_gate.py` takes that flag as the
pass condition for the M1 evidence step. The flag is two conditions:

```python
# scripts/re_demo.py, in score_benchmark()
"meets_acceptance_targets": recall_ok and decidable_ok,
```

Measured on the current tree, against the seven as written:

| target | stated | measured | in the flag |
| --- | --- | --- | --- |
| Evidence Recall@10 | ≥ 0.90 | 0.914 headline, 0.906 earned | yes |
| Citation Accuracy | ≥ 0.95 | not computed | no |
| Critical Claim Unsupported Rate | ≤ 0.02 | not computed | no |
| Negative-case Abstention | ≥ 0.90 | **0.75** | no — a different rule is |
| Revision correctness | ≥ 0.95 | not computed | no |
| Trace completeness | = 100% | not computed | no |
| Domain Pack load without kernel fork | PASS | PASS | via its own test |

Verified rather than inferred: the `acceptance` block of `re_demo.py --json`
carries no key containing `citation`, `unsupported`, `revision` or `trace`, and
the only occurrences of `0.95` or `0.02` anywhere under `src/` and `scripts/`
are a demo claim's confidence value. The mechanisms exist — citation building,
claim verification, HOTL, trace, run manifest are all real and tested. What
does not exist is any of them being computed as a number against its threshold.

The abstention row is the sharper one, because it is measured and reported and
still does not gate. The target is 0.90 over negative cases; the figure is 0.75
(15/20). The flag instead requires the two *decidable* bands to be perfect,
which they are (5/5 and 7/7), and excludes `near_miss_domain_subject` (3/8) as
D-11's known limitation. That exclusion is defensible and well documented. What
is not defensible is that the summary line does not say the target it names was
not met on its own terms.

**Why it needs a person.** Nothing here is a measurement problem. Four of the
five could be implemented; whether they *should* be, at PoC scale, against a
synthetic corpus, before the real documents land, is a scope call. So is
restating the abstention target against the band rule that replaced it.

- **A — Measure them.** Implement the four missing metrics and gate on all
  seven. Most honest, and the most work; three of the four (citation accuracy,
  unsupported rate, revision correctness) need labelled ground truth the
  benchmark does not currently carry, so this is benchmark work before it is
  code work.
- **B — Restate the targets.** Reduce `RE_POC.md` to what the PoC actually
  gates, and record the rest as M2/M3 acceptance rather than M1. Cheapest, and
  it makes the "MET" claim true as written.
- **C — Keep both, and disclose.** Leave the targets, leave the gate, and have
  the tool report which targets it checks and which it does not. Costs little
  and removes the misreading, but leaves the register carrying a target nobody
  intends to measure at PoC scale.

**Cost of being wrong.** Low if decided, high if left. The receiving team reads
"M1 meets every PoC acceptance target" as a statement about seven numbers. Five
of them are not measurements that failed — they are measurements that were
never taken, which is a different thing and reads identically from outside.

**Deliberately not pre-empted.** The 2026-08-30 session implemented the three
handover blockers around this and left the flag and the output untouched:
changing what the tool reports is this decision's implementation, not its
preparation.

---

## D-16 — `RE_POC.md` requires two model providers and the kernel may have none

> **OPEN, raised 2026-08-30.** Two canonical documents contradict each other and
> neither records it.

`docs/RE_POC.md`, under *PoC target*:

> - 2 model providers minimum

D-12 option C — a hosted model API — was excluded permanently by owner decision
on 2026-08-26 and is enforced by `tests/test_no_hosted_model_dependency.py`.
Nothing under `src/` or `scripts/` performs network access of any kind. So the
PoC target as written is unreachable by the route anyone would take to reach it,
and has been since the day the exclusion was recorded. Neither document mentions
the other.

**What is still open underneath it.** D-12 option B — a model running locally —
is not excluded, and does not affect re-derivation from a commit. Two local
models would satisfy "2 model providers" on a literal reading. Whether that is
what the target meant is the question: the target sits next to "3 retrieval
methods minimum" in a list about breadth of comparison, which suggests it meant
*independent* providers for generation and verification (`docs/MDD.md`: "may use
different providers when risk justifies it") rather than two of anything.

- **A — Strike the target.** The PoC is provider-free by decision; say so, and
  move multi-provider comparison to M5 where method ensemble already lives.
- **B — Reinterpret it as two local models.** Keeps the target and satisfies it
  within D-12 option B. Adds a heavyweight dependency and needs D-11's cost
  measured first, which is already sequenced behind the real corpus.
- **C — Leave it and record the conflict.** Cheapest, and the worst of the
  three: it is what the repository has now, and it is how a target survives
  four months without anyone noticing it cannot be met.

**Cost of being wrong.** Contained, but it is the pattern this codebase keeps
paying for — a document declaring something that is not so. It is also the
first thing an outside reviewer would find, because the two statements sit two
directories apart and contradict each other flatly.

**Related, already done.** The guard enforcing the exclusion did not cover the
provider most likely to be reached for: `HOSTED_MODEL_SDKS` listed `vertexai`
and not `google`, so `import google.generativeai` and `from google import genai`
both passed. Closed 2026-08-30, with a test proving option B's local-model
imports still pass — widening the guard must not quietly decide D-12.
