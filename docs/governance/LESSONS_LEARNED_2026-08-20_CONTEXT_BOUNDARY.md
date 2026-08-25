# Lessons Learned — Project Context Boundary / Repository Integrity

Date: 2026-08-20  
Repository: `chayobi03-cyber/agent-factory`  
Branch: `p0/opro-baseline`

## 1. Problem

Recent work showed a credible risk of project-context contamination between AgentFactory and the separate Investment repository. The failure mode is not simply an incorrect filename; it is the possibility that governance, HOTL rules, session state, workflow assumptions, or success criteria from another project can be treated as canonical inside AgentFactory.

The canonical M2 transition checkpoint for this forensic review is:

`41259e233e5273ad2fe1577e71935702956476b1`

The branch was ahead of that checkpoint, so remediation was based on an explicit descendant diff rather than assumptions about recent changes.

## 2. Lessons Learned

### 2.1 Project identity must be explicit and machine-checkable

Project, repository, branch, and governance namespace are related but distinct concepts. They must not be collapsed into a filename or conversational context.

Required identity model:

```text
PROJECT_ID
REPOSITORY
ACTIVE_BRANCH
GOVERNANCE_NAMESPACE
```

A mismatch must result in `REVIEW_REQUIRED` or `BLOCKED`, never inferred continuation.

### 2.2 HOTL terminology is not contamination evidence

A file or rule mentioning HOTL must not be classified as wrong solely because it contains HOTL terminology. HOTL is a legitimate AgentFactory architectural/governance concept.

Every suspected change must be classified by ownership:

- AgentFactory-native
- generic reusable engineering governance
- Investment-specific contamination
- mixed-purpose
- unclear / `REVIEW_REQUIRED`

Content ownership, intent, and scope matter more than filenames or keywords.

### 2.3 Audit commits at file and hunk level

A commit can contain both valid AgentFactory changes and unrelated project-specific changes. Therefore commit-level revert is not the default remediation method.

Required forensic sequence:

```text
commit
  -> file diff
  -> hunk intent
  -> ownership
  -> remediation decision
```

Prefer minimal corrective changes over history rewriting.

### 2.4 RCA must include the detection failure

Root-cause analysis must answer two separate questions:

1. Why did the wrong project context enter the repository?
2. Why was it not detected by existing review, regression, CI, or governance controls?

The second question is a control-gap analysis and is required for a durable fix.

### 2.5 Repository governance state is not runtime evidence

Governance files, session state, handoff documents, and declared statuses do not substitute for primary runtime evidence.

When execution is being claimed, the evidence chain must be independently grounded in:

```text
TARGET SHA
  -> RUN
  -> JOB
  -> LOG
  -> ARTIFACT
  -> DIGEST
```

No primary evidence means no inferred `PASS` / `GREEN`.

### 2.6 M2 preservation is separate from M2 execution

Repository-integrity remediation must preserve legitimate M2 contracts, readiness matrices, schemas, fixtures, and regression definitions.

Their existence does not authorize:

- historical performance execution;
- OOS;
- optimization;
- stress;
- Monte Carlo.

Cleanup and project-audit work must not silently become an execution session.

### 2.7 Project objectives must be audited independently of local implementation progress

A repository can contain many technically correct artifacts while still drifting from its original product objective.

Therefore project review must periodically evaluate:

```text
Project Objective
  -> Required Outcomes
  -> Milestones
  -> Workstreams / Tasks
  -> Evidence of Completion
  -> Current Status
  -> Gaps / Risks
  -> Next Actions
```

Implementation volume is not progress by itself. A milestone is complete only when its intended outcome is evidenced.

### 2.8 Governance rules must have clear ownership

A permanent rule should identify its owner scope. Generic reusable rules may be shared; project-specific rules must remain scoped to their project.

For AgentFactory:

```text
AgentFactory governance = canonical
Investment governance = external boundary reference only
```

External project names may appear only when documenting the boundary itself or an explicitly scoped external dependency.

## 3. Permanent Rules

### Rule 1 — Context Guard

Every AgentFactory session must establish:

```text
CURRENT PROJECT
    = EXPECTED REPOSITORY
    = ACTIVE BRANCH
    = GOVERNANCE CONTEXT
```

Mismatch => `REVIEW_REQUIRED` or `BLOCKED`.

### Rule 2 — Ownership Classification

Before changing governance/workflow/state artifacts, classify their ownership explicitly. HOTL terminology alone is never sufficient evidence of contamination.

### Rule 3 — Minimal Remediation

Suspected contamination must be isolated and corrected with the smallest safe change. `git reset --hard`, force-push, and history rewrite are not first-line responses.

### Rule 4 — Evidence Boundary

State/documentation never substitutes for primary execution evidence.

### Rule 5 — Bounded RCA

Material failures use at most three diagnosis/remediation cycles before escalation to architecture, specification, tooling, or human review.

### Rule 6 — Project Audit Gate

Before entering a major execution milestone, periodically audit:

1. project objective;
2. required outcomes;
3. milestone definition;
4. current task inventory;
5. actual completion evidence;
6. unresolved gaps;
7. next action priorities.

If implementation work cannot be traced to a declared objective or milestone, classify it as `REVIEW_REQUIRED` until ownership is clarified.

## 4. Preventive Controls

The preferred permanent controls are:

1. repository identity guard;
2. project-context guard;
3. governance namespace guard;
4. session-start context check;
5. CI repository/context verification;
6. cross-project contamination scan using provenance/content rather than filename-only matching;
7. regression coverage for the context boundary;
8. periodic project-objective / milestone audit.

Before adding a new rule, existing AgentFactory governance must be checked for duplication or conflict.

## 5. Remediation Principle

```text
identify
-> classify
-> preserve valid work
-> isolate contaminated change
-> minimal corrective change
-> regression
-> primary evidence verification
```

If a mixed-purpose commit cannot be safely separated, escalate for human review rather than performing a blind revert.

## 6. RCA Escalation Rule

Use up to three remediation cycles:

```text
Cycle 1: identify -> cause -> fix -> verify
Cycle 2: residual issue -> reanalyse -> strengthen -> verify
Cycle 3: recurrence risk -> final control -> verify
```

If the issue remains unresolved after cycle 3, escalate. Do not continue blind retries.

## 7. Session Boundary

This lesson does not authorize:

- OPRO promotion;
- GEPA implementation;
- audited OPRO baseline change;
- RE domain implementation;
- M2 historical execution;
- OOS;
- optimization;
- stress;
- Monte Carlo.

The audited OPRO baseline remains immutable:

`20a54b92aad0857f75c6200d984b13098c6f4927`

## 8. Expected Outcome

The durable goal is not to delete everything related to HOTL. The goal is to establish clear ownership of every governance artifact, make cross-project context contamination detectable before it becomes canonical repository state, and periodically verify that implementation remains aligned with the AgentFactory product objective and milestone plan.
