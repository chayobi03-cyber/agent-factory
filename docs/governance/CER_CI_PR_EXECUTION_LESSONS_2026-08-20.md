# CER / CI PR Execution Lessons — 2026-08-20

## Purpose

Capture reusable rules discovered while proving the PR #11 synthetic multi-domain workflow with primary GitHub Actions evidence.

## Lessons learned

### 1. PR CI must be checked from the base-branch perspective

A workflow change on the PR head is not sufficient evidence that the PR event can execute. Before diagnosing "no Actions Run", inspect the workflow definition that GitHub will use for the PR's base branch.

**Rule:** For every PR-based validation, verify both:

- the PR head workflow definition;
- the workflow definition present on the PR base branch.

The base branch is the first CI trigger authority to inspect when a PR has no observed run.

### 2. Mergeability is a pre-execution gate

A PR with `mergeable_state=dirty` can block or invalidate the intended PR execution path. CI trigger analysis must not stop at workflow YAML; PR mergeability must be checked explicitly.

**Rule:** Before waiting for or interpreting a PR Actions run, record:

- base SHA;
- head SHA;
- mergeable state;
- whether the branches have diverged.

If the PR is dirty, resolve the branch state before using the PR as runtime evidence.

### 3. Primary evidence is always bound to one exact SHA

A previous successful run must never be reused as proof for a later HEAD. Documentation-only or governance-only commits still create a new execution identity requirement.

**Rule:** Runtime-GREEN is allowed only when:

`observed_run.head_sha == current_pr_head_sha`

and the run itself completed successfully.

### 4. Static verification and runtime verification are separate

The Domain Matrix code and tests can be statically correct while no runtime evidence exists. Conversely, an artifact created with `if: always()` is not proof that the corresponding step executed successfully.

**Rule:** Evidence review must distinguish:

- workflow configuration;
- test/code inspection;
- actual step execution;
- artifact existence;
- artifact digest verification.

### 5. Evidence artifact existence is necessary but not sufficient

The final successful run produced both `factory-kernel-machine-evidence` and `domain-matrix-evidence`. Their existence became meaningful only after the corresponding execution steps were confirmed successful and the artifact was tied to the same run and SHA.

**Rule:** An evidence artifact may support GREEN only when it is linked to the same successful primary run and exact target SHA.

## Automation requirements

Future session-start / PR validation should automatically execute this sequence before deeper debugging:

```text
resolve PR
→ read base/head SHA
→ check base/head workflow configuration
→ check mergeability
→ query Actions by exact HEAD SHA
→ if absent, diagnose event/branch topology
→ if present, verify job/step results
→ verify artifacts and digests
→ only then classify GREEN
```

## Result from the 2026-08-20 run

The final validated execution used:

- PR: #11
- execution run: `32310894693`
- job: `96253482547`
- validated execution HEAD: `67e5d936d979021fd615c9d7ce788039f276904a`
- CER RC-01..RC-08: PASS
- Factory Demo: PASS
- Domain Matrix: RE/EMI/CST/ESD 4/4 PASS
- Deterministic Kernel Harness: 10/10 PASS
- OPRO Baseline E2E: PASS
- pytest: PASS
- Domain Matrix evidence artifact: `9386393619`
- machine evidence artifact: `9386393356`

This evidence established the PR as runtime-GREEN for that exact execution SHA.
