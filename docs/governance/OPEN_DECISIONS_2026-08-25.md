# Open Decisions — 2026-08-25

Everything below needs a person. Nothing here is blocked on analysis: each item
states what was verified, what the options are, and what it costs to be wrong.

Trunk at time of writing: `main`, `gate: FACTORY_KERNEL_GREEN`,
`audited_baseline_sha: 20a54b92aad0857f75c6200d984b13098c6f4927`.

**Status:** D-01 through D-10 resolved 2026-08-25. **D-11 is open** — raised by
the M1 corpus scale-up, which is the first thing large enough to measure it.
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

---

## D-11 — A lexical retriever cannot abstain on a near-miss, and no threshold changes that

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
