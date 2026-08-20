# Lessons Learned — Project Context Boundary / Repository Integrity

Date: 2026-08-20  
Repository: `chayobi03-cyber/agent-factory`  
Branch: `p0/opro-baseline`

## 1. Problem

Recent work showed a credible risk of project-context contamination between AgentFactory and the separate Investment repository. The immediate failure mode is not simply an incorrect file; it is the possibility that governance, HOTL rules, session state, or workflow assumptions from another project can be treated as canonical inside AgentFactory.

The canonical M2 transition checkpoint for this forensic review is:

`41259e233e5273ad2fe1577e71935702956476b1`

The current branch was observed to be ahead of that checkpoint, so remediation must be based on an explicit descendant diff rather than assumptions about recent commits.

## 2. Lessons

### 2.1 Project identity must be explicit

Project, repository, branch, and governance namespace are related but distinct concepts. They must not be collapsed into one identity check.

Required identity model:

```text
PROJECT_ID
REPOSITORY
ACTIVE_BRANCH
GOVERNANCE_NAMESPACE
```

A mismatch must result in `REVIEW_REQUIRED` or `BLOCKED`, not an inferred continuation.

### 2.2 HOTL is not itself evidence of contamination

A file or rule mentioning HOTL must not be classified as wrong solely because it contains HOTL terminology. HOTL can be a legitimate AgentFactory architectural or governance concept.

Every suspected change must be classified as:

- AgentFactory-native
- generic reusable engineering governance
- Investment-specific contamination
- mixed-purpose
- unclear / REVIEW_REQUIRED

### 2.3 Audit commits at file and hunk level

A commit can contain both valid AgentFactory changes and unrelated project-specific changes. Therefore commit-level revert is not the default remediation method.

The required forensic sequence is:

```text
commit
  -> file diff
  -> hunk intent
  -> ownership
  -> remediation decision
```

Minimal corrective changes are preferred over history rewriting.

### 2.4 RCA must include detection failure

Root-cause analysis must answer two separate questions:

1. Why did the wrong project context enter the repository?
2. Why was that context not detected by the existing review, regression, CI, or governance controls?

The second question is a control-gap analysis and is required for a durable fix.

### 2.5 State is not execution evidence

Governance files, session state, handoff documents, and declared statuses do not substitute for primary runtime evidence. A current-SHA status must be backed by the actual run/job/log/artifact/digest chain when execution is being claimed.

Therefore:

```text
state/documentation != primary execution evidence
```

No evidence means no inferred `PASS` / `GREEN`.

### 2.6 M2 preservation must be separated from M2 execution

During repository-integrity remediation, legitimate M2 contracts, readiness matrices, schemas, fixtures, and regression definitions should be preserved. Their existence does not authorize historical experiment execution, OOS, optimization, stress, or Monte Carlo work.

This separation prevents cleanup work from accidentally becoming an M2 execution session.

## 3. Preventive Controls

The preferred permanent controls are:

1. repository identity guard
2. project-context guard
3. governance namespace guard
4. session-start context check
5. CI repository/context verification where practical
6. cross-project contamination scan using provenance/content rather than filename-only matching
7. regression coverage for the context boundary

Before adding a new rule, existing AgentFactory governance must be checked for duplication or conflict.

## 4. Remediation Principle

Do not use `git reset --hard`, force-push, or history rewrite as the first response to suspected contamination.

Preferred sequence:

```text
identify
-> classify
-> preserve valid work
-> isolate contaminated change
-> minimal corrective commit
-> regression
-> primary evidence verification
```

If a mixed-purpose commit cannot be safely separated, escalate for human review rather than performing a blind revert.

## 5. RCA Escalation Rule

Use up to three remediation cycles:

```text
Cycle 1: identify -> cause -> fix -> verify
Cycle 2: residual issue -> reanalyse -> strengthen -> verify
Cycle 3: recurrence risk -> final control -> verify
```

If the issue remains unresolved after three cycles, escalate to architecture, specification, tooling, or human review. Do not continue blind retries.

## 6. Session Boundary

This lesson does not authorize:

- OPRO promotion
- GEPA implementation
- audited OPRO baseline change
- RE domain implementation
- M2 historical execution
- OOS
- optimization
- stress
- Monte Carlo

The audited OPRO baseline remains immutable:

`20a54b92aad0857f75c6200d984b13098c6f4927`

## 7. Expected Outcome

The durable goal is not to delete everything related to HOTL. The goal is to restore clear ownership of every governance artifact and make cross-project context contamination detectable before it becomes canonical repository state.
